"""Telegram adapter for finished PandorickKi messages.

The adapter defaults to dry-run mode. It never imports legacy Telegram modules
and never reads tokens from the old crypto bot.
"""

from __future__ import annotations

import asyncio
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from adapters.crypto_adapter import CRYPTO_ANALYSIS_FINISHED
from adapters.crypto_trade_tracker import CRYPTO_TRADE_UPDATED
from adapters.stock_adapter import STOCK_ANALYSIS_FINISHED
from event_bus import Event, EventBus


TELEGRAM_SERVICE_STARTED = "TELEGRAM_SERVICE_STARTED"
TELEGRAM_SERVICE_STOPPED = "TELEGRAM_SERVICE_STOPPED"
TELEGRAM_MESSAGE_READY = "TELEGRAM_MESSAGE_READY"
TELEGRAM_DRY_RUN_RECORDED = "TELEGRAM_DRY_RUN_RECORDED"
TELEGRAM_MESSAGE_SENT = "TELEGRAM_MESSAGE_SENT"
TELEGRAM_SERVICE_ERROR = "TELEGRAM_SERVICE_ERROR"
TELEGRAM_SERVICE_HEARTBEAT = "TELEGRAM_SERVICE_HEARTBEAT"


@dataclass
class TelegramAdapterStatus:
    """Runtime status for TelegramAdapter."""

    name: str = "telegram"
    running: bool = False
    healthy: bool = True
    enabled: bool = False
    dry_run: bool = True
    messages_ready: int = 0
    messages_sent: int = 0
    dry_run_records: int = 0
    last_message: str | None = None
    last_error: str | None = None
    last_event_at: str | None = None


