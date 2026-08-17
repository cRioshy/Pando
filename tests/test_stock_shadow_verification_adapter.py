"""Persistent adapter tests for stock-only Live Shadow verification."""

from __future__ import annotations

import asyncio
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

from adapters.decision_signal_adapter import DECISION_CREATED
from adapters.outcome_tracker import SIMULATED_TRADE_CLOSED
from adapters.stock_adapter import STOCK_ANALYSIS_FINISHED, STOCK_SHADOW_OBSERVED
from adapters.stock_shadow_verification_adapter import (
    VERIFICATION_MODE_DRAIN,
    VERIFICATION_MODE_STOPPED,
    StockShadowVerificationAdapter,
)
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
    def make_adapter(
        self,
        root: Path,
        bus: EventBus,
        *,
        mode: str = "NORMAL",
    ) -> StockShadowVerificationAdapter:
        return StockShadowVerificationAdapter(
            bus,
            ledger_file=root / "verification.jsonl",
            policy=StockShadowVerificationPolicy(horizon_seconds=1, neutral_band_percent=0.0),
            config_fingerprint="fingerprint-v1",
            mode=mode,
        )

    def test_drain_restarts_existing_cases_without_creating_new_cases(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                normal_bus = EventBus()
                normal = self.make_adapter(root, normal_bus)
                await normal.start()
                normal_bus.publish(observed())
                verification_id = normal.snapshot()["records"][0]["verification_id"]
                await normal.stop()

                drain_bus = EventBus()
                drain = self.make_adapter(root, drain_bus, mode=VERIFICATION_MODE_DRAIN)
                await drain.start()
                drain_bus.publish(observed(source_id="new-source-must-not-create"))
                drain_bus.publish(decision())
                drain_bus.publish(
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
                snapshot = drain.snapshot()
                health = await drain.health()
                await drain.stop()

                self.assertEqual(snapshot["summary"]["shadow_cases"], 1)
                self.assertEqual(snapshot["summary"]["outcomes"]["COMPLETED"], 1)
                self.assertEqual(drain.detail(verification_id)["legacy"]["decision_id"], "decision:stock-1")
                self.assertEqual(health["verification_mode"], VERIFICATION_MODE_DRAIN)

        asyncio.run(run())

    def test_stopped_and_unknown_modes_fail_closed_without_subscriptions(self) -> None:
        async def run() -> None:
            for mode, healthy in ((VERIFICATION_MODE_STOPPED, True), ("UNSUPPORTED", False)):
                with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    bus = EventBus()
                    adapter = self.make_adapter(root, bus, mode=mode)
                    await adapter.start()
                    bus.publish(observed())
                    bus.publish(decision())
                    health = await adapter.health()
                    await adapter.stop()

                    self.assertEqual(adapter.snapshot()["summary"]["shadow_cases"], 0)
                    self.assertFalse((root / "verification.jsonl").exists())
                    self.assertFalse(health["running"])
                    self.assertEqual(health["healthy"], healthy)
                    self.assertEqual(health["verification_mode"], VERIFICATION_MODE_STOPPED)

        asyncio.run(run())

    def test_ledger_lock_conflict_fails_closed_without_subscriptions(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                first = self.make_adapter(root, EventBus())
                blocked_bus = EventBus()
                blocked = self.make_adapter(root, blocked_bus, mode=VERIFICATION_MODE_DRAIN)

                await first.start()
                await blocked.start()
                blocked_bus.publish(observed())
                blocked_health = await blocked.health()

                self.assertFalse(blocked_health["running"])
                self.assertFalse(blocked_health["healthy"])
                self.assertFalse(blocked_health["ledger_lock_acquired"])
                self.assertIn("ledger lock already held", blocked_health["last_error"])
                self.assertEqual(blocked.snapshot()["summary"]["shadow_cases"], 0)

                await blocked.stop()
                await first.stop()

                restarted_bus = EventBus()
                restarted = self.make_adapter(root, restarted_bus)
                await restarted.start()
                restarted_bus.publish(observed())
                self.assertEqual(restarted.snapshot()["summary"]["shadow_cases"], 1)
                await restarted.stop()

        asyncio.run(run())

    def test_parallel_duplicate_price_events_complete_exactly_once(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                bus = EventBus()
                adapter = self.make_adapter(root, bus)
                await adapter.start()
                bus.publish(observed())
                quote = Event(
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
                barrier = threading.Barrier(8)

                def publish_once() -> None:
                    barrier.wait()
                    bus.publish(quote)

                with ThreadPoolExecutor(max_workers=8) as pool:
                    futures = [pool.submit(publish_once) for _ in range(8)]
                    for future in futures:
                        future.result()

                snapshot = adapter.snapshot()
                await adapter.stop()
                lines = [
                    json.loads(line)
                    for line in (root / "verification.jsonl").read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]

                self.assertEqual(snapshot["summary"]["outcomes"]["COMPLETED"], 1)
                self.assertEqual(
                    sum(line.get("record_type") == "OUTCOME_COMPLETED" for line in lines),
                    1,
                )

        asyncio.run(run())

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

    def test_due_outcomes_are_completed_in_restart_safe_batches(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                bus = EventBus()
                adapter = StockShadowVerificationAdapter(
                    bus,
                    ledger_file=root / "verification.jsonl",
                    policy=StockShadowVerificationPolicy(horizon_seconds=1, neutral_band_percent=0.0),
                    config_fingerprint="fingerprint-v1",
                    outcome_batch_size=1,
                )
                await adapter.start()
                for index in range(3):
                    event = observed(source_id=f"stock-source-{index}")
                    payload = event.payload["payload"]
                    payload["cycle_id"] = f"cycle-{index}"
                    payload["analysis_timestamp"] = (NOW + timedelta(seconds=index)).isoformat()
                    payload["latest_candle_timestamp"] = (NOW - timedelta(days=index + 1)).isoformat()
                    bus.publish(event)

                quote = Event(
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
                bus.publish(quote)
                first = adapter.snapshot(days=7)["summary"]["outcomes"]
                self.assertEqual(first["COMPLETED"], 1)
                self.assertEqual(first["PENDING"], 2)
                await adapter.stop()

                restarted_bus = EventBus()
                restarted = StockShadowVerificationAdapter(
                    restarted_bus,
                    ledger_file=root / "verification.jsonl",
                    policy=StockShadowVerificationPolicy(horizon_seconds=1, neutral_band_percent=0.0),
                    config_fingerprint="fingerprint-v1",
                    outcome_batch_size=1,
                )
                await restarted.start()
                restarted_bus.publish(quote)
                second = restarted.snapshot(days=7)["summary"]["outcomes"]
                self.assertEqual(second["COMPLETED"], 2)
                self.assertEqual(second["PENDING"], 1)
                await restarted.stop()

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
