"""Tests for the final decision and signal bridge."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from adapters.brain_adapter import BRAIN_DECISION_RECEIVED
from adapters.decision_signal_adapter import (
    DECISION_CREATED,
    SIGNAL_CREATED,
    DecisionSignalAdapter,
)
from event_bus import Event, EventBus
from event_payload_contract import CONTRACT_NAME, CONTRACT_VERSION, contract_errors


class DecisionSignalAdapterTest(unittest.TestCase):
    def test_events_and_ledgers_use_compact_versioned_payloads(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                bus = EventBus()
                decisions: list[Event] = []
                signals: list[Event] = []
                bus.subscribe(DECISION_CREATED, decisions.append)
                bus.subscribe(SIGNAL_CREATED, signals.append)
                adapter = DecisionSignalAdapter(
                    bus,
                    decisions_file=temp_path / "decisions.jsonl",
                    signals_file=temp_path / "signals.jsonl",
                )
                brain_payload = {
                    "market_type": "crypto",
                    "symbol": "BTCUSDT",
                    "direction": "LONG",
                    "probability": 74.0,
                    "confidence": 74.0,
                    "price": 64260.0,
                    "source_event_id": "analysis-compact-1",
                    "source_timestamp": "2026-08-01T18:00:00+00:00",
                    "indicators": {"atr": 250.0},
                    "risk": {"stop_loss": 63000.0},
                    "feature_quality": {
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
                    },
                    "raw_result": {
                        "result": "OPEN",
                        "market_data": {
                            "candles": [
                                {"low": 62000.0 + index, "high": 65000.0 + index}
                                for index in range(500)
                            ]
                        },
                        "private_reasoning": "must not be copied",
                    },
                    "features": {"training_only": list(range(500))},
                }

                await adapter.start()
                bus.publish(
                    Event(
                        topic=BRAIN_DECISION_RECEIVED,
                        source="brain",
                        payload={"payload": brain_payload},
                    )
                )
                await adapter.stop()

                decision_record = json.loads(
                    (temp_path / "decisions.jsonl").read_text(encoding="utf-8").splitlines()[0]
                )["payload"]
                signal_record = json.loads(
                    (temp_path / "signals.jsonl").read_text(encoding="utf-8").splitlines()[0]
                )["payload"]
                payloads = (
                    decisions[0].payload["payload"],
                    signals[0].payload["payload"],
                    decision_record,
                    signal_record,
                )
                for compact in payloads:
                    self.assertEqual(compact["schema_name"], CONTRACT_NAME)
                    self.assertEqual(compact["schema_version"], CONTRACT_VERSION)
                    self.assertEqual(contract_errors(compact), [])
                    encoded = json.dumps(compact)
                    self.assertNotIn("raw_result", encoded)
                    self.assertNotIn("features", encoded)
                    self.assertNotIn('"candles"', encoded)
                    self.assertNotIn("private_reasoning", encoded)
                    self.assertEqual(compact["feature_quality"]["status"], "PASS")
                self.assertEqual(decision_record["source_event_id"], "analysis-compact-1")
                self.assertEqual(signal_record["decision_id"], decision_record["decision_id"])
                self.assertEqual(signal_record["decision_event_id"], decisions[0].event_id)
                self.assertEqual(decision_record["public_result"], "OPEN")
                self.assertLess(len(json.dumps(signal_record)), len(json.dumps(brain_payload)) // 4)

        asyncio.run(run())

    def test_brain_decision_creates_final_decision_and_signal_once(self) -> None:
        async def run() -> None:
            bus = EventBus()
            adapter = DecisionSignalAdapter(bus)
            events: list[Event] = []
            bus.subscribe("*", events.append)

            await adapter.start()
            brain_event = Event(
                topic=BRAIN_DECISION_RECEIVED,
                source="brain",
                payload={
                    "payload": {
                        "market_type": "crypto",
                        "symbol": "BTCUSDT",
                        "direction": "LONG",
                        "probability": 74.0,
                        "confidence": 74.0,
                        "price": 64260.0,
                        "source_event_id": "analysis-1",
                        "source_timestamp": "2026-07-11T12:00:00+00:00",
                    }
                },
            )

            bus.publish(brain_event)
            bus.publish(brain_event)
            await adapter.stop()

            decisions = [event for event in events if event.topic == DECISION_CREATED]
            signals = [event for event in events if event.topic == SIGNAL_CREATED]
            health = await adapter.health()

            self.assertEqual(len(decisions), 1)
            self.assertEqual(len(signals), 1)
            self.assertEqual(health["decisions_created"], 1)
            self.assertEqual(health["signals_created"], 1)
            self.assertEqual(health["duplicates_ignored"], 1)
            self.assertEqual(decisions[0].payload["payload"]["symbol"], "BTCUSDT")
            self.assertTrue(decisions[0].payload["payload"]["decision_id"].startswith("decision:"))
            self.assertEqual(
                signals[0].payload["payload"]["decision_id"],
                decisions[0].payload["payload"]["decision_id"],
            )
            self.assertEqual(signals[0].payload["payload"]["ready_for_telegram"], True)

        asyncio.run(run())

    def test_final_decision_and_signal_are_persisted_with_same_decision_id(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                bus = EventBus()
                adapter = DecisionSignalAdapter(
                    bus,
                    decisions_file=temp_path / "decisions.jsonl",
                    signals_file=temp_path / "signals.jsonl",
                )

                await adapter.start()
                bus.publish(
                    Event(
                        topic=BRAIN_DECISION_RECEIVED,
                        source="brain",
                        payload={
                            "payload": {
                                "market_type": "crypto",
                                "symbol": "BTCUSDT",
                                "direction": "LONG",
                                "probability": 74.0,
                                "confidence": 74.0,
                                "price": 64260.0,
                                "source_event_id": "analysis-ledger-1",
                                "source_timestamp": "2026-07-11T12:00:00+00:00",
                            }
                        },
                    )
                )
                health = await adapter.health()
                await adapter.stop()

                decision_record = json.loads((temp_path / "decisions.jsonl").read_text(encoding="utf-8").splitlines()[0])
                signal_record = json.loads((temp_path / "signals.jsonl").read_text(encoding="utf-8").splitlines()[0])
                decision_payload = decision_record["payload"]
                signal_payload = signal_record["payload"]

                self.assertEqual(health["decisions_persisted"], 1)
                self.assertEqual(health["signals_persisted"], 1)
                self.assertTrue(decision_payload["decision_id"].startswith("decision:"))
                self.assertEqual(signal_payload["decision_id"], decision_payload["decision_id"])
                self.assertTrue(signal_payload["signal_id"].startswith("signal:"))

        asyncio.run(run())

    def test_ledgers_rotate_without_losing_decision_ids(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                decisions_file = temp_path / "decisions.jsonl"
                signals_file = temp_path / "signals.jsonl"
                decisions_file.write_text(
                    json.dumps({"old": "decision", "padding": "x" * 1024 * 1024}, ensure_ascii=True) + "\n",
                    encoding="utf-8",
                )
                bus = EventBus()
                adapter = DecisionSignalAdapter(
                    bus,
                    decisions_file=decisions_file,
                    signals_file=signals_file,
                    ledger_rotation_bytes=1024 * 1024,
                )

                await adapter.start()
                bus.publish(
                    Event(
                        topic=BRAIN_DECISION_RECEIVED,
                        source="brain",
                        payload={
                            "payload": {
                                "market_type": "crypto",
                                "symbol": "BTCUSDT",
                                "direction": "LONG",
                                "probability": 74.0,
                                "confidence": 74.0,
                                "price": 64260.0,
                                "source_event_id": "analysis-rotated-1",
                            }
                        },
                    )
                )
                await adapter.stop()

                archived = list((temp_path / "archive" / "decisions").glob("decisions_*.jsonl"))
                active_payload = json.loads(decisions_file.read_text(encoding="utf-8").splitlines()[0])["payload"]

                self.assertEqual(len(archived), 1)
                self.assertTrue(active_payload["decision_id"].startswith("decision:"))

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
