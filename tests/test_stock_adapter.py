"""Tests for the Phase 4 stock adapter."""

from __future__ import annotations

import asyncio
import sqlite3
import time
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from adapters.stock_candle_service import StockCandleSnapshot
from adapters.stock_adapter import (
    STOCK_ANALYSIS_FINISHED,
    STOCK_SERVICE_ERROR,
    STOCK_SERVICE_STOPPED,
    StockAdapter,
)
from event_bus import EventBus
from stock_data_contract import StockDataPolicy
from stock_shadow_candidate import StockShadowPolicy
from stock_shadow_risk import StockShadowRiskPolicy


STOCK_PATH = Path(__file__).resolve().parents[2] / "pandorick_stock_bot"


class StockAdapterTest(unittest.TestCase):
    def test_public_candles_are_audited_without_reclassifying_placeholder_decision(self) -> None:
        class CandleService:
            def fetch_daily_candles(self, symbol: str, *, limit: int) -> StockCandleSnapshot:
                start = datetime.now(UTC) - timedelta(days=200)
                rows = []
                for index in range(200):
                    close = 100.0 + index * 0.1
                    rows.append({
                        "timestamp": (start + timedelta(days=index)).isoformat(),
                        "open": close - 0.2,
                        "high": close + 0.5,
                        "low": close - 0.5,
                        "close": close,
                        "volume": 1_000_000,
                    })
                return StockCandleSnapshot(symbol=symbol, timeframe="1d", candles=rows[-limit:], source="test_public")

            def diagnostics(self) -> dict:
                return {"attempts": [{"source": "test_public", "status": "ok"}], "last_error": None}

        policy = StockDataPolicy(
            minimum_candles=200,
            full_warmup_candles=200,
            maximum_candle_age_seconds=4 * 24 * 60 * 60,
            maximum_quote_age_seconds=900,
            allowed_price_sources=("yahoo_finance_chart",),
        )
        adapter = StockAdapter(
            EventBus(),
            STOCK_PATH,
            stock_data_observer_enabled=True,
            stock_data_policy=policy,
            stock_shadow_policy=StockShadowPolicy(
                minimum_candles=200,
                full_warmup_candles=200,
            ),
            stock_shadow_risk_policy=StockShadowRiskPolicy(
                atr_multiplier=1.0,
                minimum_distance_percent=0.5,
                take_profit_multiples=(1.0, 2.0, 3.0),
                price_decimals=4,
            ),
            candle_service=CandleService(),  # type: ignore[arg-type]
        )
        audit = adapter._build_stock_data_audit(
            symbol="AAPL",
            direction="LONG",
            legacy_probability=71.0,
            current_price=120.0,
            price_source="yahoo_finance_chart",
            price_timestamp=datetime.now(UTC).isoformat(),
        )

        self.assertEqual(audit["candle_count"], 200)
        self.assertEqual(audit["audit"]["feature_quality"]["status"], "PASS")
        self.assertEqual(audit["audit"]["status"], "READY")
        self.assertNotIn("SD_SOURCE_NOT_LIVE", audit["audit"]["reason_codes"])
        self.assertNotIn("SD_RISK_MISSING", audit["audit"]["reason_codes"])
        self.assertNotIn("candles", audit["audit"])
        self.assertEqual(audit["shadow_candidate"]["direction"], "LONG")
        self.assertEqual(audit["shadow_candidate"]["source_kind"], "PUBLIC_LIVE")
        self.assertNotIn("candles", audit["shadow_candidate"])
        self.assertFalse(audit["shadow_candidate"]["ready_for_telegram"])
        self.assertFalse(audit["shadow_candidate"]["order_execution_allowed"])
        self.assertEqual(audit["shadow_risk"]["status"], "CALCULATED")
        self.assertEqual(audit["shadow_candidate"]["risk"], audit["shadow_risk"]["risk"])
        self.assertNotIn("candles", audit["shadow_risk"])
        self.assertFalse(audit["shadow_risk"]["affects_active_decision"])
        self.assertEqual(audit["comparison"]["legacy"]["probability"], 71.0)
        self.assertEqual(audit["comparison"]["public_shadow"]["direction"], "LONG")
        self.assertTrue(audit["comparison"]["direction_matches"])
        self.assertFalse(audit["comparison"]["affects_active_decision"])
        health = asyncio.run(adapter.health())
        self.assertEqual(health["stock_data_audits"], 1)
        self.assertEqual(health["stock_data_ready"], 1)
        self.assertEqual(health["stock_data_blocked"], 0)
        self.assertEqual(health["stock_candle_successes"], 1)
        self.assertEqual(health["stock_shadow_candidates"], 1)
        self.assertEqual(health["stock_shadow_long"], 1)
        self.assertEqual(health["stock_shadow_risk_plans"], 1)
        self.assertEqual(health["stock_shadow_risk_blocked"], 0)

        seen = []
        adapter.event_bus.subscribe(STOCK_ANALYSIS_FINISHED, seen.append)
        adapter._publish_analysis_finished(
            {
                "symbol": "AAPL",
                "timeframe": "1d",
                "direction": "LONG",
                "stock_data_audit": audit["audit"],
                "stock_shadow_candidate": audit["shadow_candidate"],
                "stock_shadow_comparison": audit["comparison"],
                "stock_shadow_risk": audit["shadow_risk"],
                "stock_candle_source": audit["candle_source"],
                "stock_candle_count": audit["candle_count"],
                "stock_candle_error": audit["candle_error"],
            }
        )
        published = seen[0].payload["payload"]
        self.assertEqual(published["direction"], "LONG")
        self.assertFalse(any(key.startswith("stock_shadow_") for key in published))
        self.assertNotIn("stock_data_audit", published)
        self.assertNotIn("stock_candle_source", published)

    def test_observer_requires_explicit_stock_data_policy(self) -> None:
        with self.assertRaises(ValueError):
            StockAdapter(EventBus(), STOCK_PATH, stock_data_observer_enabled=True)

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
