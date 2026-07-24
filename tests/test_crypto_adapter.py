"""Tests for the PandorickKi crypto adapter."""

from __future__ import annotations

import asyncio
import unittest
from pathlib import Path

from adapters.crypto_adapter import CRYPTO_ANALYSIS_FINISHED, CryptoAdapter
from event_bus import EventBus


CRYPTO_PROJECT = Path("C:/Users/Admin/Desktop/VIP-Trade-Engine-4.5(Monitor)")


class CryptoAdapterTest(unittest.TestCase):
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
