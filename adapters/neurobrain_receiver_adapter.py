"""Read-only NeuroBrain receiver for PandorickKi event coexistence."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from event_bus import Event, EventBus
from jsonl_ledger import RotatingJsonlLedger


NEUROBRAIN_RECEIVER_STARTED = "NEUROBRAIN_RECEIVER_STARTED"
NEUROBRAIN_EVENT_RECEIVED = "NEUROBRAIN_EVENT_RECEIVED"
NEUROBRAIN_RECEIVER_HEARTBEAT = "NEUROBRAIN_RECEIVER_HEARTBEAT"
NEUROBRAIN_RECEIVER_ERROR = "NEUROBRAIN_RECEIVER_ERROR"
NEUROBRAIN_RECEIVER_STOPPED = "NEUROBRAIN_RECEIVER_STOPPED"

DEFAULT_NEUROBRAIN_TOPICS = frozenset(
    {
        "CRYPTO_MARKET_DATA_UPDATED",
        "STOCK_MARKET_DATA_UPDATED",
        "COMMODITY_MARKET_DATA_UPDATED",
        "CRYPTO_ANALYSIS_FINISHED",
        "STOCK_ANALYSIS_FINISHED",
        "COMMODITY_ANALYSIS_FINISHED",
        "BRAIN_DECISION_RECEIVED",
        "DECISION_CREATED",
        "SIGNAL_CREATED",
        "SIMULATED_TRADE_OPENED",
        "SIMULATED_TRADE_UPDATED",
        "SIMULATED_TRADE_CLOSED",
        "AI_LEARNING_UPDATED",
    }
)


@dataclass
class NeuroBrainReceiverStatus:
    """Runtime state for the read-only NeuroBrain receiver."""

    name: str = "neurobrain_receiver"
    running: bool = False
    healthy: bool = True
    received_events: int = 0
    ignored_events: int = 0
    duplicate_events: int = 0
    last_topic: str | None = None
    last_symbol: str | None = None
    last_error: str | None = None
    last_event_at: str | None = None
    inbox_path: str | None = None
    status_path: str | None = None


class NeuroBrainReceiverAdapter:
    """Mirror selected PandorickKi events into a separate NeuroBrain inbox.

    The receiver is intentionally read-only from PandorickKi's perspective. It
    does not mutate SharedState, Brain memory, decisions, signals or trading
    adapters. It only stores normalized event copies for later NeuroBrain
    research, quality checks and simulated outcome evaluation.
    """

    name = "neurobrain_receiver"

    def __init__(
        self,
        event_bus: EventBus,
        *,
        inbox_file: Path,
        status_file: Path,
        allowed_topics: set[str] | frozenset[str] | None = None,
        ledger_rotation_bytes: int = 128 * 1024 * 1024,
    ) -> None:
        self.event_bus = event_bus
        self.inbox_file = inbox_file
        self.status_file = status_file
        self.allowed_topics = frozenset(allowed_topics or DEFAULT_NEUROBRAIN_TOPICS)
        self.ledger = RotatingJsonlLedger(inbox_file, max_bytes=ledger_rotation_bytes)
        self.status = NeuroBrainReceiverStatus(
            inbox_path=str(inbox_file),
            status_path=str(status_file),
        )
        self._subscribed = False
        self._lock = RLock()
        self._seen_event_ids: set[str] = set()

    async def start(self) -> None:
        """Start receiving selected EventBus events."""

        if not self._subscribed:
            self.event_bus.subscribe("*", self._handle_event)
            self._subscribed = True
        with self._lock:
            self.status.running = True
            self.status.healthy = True
            self.status.last_error = None
        self._write_status()
        self._publish(NEUROBRAIN_RECEIVER_STARTED, {"status": "started", "mode": "read_only"})

    async def stop(self) -> None:
        """Stop receiving events and persist the latest status."""

        if self._subscribed:
            self.event_bus.unsubscribe("*", self._handle_event)
            self._subscribed = False
        with self._lock:
            self.status.running = False
        self._write_status()
        self._publish(NEUROBRAIN_RECEIVER_STOPPED, {"status": "stopped"})

    async def run_once(self) -> list[Event]:
        """Emit a lightweight heartbeat; event capture happens in callbacks."""

        with self._lock:
            payload = {
                "status": "ok" if self.status.healthy else "warning",
                "received_events": self.status.received_events,
                "ignored_events": self.status.ignored_events,
                "duplicate_events": self.status.duplicate_events,
                "last_topic": self.status.last_topic,
            }
        return [Event(topic=NEUROBRAIN_RECEIVER_HEARTBEAT, source=self.name, payload=payload)]

    async def health(self) -> dict[str, Any]:
        """Return public receiver health."""

        with self._lock:
            return {
                "name": self.status.name,
                "running": self.status.running,
                "healthy": self.status.healthy,
                "received_events": self.status.received_events,
                "ignored_events": self.status.ignored_events,
                "duplicate_events": self.status.duplicate_events,
                "last_topic": self.status.last_topic,
                "last_symbol": self.status.last_symbol,
                "last_error": self.status.last_error,
                "inbox_path": self.status.inbox_path,
            }

    def _handle_event(self, event: Event) -> None:
        """Persist one allowed event copy without feeding back into PandorickKi."""

        if event.source == self.name or event.topic.startswith("NEUROBRAIN_"):
            return
        if event.topic not in self.allowed_topics:
            with self._lock:
                self.status.ignored_events += 1
            return

        with self._lock:
            if event.event_id in self._seen_event_ids:
                self.status.duplicate_events += 1
                return
            self._seen_event_ids.add(event.event_id)

        try:
            record = self._to_record(event)
            self.ledger.append(record)
            with self._lock:
                self.status.received_events += 1
                self.status.last_topic = event.topic
                self.status.last_symbol = record.get("symbol")
                self.status.last_event_at = record["received_at"]
                self.status.healthy = True
                self.status.last_error = None
            self._write_status()
            self._publish(
                NEUROBRAIN_EVENT_RECEIVED,
                {
                    "source_event_id": event.event_id,
                    "topic": event.topic,
                    "symbol": record.get("symbol"),
                    "market_type": record.get("market_type"),
                    "received_events": self.status.received_events,
                },
            )
        except Exception as exc:
            with self._lock:
                self.status.healthy = False
                self.status.last_error = str(exc)
            self._write_status()
            self._publish(NEUROBRAIN_RECEIVER_ERROR, {"error": str(exc), "topic": event.topic})

    def _to_record(self, event: Event) -> dict[str, Any]:
        """Convert an EventBus event to a stable NeuroBrain inbox record."""

        payload = event.payload if isinstance(event.payload, dict) else {"raw_payload": event.payload}
        nested_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
        return {
            "received_at": datetime.now(UTC).isoformat(),
            "source_event_id": event.event_id,
            "topic": event.topic,
            "source": event.source,
            "source_created_at": event.created_at,
            "event_type": payload.get("event_type", event.topic),
            "market_type": nested_payload.get("market_type") or payload.get("market_type"),
            "symbol": nested_payload.get("symbol") or payload.get("symbol"),
            "decision_id": nested_payload.get("decision_id") or payload.get("decision_id"),
            "signal_id": nested_payload.get("signal_id") or payload.get("signal_id"),
            "direction": nested_payload.get("direction") or payload.get("direction"),
            "probability": nested_payload.get("probability") or payload.get("probability"),
            "source_timestamp": nested_payload.get("source_timestamp") or payload.get("source_timestamp"),
            "payload": payload,
        }

    def _write_status(self) -> None:
        """Atomically write a small public receiver status file."""

        with self._lock:
            payload = {
                "name": self.status.name,
                "running": self.status.running,
                "healthy": self.status.healthy,
                "received_events": self.status.received_events,
                "ignored_events": self.status.ignored_events,
                "duplicate_events": self.status.duplicate_events,
                "last_topic": self.status.last_topic,
                "last_symbol": self.status.last_symbol,
                "last_error": self.status.last_error,
                "last_event_at": self.status.last_event_at,
                "inbox_path": str(self.inbox_file),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.status_file.with_suffix(self.status_file.suffix + ".tmp")
        text = json.dumps(payload, ensure_ascii=True, indent=2)
        json.loads(text)
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.status_file)

    def _publish(self, topic: str, payload: dict[str, Any]) -> None:
        """Publish receiver lifecycle/status events."""

        self.event_bus.publish(
            Event(
                topic=topic,
                source=self.name,
                payload={
                    "event_type": topic,
                    "source": self.name,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "payload": payload,
                },
            )
        )
