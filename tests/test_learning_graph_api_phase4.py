"""Phase 4 API tests for the Pandorick Learning Graph."""

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
from orchestrator import NoopAdapter, Orchestrator
from shared_state import SharedState
from web.api import WebControlServer


def get_json(url: str) -> dict:
    """Read one JSON response from the local test server."""

    with urllib.request.urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def sample_record(symbol: str = "BTCUSDT", direction: str = "LONG") -> dict:
    """Return one brain event containing private fields that must stay hidden."""

    return {
        "received_at": "2026-07-12T10:00:00+00:00",
        "source_event_id": f"event-{symbol}",
        "event_type": "CRYPTO_ANALYSIS_FINISHED",
        "source": "crypto",
        "market_type": "crypto",
        "symbol": symbol,
        "direction": direction,
        "probability": 73.0,
        "source_timestamp": "2026-07-12T09:59:00+00:00",
        "payload": {
            "project_root": "C:\\Users\\Admin\\Desktop\\PandorickKi",
            "telegram_bot_token": "secret-token",
            "indicators": {
                "ema20": 100.0,
                "rsi": 55.0,
                "macd": 0.4,
                "volume": 1500,
            },
            "raw_result": {
                "reasoning": ["private explanation"],
                "calculation": "73 * 0.5",
                "weight": 0.5,
            },
        },
    }


class LearningGraphApiPhase4Test(unittest.TestCase):
    """Verify read-only graph endpoints and public field safety."""

    def make_server(self, temp_path: Path) -> tuple[Orchestrator, WebControlServer]:
        """Create a local server using only no-op adapters."""

        config = PlatformConfig(
            project_root=temp_path,
            data_dir=temp_path,
            shared_state_file=temp_path / "shared_state.json",
            brain_events_file=temp_path / "brain_events.jsonl",
            stock_project_path=temp_path / "missing_stock_bot",
            crypto_project_path=temp_path / "missing_crypto_bot",
            telegram_bot_token="super-secret-token",
            telegram_chat_id="hidden-chat",
        )
        shared_state = SharedState(temp_path / "shared_state.json")
        orchestrator = Orchestrator(
            config=config,
            shared_state=shared_state,
            adapters=[],
        )
        bus = orchestrator.event_bus
        orchestrator.adapters = [
            NoopAdapter("crypto", "test"),
            NoopAdapter("stock", "test"),
            NoopAdapter("brain", "test"),
            NoopAdapter("telegram", "test"),
            ControlCenterAdapter(bus, shared_state, print_output=False),
        ]
        server = WebControlServer(orchestrator, port=0, command_log_file=temp_path / "commands.jsonl")
        return orchestrator, server

    def write_events(self, temp_path: Path, records: list[dict] | None = None) -> None:
        """Write graph source events to the configured JSONL file."""

        records = records or [sample_record()]
        temp_path.joinpath("brain_events.jsonl").write_text(
            "".join(json.dumps(record, ensure_ascii=True) + "\n" for record in records),
            encoding="utf-8",
        )

    def test_learning_graph_endpoint_returns_public_graph(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                self.write_events(temp_path)
                orchestrator, server = self.make_server(temp_path)
                await orchestrator.start()
                server.start()
                try:
                    response = get_json(f"{server.url}/api/v1/learning-graph")
                finally:
                    server.stop()
                    await orchestrator.stop()

                graph = response["learning_graph"]
                self.assertIn("nodes", graph)
                self.assertIn("edges", graph)
                self.assertIn("stats", graph)
                self.assertGreater(graph["stats"]["visible_nodes"], 0)

        asyncio.run(run())

    def test_learning_graph_sub_endpoints_return_expected_shapes(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                self.write_events(temp_path)
                orchestrator, server = self.make_server(temp_path)
                await orchestrator.start()
                server.start()
                try:
                    nodes = get_json(f"{server.url}/api/v1/learning-graph/nodes")
                    edges = get_json(f"{server.url}/api/v1/learning-graph/edges")
                    stats = get_json(f"{server.url}/api/v1/learning-graph/stats")
                    recent = get_json(f"{server.url}/api/v1/learning-graph/recent")
                finally:
                    server.stop()
                    await orchestrator.stop()

                self.assertIsInstance(nodes["nodes"], list)
                self.assertIsInstance(edges["edges"], list)
                self.assertIsInstance(stats["stats"], dict)
                self.assertIsInstance(recent["recent"], list)

        asyncio.run(run())

    def test_learning_graph_node_endpoint_and_missing_node(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                self.write_events(temp_path)
                orchestrator, server = self.make_server(temp_path)
                await orchestrator.start()
                server.start()
                try:
                    nodes = get_json(f"{server.url}/api/v1/learning-graph/nodes")["nodes"]
                    node_id = urllib.parse.quote(nodes[0]["id"], safe="")
                    node = get_json(f"{server.url}/api/v1/learning-graph/node/{node_id}")
                    with self.assertRaises(urllib.error.HTTPError) as missing:
                        get_json(f"{server.url}/api/v1/learning-graph/node/not-found")
                finally:
                    server.stop()
                    await orchestrator.stop()

                self.assertEqual(node["node"]["id"], nodes[0]["id"])
                self.assertEqual(missing.exception.code, 404)

        asyncio.run(run())

    def test_learning_graph_api_does_not_expose_internal_data(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                self.write_events(temp_path)
                orchestrator, server = self.make_server(temp_path)
                await orchestrator.start()
                server.start()
                try:
                    payload = get_json(f"{server.url}/api/v1/learning-graph")
                finally:
                    server.stop()
                    await orchestrator.stop()

                text = json.dumps(payload, ensure_ascii=False).lower()
                for forbidden in (
                    "raw_result",
                    "reasoning",
                    "calculation",
                    "weight",
                    "secret-token",
                    "super-secret-token",
                    "c:\\users\\",
                ):
                    self.assertNotIn(forbidden, text)

        asyncio.run(run())

    def test_learning_graph_api_handles_empty_and_broken_data(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                temp_path.joinpath("brain_events.jsonl").write_text("{bad json}\n", encoding="utf-8")
                orchestrator, server = self.make_server(temp_path)
                await orchestrator.start()
                server.start()
                try:
                    response = get_json(f"{server.url}/api/v1/learning-graph")
                    health = get_json(f"{server.url}/api/health")
                finally:
                    server.stop()
                    await orchestrator.stop()

                graph = response["learning_graph"]
                self.assertEqual(graph["nodes"], [])
                self.assertEqual(graph["edges"], [])
                self.assertTrue(health["web_running"])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
