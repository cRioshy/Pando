"""Tests for queued observer-only market regime persistence."""

from __future__ import annotations

import asyncio
import json
import tempfile
import time
import unittest
from pathlib import Path

from adapters.market_regime_observer_adapter import (
    MARKET_REGIME_OBSERVED,
    MarketRegimeObserverAdapter,
)
from event_bus import EventBus


def candles(count: int = 220, *, start: int = 1_700_000_000, direction: int = 1) -> list[dict]:
    return [
        {
            "timestamp": start + index * 900,
            "open": 100.0 + direction * index * 0.2,
            "high": 100.8 + direction * index * 0.2,
            "low": 99.2 + direction * index * 0.2,
            "close": 100.3 + direction * index * 0.2,
            "volume": 1_000 + index,
        }
        for index in range(count)
    ]


class MarketRegimeObserverAdapterTest(unittest.TestCase):
    def test_submit_is_nonblocking_and_worker_persists_compact_event(self) -> None:
        class SlowLedger:
            def __init__(self) -> None:
                self.records: list[dict] = []

            def append_many(self, records: list[dict]) -> Path:
                time.sleep(0.15)
                self.records.extend(records)
                return Path("regimes.jsonl")

        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                seen = []
                bus.subscribe(MARKET_REGIME_OBSERVED, seen.append)
                adapter = MarketRegimeObserverAdapter(
                    bus,
                    ledger_file=Path(temp) / "regimes.jsonl",
                    queue_capacity=8,
                    batch_size=2,
                    flush_interval_seconds=0.01,
                )
                slow = SlowLedger()
                adapter.ledger = slow  # type: ignore[assignment]
                await adapter.start()
                started = time.monotonic()
                accepted = adapter.submit(
                    symbol="BTCUSDT",
                    asset_type="crypto",
                    timeframe="15m",
                    candles=candles(),
                    source_event_id="source-1",
                )
                elapsed = time.monotonic() - started
                await adapter.stop()

                self.assertTrue(accepted)
                self.assertLess(elapsed, 0.05)
                self.assertEqual(len(slow.records), 1)
                self.assertEqual(len(seen), 1)
                payload = seen[0].payload["payload"]
                encoded = json.dumps(payload, allow_nan=False)
                self.assertNotIn("candles", encoded)
                self.assertNotIn("features", encoded)
                self.assertNotIn("raw_result", encoded)
                self.assertFalse(payload["affects_active_decision"])
                self.assertFalse(payload["ready_for_telegram"])
                self.assertFalse(payload["order_execution_allowed"])

        asyncio.run(run())

    def test_restart_and_duplicate_source_events_do_not_duplicate_regime(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                ledger = Path(temp) / "regimes.jsonl"
                first = MarketRegimeObserverAdapter(EventBus(), ledger_file=ledger, flush_interval_seconds=0.01)
                await first.start()
                self.assertTrue(first.submit(
                    symbol="AAPL", asset_type="stock", timeframe="1d", candles=candles(), source_event_id="event-1"
                ))
                self.assertTrue(first.submit(
                    symbol="AAPL", asset_type="stock", timeframe="1d", candles=candles(), source_event_id="event-duplicate"
                ))
                await first.stop()
                self.assertEqual(len(ledger.read_text(encoding="utf-8").splitlines()), 1)
                first_health = await first.health()
                self.assertEqual(first_health["duplicates_ignored"], 1)

                restarted = MarketRegimeObserverAdapter(EventBus(), ledger_file=ledger, flush_interval_seconds=0.01)
                await restarted.start()
                self.assertTrue(restarted.submit(
                    symbol="AAPL", asset_type="stock", timeframe="1d", candles=candles(), source_event_id="event-after-restart"
                ))
                await restarted.stop()
                self.assertEqual(len(ledger.read_text(encoding="utf-8").splitlines()), 1)
                health = await restarted.health()
                self.assertEqual(health["duplicates_ignored"], 1)

        asyncio.run(run())

    def test_shutdown_drains_queue_in_batches_and_statistics_are_filterable(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                adapter = MarketRegimeObserverAdapter(
                    EventBus(),
                    ledger_file=Path(temp) / "regimes.jsonl",
                    queue_capacity=8,
                    batch_size=3,
                    flush_interval_seconds=0.01,
                )
                await adapter.start()
                for index, (symbol, asset, timeframe) in enumerate(
                    (("BTCUSDT", "crypto", "15m"), ("ETHUSDT", "crypto", "15m"), ("AAPL", "stock", "1d"))
                ):
                    self.assertTrue(adapter.submit(
                        symbol=symbol,
                        asset_type=asset,
                        timeframe=timeframe,
                        candles=candles(start=1_700_000_000 + index * 1_000_000),
                        source_event_id=f"source-{index}",
                    ))
                await adapter.stop()

                health = await adapter.health()
                self.assertFalse(health["worker_running"])
                self.assertEqual(health["queue_depth"], 0)
                self.assertEqual(health["persisted"], 3)
                history = adapter.history(asset_type="crypto", limit=1, offset=0)
                self.assertEqual(history["pagination"]["total"], 2)
                self.assertEqual(history["pagination"]["returned"], 1)
                self.assertTrue(history["pagination"]["has_more"])
                current = adapter.current(symbol="AAPL")
                self.assertEqual(current["count"], 1)
                statistics = adapter.statistics(asset_type="crypto")
                self.assertEqual(statistics["count"], 2)
                self.assertEqual(statistics["by_asset_type"], {"crypto": 2})
                self.assertEqual(
                    set(statistics["trend"]),
                    {"STRONG_UP", "UP", "SIDEWAYS", "DOWN", "STRONG_DOWN", "UNKNOWN"},
                )
                self.assertIn(0, statistics["trend"].values())
                self.assertFalse(statistics["legacy_labels_included"])

        asyncio.run(run())

    def test_current_returns_newest_snapshot_for_symbol(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                adapter = MarketRegimeObserverAdapter(
                    EventBus(), ledger_file=Path(temp) / "regimes.jsonl", flush_interval_seconds=0.01
                )
                await adapter.start()
                self.assertTrue(adapter.submit(
                    symbol="BTCUSDT", asset_type="crypto", timeframe="15m",
                    candles=candles(start=1_700_000_000), source_event_id="older",
                ))
                self.assertTrue(adapter.submit(
                    symbol="BTCUSDT", asset_type="crypto", timeframe="15m",
                    candles=candles(start=1_800_000_000), source_event_id="newer",
                ))
                await adapter.stop()

                current = adapter.current(symbol="BTCUSDT")
                self.assertEqual(current["count"], 1)
                self.assertEqual(current["items"][0]["source_event_id"], "newer")

        asyncio.run(run())

    def test_queue_full_is_visible_and_drops_newest(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                adapter = MarketRegimeObserverAdapter(
                    EventBus(),
                    ledger_file=Path(temp) / "regimes.jsonl",
                    queue_capacity=1,
                    flush_interval_seconds=1.0,
                )
                adapter._accepting = False
                self.assertFalse(adapter.submit(
                    symbol="BTCUSDT", asset_type="crypto", timeframe="15m", candles=candles(), source_event_id="closed"
                ))
                adapter._accepting = True
                adapter._queue.put_nowait({"occupied": True})
                self.assertFalse(adapter.submit(
                    symbol="BTCUSDT", asset_type="crypto", timeframe="15m", candles=candles(), source_event_id="full"
                ))
                adapter._queue.get_nowait()
                adapter._queue.task_done()
                adapter._accepting = False
                health = await adapter.health()
                self.assertEqual(health["dropped_inputs"], 1)
                self.assertFalse(health["healthy"])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
