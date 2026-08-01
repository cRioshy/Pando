"""Bounded, secret-filtered persistence for service error events."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from event_bus import Event, EventBus
from jsonl_ledger import RotatingJsonlLedger


SENSITIVE_KEY_PARTS = (
    "authorization",
    "api_key",
    "apikey",
    "bot_token",
    "chat_id",
    "cookie",
    "password",
    "secret",
    "token",
)
SECRET_ASSIGNMENT = re.compile(
    r"(?i)(authorization|api[_-]?key|bot[_-]?token|chat[_-]?id|cookie|password|secret|token)"
    r"(\s*[:=]\s*)[^\s,;&]+"
)
BEARER_VALUE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+\-/=]+")
QUERY_SECRET = re.compile(
    r"(?i)([?&](?:api[_-]?key|authorization|password|secret|token)=)[^&#\s]+"
)


class ServiceErrorJournal:
    """Persist compact error projections and durable first/last summaries."""

    name = "service_error_journal"

    def __init__(
        self,
        event_bus: EventBus,
        *,
        journal_file: Path,
        summary_file: Path,
        rotation_bytes: int = 5 * 1024 * 1024,
        max_archives: int = 4,
        max_summary_entries: int = 500,
        max_message_chars: int = 500,
    ) -> None:
        self.event_bus = event_bus
        self.journal_file = journal_file
        self.summary_file = summary_file
        self.max_summary_entries = max(int(max_summary_entries), 1)
        self.max_message_chars = max(int(max_message_chars), 80)
        self._ledger = RotatingJsonlLedger(
            journal_file,
            max_bytes=rotation_bytes,
            max_archives=max_archives,
        )
        self._summary = self._load_summary()
        self._lock = RLock()
        self._running = False
        self._last_error: str | None = None
        self._failed_writes = 0

    def start(self) -> None:
        """Subscribe before platform adapters can publish startup failures."""

        with self._lock:
            if self._running:
                return
            self.event_bus.subscribe("*", self.apply_event)
            self._running = True

    def stop(self) -> None:
        """Unsubscribe after all other services have stopped."""

        with self._lock:
            if not self._running:
                return
            self.event_bus.unsubscribe("*", self.apply_event)
            self._running = False

    def apply_event(self, event: Event) -> None:
        """Persist one error event without ever breaking its publisher."""

        if not self.is_error_event(event):
            return
        try:
            record = self._project(event)
            with self._lock:
                self._ledger.append(record)
                self._update_summary(record)
                self._persist_summary()
                self._last_error = None
        except Exception as exc:  # noqa: BLE001 - observability must not break publishers
            with self._lock:
                self._failed_writes += 1
                self._last_error = self._safe_text(str(exc), secrets=[])

    @staticmethod
    def is_error_event(event: Event) -> bool:
        """Return whether an event belongs to the service-error contract."""

        topic = str(event.topic or "").upper()
        return topic == "SERVICE.ERROR" or topic == "SYSTEM_ERROR" or topic.endswith("_ERROR")

    def health(self) -> dict[str, Any]:
        """Return compact journal health without exposing local paths or payloads."""

        with self._lock:
            return {
                "name": self.name,
                "running": self._running,
                "healthy": self._last_error is None,
                "events_recorded": int(self._summary.get("total_events", 0)),
                "unique_errors": len(self._summary.get("errors", {})),
                "failed_writes": self._failed_writes,
                "last_error": self._last_error,
            }

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-safe copy of the bounded summary for tests and diagnostics."""

        with self._lock:
            return json.loads(json.dumps(self._summary, ensure_ascii=True))

    def _project(self, event: Event) -> dict[str, Any]:
        payload = event.payload if isinstance(event.payload, dict) else {}
        nested = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
        data = {**payload, **nested}
        secrets = self._collect_secret_values(payload)
        attempts = self._project_attempts(data, secrets)
        providers = self._providers(data, attempts)
        error_type = self._safe_text(data.get("error_type") or event.topic, secrets)
        record = {
            "version": 1,
            "event_id": str(event.event_id),
            "occurred_at": str(event.created_at),
            "recorded_at": datetime.now(UTC).isoformat(),
            "topic": str(event.topic),
            "service": self._safe_text(event.source or data.get("source") or "unknown", secrets, 80),
            "stage": self._safe_text(data.get("stage") or "unknown", secrets, 80),
            "symbol": self._safe_text(data.get("symbol") or "-", secrets, 80),
            "providers": providers,
            "error_type": error_type,
            "message": self._safe_text(data.get("error") or data.get("message") or event.topic, secrets),
            "correlation_id": self._safe_text(payload.get("correlation_id") or "", secrets, 120) or None,
            "attempts": attempts,
        }
        fingerprint_source = "|".join(
            str(record[key]).lower()
            for key in ("topic", "service", "stage", "symbol", "providers", "error_type")
        )
        record["fingerprint"] = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:24]
        return record

    def _project_attempts(self, data: dict[str, Any], secrets: list[str]) -> list[dict[str, Any]]:
        diagnostics = data.get("diagnostics") if isinstance(data.get("diagnostics"), dict) else {}
        raw_attempts = diagnostics.get("attempts") if isinstance(diagnostics.get("attempts"), list) else []
        projected: list[dict[str, Any]] = []
        for attempt in raw_attempts[:10]:
            if not isinstance(attempt, dict):
                continue
            projected.append(
                {
                    "provider": self._safe_text(attempt.get("source") or attempt.get("provider") or "unknown", secrets, 80),
                    "data_type": self._safe_text(attempt.get("data_type") or "unknown", secrets, 80),
                    "status": self._safe_text(attempt.get("status") or "unknown", secrets, 40),
                    "attempt": int(attempt.get("attempt") or 0),
                    "error_type": self._safe_text(attempt.get("error_type") or "", secrets, 120) or None,
                    "message": self._safe_text(attempt.get("error") or "", secrets, 200) or None,
                }
            )
        return projected

    def _providers(self, data: dict[str, Any], attempts: list[dict[str, Any]]) -> list[str]:
        diagnostics = data.get("diagnostics") if isinstance(data.get("diagnostics"), dict) else {}
        values = [data.get("provider"), diagnostics.get("candle_source")]
        values.extend(attempt.get("provider") for attempt in attempts)
        providers: list[str] = []
        for value in values:
            normalized = str(value or "").strip()
            if normalized and normalized != "unknown" and normalized not in providers:
                providers.append(normalized[:80])
        return providers[:5]

    def _update_summary(self, record: dict[str, Any]) -> None:
        errors = self._summary.setdefault("errors", {})
        fingerprint = record["fingerprint"]
        existing = errors.get(fingerprint)
        if existing is None:
            if len(errors) >= self.max_summary_entries:
                oldest = min(errors, key=lambda key: str(errors[key].get("last_seen_at") or ""))
                errors.pop(oldest, None)
                self._summary["summary_entries_evicted"] = int(
                    self._summary.get("summary_entries_evicted", 0)
                ) + 1
            errors[fingerprint] = {
                "count": 1,
                "first_seen_at": record["occurred_at"],
                "last_seen_at": record["occurred_at"],
                "first": record,
                "last": record,
            }
        else:
            existing["count"] = int(existing.get("count", 0)) + 1
            existing["last_seen_at"] = record["occurred_at"]
            existing["last"] = record
        self._summary["total_events"] = int(self._summary.get("total_events", 0)) + 1
        self._summary["updated_at"] = record["recorded_at"]

    def _persist_summary(self) -> None:
        self.summary_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.summary_file.with_suffix(self.summary_file.suffix + ".tmp")
        text = json.dumps(self._summary, indent=2, ensure_ascii=True)
        json.loads(text)
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.summary_file)

    def _load_summary(self) -> dict[str, Any]:
        default = {
            "version": 1,
            "updated_at": None,
            "total_events": 0,
            "summary_entries_evicted": 0,
            "errors": {},
        }
        try:
            loaded = json.loads(self.summary_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default
        if not isinstance(loaded, dict) or not isinstance(loaded.get("errors"), dict):
            return default
        return {**default, **loaded}

    def _safe_text(self, value: Any, secrets: list[str], limit: int | None = None) -> str:
        text = str(value or "").replace("\r", " ").replace("\n", " ")
        for secret in secrets:
            if secret:
                text = text.replace(secret, "[REDACTED]")
        text = SECRET_ASSIGNMENT.sub(lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", text)
        text = BEARER_VALUE.sub("Bearer [REDACTED]", text)
        text = QUERY_SECRET.sub(lambda match: f"{match.group(1)}[REDACTED]", text)
        return text[: (limit or self.max_message_chars)]

    @classmethod
    def _collect_secret_values(cls, value: Any, key: str = "") -> list[str]:
        secrets: list[str] = []
        normalized_key = key.lower().replace("-", "_")
        if any(part in normalized_key for part in SENSITIVE_KEY_PARTS):
            if isinstance(value, (str, int, float)) and str(value):
                secrets.append(str(value))
            return secrets
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                secrets.extend(cls._collect_secret_values(nested_value, str(nested_key)))
        elif isinstance(value, list):
            for item in value:
                secrets.extend(cls._collect_secret_values(item, key))
        return secrets
