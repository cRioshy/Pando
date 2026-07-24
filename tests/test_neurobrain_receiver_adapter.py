"""Tests for the read-only NeuroBrain coexistence receiver."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from adapters.neurobrain_receiver_adapter import (
    NEUROBRAIN_EVENT_RECEIVED,
    NEUROBRAIN_RECEIVER_STOPPED,
    NeuroBrainReceiverAdapter,
)
from config import PlatformConfig
from event_bus import Event, EventBus
from orchestrator import Orchestrator


class NeuroBrainReceiverAdapterTest(unittest.TestCase):
    def test_receiver_stores_allowed_events_without_changing_source_event(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                bus = EventBus()
                seen: list[Event] = []
                bus.subscribe(NEUROBRAIN_EVENT_RECEIVED, seen.append)
                adapter = NeuroBrainReceiverAdapter(
                    bus,
                    inbox_file=root / "neurobrain" / "inbox.jsonl",
                    status_file=root / "neurobrain" / "status.json",
                )

                await adapter.start()
                source = Event(
                    topic="DECISION_CREATED",
                    source="decision_core",
                    payload={
                        "event_type": "DECISION_CREATED",
                        "payload": {
                            "market_type": "crypto",
                            "symbol": "BTCUSDT",
                            "decision_id": "decision-1",
                            "direction": "LONG",
                            "probability": 72.5,
                            "source_timestamp": "2026-07-24T20:00:00+00:00",
                        },
                    },
                )
                bus.publish(source)
                await adapter.stop()

                lines = (root / "neurobrain" / "inbox.jsonl").read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(lines), 1)
                record = json.loads(lines[0])
                self.assertEqual(record["source_event_id"], source.event_id)
                self.assertEqual(record["topic"], "DECISION_CREATED")
                self.assertEqual(record["market_type"], "crypto")
                self.assertEqual(record["symbol"], "BTCUSDT")
                self.assertEqual(record["decision_id"], "decision-1")
                self.assertEqual(record["direction"], "LONG")
                self.assertTrue(seen)

                status = json.loads((root / "neurobrain" / "status.json").read_text(encoding="utf-8"))
                self.assertFalse(status["running"])
                self.assertEqual(status["received_events"], 1)

        asyncio.run(run())

    def test_receiver_ignores_duplicates_and_unwanted_topics(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                bus = EventBus()
                adapter = NeuroBrainReceiverAdapter(
                    bus,
                    inbox_file=root / "inbox.jsonl",
                    status_file=root / "status.json",
                    allowed_topics={"SIGNAL_CREATED"},
                )
                await adapter.start()
                event = Event(topic="SIGNAL_CREATED", source="decision_core", payload={"symbol": "ETHUSDT"})
                bus.publish(event)
                bus.publish(event)
                bus.publish(Event(topic="SERVICE_HEARTBEAT", source="crypto", payload={"status": "ok"}))
                await adapter.stop()

                records = (root / "inbox.jsonl").read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(records), 1)
                health = await adapter.health()
                self.assertEqual(health["received_events"], 1)
                self.assertEqual(health["duplicate_events"], 1)
                self.assertGreaterEqual(health["ignored_events"], 1)

        asyncio.run(run())

    def test_orchestrator_can_enable_receiver_as_default_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = PlatformConfig(
                data_dir=root,
                shared_state_file=root / "shared_state.json",
                neurobrain_receiver_enabled=True,
                neurobrain_inbox_file=root / "neurobrain" / "inbox.jsonl",
                neurobrain_status_file=root / "neurobrain" / "status.json",
            )
            orchestrator = Orchestrator(config=config)

            self.assertIn("neurobrain_receiver", [adapter.name for adapter in orchestrator.adapters])

    def test_receiver_stop_publishes_lifecycle_event_without_looping(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                bus = EventBus()
                stopped: list[Event] = []
                bus.subscribe(NEUROBRAIN_RECEIVER_STOPPED, stopped.append)
                adapter = NeuroBrainReceiverAdapter(
                    bus,
                    inbox_file=root / "inbox.jsonl",
                    status_file=root / "status.json",
                )
                await adapter.start()
                await adapter.stop()

                self.assertEqual(len(stopped), 1)
                self.assertFalse((root / "inbox.jsonl").exists())

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
