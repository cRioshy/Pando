"""Tests for the PandorickKi brain adapter."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from adapters.brain_adapter import AI_LEARNING_UPDATED, BRAIN_DECISION_RECEIVED, BrainAdapter
from brain_event_store import BrainEventReader
from adapters.stock_adapter import STOCK_ANALYSIS_FINISHED
from event_bus import Event, EventBus
from event_payload_contract import CONTRACT_NAME, CONTRACT_VERSION, contract_errors


class BrainAdapterTest(unittest.TestCase):
    def test_brain_persists_and_publishes_only_compact_versioned_payload(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                seen = []
                bus.subscribe(BRAIN_DECISION_RECEIVED, seen.append)
                path = Path(temp) / "brain_events.jsonl"
                adapter = BrainAdapter(bus, path)
                market_payload = {
                    "market_type": "stock",
                    "symbol": "AAPL",
                    "direction": "LONG",
                    "probability": 68.0,
                    "price": 220.0,
                    "current_price": 220.0,
                    "indicators": {"atr": 4.0, "rsi": 55.0},
                    "risk": {"stop_loss": 214.0, "take_profit_1": 229.0},
                    "source_timestamp": "2026-08-01T18:00:00+00:00",
                    "raw_result": {
                        "result": "OPEN",
                        "market_data": {
                            "candles": [
                                {"low": 210.0 + index, "high": 230.0 + index, "close": 220.0}
                                for index in range(500)
                            ]
                        },
                        "private_reasoning": "must not be persisted",
                    },
                    "features": {
                        "training_only": list(range(500)),
                        "metadata": {"data_quality": {
                            "schema_name": "pandorickki.feature-data-quality",
                            "schema_version": 1,
                            "status": "PASS",
                            "input_rows": 240,
                            "accepted_rows": 240,
                            "output_rows": 240,
                            "dropped_rows": 0,
                            "duplicate_rows": 0,
                            "timestamped_rows": 240,
                            "order": {"status": "VERIFIED", "reason": "sorted"},
                            "warmup": {"status": "READY", "available_candles": 240},
                            "warnings": ["must be omitted"],
                        }},
                    },
                    "market_data_diagnostics": {"responses": ["large"] * 500},
                }
                source_event = Event(
                    topic=STOCK_ANALYSIS_FINISHED,
                    source="stock",
                    payload={"event_type": STOCK_ANALYSIS_FINISHED, "payload": market_payload},
                )

                await adapter.start()
                bus.publish(source_event)
                await adapter.stop()

                rows = BrainEventReader(
                    legacy_file=path,
                    rotated_root=path.parent / "brain_events",
                ).recent(limit=10)
                persisted = rows[0]["payload"]
                published = seen[0].payload["payload"]
                for compact in (persisted, published):
                    self.assertEqual(compact["schema_name"], CONTRACT_NAME)
                    self.assertEqual(compact["schema_version"], CONTRACT_VERSION)
                    self.assertEqual(compact["source_event_id"], source_event.event_id)
                    self.assertEqual(compact["public_result"], "OPEN")
                    self.assertEqual(contract_errors(compact), [])
                    encoded = json.dumps(compact)
                    self.assertNotIn("raw_result", encoded)
                    self.assertNotIn("features", encoded)
                    self.assertNotIn('"candles"', encoded)
                    self.assertNotIn("private_reasoning", encoded)
                    self.assertEqual(compact["feature_quality"]["status"], "PASS")
                    self.assertNotIn("warnings", compact["feature_quality"])
                self.assertLess(len(json.dumps(persisted)), len(json.dumps(market_payload)) // 4)

        asyncio.run(run())

    def test_import_and_start_do_not_touch_existing_brains(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                adapter = BrainAdapter(bus, Path(temp) / "brain_events.jsonl")
                await adapter.start()
                health = await adapter.health()
                await adapter.stop()

                self.assertTrue(health["healthy"])
                self.assertEqual(health["received_decisions"], 0)

        asyncio.run(run())

    def test_stock_decision_event_is_persisted(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                seen = []
                learning = []
                bus.subscribe(BRAIN_DECISION_RECEIVED, seen.append)
                bus.subscribe(AI_LEARNING_UPDATED, learning.append)
                path = Path(temp) / "brain_events.jsonl"
                adapter = BrainAdapter(bus, path)
                await adapter.start()
                bus.publish(
                    Event(
                        topic=STOCK_ANALYSIS_FINISHED,
                        source="stock",
                        payload={
                            "event_type": STOCK_ANALYSIS_FINISHED,
                            "payload": {
                                "market_type": "stock",
                                "symbol": "AAPL",
                                "direction": "LONG",
                                "probability": 61.5,
                                "source_timestamp": "2026-07-10T00:00:00+00:00",
                            },
                        },
                    )
                )
                health = await adapter.health()
                await adapter.stop()

                self.assertEqual(health["received_decisions"], 1)
                self.assertEqual(health["last_symbol"], "AAPL")
                self.assertTrue(seen)
                self.assertTrue(learning)
                brain_payload = seen[0].payload["payload"]
                learning_payload = learning[0].payload["payload"]
                self.assertEqual(brain_payload["direction"], "LONG")
                self.assertEqual(brain_payload["confidence"], 61.5)
                self.assertEqual(learning_payload["updates"], 1)
                self.assertEqual(learning_payload["last_confidence"], 61.5)
                rows = BrainEventReader(
                    legacy_file=path,
                    rotated_root=path.parent / "brain_events",
                ).recent(limit=10)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["symbol"], "AAPL")

        asyncio.run(run())

    def test_run_once_emits_heartbeat_and_stop(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                adapter = BrainAdapter(bus, Path(temp) / "brain_events.jsonl")
                await adapter.start()
                events = await adapter.run_once()
                await adapter.stop()
                health = await adapter.health()

                self.assertEqual(len(events), 1)
                self.assertFalse(health["running"])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
