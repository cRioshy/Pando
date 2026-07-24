"""Phase 2 tests for the interactive Pandorick Knowledge Graph backend."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from adapters.control_center_adapter import ControlCenterAdapter
from config import PlatformConfig
from learning_graph.knowledge_graph_builder import KnowledgeGraphBuilder
from learning_graph.knowledge_graph_models import stable_knowledge_edge_id, stable_knowledge_node_id
from learning_graph.knowledge_graph_service import KnowledgeGraphService
from orchestrator import NoopAdapter, Orchestrator
from shared_state import SharedState
from web.api import WebControlServer


def get_json(url: str) -> dict:
    """Read one JSON response from the local test server."""

    with urllib.request.urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def sample_record(symbol: str = "BTCUSDT", market_type: str = "crypto", direction: str = "LONG") -> dict:
    """Return one normalized Pandorick source record."""

    return {
        "received_at": "2026-07-21T10:00:00+00:00",
        "source_event_id": f"event-{symbol}-{direction}",
        "event_type": "CRYPTO_ANALYSIS_FINISHED" if market_type == "crypto" else "STOCK_ANALYSIS_FINISHED",
        "source": market_type,
        "market_type": market_type,
        "symbol": symbol,
        "direction": direction,
        "probability": 72.5,
        "source_timestamp": "2026-07-21T10:00:00+00:00",
        "payload": {
            "project_root": "C:\\Users\\Admin\\Desktop\\PandorickKi",
            "telegram_bot_token": "secret-token",
            "indicators": {
                "ema20": 100,
                "rsi": 52,
                "macd": 0.2,
                "volume": 1200,
            },
            "raw_result": {
                "calculation": "secret",
                "weight": 0.4,
            },
        },
    }


class KnowledgeGraphPhase2Test(unittest.TestCase):
    """Verify the read-only Knowledge Graph layer."""

    def test_stable_ids_are_deterministic(self) -> None:
        first = stable_knowledge_node_id("crypto", "crypto", "BTCUSDT")
        second = stable_knowledge_node_id("crypto", "crypto", "BTCUSDT")

        self.assertEqual(first, second)
        self.assertEqual(
            stable_knowledge_edge_id(first, "uses", second),
            stable_knowledge_edge_id(first, "uses", second),
        )

    def test_builder_creates_required_node_and_edge_fields(self) -> None:
        graph = KnowledgeGraphBuilder().build([sample_record(), sample_record("AAPL", "stock", "WAIT")])
        node = graph.nodes[0]
        edge = graph.edges[0]

        for field in (
            "id",
            "label",
            "type",
            "group",
            "importance",
            "count",
            "status",
            "health",
            "metadata",
            "details_url",
        ):
            self.assertIn(field, node)
        for field in (
            "id",
            "source",
            "target",
            "relation",
            "weight",
            "event_count",
            "direction",
        ):
            self.assertIn(field, edge)

    def test_builder_deduplicates_nodes_and_removes_missing_edges(self) -> None:
        graph = KnowledgeGraphBuilder().build([sample_record(), sample_record()], node_limit=300, edge_limit=800)
        node_ids = [node["id"] for node in graph.nodes]
        allowed = set(node_ids)

        self.assertEqual(len(node_ids), len(set(node_ids)))
        self.assertTrue(all(edge["source"] in allowed and edge["target"] in allowed for edge in graph.edges))

    def test_builder_clusters_crypto_stocks_brain_and_system(self) -> None:
        graph = KnowledgeGraphBuilder().build([sample_record(), sample_record("NVDA", "stock", "WATCHLIST")])
        groups = {node["group"] for node in graph.nodes}

        self.assertIn("crypto", groups)
        self.assertIn("stocks", groups)
        self.assertIn("brain", groups)
        self.assertIn("infrastructure", groups)

    def test_graph_does_not_expose_secrets_or_internal_formulas(self) -> None:
        graph = KnowledgeGraphBuilder().build([sample_record()])
        text = json.dumps(graph.to_dict(), ensure_ascii=False).lower()

        for forbidden in (
            "secret-token",
            "telegram_bot_token",
            "project_root",
            "c:\\users\\",
            "raw_result",
            "calculation",
        ):
            self.assertNotIn(forbidden, text)

    def test_service_search_cluster_node_and_changes(self) -> None:
        class FakeRepository:
            def source_records(self, *, limit: int | None = None) -> list[dict]:
                return [sample_record(), sample_record("MSFT", "stock", "WAIT")]

        service = KnowledgeGraphService(
            brain_events_file=Path("unused.jsonl"),
            repository=FakeRepository(),  # type: ignore[arg-type]
        )
        overview = service.overview()
        search = service.search("BTC")
        cluster = service.cluster("crypto")
        node = service.node(search["nodes"][0]["id"])
        changes = service.changes(since_version=0)

        self.assertGreater(overview["node_count"], 0)
        self.assertGreater(search["node_count"], 0)
        self.assertGreater(cluster["node_count"], 0)
        self.assertIsNotNone(node)
        self.assertTrue(changes["changed"])

    def test_api_routes_return_public_graph_shapes(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                data_dir = temp_path / "data"
                data_dir.mkdir()
                brain_events = data_dir / "brain_events.jsonl"
                brain_events.write_text(json.dumps(sample_record()) + "\n", encoding="utf-8")
                config = PlatformConfig(
                    project_root=temp_path,
                    data_dir=data_dir,
                    shared_state_file=data_dir / "shared_state.json",
                    brain_events_file=brain_events,
                    stock_project_path=temp_path / "missing_stock",
                    crypto_project_path=temp_path / "missing_crypto",
                    telegram_bot_token="secret-token",
                )
                shared_state = SharedState(config.shared_state_file)
                orchestrator = Orchestrator(config=config, shared_state=shared_state, adapters=[])
                bus = orchestrator.event_bus
                orchestrator.adapters = [
                    NoopAdapter("crypto", "test"),
                    NoopAdapter("stock", "test"),
                    NoopAdapter("brain", "test"),
                    ControlCenterAdapter(bus, shared_state, print_output=False),
                ]
                server = WebControlServer(orchestrator, port=0)
                await orchestrator.start()
                server.start()
                try:
                    overview = get_json(f"{server.url}/api/v1/graph/overview")
                    search = get_json(f"{server.url}/api/v1/graph/search?q=BTC")
                    cluster = get_json(f"{server.url}/api/v1/graph/cluster/crypto")
                    node_id = urllib.parse.quote(search["nodes"][0]["id"], safe="")
                    node = get_json(f"{server.url}/api/v1/graph/node/{node_id}")
                    changes = get_json(f"{server.url}/api/v1/graph/changes?since_version=0")
                    with self.assertRaises(urllib.error.HTTPError) as missing:
                        get_json(f"{server.url}/api/v1/graph/node/not-found")
                finally:
                    server.stop()
                    await orchestrator.stop()

                self.assertIn("generated_at", overview)
                self.assertGreater(overview["node_count"], 0)
                self.assertGreater(search["node_count"], 0)
                self.assertGreater(cluster["node_count"], 0)
                self.assertIn("neighbors", node)
                self.assertTrue(changes["changed"])
                self.assertEqual(missing.exception.code, 404)
                text = json.dumps(overview, ensure_ascii=False).lower()
                self.assertNotIn("secret-token", text)
                self.assertNotIn("c:\\users\\", text)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
