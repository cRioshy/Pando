"""Read-only Decision Gate observer for Brain decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from adapters.brain_adapter import BRAIN_DECISION_RECEIVED
from decision_gate_contract import DecisionGatePolicy, evaluate_decision_gate
from event_bus import Event, EventBus
from jsonl_ledger import RotatingJsonlLedger


DECISION_GATE_AUDIT_STARTED = "DECISION_GATE_AUDIT_STARTED"
DECISION_GATE_EVALUATED = "DECISION_GATE_EVALUATED"
DECISION_GATE_AUDIT_ERROR = "DECISION_GATE_AUDIT_ERROR"
DECISION_GATE_AUDIT_HEARTBEAT = "DECISION_GATE_AUDIT_HEARTBEAT"
DECISION_GATE_AUDIT_STOPPED = "DECISION_GATE_AUDIT_STOPPED"


@dataclass
class DecisionGateAuditStatus:
    name: str = "decision_gate_observer"
    running: bool = False
    healthy: bool = True
    evaluations: int = 0
    qualified: int = 0
    blocked: int = 0
    duplicates_ignored: int = 0
    persisted: int = 0
    last_symbol: str | None = None
    last_reason_codes: list[str] | None = None
    last_event_at: str | None = None
    last_error: str | None = None


class DecisionGateAuditAdapter:
    """Evaluate Brain decisions without releasing or replacing any signal."""

    name = "decision_gate_observer"

    def __init__(
        self,
        event_bus: EventBus,
        *,
        policy: DecisionGatePolicy,
        audit_file: Path,
        ledger_rotation_bytes: int = 5 * 1024 * 1024,
        ledger_max_archives: int = 4,
    ) -> None:
        self.event_bus = event_bus
        self.policy = policy
        self.audit_file = audit_file
        self.ledger = RotatingJsonlLedger(
            audit_file,
            max_bytes=ledger_rotation_bytes,
            max_archives=ledger_max_archives,
        )
        self.status = DecisionGateAuditStatus()
        self._subscribed = False
        self._seen_source_events: set[str] = set()
        self._lock = RLock()

    async def start(self) -> None:
        if not self._subscribed:
            self.event_bus.subscribe(BRAIN_DECISION_RECEIVED, self._handle_brain_decision)
            self._subscribed = True
        self.status.running = True
        self.status.healthy = True
        self.status.last_error = None
        self._publish(DECISION_GATE_AUDIT_STARTED, {"status": "started", "mode": "OBSERVER"})

    async def stop(self) -> None:
        self.status.running = False
        self._publish(DECISION_GATE_AUDIT_STOPPED, {"status": "stopped", "mode": "OBSERVER"})

    async def run_once(self) -> list[Event]:
        return [Event(topic=DECISION_GATE_AUDIT_HEARTBEAT, source=self.name, payload={
            "status": "ok",
            "mode": "OBSERVER",
            "evaluations": self.status.evaluations,
            "qualified": self.status.qualified,
            "blocked": self.status.blocked,
        })]

    async def health(self) -> dict[str, Any]:
        return {
            "name": self.status.name,
            "running": self.status.running,
            "healthy": self.status.healthy,
            "mode": "OBSERVER",
            "evaluations": self.status.evaluations,
            "qualified": self.status.qualified,
            "blocked": self.status.blocked,
            "duplicates_ignored": self.status.duplicates_ignored,
            "persisted": self.status.persisted,
            "last_symbol": self.status.last_symbol,
            "last_reason_codes": self.status.last_reason_codes,
            "last_error": self.status.last_error,
        }

    async def get_status(self) -> dict[str, Any]:
        result = await self.health()
        result["last_event_at"] = self.status.last_event_at
        result["audit_file"] = str(self.audit_file)
        return result

    def _handle_brain_decision(self, event: Event) -> None:
        if not self.status.running:
            return
        try:
            data = event.payload.get("payload", event.payload)
            data = data if isinstance(data, dict) else {}
            source_event_id = str(data.get("source_event_id") or event.event_id)
            with self._lock:
                if source_event_id in self._seen_source_events:
                    self.status.duplicates_ignored += 1
                    return
                self._seen_source_events.add(source_event_id)

            result = evaluate_decision_gate(data, policy=self.policy)
            evaluated_at = datetime.now(UTC).isoformat()
            record = {
                "event_type": DECISION_GATE_EVALUATED,
                "evaluated_at": evaluated_at,
                "source_event_id": source_event_id,
                "result": result,
            }
            self.ledger.append(record)
            with self._lock:
                self.status.evaluations += 1
                self.status.qualified += int(result["qualified"])
                self.status.blocked += int(not result["qualified"])
                self.status.persisted += 1
                self.status.last_symbol = result.get("symbol")
                self.status.last_reason_codes = list(result["reason_codes"])
                self.status.last_event_at = evaluated_at
                self.status.healthy = True
                self.status.last_error = None
            self._publish(DECISION_GATE_EVALUATED, result)
        except Exception as exc:  # noqa: BLE001 - observer must not interrupt the event flow
            self.status.healthy = False
            self.status.last_error = str(exc)
            self._publish(DECISION_GATE_AUDIT_ERROR, {"error": str(exc), "mode": "OBSERVER"})

    def _publish(self, topic: str, payload: dict[str, Any]) -> None:
        event = Event(topic=topic, source=self.name, payload={
            "event_type": topic,
            "source": self.name,
            "timestamp": datetime.now(UTC).isoformat(),
            "payload": payload,
        })
        event.payload["event_id"] = event.event_id
        self.event_bus.publish(event)
