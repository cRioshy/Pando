"""Tests for the PandorickKi brain adapter."""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from adapters.brain_adapter import AI_LEARNING_UPDATED, BRAIN_DECISION_RECEIVED, BrainAdapter
from brain_event_store import BrainEventReader
from adapters.stock_adapter import STOCK_ANALYSIS_FINISHED
from event_bus import Event, EventBus


class BrainAdapterTest(unittest.TestCase):
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
