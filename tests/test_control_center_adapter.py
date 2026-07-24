"""Tests for the PandorickKi ControlCenter adapter."""

from __future__ import annotations

import asyncio
import io
import unittest
from contextlib import redirect_stdout

from adapters.control_center_adapter import (
    CONTROL_STATUS_UPDATED,
    ControlCenterAdapter,
)
from event_bus import Event, EventBus
from shared_state import SharedState


class ControlCenterAdapterTest(unittest.TestCase):
    def test_records_events_and_reports_health(self) -> None:
        async def run() -> None:
            bus = EventBus()
            state = SharedState()
            adapter = ControlCenterAdapter(bus, state, print_output=False)

            await adapter.start()
            bus.publish(Event(topic="STOCK_ANALYSIS_FINISHED", source="stock", payload={}))
            bus.publish(Event(topic="BRAIN_DECISION_RECEIVED", source="brain", payload={}))
            health = await adapter.health()
            await adapter.stop()

            self.assertTrue(health["healthy"])
            self.assertEqual(health["event_counts"]["STOCK_ANALYSIS_FINISHED"], 1)
            self.assertEqual(health["event_counts"]["BRAIN_DECISION_RECEIVED"], 1)

        asyncio.run(run())

    def test_run_once_emits_status_event(self) -> None:
        async def run() -> None:
            bus = EventBus()
            state = SharedState()
            state.update_service("stock", "OK", {"events": 4})
            adapter = ControlCenterAdapter(bus, state, print_output=False)

            await adapter.start()
            results = await adapter.run_once()
            await adapter.stop()

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].topic, CONTROL_STATUS_UPDATED)
            self.assertEqual(results[0].payload["services"]["stock"]["status"], "OK")

        asyncio.run(run())

    def test_power_shell_panel_can_be_printed(self) -> None:
        async def run() -> str:
            bus = EventBus()
            state = SharedState()
            state.update_service("stock", "OK")
            adapter = ControlCenterAdapter(bus, state, print_output=True)
            stream = io.StringIO()

            await adapter.start()
            with redirect_stdout(stream):
                await adapter.run_once()
            await adapter.stop()
            return stream.getvalue()

        output = asyncio.run(run())
        self.assertIn("PANDORICK CONTROL CENTER", output)
        self.assertIn("stock", output)

    def test_crypto_trade_update_is_visible_in_snapshot(self) -> None:
        async def run() -> None:
            bus = EventBus()
            state = SharedState()
            adapter = ControlCenterAdapter(bus, state, print_output=False)

            await adapter.start()
            bus.publish(
                Event(
                    topic="CRYPTO_TRADE_UPDATED",
                    source="crypto_trade_tracker",
                    payload={
                        "payload": {
                            "symbol": "BTCUSDT",
                            "direction": "LONG",
                            "entry_price": 100.0,
                            "current_stop_loss": 98.0,
                            "take_profit_1": 103.0,
                            "current_profit_percent": 1.5,
                            "current_price": 101.5,
                            "trade_status": "ACTIVE",
                            "updated_at": "2026-07-11T12:00:00+00:00",
                        }
                    },
                )
            )
            snapshot = await adapter.get_snapshot()
            await adapter.stop()

            crypto = snapshot["last_crypto_analysis"]["BTCUSDT"]
            self.assertEqual(crypto["entry_price"], 100.0)
            self.assertEqual(crypto["current_stop_loss"], 98.0)
            self.assertEqual(crypto["take_profit_1"], 103.0)
            self.assertEqual(crypto["trade_status"], "ACTIVE")

        asyncio.run(run())

    def test_commodity_analysis_is_visible_in_snapshot(self) -> None:
        async def run() -> None:
            bus = EventBus()
            state = SharedState()
            adapter = ControlCenterAdapter(bus, state, print_output=False)

            await adapter.start()
            bus.publish(
                Event(
                    topic="COMMODITY_ANALYSIS_FINISHED",
                    source="commodity",
                    payload={
                        "payload": {
                            "market_type": "commodity",
                            "symbol": "GC=F",
                            "label": "Gold",
                            "direction": "HOLD",
                            "probability": 50.5,
                            "current_price": 2421.75,
                            "price_source": "yahoo_finance_chart",
                            "price_timestamp": "2026-07-23T04:21:00+00:00",
                            "received_at": "2026-07-23T04:21:01+00:00",
                        }
                    },
                )
            )
            snapshot = await adapter.get_snapshot()
            await adapter.stop()

            commodity = snapshot["last_commodity_analysis"]["GC=F"]
            self.assertEqual(commodity["label"], "Gold")
            self.assertEqual(commodity["price"], 2421.75)
            self.assertEqual(snapshot["last_commodity_price"]["GC=F"], 2421.75)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
