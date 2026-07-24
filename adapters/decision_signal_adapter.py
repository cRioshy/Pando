"""Final decision and signal bridge for PandorickKi."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from adapters.brain_adapter import BRAIN_DECISION_RECEIVED
from event_bus import Event, EventBus
from jsonl_ledger import RotatingJsonlLedger


DECISION_CREATED = "DECISION_CREATED"
SIGNAL_CREATED = "SIGNAL_CREATED"
DECISION_SIGNAL_SERVICE_STARTED = "DECISION_SIGNAL_SERVICE_STARTED"
DECISION_SIGNAL_SERVICE_STOPPED = "DECISION_SIGNAL_SERVICE_STOPPED"
DECISION_SIGNAL_SERVICE_HEARTBEAT = "DECISION_SIGNAL_SERVICE_HEARTBEAT"
DECISION_SIGNAL_SERVICE_ERROR = "DECISION_SIGNAL_SERVICE_ERROR"


@dataclass
class DecisionSignalStatus:
    """Runtime status for the final decision bridge."""

    name: str = "decision_core"
    running: bool = False
    healthy: bool = True
    decisions_created: int = 0
    signals_created: int = 0
    decisions_persisted: int = 0
    signals_persisted: int = 0
    duplicates_ignored: int = 0
    last_symbol: str | None = None
    last_error: str | None = None
    last_event_at: str | None = None


class DecisionSignalAdapter:
    """Convert Brain decisions into final platform decisions and signals."""

    name = "decision_core"

    def __init__(
        self,
        event_bus: EventBus,
        *,
        decisions_file: Path | None = None,
        signals_file: Path | None = None,
        ledger_rotation_bytes: int = 128 * 1024 * 1024,
    ) -> None:
        self.event_bus = event_bus
        self.status = DecisionSignalStatus()
        self.decisions_file = decisions_file
        self.signals_file = signals_file
        self.ledger_rotation_bytes = ledger_rotation_bytes
        self._subscribed = False
        self._seen_source_events: set[str] = set()
        self._lock = RLock()

    async def start(self) -> None:
        """Subscribe to Brain decision events."""

        if not self._subscribed:
            self.event_bus.subscribe(BRAIN_DECISION_RECEIVED, self._handle_brain_decision)
            self._subscribed = True
        self.status.running = True
        self.status.healthy = True
        self.status.last_error = None
        self._publish_lifecycle(DECISION_SIGNAL_SERVICE_STARTED, {"status": "started"})

    async def stop(self) -> None:
        """Stop the adapter."""

        self.status.running = False
        self._publish_lifecycle(DECISION_SIGNAL_SERVICE_STOPPED, {"status": "stopped"})

    async def run_once(self) -> list[Event]:
        """Emit a heartbeat; final decisions are created from event callbacks."""

        return [
            Event(
                topic=DECISION_SIGNAL_SERVICE_HEARTBEAT,
                source=self.name,
                payload={
                    "status": "ok",
                    "decisions_created": self.status.decisions_created,
                    "signals_created": self.status.signals_created,
                    "duplicates_ignored": self.status.duplicates_ignored,
                },
            )
        ]

    async def health(self) -> dict[str, Any]:
        """Return adapter health."""

        return {
            "name": self.status.name,
            "running": self.status.running,
            "healthy": self.status.healthy,
            "decisions_created": self.status.decisions_created,
            "signals_created": self.status.signals_created,
            "decisions_persisted": self.status.decisions_persisted,
            "signals_persisted": self.status.signals_persisted,
            "duplicates_ignored": self.status.duplicates_ignored,
            "last_symbol": self.status.last_symbol,
            "last_error": self.status.last_error,
        }

    def _handle_brain_decision(self, event: Event) -> None:
        """Create one final decision and one browser-ready signal."""

        try:
            data = event.payload.get("payload", event.payload)
            data = data if isinstance(data, dict) else {}
            source_event_id = str(data.get("source_event_id") or event.event_id)
            with self._lock:
                if source_event_id in self._seen_source_events:
                    self.status.duplicates_ignored += 1
                    return
                self._seen_source_events.add(source_event_id)

            decision_payload = self._decision_payload(event, data)
            decision_event = Event(
                topic=DECISION_CREATED,
                source=self.name,
                payload={
                    "event_type": DECISION_CREATED,
                    "source": self.name,
                    "timestamp": decision_payload["created_at"],
                    "payload": decision_payload,
                },
            )
            decision_event.payload["event_id"] = decision_event.event_id
            self.event_bus.publish(decision_event)
            self._append_ledger_record(self.decisions_file, decision_event)

            signal_payload = self._signal_payload(decision_payload, decision_event.event_id)
            signal_event = Event(
                topic=SIGNAL_CREATED,
                source=self.name,
                payload={
                    "event_type": SIGNAL_CREATED,
                    "source": self.name,
                    "timestamp": signal_payload["created_at"],
                    "payload": signal_payload,
                },
            )
            signal_event.payload["event_id"] = signal_event.event_id
            self.event_bus.publish(signal_event)
            self._append_ledger_record(self.signals_file, signal_event)

            with self._lock:
                self.status.decisions_created += 1
                self.status.signals_created += 1
                self.status.decisions_persisted += 1 if self.decisions_file is not None else 0
                self.status.signals_persisted += 1 if self.signals_file is not None else 0
                self.status.last_symbol = str(decision_payload.get("symbol"))
                self.status.last_event_at = signal_payload["created_at"]
                self.status.healthy = True
                self.status.last_error = None
        except Exception as exc:  # noqa: BLE001 - service errors must not stop the platform
            self.status.healthy = False
            self.status.last_error = str(exc)
            self._publish_lifecycle(DECISION_SIGNAL_SERVICE_ERROR, {"error": str(exc)})

    def _decision_payload(self, event: Event, data: dict[str, Any]) -> dict[str, Any]:
        """Build the normalized final decision payload."""

        created_at = datetime.now(UTC).isoformat()
        probability = data.get("probability")
        confidence = data.get("confidence", probability)
        source_event_id = str(data.get("source_event_id") or event.event_id)
        decision_id = str(data.get("decision_id") or uuid5(
            NAMESPACE_URL,
            f"pandorickki:decision:{source_event_id}:{data.get('market_type')}:{data.get('symbol')}:{data.get('direction')}",
        ))
        return {
            "decision_id": f"decision:{decision_id}",
            "market_type": data.get("market_type"),
            "symbol": data.get("symbol"),
            "direction": data.get("direction"),
            "probability": probability,
            "confidence": confidence,
            "price": data.get("price"),
            "current_price": data.get("current_price") or data.get("price"),
            "indicators": data.get("indicators"),
            "risk": data.get("risk"),
            "raw_result": data.get("raw_result"),
            "source_event_id": source_event_id,
            "source_timestamp": data.get("source_timestamp"),
            "created_at": created_at,
            "reason": "Final platform decision created from Brain evaluation.",
        }

    def _signal_payload(self, decision: dict[str, Any], decision_event_id: str) -> dict[str, Any]:
        """Build the normalized final signal payload."""

        return {
            "signal_id": f"signal:{decision_event_id}",
            "decision_id": decision.get("decision_id"),
            "decision_event_id": decision_event_id,
            "market_type": decision.get("market_type"),
            "symbol": decision.get("symbol"),
            "direction": decision.get("direction"),
            "probability": decision.get("probability"),
            "confidence": decision.get("confidence"),
            "price": decision.get("price"),
            "current_price": decision.get("current_price"),
            "indicators": decision.get("indicators"),
            "risk": decision.get("risk"),
            "raw_result": decision.get("raw_result"),
            "ready_for_telegram": True,
            "created_at": datetime.now(UTC).isoformat(),
        }

    def _publish_lifecycle(self, topic: str, payload: dict[str, Any]) -> None:
        """Publish one lifecycle event."""

        event = Event(
            topic=topic,
            source=self.name,
            payload={
                "event_type": topic,
                "source": self.name,
                "timestamp": datetime.now(UTC).isoformat(),
                "payload": payload,
            },
        )
        event.payload["event_id"] = event.event_id
        self.event_bus.publish(event)

    def _append_ledger_record(self, path: Path | None, event: Event) -> None:
        """Persist one final decision or signal as append-only JSONL."""

        if path is None:
            return
        payload = event.payload.get("payload", event.payload)
        record = {
            "event_id": event.event_id,
            "event_type": event.topic,
            "source": event.source,
            "created_at": event.created_at,
            "payload": payload,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        RotatingJsonlLedger(path, max_bytes=self.ledger_rotation_bytes).append(record)
