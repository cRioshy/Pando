"""Brain adapter for completed PandorickKi decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from adapters.crypto_adapter import CRYPTO_ANALYSIS_FINISHED
from adapters.commodity_adapter import COMMODITY_ANALYSIS_FINISHED
from adapters.stock_adapter import STOCK_ANALYSIS_FINISHED
from brain_event_store import BrainEventWriter, DEFAULT_DAY_WARNING_BYTES, DEFAULT_ROTATION_BYTES
from event_bus import Event, EventBus


BRAIN_SERVICE_STARTED = "BRAIN_SERVICE_STARTED"
BRAIN_DECISION_RECEIVED = "BRAIN_DECISION_RECEIVED"
BRAIN_SERVICE_ERROR = "BRAIN_SERVICE_ERROR"
BRAIN_SERVICE_STOPPED = "BRAIN_SERVICE_STOPPED"
BRAIN_SERVICE_HEARTBEAT = "BRAIN_SERVICE_HEARTBEAT"
AI_LEARNING_UPDATED = "AI_LEARNING_UPDATED"


@dataclass
class BrainAdapterStatus:
    """Runtime status for the brain adapter."""

    name: str = "brain"
    running: bool = False
    healthy: bool = True
    received_decisions: int = 0
    last_symbol: str | None = None
    last_error: str | None = None
    last_event_at: str | None = None


class BrainAdapter:
    """Receive completed decisions and persist them for the brain layer."""

    name = "brain"

    def __init__(
        self,
        event_bus: EventBus,
        storage_path: Path,
        *,
        event_root: Path | None = None,
        rotation_bytes: int = DEFAULT_ROTATION_BYTES,
        day_warning_bytes: int = DEFAULT_DAY_WARNING_BYTES,
    ) -> None:
        self.event_bus = event_bus
        self.storage_path = storage_path
        self.event_root = event_root or storage_path.parent / "brain_events"
        self.event_writer = BrainEventWriter(
            self.event_root,
            rotation_bytes=rotation_bytes,
            day_warning_bytes=day_warning_bytes,
        )
        self.status = BrainAdapterStatus()
        self._subscribed = False

    async def start(self) -> None:
        """Subscribe to completed market decisions."""

        if not self._subscribed:
            self.event_bus.subscribe(STOCK_ANALYSIS_FINISHED, self._handle_stock_decision)
            self.event_bus.subscribe(CRYPTO_ANALYSIS_FINISHED, self._handle_market_decision)
            self.event_bus.subscribe(COMMODITY_ANALYSIS_FINISHED, self._handle_market_decision)
            self._subscribed = True
        self.status.running = True
        self.status.healthy = True
        self.status.last_error = None
        self._publish(BRAIN_SERVICE_STARTED, {"status": "started"})

    async def stop(self) -> None:
        """Stop the adapter. Subscriptions remain harmless for process lifetime."""

        self.status.running = False
        self._publish(BRAIN_SERVICE_STOPPED, {"status": "stopped"})

    async def run_once(self) -> list[Event]:
        """Emit a heartbeat; decision processing happens through event callbacks."""

        return [
            Event(
                topic=BRAIN_SERVICE_HEARTBEAT,
                source=self.name,
                payload={
                    "status": "ok",
                    "received_decisions": self.status.received_decisions,
                },
            )
        ]

    async def health(self) -> dict[str, Any]:
        """Return adapter health."""

        return {
            "name": self.status.name,
            "running": self.status.running,
            "healthy": self.status.healthy,
            "received_decisions": self.status.received_decisions,
            "last_symbol": self.status.last_symbol,
            "last_error": self.status.last_error,
        }

    async def get_status(self) -> dict[str, Any]:
        """Return detailed status."""

        data = await self.health()
        data["last_event_at"] = self.status.last_event_at
        data["storage_path"] = str(self.storage_path)
        data["event_root"] = str(self.event_root)
        return data

    def _handle_stock_decision(self, event: Event) -> None:
        """Store one completed stock decision event."""

        self._handle_market_decision(event)

    def _handle_market_decision(self, event: Event) -> None:
        """Store one completed market decision event."""

        try:
            payload = event.payload.get("payload", {})
            record = {
                "received_at": datetime.now(UTC).isoformat(),
                "source_event_id": event.event_id,
                "event_type": event.payload.get("event_type", event.topic),
                "source": event.source,
                "market_type": payload.get("market_type"),
                "symbol": payload.get("symbol"),
                "direction": payload.get("direction"),
                "probability": payload.get("probability"),
                "source_timestamp": payload.get("source_timestamp"),
                "payload": payload,
            }
            self._append_jsonl(record)
            self.status.received_decisions += 1
            self.status.last_symbol = str(payload.get("symbol"))
            self.status.last_event_at = record["received_at"]
            self.status.healthy = True
            self.status.last_error = None
            self._publish(
                BRAIN_DECISION_RECEIVED,
                {
                    "symbol": self.status.last_symbol,
                    "market_type": record["market_type"],
                    "direction": record["direction"],
                    "probability": record["probability"],
                    "confidence": record["probability"],
                    "price": payload.get("price"),
                    "current_price": payload.get("current_price") or payload.get("price"),
                    "indicators": payload.get("indicators"),
                    "risk": payload.get("risk"),
                    "raw_result": payload.get("raw_result"),
                    "received_decisions": self.status.received_decisions,
                    "source_event_id": record["source_event_id"],
                    "source_timestamp": record["source_timestamp"],
                    "received_at": record["received_at"],
                },
            )
            self._publish(
                AI_LEARNING_UPDATED,
                {
                    "status": "updated",
                    "updates": self.status.received_decisions,
                    "memory_size": self.status.received_decisions,
                    "last_symbol": self.status.last_symbol,
                    "last_direction": record["direction"],
                    "last_confidence": record["probability"],
                    "last_update_at": record["received_at"],
                },
            )
        except Exception as exc:
            self.status.healthy = False
            self.status.last_error = str(exc)
            self._publish(BRAIN_SERVICE_ERROR, {"error": str(exc)})

    def _append_jsonl(self, record: dict[str, Any]) -> None:
        """Append one event to the rotating brain event storage."""

        self.event_writer.append(record)

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish a brain adapter lifecycle event."""

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
