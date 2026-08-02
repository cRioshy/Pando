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
from event_payload_contract import CONTRACT_NAME, CONTRACT_VERSION, contract_errors
from orchestrator import Orchestrator


class NeuroBrainReceiverAdapterTest(unittest.TestCase):
    def test_receiver_uses_observer_schema_for_learning_updates(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                bus = EventBus()
                adapter = NeuroBrainReceiverAdapter(
                    bus,
                    inbox_file=root / "inbox.jsonl",
                    status_file=root / "status.json",
                )
                await adapter.start()
                bus.publish(
                    Event(
                        topic="AI_LEARNING_UPDATED",
                        source="brain",
                        payload={
                            "event_type": "AI_LEARNING_UPDATED",
                            "payload": {
                                "status": "updated",
                                "updates": 17,
                                "memory_size": 17,
                                "last_symbol": "BTCUSDT",
                                "last_direction": "LONG",
                                "last_confidence": 72.5,
                                "last_update_at": "2026-08-02T09:00:00+00:00",
                                "raw_result": {"must": "not survive"},
                            },
                        },
                    )
                )
                await adapter.stop()

                record = json.loads((root / "inbox.jsonl").read_text(encoding="utf-8"))
                payload = record["payload"]
                self.assertEqual(payload["schema_name"], "pandorickki.compact-observer-event")
                self.assertEqual(payload["schema_version"], 1)
                self.assertEqual(payload["event_type"], "AI_LEARNING_UPDATED")
                self.assertEqual(payload["status"], "updated")
                self.assertEqual(payload["updates"], 17)
                self.assertEqual(payload["memory_size"], 17)
                self.assertEqual(payload["last_symbol"], "BTCUSDT")
                self.assertEqual(payload["last_direction"], "LONG")
                self.assertEqual(payload["last_confidence"], 72.5)
                self.assertNotIn("raw_result", json.dumps(payload))

        asyncio.run(run())

    def test_receiver_uses_observer_schema_for_aggregate_stock_update(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                bus = EventBus()
                adapter = NeuroBrainReceiverAdapter(
                    bus,
                    inbox_file=root / "inbox.jsonl",
                    status_file=root / "status.json",
                )
                await adapter.start()
                bus.publish(
                    Event(
                        topic="STOCK_MARKET_DATA_UPDATED",
                        source="stock",
                        payload={"count": 2, "symbols": ["AAPL", "MSFT"]},
                    )
                )
                await adapter.stop()

                record = json.loads((root / "inbox.jsonl").read_text(encoding="utf-8"))
                payload = record["payload"]
                self.assertEqual(payload["schema_name"], "pandorickki.compact-observer-event")
                self.assertEqual(payload["event_type"], "STOCK_MARKET_DATA_UPDATED")
                self.assertEqual(payload["count"], 2)
                self.assertEqual(payload["symbols"], ["AAPL", "MSFT"])
                self.assertNotIn("market_type", payload)
                self.assertNotIn("symbol", payload)

        asyncio.run(run())

    def test_receiver_infers_market_type_for_single_crypto_market_update(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                bus = EventBus()
                adapter = NeuroBrainReceiverAdapter(
                    bus,
                    inbox_file=root / "inbox.jsonl",
                    status_file=root / "status.json",
                )
                await adapter.start()
                bus.publish(
                    Event(
                        topic="CRYPTO_MARKET_DATA_UPDATED",
                        source="crypto",
                        payload={"symbol": "BTCUSDT", "timeframe": "15m", "price": 65000.0},
                    )
                )
                await adapter.stop()

                record = json.loads((root / "inbox.jsonl").read_text(encoding="utf-8"))
                payload = record["payload"]
                self.assertEqual(payload["schema_name"], CONTRACT_NAME)
                self.assertEqual(payload["market_type"], "crypto")
                self.assertEqual(payload["symbol"], "BTCUSDT")
                self.assertEqual(contract_errors(payload), [])

        asyncio.run(run())

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
                            "source_event_id": "analysis-1",
                            "direction": "LONG",
                            "probability": 72.5,
                            "source_timestamp": "2026-07-24T20:00:00+00:00",
                            "raw_result": {
                                "result": "OPEN",
                                "market_data": {
                                    "candles": [
                                        {"low": 62000.0 + index, "high": 65000.0 + index}
                                        for index in range(500)
                                    ]
                                },
                                "private_reasoning": "must not be stored",
                            },
                            "features": {"training_only": list(range(500))},
                        },
                    },
                )
                original_payload = json.loads(json.dumps(source.payload))
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
                compact = record["payload"]
                self.assertEqual(compact["schema_name"], CONTRACT_NAME)
                self.assertEqual(compact["schema_version"], CONTRACT_VERSION)
                self.assertEqual(compact["source_event_id"], "analysis-1")
                self.assertEqual(compact["public_result"], "OPEN")
                self.assertEqual(contract_errors(compact), [])
                encoded = json.dumps(compact)
                self.assertNotIn("raw_result", encoded)
                self.assertNotIn("features", encoded)
                self.assertNotIn("candles", encoded)
                self.assertNotIn("private_reasoning", encoded)
                self.assertLess(len(encoded), len(json.dumps(original_payload)) // 4)
                self.assertEqual(source.payload, original_payload)

                status = json.loads((root / "neurobrain" / "status.json").read_text(encoding="utf-8"))
                self.assertFalse(status["running"])
                self.assertEqual(status["received_events"], 1)

        asyncio.run(run())

    def test_existing_legacy_inbox_is_preserved_when_compact_rows_are_appended(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                inbox = root / "inbox.jsonl"
                legacy = {
                    "source_event_id": "legacy-event",
                    "topic": "DECISION_CREATED",
                    "payload": {"raw_result": {"legacy": True}},
                }
                legacy_line = json.dumps(legacy, ensure_ascii=True)
                inbox.write_text(legacy_line + "\n", encoding="utf-8")
                bus = EventBus()
                adapter = NeuroBrainReceiverAdapter(
                    bus,
                    inbox_file=inbox,
                    status_file=root / "status.json",
                )

                await adapter.start()
                bus.publish(
                    Event(
                        topic="SIGNAL_CREATED",
                        source="decision_core",
                        payload={
                            "event_type": "SIGNAL_CREATED",
                            "payload": {
                                "market_type": "crypto",
                                "symbol": "ETHUSDT",
                                "direction": "SHORT",
                                "probability": 66.0,
                                "decision_id": "decision-new",
                                "signal_id": "signal-new",
                                "source_event_id": "analysis-new",
                            },
                        },
                    )
                )
                await adapter.stop()

                lines = inbox.read_text(encoding="utf-8").splitlines()
                self.assertEqual(lines[0], legacy_line)
                self.assertEqual(len(lines), 2)
                new_record = json.loads(lines[1])
                self.assertEqual(new_record["payload"]["schema_name"], CONTRACT_NAME)
                self.assertEqual(new_record["decision_id"], "decision-new")
                self.assertEqual(new_record["signal_id"], "signal-new")

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
