"""Phase 3 tests for the Pandorick Learning Graph backend."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from learning_graph.graph_builder import GraphBuilder
from learning_graph.graph_models import stable_edge_id, stable_node_id
from learning_graph.graph_repository import GraphRepository
from learning_graph.graph_sanitizer import GraphSanitizer
from learning_graph.graph_service import LearningGraphService


def sample_record(symbol: str = "BTCUSDT", direction: str = "LONG") -> dict:
    return {
        "received_at": "2026-07-12T10:00:00+00:00",
        "source_event_id": "event-1",
        "event_type": "CRYPTO_ANALYSIS_FINISHED",
        "source": "crypto",
        "market_type": "crypto",
        "symbol": symbol,
        "direction": direction,
        "probability": 72.5,
        "source_timestamp": "2026-07-12T09:59:00+00:00",
        "payload": {
            "indicators": {
                "ema20": 1,
                "rsi": 51,
                "macd": 0.2,
                "volume": 100,
                "open_interest": 1000,
                "funding_rate": 0.0001,
            },
            "raw_result": {
                "reasoning": ["secret internal logic"],
                "calculation": "72 * 0.5",
            },
            "risk": {"steps": [{"weight": 0.5}]},
        },
    }


class LearningGraphPhase3Test(unittest.TestCase):
    def test_public_result_is_preferred_over_legacy_raw_result(self) -> None:
        record = sample_record()
        record["payload"]["public_result"] = "DIRECT_STOP"
        record["payload"]["raw_result"]["result"] = "TP3_WIN"

        self.assertEqual(GraphBuilder()._public_result(record), "DIRECT_STOP")

    def test_legacy_raw_result_remains_a_result_fallback(self) -> None:
        record = sample_record()
        record["payload"]["raw_result"]["result"] = "TP2_THEN_STOP"

        self.assertEqual(GraphBuilder()._public_result(record), "TP2_THEN_STOP")

    def test_graph_sanitizer_removes_secret_fields(self) -> None:
        sanitizer = GraphSanitizer()
        node = sanitizer.sanitize_node(
            {
                "id": "market:btcusdt",
                "label": "BTCUSDT",
                "type": "MARKET",
                "project_root": "C:\\Users\\Admin\\Desktop\\PandorickKi",
                "raw_result": {"secret": True},
                "api_key": "hidden",
            }
        )

        self.assertEqual(node["label"], "BTCUSDT")
        self.assertNotIn("project_root", node)
        self.assertNotIn("raw_result", node)
        self.assertNotIn("api_key", node)

    def test_builder_creates_nodes_and_edges(self) -> None:
        graph = GraphBuilder().build([sample_record()])
        node_types = {node["type"] for node in graph.nodes}
        edge_types = {edge["type"] for edge in graph.edges}

        self.assertIn("MARKET", node_types)
        self.assertIn("INDICATOR", node_types)
        self.assertIn("DECISION", node_types)
        self.assertIn("USES_PUBLIC_FACTOR", edge_types)
        self.assertIn("CREATED_DECISION", edge_types)

    def test_duplicate_edges_are_merged(self) -> None:
        graph = GraphBuilder().build([sample_record(), sample_record()])
        edge_id = stable_edge_id(
            stable_node_id("MARKET", "BTCUSDT"),
            "ANALYZED_BY",
            stable_node_id("SYSTEM", "Crypto Engine"),
        )
        matching = [edge for edge in graph.edges if edge["id"] == edge_id]

        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["count"], 2)

    def test_node_limit_works(self) -> None:
        records = [sample_record(f"BTC{i}USDT") for i in range(20)]
        graph = GraphBuilder().build(records, node_limit=5, edge_limit=100)

        self.assertLessEqual(len(graph.nodes), 5)
        self.assertTrue(all(edge["source"] in {node["id"] for node in graph.nodes} for edge in graph.edges))

    def test_repository_handles_empty_and_broken_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "brain_events.jsonl"
            path.write_text("{bad json}\n" + json.dumps(sample_record()) + "\n", encoding="utf-8")
            repository = GraphRepository(brain_events_file=path, max_records=10)

            records = repository.recent_brain_events()

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["symbol"], "BTCUSDT")

    def test_service_starts_and_returns_public_graph(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "brain_events.jsonl"
            path.write_text(json.dumps(sample_record()) + "\n", encoding="utf-8")
            service = LearningGraphService(brain_events_file=path)

            graph = service.graph()

            self.assertIn("nodes", graph)
            self.assertIn("edges", graph)
            self.assertIn("stats", graph)
            self.assertGreater(graph["stats"]["visible_nodes"], 0)
            self.assertIn("pattern_buckets", graph["stats"])
            self.assertIn("learning_projection_records_today", graph["stats"])
            self.assertFalse(graph["stats"]["ml_training_active"])
            self.assertEqual(graph["stats"]["model_updates"], 0)

    def test_no_internal_formulas_or_paths_in_graph(self) -> None:
        graph = GraphBuilder().build([sample_record()])
        text = json.dumps(graph.to_dict(), ensure_ascii=False).lower()

        self.assertNotIn("calculation", text)
        self.assertNotIn("reasoning", text)
        self.assertNotIn("weight", text)
        self.assertNotIn("c:\\users\\", text)


if __name__ == "__main__":
    unittest.main()
