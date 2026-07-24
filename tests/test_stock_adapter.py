"""Tests for the Phase 4 stock adapter."""

from __future__ import annotations

import asyncio
import sqlite3
import time
import unittest
from pathlib import Path

from adapters.stock_adapter import (
    STOCK_ANALYSIS_FINISHED,
    STOCK_SERVICE_ERROR,
    STOCK_SERVICE_STOPPED,
    StockAdapter,
)
from event_bus import EventBus


STOCK_PATH = Path(__file__).resolve().parents[2] / "pandorick_stock_bot"


class StockAdapterTest(unittest.TestCase):
    def test_import_does_not_start_loop(self) -> None:
        bus = EventBus()
        adapter = StockAdapter(bus, STOCK_PATH, test_mode=True)
        self.assertFalse(adapter.status.running)
        self.assertEqual(bus.history(), [])

    def test_run_once_returns_normalized_results_and_event(self) -> None:
        async def run() -> None:
            bus = EventBus()
            seen = []
            bus.subscribe(STOCK_ANALYSIS_FINISHED, seen.append)
            adapter = StockAdapter(bus, STOCK_PATH, test_mode=True)
            await adapter.start()
            results = await adapter.run_once()
            health = await adapter.health()
            sqlite_file = adapter._config.sqlite_file

            self.assertTrue(results)
            self.assertEqual(results[0]["market_type"], "stock")
            self.assertIn(results[0]["direction"], {"LONG", "SHORT", "HOLD", None})
            self.assertIsNone(results[0]["price"])
            self.assertIsNone(results[0]["current_price"])
            self.assertIsNotNone(results[0]["analysis_close"])
            self.assertEqual(results[0]["price_source"], "live_unavailable_placeholder_hidden")
            self.assertEqual(results[0]["price_status"], "disabled")
            self.assertTrue(seen)
            self.assertEqual(health["cycles"], 1)
            self.assertTrue(sqlite_file.exists())
            connection = sqlite3.connect(sqlite_file)
            try:
                decision_count = connection.execute("SELECT COUNT(*) FROM stock_decisions").fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(decision_count, len(results))
            await adapter.stop()

        asyncio.run(run())

    def test_dashboard_stock_price_uses_free_live_quote_when_available(self) -> None:
        async def run() -> None:
            bus = EventBus()
            adapter = StockAdapter(
                bus,
                STOCK_PATH,
                test_mode=True,
                live_price_display=True,
            )
            adapter._fetch_live_stock_price = lambda symbol: 214.25
            adapter._last_live_price_source = "yahoo_finance_chart"
            adapter._last_live_price_timestamp = "2026-07-23T09:42:00+00:00"

            await adapter.start()
            try:
                results = await adapter.run_once()
            finally:
                await adapter.stop()

            self.assertEqual(results[0]["price"], 214.25)
            self.assertEqual(results[0]["current_price"], 214.25)
            self.assertEqual(results[0]["price_source"], "yahoo_finance_chart")
            self.assertEqual(results[0]["price_status"], "ok")
            self.assertEqual(results[0]["price_timestamp"], "2026-07-23T09:42:00+00:00")
            self.assertNotEqual(results[0]["analysis_close"], 214.25)

        asyncio.run(run())

    def test_duplicate_events_are_prevented(self) -> None:
        async def run() -> None:
            bus = EventBus()
            seen = []
            bus.subscribe(STOCK_ANALYSIS_FINISHED, seen.append)
            adapter = StockAdapter(bus, STOCK_PATH, test_mode=True)
            result = {
                "market_type": "stock",
                "symbol": "AAPL",
                "timeframe": None,
                "direction": "LONG",
                "strength": 55,
                "probability": 55.0,
                "facts": [],
                "indicators": {},
                "price": 1.0,
                "source_timestamp": "2026-07-10T00:00:00+00:00",
                "received_at": "2026-07-10T00:00:01+00:00",
                "raw_result": {},
            }

            self.assertTrue(adapter._publish_analysis_if_new(result))
            self.assertFalse(adapter._publish_analysis_if_new(result))
            self.assertEqual(len(seen), 1)
            self.assertEqual(adapter.status.duplicate_results, 1)

        asyncio.run(run())

    def test_health_and_stop(self) -> None:
        async def run() -> None:
            bus = EventBus()
            stopped = []
            bus.subscribe(STOCK_SERVICE_STOPPED, stopped.append)
            adapter = StockAdapter(bus, STOCK_PATH, test_mode=True)
            await adapter.start()
            await adapter.stop()
            health = await adapter.health()

            self.assertFalse(health["running"])
            self.assertTrue(stopped)

        asyncio.run(run())

    def test_slow_stock_cycle_times_out_without_overlap(self) -> None:
        class SlowStockAdapter(StockAdapter):
            def _run_stock_once_sync(self) -> list:
                time.sleep(0.2)
                return []

        async def run() -> None:
            bus = EventBus()
            errors = []
            bus.subscribe(STOCK_SERVICE_ERROR, errors.append)
            adapter = SlowStockAdapter(bus, STOCK_PATH, test_mode=True, cycle_timeout_seconds=0.05)
            await adapter.start()
            first = await adapter.run_once()
            second = await adapter.run_once()
            await asyncio.sleep(0.25)
            third = await adapter.run_once()
            await adapter.stop()

            self.assertEqual(first, [])
            self.assertEqual(second, [])
            self.assertEqual(third, [])
            self.assertGreaterEqual(len(errors), 2)
            self.assertIn("exceeded", errors[0].payload["payload"]["error"])
            self.assertIn("still running", errors[1].payload["payload"]["error"])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
