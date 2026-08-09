"""Persistent adapter tests for stock-only Live Shadow verification."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

from adapters.decision_signal_adapter import DECISION_CREATED
from adapters.outcome_tracker import SIMULATED_TRADE_CLOSED
from adapters.stock_adapter import STOCK_ANALYSIS_FINISHED, STOCK_SHADOW_OBSERVED
from adapters.stock_shadow_verification_adapter import StockShadowVerificationAdapter
from event_bus import Event, EventBus
from stock_shadow_verification_contract import StockShadowVerificationPolicy


NOW = datetime.now(UTC) - timedelta(minutes=10)


def observed(*, source_id: str = "stock-source-1", legacy: str = "LONG", shadow: str = "SHORT") -> Event:
    payload = {
        "symbol": "AAPL",
        "cycle_id": "cycle-1",
        "source_event_id": source_id,
        "analysis_timestamp": NOW.isoformat(),
        "source_timestamp": (NOW - timedelta(seconds=1)).isoformat(),
        "quote_timestamp": (NOW - timedelta(seconds=2)).isoformat(),
        "latest_candle_timestamp": (NOW - timedelta(days=1)).isoformat(),
        "entry_price": 100.0,
        "legacy": {"direction": legacy, "probability": 70.0},
        "shadow": {
            "status": "CALCULATED",
            "direction": shadow,
            "probability": 65.0,
            "probability_kind": "UNVALIDATED_HEURISTIC_SCORE",
            "feature_quality": {"status": "PASS"},
            "reason_codes": ["SS_CALCULATED"],
        },
        "data_audit": {
            "status": "READY",
            "feature_quality": {"status": "PASS"},
            "reason_codes": ["SD_READY"],
        },
        "shadow_risk": {
            "status": "CALCULATED",
            "reason_codes": ["SSR_CALCULATED"],
            "risk": {
                "action": shadow,
                "entry_price": 100.0,
                "stop_loss": 102.0 if shadow == "SHORT" else 98.0,
                "take_profit": [98.0, 96.0, 94.0] if shadow == "SHORT" else [102.0, 104.0, 106.0],
            },
        },
    }
    return Event(topic=STOCK_SHADOW_OBSERVED, source="stock", payload={"payload": payload})


def decision(*, source_id: str = "stock-source-1", decision_id: str = "decision:stock-1") -> Event:
    return Event(
        topic=DECISION_CREATED,
        source="decision_core",
        payload={
            "payload": {
                "market_type": "stock",
                "source_event_id": source_id,
                "decision_id": decision_id,
                "direction": "LONG",
            }
        },
    )


class StockShadowVerificationAdapterTest(unittest.TestCase):
    def make_adapter(self, root: Path, bus: EventBus) -> StockShadowVerificationAdapter:
        return StockShadowVerificationAdapter(
            bus,
            ledger_file=root / "verification.jsonl",
            policy=StockShadowVerificationPolicy(horizon_seconds=1, neutral_band_percent=0.0),
            config_fingerprint="fingerprint-v1",
        )

    def test_creation_idempotence_decision_link_outcome_and_restart(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                bus = EventBus()
                adapter = self.make_adapter(root, bus)
                await adapter.start()
                event = observed()
                original = deepcopy(event.payload)
                bus.publish(event)
                bus.publish(observed(source_id="stock-source-2"))
                bus.publish(decision())
                bus.publish(
                    Event(
                        topic=STOCK_ANALYSIS_FINISHED,
                        source="stock",
                        payload={
                            "payload": {
                                "market_type": "stock",
                                "symbol": "AAPL",
                                "current_price": 102.0,
                                "price_timestamp": datetime.now(UTC).isoformat(),
                            }
                        },
                    )
                )
                snapshot = adapter.snapshot(days=7)
                verification_id = snapshot["records"][0]["verification_id"]
                snapshot["records"][0]["symbol"] = "MUTATED-COPY"
                self.assertEqual(adapter.snapshot(days=7)["records"][0]["symbol"], "AAPL")
                self.assertEqual(event.payload, original)
                self.assertEqual(snapshot["summary"]["shadow_cases"], 1)
                self.assertEqual(snapshot["summary"]["disagreement"], 1)
                self.assertEqual(snapshot["summary"]["outcomes"]["COMPLETED"], 1)
                self.assertEqual(snapshot["records"][0]["legacy"]["decision_id"], "decision:stock-1")
                self.assertEqual(snapshot["records"][0]["outcome"]["legacy"]["status"], "WIN")
                self.assertEqual(snapshot["records"][0]["outcome"]["shadow"]["status"], "LOSS")
                self.assertEqual(len(snapshot["records"][0]["source_event_ids"]), 2)
                await adapter.stop()

                restarted = self.make_adapter(root, EventBus())
                await restarted.start()
                restored = restarted.detail(verification_id)
                self.assertIsNotNone(restored)
                self.assertEqual(restored["outcome"]["status"], "COMPLETED")
                self.assertEqual(restored["legacy"]["decision_id"], "decision:stock-1")
                await restarted.stop()

        asyncio.run(run())

    def test_tracker_link_is_additive_and_crypto_is_ignored(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                bus = EventBus()
                adapter = self.make_adapter(root, bus)
                await adapter.start()
                bus.publish(observed())
                bus.publish(decision())
                bus.publish(
                    Event(
                        topic=SIMULATED_TRADE_CLOSED,
                        source="outcome_tracker",
                        payload={
                            "payload": {
                                "market_type": "stock",
                                "decision_id": "decision:stock-1",
                                "result_type": "WIN",
                                "gross_profit_percent": 1.5,
                            }
                        },
                    )
                )
                bus.publish(
                    Event(
                        topic=DECISION_CREATED,
                        source="decision_core",
                        payload={"payload": {"market_type": "crypto", "decision_id": "crypto-1"}},
                    )
                )
                record = adapter.snapshot()["records"][0]
                await adapter.stop()

                self.assertEqual(record["outcome"]["tracker"]["result_type"], "WIN")
                lines = [json.loads(line) for line in (root / "verification.jsonl").read_text().splitlines()]
                self.assertEqual(sum(line["record_type"] == "VERIFICATION_CREATED" for line in lines), 1)
                self.assertEqual(sum(line["record_type"] == "TRACKER_OUTCOME_LINKED" for line in lines), 1)
                self.assertNotIn("candles", json.dumps(lines).lower())

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
