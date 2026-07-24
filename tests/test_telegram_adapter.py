"""Tests for TelegramAdapter dry-run behavior."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from adapters.crypto_adapter import CRYPTO_ANALYSIS_FINISHED
from adapters.crypto_trade_tracker import CRYPTO_TRADE_UPDATED
from adapters.telegram_adapter import (
    TELEGRAM_DRY_RUN_RECORDED,
    TELEGRAM_MESSAGE_READY,
    TELEGRAM_MESSAGE_SENT,
    TELEGRAM_SERVICE_ERROR,
    TelegramAdapter,
)
from event_bus import Event, EventBus


def analysis_event() -> Event:
    return Event(
        topic=CRYPTO_ANALYSIS_FINISHED,
        source="crypto",
        payload={
            "symbol": "BTCUSDT",
            "payload": {
                "market_type": "crypto",
                "symbol": "BTCUSDT",
                "direction": "LONG",
                "probability": 74,
                "price": 58420.1,
            },
        },
    )


class TelegramAdapterTest(unittest.TestCase):
    def test_disabled_adapter_builds_ready_message_but_does_not_send(self) -> None:
        async def run() -> None:
            bus = EventBus()
            adapter = TelegramAdapter(bus, enabled=False, dry_run=True)
            seen = []
            bus.subscribe("*", seen.append)

            await adapter.start()
            bus.publish(analysis_event())
            await adapter.stop()

            topics = [event.topic for event in seen]
            self.assertIn(TELEGRAM_MESSAGE_READY, topics)
            self.assertNotIn(TELEGRAM_DRY_RUN_RECORDED, topics)
            self.assertNotIn(TELEGRAM_MESSAGE_SENT, topics)

        asyncio.run(run())

    def test_dry_run_records_message_without_live_send(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                log_file = Path(temp) / "telegram.jsonl"
                bus = EventBus()
                adapter = TelegramAdapter(bus, enabled=True, dry_run=True, log_file=log_file)
                seen = []
                bus.subscribe("*", seen.append)

                await adapter.start()
                bus.publish(analysis_event())
                await adapter.stop()

                topics = [event.topic for event in seen]
                records = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]

                self.assertIn(TELEGRAM_DRY_RUN_RECORDED, topics)
                self.assertNotIn(TELEGRAM_MESSAGE_SENT, topics)
                self.assertEqual(len(records), 1)
                self.assertIn("BTCUSDT", records[0]["message"])

        asyncio.run(run())

    def test_missing_live_credentials_publish_error_without_crashing(self) -> None:
        async def run() -> None:
            bus = EventBus()
            adapter = TelegramAdapter(bus, enabled=True, dry_run=False)
            seen = []
            bus.subscribe("*", seen.append)

            await adapter.start()
            bus.publish(analysis_event())
            await asyncio.sleep(0.05)
            health = await adapter.health()
            await adapter.stop()

            topics = [event.topic for event in seen]
            self.assertIn(TELEGRAM_SERVICE_ERROR, topics)
            self.assertFalse(health["healthy"])

        asyncio.run(run())

    def test_trade_update_message_contains_entry_stop_and_profit(self) -> None:
        async def run() -> None:
            bus = EventBus()
            adapter = TelegramAdapter(bus, enabled=False, dry_run=True)
            seen = []
            bus.subscribe(TELEGRAM_MESSAGE_READY, seen.append)

            await adapter.start()
            bus.publish(
                Event(
                    topic=CRYPTO_TRADE_UPDATED,
                    source="crypto_trade_tracker",
                    payload={
                        "payload": {
                            "market_type": "crypto",
                            "symbol": "BTCUSDT",
                            "direction": "LONG",
                            "entry_price": 100.0,
                            "current_stop_loss": 98.0,
                            "take_profit_1": 103.0,
                            "current_profit_percent": 1.5,
                            "price": 101.5,
                            "trade_status": "ACTIVE",
                        }
                    },
                )
            )
            await adapter.stop()

            message = seen[-1].payload["payload"]["message"]
            self.assertIn("Entry: 100.0000", message)
            self.assertIn("Stop: 98.0000", message)
            self.assertIn("P/L: +1.50%", message)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
