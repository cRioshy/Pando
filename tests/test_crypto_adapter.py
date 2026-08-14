"""Tests for the PandorickKi crypto adapter."""

from __future__ import annotations

import asyncio
import unittest
from pathlib import Path

from adapters.crypto_adapter import (
    CRYPTO_ANALYSIS_FINISHED,
    CRYPTO_SERVICE_ERROR,
    CRYPTO_SERVICE_HEARTBEAT,
    CryptoAdapter,
)
from adapters.crypto_market_data_service import (
    CryptoMarketDataError,
    CryptoMarketDataSnapshot,
)
from event_bus import EventBus


CRYPTO_PROJECT = Path("C:/Users/Admin/Desktop/VIP-Trade-Engine-4.5(Monitor)")


class CryptoAdapterTest(unittest.TestCase):
    class _SuccessfulMarketService:
        def fetch(self, symbol: str, timeframe: str, limit: int) -> CryptoMarketDataSnapshot:
            candles = [
                {
                    "open": 100.0 + index,
                    "high": 101.0 + index,
                    "low": 99.0 + index,
                    "close": 100.5 + index,
                    "volume": 1000.0 + index,
                }
                for index in range(limit)
            ]
            return CryptoMarketDataSnapshot(
                symbol=symbol,
                timeframe=timeframe,
                candles=candles,
                open_interest=None,
                funding_rate=None,
                diagnostics={
                    "candle_source": "bitget",
                    "open_interest_status": "unavailable",
                    "funding_rate_status": "unavailable",
                    "attempts": [],
                },
            )

    class _FailingMarketService:
        def fetch(self, symbol: str, timeframe: str, limit: int) -> CryptoMarketDataSnapshot:
            del timeframe, limit
            diagnostics = {"candle_source": None, "attempts": [{"source": "binance"}]}
            raise CryptoMarketDataError(
                f"No candle provider available for {symbol}.", diagnostics=diagnostics
            )

    def test_regime_observer_receives_candles_without_changing_analysis_event(self) -> None:
        async def run() -> None:
            submitted = []
            bus = EventBus()
            seen = []
            bus.subscribe(CRYPTO_ANALYSIS_FINISHED, seen.append)
            adapter = CryptoAdapter(
                bus,
                CRYPTO_PROJECT,
                symbols=["BTCUSDT"],
                candle_limit=60,
                test_mode=False,
                market_data_service=self._SuccessfulMarketService(),
                regime_submitter=lambda **item: submitted.append(item) is None,
            )
            await adapter.start()
            try:
                results = await adapter.run_once()
            finally:
                await adapter.stop()

            self.assertEqual(len(submitted), 1)
            self.assertEqual(submitted[0]["asset_type"], "crypto")
            self.assertEqual(submitted[0]["timeframe"], "15m")
            self.assertEqual(len(submitted[0]["candles"]), 60)
            self.assertEqual(submitted[0]["source_event_id"], seen[0].event_id)
            active = seen[0].payload["payload"]
            self.assertEqual(active, results[0])
            self.assertNotIn("market_regime", active)

        asyncio.run(run())

    def test_crypto_adapter_uses_pipeline_without_bot_loop(self) -> None:
        async def run() -> None:
            bus = EventBus()
            adapter = CryptoAdapter(
                bus,
                CRYPTO_PROJECT,
                symbols=["BTCUSDT"],
                test_mode=True,
                persist_existing=False,
            )
            seen = []
            bus.subscribe(CRYPTO_ANALYSIS_FINISHED, seen.append)

            await adapter.start()
            try:
                results = await adapter.run_once()
            finally:
                await adapter.stop()

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["market_type"], "crypto")
            self.assertEqual(results[0]["symbol"], "BTCUSDT")
            self.assertTrue(seen)
            self.assertEqual(seen[0].payload["event_type"], CRYPTO_ANALYSIS_FINISHED)

        asyncio.run(run())

    def test_crypto_adapter_health_reports_test_mode(self) -> None:
        async def run() -> None:
            adapter = CryptoAdapter(EventBus(), CRYPTO_PROJECT, symbols=["ETHUSDT"], test_mode=True)

            await adapter.start()
            try:
                await adapter.run_once()
                health = await adapter.health()
            finally:
                await adapter.stop()

            self.assertTrue(health["healthy"])
            self.assertTrue(health["test_mode"])
            self.assertEqual(health["published_results"], 1)

        asyncio.run(run())

    def test_dashboard_price_prefers_live_spot_price(self) -> None:
        async def run() -> None:
            bus = EventBus()
            adapter = CryptoAdapter(
                bus,
                CRYPTO_PROJECT,
                symbols=["XRPUSDT"],
                test_mode=True,
                live_price_display=True,
            )
            adapter._fetch_live_spot_price = lambda symbol: 2.3456

            await adapter.start()
            try:
                results = await adapter.run_once()
            finally:
                await adapter.stop()

            self.assertEqual(results[0]["price"], 2.3456)
            self.assertEqual(results[0]["current_price"], 2.3456)
            self.assertEqual(results[0]["price_source"], "live_spot_ticker")
            self.assertEqual(results[0]["price_status"], "ok")
            self.assertNotEqual(results[0]["analysis_close"], 2.3456)

        asyncio.run(run())

    def test_dashboard_price_records_bitget_fallback_source(self) -> None:
        async def run() -> None:
            bus = EventBus()
            adapter = CryptoAdapter(
                bus,
                CRYPTO_PROJECT,
                symbols=["ETHUSDT"],
                test_mode=True,
                live_price_display=True,
            )
            adapter._fetch_live_spot_price = lambda symbol: 3650.25
            adapter._last_live_price_source = "bitget"

            await adapter.start()
            try:
                results = await adapter.run_once()
            finally:
                await adapter.stop()

            self.assertEqual(results[0]["price"], 3650.25)
            self.assertEqual(results[0]["current_price"], 3650.25)
            self.assertEqual(results[0]["price_source"], "bitget")

        asyncio.run(run())

    def test_live_analysis_uses_internal_market_service_without_requests(self) -> None:
        async def run() -> None:
            adapter = CryptoAdapter(
                EventBus(),
                CRYPTO_PROJECT,
                symbols=["BTCUSDT"],
                candle_limit=60,
                test_mode=False,
                market_data_service=self._SuccessfulMarketService(),
            )

            await adapter.start()
            try:
                results = await adapter.run_once()
                health = await adapter.health()
            finally:
                await adapter.stop()

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["market_data_diagnostics"]["candle_source"], "bitget")
            self.assertTrue(health["healthy"])
            self.assertIsNone(health["last_error"])

        asyncio.run(run())

    def test_zero_results_publish_error_heartbeat_and_unhealthy_status(self) -> None:
        async def run() -> None:
            bus = EventBus()
            adapter = CryptoAdapter(
                bus,
                CRYPTO_PROJECT,
                symbols=["BTCUSDT"],
                test_mode=False,
                market_data_service=self._FailingMarketService(),
            )
            errors = []
            heartbeats = []
            bus.subscribe(CRYPTO_SERVICE_ERROR, errors.append)
            bus.subscribe(CRYPTO_SERVICE_HEARTBEAT, heartbeats.append)

            await adapter.start()
            try:
                results = await adapter.run_once()
                health = await adapter.health()
            finally:
                await adapter.stop()

            self.assertEqual(results, [])
            self.assertFalse(health["healthy"])
            self.assertEqual(health["last_error_details"]["stage"], "market_data")
            self.assertEqual(errors[-1].payload["payload"]["error_type"], "CryptoMarketDataError")
            self.assertEqual(heartbeats[-1].payload["payload"]["status"], "error")

        asyncio.run(run())

    def test_offline_test_candle_is_not_exposed_as_dashboard_price(self) -> None:
        async def run() -> None:
            adapter = CryptoAdapter(
                EventBus(),
                CRYPTO_PROJECT,
                symbols=["BTCUSDT"],
                test_mode=True,
                live_price_display=True,
            )
            adapter._fetch_live_spot_price = lambda symbol: None

            await adapter.start()
            try:
                results = await adapter.run_once()
            finally:
                await adapter.stop()

            self.assertIsNone(results[0]["price"])
            self.assertIsNone(results[0]["current_price"])
            self.assertIsNotNone(results[0]["analysis_close"])
            self.assertEqual(results[0]["price_source"], "live_unavailable_offline_test_hidden")
            self.assertEqual(results[0]["price_status"], "unavailable")
            self.assertIn("price_attempts", results[0])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
