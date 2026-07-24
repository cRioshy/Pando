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


class DecisionSignalAdapterTest(unittest.TestCase):
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