class TelegramAdapter:
    """Build and optionally send Telegram messages from completed decisions."""

    name = "telegram"

    def __init__(
        self,
        event_bus: EventBus,
        *,
        enabled: bool = False,
        dry_run: bool = True,
        bot_token: str | None = None,
        chat_id: str | None = None,
        log_file: Path | None = None,
    ) -> None:
        self.event_bus = event_bus
        self.enabled = enabled
        self.dry_run = dry_run
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.log_file = log_file or Path("data/telegram_dry_run.jsonl")
        self.status = TelegramAdapterStatus(enabled=enabled, dry_run=dry_run)
        self._subscribed = False

    async def start(self) -> None:
        """Subscribe to completed market analysis events."""

        if not self._subscribed:
            self.event_bus.subscribe(CRYPTO_ANALYSIS_FINISHED, self._handle_finished_analysis)
            self.event_bus.subscribe(STOCK_ANALYSIS_FINISHED, self._handle_finished_analysis)
            self.event_bus.subscribe(CRYPTO_TRADE_UPDATED, self._handle_finished_analysis)
            self._subscribed = True
        self.status.running = True
        self.status.healthy = True
        self.status.last_error = None
        self._publish(
            TELEGRAM_SERVICE_STARTED,
            {"enabled": self.enabled, "dry_run": self.dry_run},
        )

    async def stop(self) -> None:
        """Stop the adapter."""

        self.status.running = False
        self._publish(TELEGRAM_SERVICE_STOPPED, {"status": "stopped"})

    async def run_once(self) -> list[Event]:
        """Emit a heartbeat; event callbacks do message work."""

        return [
            Event(
                topic=TELEGRAM_SERVICE_HEARTBEAT,
                source=self.name,
                payload={
                    "enabled": self.enabled,
                    "dry_run": self.dry_run,
                    "messages_ready": self.status.messages_ready,
                    "messages_sent": self.status.messages_sent,
                    "dry_run_records": self.status.dry_run_records,
                },
            )
        ]

    async def health(self) -> dict[str, Any]:
        """Return adapter health."""

        return {
            "name": self.name,
            "running": self.status.running,
            "healthy": self.status.healthy,
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "messages_ready": self.status.messages_ready,
            "messages_sent": self.status.messages_sent,
            "dry_run_records": self.status.dry_run_records,
            "last_error": self.status.last_error,
        }

    def get_status(self) -> dict[str, Any]:
        """Return synchronous status."""

        return {
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "messages_ready": self.status.messages_ready,
            "messages_sent": self.status.messages_sent,
            "dry_run_records": self.status.dry_run_records,
            "last_message": self.status.last_message,
            "last_error": self.status.last_error,
            "last_event_at": self.status.last_event_at,
        }

    def _handle_finished_analysis(self, event: Event) -> None:
        """Build a Telegram message from a completed analysis event."""

        try:
            payload = event.payload.get("payload", {})
            message = self._build_message(event.topic, payload)
            self.status.messages_ready += 1
            self.status.last_message = message
            self.status.last_event_at = datetime.now(UTC).isoformat()
            self._publish(
                TELEGRAM_MESSAGE_READY,
                {
                    "source_event_id": event.event_id,
                    "topic": event.topic,
                    "message": message,
                    "enabled": self.enabled,
                    "dry_run": self.dry_run,
                },
            )

            if not self.enabled:
                return
            if self.dry_run:
                self._record_dry_run(event, message)
                return
            asyncio.create_task(self._send_live_message(message))
        except Exception as exc:
            self.status.healthy = False
            self.status.last_error = str(exc)
            self._publish(TELEGRAM_SERVICE_ERROR, {"error": str(exc)})

    def _build_message(self, event_topic: str, payload: dict[str, Any]) -> str:
        """Format one completed market decision for Telegram."""

        market_type = str(payload.get("market_type") or "market").upper()
        symbol = payload.get("symbol", "-")
        direction = payload.get("direction", "-")
        probability = payload.get("probability")
        price = payload.get("price")
        entry = payload.get("entry_price")
        stop = payload.get("current_stop_loss")
        tp1 = payload.get("take_profit_1")
        profit = payload.get("current_profit_percent")
        trade_status = payload.get("trade_status")
        probability_text = "-" if probability is None else f"{float(probability):.2f}%"
        price_text = "-" if price is None else f"{float(price):,.4f}"
        trade_lines = ""
        if entry is not None or stop is not None or tp1 is not None:
            entry_text = "-" if entry is None else f"{float(entry):,.4f}"
            stop_text = "-" if stop is None else f"{float(stop):,.4f}"
            tp1_text = "-" if tp1 is None else f"{float(tp1):,.4f}"
            profit_text = "-" if profit is None else f"{float(profit):+.2f}%"
            trade_lines = (
                f"Entry: {entry_text}\n"
                f"Stop: {stop_text}\n"
                f"TP1: {tp1_text}\n"
                f"P/L: {profit_text}\n"
                f"Trade Status: {trade_status or '-'}\n"
            )
        return (
            "PandorickKi Signal\n"
            f"Type: {market_type}\n"
            f"Symbol: {symbol}\n"
            f"Direction: {direction}\n"
            f"Probability: {probability_text}\n"
            f"{trade_lines}"
            f"Price: {price_text}\n"
            f"Source: {event_topic}"
        )

    def _record_dry_run(self, event: Event, message: str) -> None:
        """Persist one dry-run Telegram message."""

        record = {
            "recorded_at": datetime.now(UTC).isoformat(),
            "source_event_id": event.event_id,
            "source_topic": event.topic,
            "message": message,
        }
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
        self.status.dry_run_records += 1
        self._publish(
            TELEGRAM_DRY_RUN_RECORDED,
            {
                "source_event_id": event.event_id,
                "log_file": str(self.log_file),
                "message": message,
            },
        )

    async def _send_live_message(self, message: str) -> None:
        """Send one Telegram message using the Bot API."""

        if not self.bot_token or not self.chat_id:
            self.status.healthy = False
            self.status.last_error = "Telegram token or chat id missing."
            self._publish(TELEGRAM_SERVICE_ERROR, {"error": self.status.last_error})
            return

        try:
            await asyncio.to_thread(self._send_live_message_sync, message)
            self.status.messages_sent += 1
            self.status.healthy = True
            self.status.last_error = None
            self._publish(TELEGRAM_MESSAGE_SENT, {"message": message})
        except Exception as exc:
            self.status.healthy = False
            self.status.last_error = str(exc)
            self._publish(TELEGRAM_SERVICE_ERROR, {"error": str(exc)})

    def _send_live_message_sync(self, message: str) -> None:
        """Synchronous Telegram HTTP call for asyncio.to_thread."""

        assert self.bot_token is not None
        assert self.chat_id is not None
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": self.chat_id, "text": message}).encode("utf-8")
        request = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read()

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish one Telegram lifecycle event."""

        event = Event(
            topic=event_type,
            source=self.name,
            payload={
                "event_type": event_type,
                "source": self.name,
                "timestamp": datetime.now(UTC).isoformat(),
                "payload": payload,
            },
        )
        event.payload["event_id"] = event.event_id
        self.event_bus.publish(event)
