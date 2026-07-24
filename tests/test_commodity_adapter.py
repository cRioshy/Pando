"""Tests for the commodity adapter."""

from __future__ import annotations

import asyncio
import time
import unittest

from adapters.commodity_adapter import (
    COMMODITY_ANALYSIS_FINISHED,
    COMMODITY_DATA_WARNING,
    COMMODITY_MARKET_DATA_UPDATED,
    CommodityAdapter,
)
from adapters.commodity_price_service import CommodityPriceQuote
from event_bus import EventBus


class FakeCommodityPriceService:
    """Deterministic commodity quote source."""

    def fetch_price(self, symbol: str) -> CommodityPriceQuote:
        return CommodityPriceQuote(
            symbol=symbol,
            label="Gold",
            price=2421.75,
            source="test",
            timestamp=1784780460,
            previous_price=2420.5,
            change_percent=0.052,
        )


class CommodityAdapterTest(unittest.TestCase):
    def test_run_once_publishes_market_and_analysis_events(self) -> None:
        async def run() -> None:
            bus = EventBus()
            market_events = []
            analysis_events = []
            bus.subscribe(COMMODITY_MARKET_DATA_UPDATED, market_events.append)
            bus.subscribe(COMMODITY_ANALYSIS_FINISHED, analysis_events.append)
            adapter = CommodityAdapter(bus, symbols=["GC=F"], price_service=FakeCommodityPriceService())

            await adapter.start()
            try:
                results = await adapter.run_once()
            finally:
                await adapter.stop()

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["market_type"], "commodity")
            self.assertEqual(results[0]["symbol"], "GC=F")
            self.assertEqual(results[0]["label"], "Gold")
            self.assertEqual(results[0]["price"], 2421.75)
            self.assertEqual(results[0]["price_status"], "ok")
            self.assertEqual(results[0]["price_timestamp"], "2026-07-23T04:21:00+00:00")
            self.assertTrue(market_events)
            self.assertTrue(analysis_events)

        asyncio.run(run())

    def test_missing_price_publishes_provider_diagnostics(self) -> None:
        class MissingPriceService:
            def fetch_price(self, symbol: str) -> None:
                return None

            def diagnostics(self) -> dict:
                return {
                    "attempts": [{"source": "yahoo_finance_chart", "status": "error", "error": "network down"}],
                    "last_error": "yahoo_finance_chart: network down",
                }

        async def run() -> None:
            bus = EventBus()
            warnings = []
            bus.subscribe(COMMODITY_DATA_WARNING, warnings.append)
            adapter = CommodityAdapter(bus, symbols=["CL=F"], price_service=MissingPriceService())

            await adapter.start()
            try:
                results = await adapter.run_once()
            finally:
                await adapter.stop()

            self.assertEqual(results, [])
            self.assertTrue(warnings)
            payload = warnings[0].payload["payload"]
            self.assertIn("network down", payload["warning"])
            self.assertEqual(payload["price_attempts"][0]["status"], "error")

        asyncio.run(run())

    def test_symbol_timeout_does_not_block_cycle(self) -> None:
        class SlowCommodityPriceService:
            def fetch_price(self, symbol: str) -> CommodityPriceQuote | None:
                time.sleep(0.3)
                return CommodityPriceQuote(
                    symbol=symbol,
                    label="Silver",
                    price=57.75,
                    source="test",
                )

            def diagnostics(self) -> dict:
                return {"attempts": [], "last_error": None}

        async def run() -> None:
            bus = EventBus()
            warnings = []
            bus.subscribe(COMMODITY_DATA_WARNING, warnings.append)
            adapter = CommodityAdapter(
                bus,
                symbols=["SI=F"],
                price_service=SlowCommodityPriceService(),
                symbol_timeout_seconds=0.1,
            )

            await adapter.start()
            try:
                results = await adapter.run_once()
            finally:
                await adapter.stop()

            self.assertEqual(results, [])
            self.assertEqual(len(warnings), 1)
            payload = warnings[0].payload["payload"]
            self.assertEqual(payload["symbol"], "SI=F")
            self.assertIn("timed out", payload["warning"])
            self.assertEqual(payload["price_attempts"][0]["status"], "timeout")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
