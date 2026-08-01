"""Tests for simulated crypto trade tracking."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from adapters.crypto_adapter import CRYPTO_ANALYSIS_FINISHED
from adapters.crypto_trade_tracker import CRYPTO_TRADE_UPDATED, CryptoTradeTracker
from adapters.decision_signal_adapter import SIGNAL_CREATED
from event_bus import Event, EventBus


def signal(direction: str, *, price: float = 100.0, symbol: str = "BTCUSDT") -> Event:
    return Event(
        topic=SIGNAL_CREATED,
        source="decision_core",
        payload={
            "payload": {
                "signal_id": "signal-1",
                "market_type": "crypto",
                "symbol": symbol,
                "direction": direction,
                "probability": 74,
                "current_price": price,
                "indicators": {"atr": 2.0},
                "raw_result": {
                    "market_data": {
                        "candles": [
                            {"low": 96.0 + index * 0.01, "high": 104.0 + index * 0.01}
                            for index in range(20)
                        ]
                    }
                },
            }
        },
    )


def analysis(price: float, *, symbol: str = "BTCUSDT") -> Event:
    return Event(
        topic=CRYPTO_ANALYSIS_FINISHED,
        source="crypto",
        payload={
            "payload": {
                "market_type": "crypto",
                "symbol": symbol,
                "direction": "LONG",
                "current_price": price,
                "price": price,
                "indicators": {"atr": 2.0},
            }
        },
    )


class CryptoTradeTrackerTest(unittest.TestCase):
    def test_compact_market_context_is_preferred_over_legacy_candles(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            tracker = CryptoTradeTracker(
                EventBus(),
                active_file=Path(temp) / "active.json",
                history_file=Path(temp) / "history.jsonl",
            )
            data = {
                "market_context": {
                    "recent_swing_low": 98.5,
                    "recent_swing_high": 101.5,
                },
                "raw_result": {
                    "market_data": {
                        "candles": [
                            {"low": 90.0, "high": 110.0},
                        ]
                    }
                },
            }

            self.assertEqual(tracker._swing_price("LONG", data), 98.5)
            self.assertEqual(tracker._swing_price("SHORT", data), 101.5)

    def test_legacy_candles_remain_a_swing_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            tracker = CryptoTradeTracker(
                EventBus(),
                active_file=Path(temp) / "active.json",
                history_file=Path(temp) / "history.jsonl",
            )
            data = {
                "raw_result": {
                    "market_data": {
                        "candles": [
                            {"low": 97.0, "high": 103.0},
                            {"low": 96.0, "high": 104.0},
                        ]
                    }
                }
            }

            self.assertEqual(tracker._swing_price("LONG", data), 96.0)
            self.assertEqual(tracker._swing_price("SHORT", data), 104.0)

    def test_long_signal_creates_entry_with_stop_below_entry(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                updates = []
                bus.subscribe(CRYPTO_TRADE_UPDATED, updates.append)
                tracker = CryptoTradeTracker(
                    bus,
                    active_file=Path(temp) / "active.json",
                    history_file=Path(temp) / "history.jsonl",
                )

                await tracker.start()
                bus.publish(signal("LONG", price=100.0))
                await tracker.stop()

                payload = updates[-1].payload["payload"]
                self.assertEqual(payload["trade_status"], "ACTIVE")
                self.assertEqual(payload["entry_price"], 100.0)
                self.assertLess(payload["current_stop_loss"], payload["entry_price"])
                self.assertGreater(payload["take_profit_1"], payload["entry_price"])

        asyncio.run(run())

    def test_short_signal_creates_stop_above_entry(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                updates = []
                bus.subscribe(CRYPTO_TRADE_UPDATED, updates.append)
                tracker = CryptoTradeTracker(
                    bus,
                    active_file=Path(temp) / "active.json",
                    history_file=Path(temp) / "history.jsonl",
                )

                await tracker.start()
                bus.publish(signal("SHORT", price=100.0))
                await tracker.stop()

                payload = updates[-1].payload["payload"]
                self.assertGreater(payload["current_stop_loss"], payload["entry_price"])
                self.assertLess(payload["take_profit_1"], payload["entry_price"])

        asyncio.run(run())

    def test_wait_signal_does_not_create_artificial_entry(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                updates = []
                bus.subscribe(CRYPTO_TRADE_UPDATED, updates.append)
                tracker = CryptoTradeTracker(
                    bus,
                    active_file=Path(temp) / "active.json",
                    history_file=Path(temp) / "history.jsonl",
                )

                await tracker.start()
                bus.publish(signal("WAIT", price=100.0))
                health = await tracker.health()
                await tracker.stop()

                self.assertEqual(updates, [])
                self.assertEqual(health["active_trades"], 0)
                self.assertEqual(health["ignored_signals"], 1)

        asyncio.run(run())

    def test_active_entry_is_not_overwritten_and_updates_profit(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                tracker = CryptoTradeTracker(
                    bus,
                    active_file=Path(temp) / "active.json",
                    history_file=Path(temp) / "history.jsonl",
                )

                await tracker.start()
                bus.publish(signal("LONG", price=100.0))
                bus.publish(signal("LONG", price=120.0))
                bus.publish(analysis(103.0))
                await tracker.stop()

                active = json.loads((Path(temp) / "active.json").read_text(encoding="utf-8"))
                trade = active["BTCUSDT"]
                self.assertEqual(trade["entry_price"], 100.0)
                self.assertGreater(trade["current_profit_percent"], 0)
                self.assertGreaterEqual(trade["max_profit_percent"], trade["current_profit_percent"])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
