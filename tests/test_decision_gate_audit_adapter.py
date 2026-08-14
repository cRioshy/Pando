"""Tests for the read-only Decision Gate observer."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from adapters.brain_adapter import BRAIN_DECISION_RECEIVED
from adapters.decision_gate_audit_adapter import DECISION_GATE_EVALUATED, DecisionGateAuditAdapter
from adapters.decision_signal_adapter import DECISION_CREATED, SIGNAL_CREATED
from decision_gate_contract import DecisionGatePolicy
from event_bus import Event, EventBus


def _quality() -> dict:
    return {
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
    }


class DecisionGateAuditAdapterTest(unittest.TestCase):
    def test_observes_persists_and_never_releases(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                seen: list[Event] = []
                bus.subscribe("*", seen.append)
                path = Path(temp) / "decision_gate_audit.jsonl"
                adapter = DecisionGateAuditAdapter(
                    bus,
                    policy=DecisionGatePolicy(minimum_probability=60, minimum_confidence=60),
                    audit_file=path,
                    ledger_rotation_bytes=1024 * 1024,
                    ledger_max_archives=2,
                )
                await adapter.start()
                brain_event = Event(topic=BRAIN_DECISION_RECEIVED, source="brain", payload={"payload": {
                    "market_type": "crypto",
                    "symbol": "BTCUSDT",
                    "direction": "LONG",
                    "probability": 74.0,
                    "confidence": 74.0,
                    "price": 64260.0,
                    "facts": {"trend": "bullish"},
                    "risk": {"action": "LONG", "stop_loss": 63000.0, "take_profit": [66000.0]},
                    "feature_quality": _quality(),
                    "source_event_id": "analysis-1",
                }})
                bus.publish(brain_event)
                bus.publish(brain_event)
                await adapter.stop()

                evaluated = [event for event in seen if event.topic == DECISION_GATE_EVALUATED]
                self.assertEqual(len(evaluated), 1)
                result = evaluated[0].payload["payload"]
                self.assertTrue(result["qualified"])
                self.assertFalse(result["ready_for_telegram"])
                self.assertFalse(result["order_execution_allowed"])
                self.assertFalse(any(event.topic in {DECISION_CREATED, SIGNAL_CREATED} for event in seen))
                record = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
                self.assertEqual(record["result"]["release_status"], "OBSERVER_ONLY")
                health = await adapter.health()
                self.assertEqual(health["evaluations"], 1)
                self.assertEqual(health["duplicates_ignored"], 1)

        asyncio.run(run())

    def test_missing_quality_is_audited_as_blocked_and_stop_is_inert(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                path = Path(temp) / "audit.jsonl"
                adapter = DecisionGateAuditAdapter(
                    bus,
                    policy=DecisionGatePolicy(minimum_probability=60, minimum_confidence=60),
                    audit_file=path,
                )
                await adapter.start()
                await adapter.stop()
                bus.publish(Event(topic=BRAIN_DECISION_RECEIVED, source="brain", payload={"payload": {
                    "market_type": "crypto", "symbol": "BTCUSDT", "direction": "LONG",
                    "probability": 70.0, "confidence": 70.0, "price": 100.0,
                }}))
                self.assertFalse(path.exists())

                await adapter.start()
                bus.publish(Event(topic=BRAIN_DECISION_RECEIVED, source="brain", payload={"payload": {
                    "market_type": "crypto", "symbol": "BTCUSDT", "direction": "LONG",
                    "probability": 70.0, "confidence": 70.0, "price": 100.0,
                    "facts": {"trend": "up"},
                    "risk": {"action": "LONG", "stop_loss": 90.0, "take_profit": [110.0]},
                    "source_event_id": "missing-quality",
                }}))
                health = await adapter.health()
                self.assertEqual(health["blocked"], 1)
                self.assertIn("DG_QUALITY_MISSING", health["last_reason_codes"])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
