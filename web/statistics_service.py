"""Persistent analysis and storage statistics for the web ControlCenter."""

from __future__ import annotations

import asyncio
import csv
import hashlib
import json
import os
import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from threading import Event as ThreadEvent
from threading import Lock, RLock, Thread
from typing import Any
from uuid import uuid4

from brain_event_store import BrainEventReader
from config import PlatformConfig
from event_bus import Event


STATISTICS_UPDATED = "STATISTICS_UPDATED"
MAX_JSON_BYTES_FOR_RECORD_SCAN = 10 * 1024 * 1024
MAX_JSONL_BYTES_FOR_STARTUP_RECORD_SCAN = 50 * 1024 * 1024


COUNTER_KEYS = [
    "total_analyses",
    "crypto_analyses",
    "stock_analyses",
    "brain_evaluations",
    "decisions_created",
    "signals_created",
    "long_count",
    "short_count",
    "hold_count",
    "error_count",
    "duplicate_events_ignored",
    "telegram_messages_sent",
    "learning_updates",
]

PROFESSIONAL_COUNTER_KEYS = [
    "api_calls",
    "database_writes",
    "retry_events",
    "service_errors",
    "data_warnings",
    "unique_error_types",
    "repeated_errors",
    "final_long",
    "final_short",
    "final_hold",
    "watchlist",
    "final_decisions",
    "learned_patterns",
    "successful_learnings",
    "confidence_total",
    "confidence_count",
    "analysis_time_total_ms",
    "analysis_time_count",
    "simulated_trades_opened",
    "simulated_trade_updates",
    "simulated_trades_closed",
    "simulated_wins",
    "simulated_losses",
    "simulated_breakeven",
    "simulated_unknown",
    "outcome_profit_total_bp",
    "outcome_profit_count",
    "outcome_holding_total_seconds",
    "outcome_holding_count",
]

SERVICE_ERROR_TOPICS = {
    "SYSTEM_ERROR",
    "CRYPTO_SERVICE_ERROR",
    "STOCK_SERVICE_ERROR",
    "BRAIN_SERVICE_ERROR",
    "CONTROL_CENTER_ERROR",
    "TELEGRAM_SERVICE_ERROR",
    "DECISION_SIGNAL_SERVICE_ERROR",
    "CRYPTO_TRADE_TRACKER_ERROR",
}

DATA_WARNING_MARKERS = {"NO_DATA", "MISSING", "INVALID_PRICE", "CANDLE", "FUNDING", "OPEN_INTEREST", "WARNING"}
RETRY_MARKERS = {"RETRY", "API_RETRY"}


@dataclass
class AnalysisStatisticsService:
    """Thread-safe persistent event statistics."""

    path: Path
    counters: dict[str, int] = field(default_factory=lambda: {key: 0 for key in COUNTER_KEYS})
    professional_counters: dict[str, int] = field(default_factory=lambda: {key: 0 for key in PROFESSIONAL_COUNTER_KEYS})
    error_type_counts: dict[str, int] = field(default_factory=dict)
    error_module_counts: dict[str, int] = field(default_factory=dict)
    error_symbol_counts: dict[str, int] = field(default_factory=dict)
    error_source_counts: dict[str, int] = field(default_factory=dict)
    warning_type_counts: dict[str, int] = field(default_factory=dict)
    seen_event_ids: set[str] = field(default_factory=set)
    seen_signatures: set[str] = field(default_factory=set)
    reconstructed: bool = False
    reconstructed_at: str | None = None
    outcome_reconstructed: bool = False
    outcome_reconstructed_at: str | None = None
    last_update_at: str | None = None
    _lock: RLock = field(default_factory=RLock, repr=False)

    def start(self, config: PlatformConfig) -> None:
        """Load persisted counters and reconstruct existing data when needed."""

        self.load()
        if not self.reconstructed:
            self.reconstruct(config)
            self.reconstructed = True
            self.reconstructed_at = datetime.now(UTC).isoformat()
            self.save()
        if not self.outcome_reconstructed:
            self.reconstruct_outcomes(config)
            self.outcome_reconstructed = True
            self.outcome_reconstructed_at = datetime.now(UTC).isoformat()
            self.save()

    def load(self) -> None:
        """Load persisted statistics from JSON."""

        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        with self._lock:
            stored = data.get("counters", {})
            for key in COUNTER_KEYS:
                self.counters[key] = int(stored.get(key, self.counters.get(key, 0)))
            professional = data.get("professional_counters", {})
            for key in PROFESSIONAL_COUNTER_KEYS:
                self.professional_counters[key] = int(professional.get(key, self.professional_counters.get(key, 0)))
            self.error_type_counts = {str(key): int(value) for key, value in data.get("error_type_counts", {}).items()}
            self.error_module_counts = {str(key): int(value) for key, value in data.get("error_module_counts", {}).items()}
            self.error_symbol_counts = {str(key): int(value) for key, value in data.get("error_symbol_counts", {}).items()}
            self.error_source_counts = {str(key): int(value) for key, value in data.get("error_source_counts", {}).items()}
            self.warning_type_counts = {str(key): int(value) for key, value in data.get("warning_type_counts", {}).items()}
            self.seen_event_ids = set(data.get("seen_event_ids", []))
            self.seen_signatures = set(data.get("seen_signatures", []))
            self.reconstructed = bool(data.get("reconstructed", False))
            self.reconstructed_at = data.get("reconstructed_at")
            self.outcome_reconstructed = bool(data.get("outcome_reconstructed", False))
            self.outcome_reconstructed_at = data.get("outcome_reconstructed_at")
            self.last_update_at = data.get("last_update_at")

    def save(self) -> None:
        """Persist counters and dedupe state."""

        with self._lock:
            data = {
                "counters": dict(self.counters),
                "professional_counters": dict(self.professional_counters),
                "error_type_counts": dict(sorted(self.error_type_counts.items())),
                "error_module_counts": dict(sorted(self.error_module_counts.items())),
                "error_symbol_counts": dict(sorted(self.error_symbol_counts.items())),
                "error_source_counts": dict(sorted(self.error_source_counts.items())),
                "warning_type_counts": dict(sorted(self.warning_type_counts.items())),
                "seen_event_ids": sorted(self.seen_event_ids),
                "seen_signatures": sorted(self.seen_signatures),
                "reconstructed": self.reconstructed,
                "reconstructed_at": self.reconstructed_at,
                "outcome_reconstructed": self.outcome_reconstructed,
                "outcome_reconstructed_at": self.outcome_reconstructed_at,
                "last_update_at": self.last_update_at,
            }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")

    def apply_event(self, event: Event) -> bool:
        """Apply one countable event once. Return True when counters changed."""

        signature = self._event_signature(event)
        with self._lock:
            if event.event_id in self.seen_event_ids or signature in self.seen_signatures:
                self.counters["duplicate_events_ignored"] += 1
                self.last_update_at = datetime.now(UTC).isoformat()
                self._remember(event.event_id, signature)
                changed = True
            else:
                changed = self._count_event_unlocked(event)
                self._remember(event.event_id, signature)
                if changed:
                    self.last_update_at = datetime.now(UTC).isoformat()
        if changed:
            self.save()
        return changed

    def snapshot(self) -> dict[str, Any]:
        """Return browser-safe counters."""

        with self._lock:
            return {
                **dict(self.counters),
                "developer": self._developer_snapshot_unlocked(),
                "trading": self._trading_snapshot_unlocked(),
                "errors_detail": self._error_snapshot_unlocked(),
                "reconstructed": self.reconstructed,
                "reconstructed_at": self.reconstructed_at,
                "outcome_reconstructed": self.outcome_reconstructed,
                "outcome_reconstructed_at": self.outcome_reconstructed_at,
                "last_update_at": self.last_update_at,
            }

    def reconstruct(self, config: PlatformConfig) -> None:
        """Reconstruct reliable counters from existing JSONL brain records."""

        reader = BrainEventReader(
            legacy_file=config.brain_events_file,
            rotated_root=config.brain_events_dir,
        )
        for record in reader.all():
            self._reconstruct_record(record)

        telegram_log = config.data_dir / "telegram_dry_run.jsonl"
        if telegram_log.exists() and telegram_log.suffix.lower() == ".jsonl":
            self._reconstruct_jsonl(telegram_log)

    def reconstruct_outcomes(self, config: PlatformConfig) -> None:
        """Reconstruct reliable simulated outcome counters from JSONL records."""

        if config.trade_outcomes_file.exists():
            self._reconstruct_outcome_jsonl(config.trade_outcomes_file)

    def _reconstruct_outcome_jsonl(self, path: Path) -> None:
        """Reconstruct simulated trade outcome records from JSONL."""

        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    self._reconstruct_outcome_record(record)
        except OSError:
            return

    def _reconstruct_outcome_record(self, record: dict[str, Any]) -> None:
        """Reconstruct one simulated outcome lifecycle record once."""

        payload = record.get("payload", {})
        payload = payload if isinstance(payload, dict) else {}
        record_type = str(record.get("record_type") or record.get("event_type") or "")
        decision_id = str(payload.get("decision_id") or "")
        timestamp = str(record.get("timestamp") or payload.get("updated_at") or payload.get("exit_time") or "")
        signature = f"outcome|{record_type}|{decision_id}|{timestamp}"
        with self._lock:
            if signature in self.seen_signatures:
                return
            self._count_outcome_record_unlocked(record_type, payload)
            self.seen_signatures.add(signature)

    def _reconstruct_jsonl(self, path: Path) -> None:
        """Reconstruct from JSONL records that contain clear market fields."""

        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    self._reconstruct_record(record)
        except OSError:
            return

    def _reconstruct_record(self, record: dict[str, Any]) -> None:
        """Reconstruct one reliable analysis record."""

        market_type = str(record.get("market_type", "")).lower()
        direction = record.get("direction")
        source_event_id = record.get("source_event_id") or record.get("event_id")
        signature = self._record_signature(record)
        with self._lock:
            if source_event_id and str(source_event_id) in self.seen_event_ids:
                return
            if signature in self.seen_signatures:
                return
            if market_type == "crypto":
                self.counters["crypto_analyses"] += 1
                self.counters["total_analyses"] += 1
                self.counters["brain_evaluations"] += 1
                self._count_direction_unlocked(direction)
                self._count_developer_analysis_unlocked(record)
            elif market_type == "stock":
                self.counters["stock_analyses"] += 1
                self.counters["total_analyses"] += 1
                self.counters["brain_evaluations"] += 1
                self._count_direction_unlocked(direction)
                self._count_developer_analysis_unlocked(record)
            if source_event_id:
                self.seen_event_ids.add(str(source_event_id))
            self.seen_signatures.add(signature)

    def _count_event_unlocked(self, event: Event) -> bool:
        """Count one event. Caller must hold lock."""

        payload = event.payload if isinstance(event.payload, dict) else {}
        data = payload.get("payload", payload)
        data = data if isinstance(data, dict) else {}
        changed = True
        if event.topic == "CRYPTO_ANALYSIS_FINISHED":
            self.counters["crypto_analyses"] += 1
            self.counters["total_analyses"] += 1
            self._count_direction_unlocked(data.get("direction"))
            self._count_developer_analysis_unlocked(data)
        elif event.topic == "STOCK_ANALYSIS_FINISHED":
            self.counters["stock_analyses"] += 1
            self.counters["total_analyses"] += 1
            self._count_direction_unlocked(data.get("direction"))
            self._count_developer_analysis_unlocked(data)
        elif event.topic == "BRAIN_DECISION_RECEIVED":
            self.counters["brain_evaluations"] += 1
        elif event.topic == "DECISION_CREATED":
            self.counters["decisions_created"] += 1
            self._count_direction_unlocked(data.get("direction"))
            self._count_final_decision_unlocked(data)
        elif event.topic == "SIGNAL_CREATED":
            self.counters["signals_created"] += 1
            self._count_direction_unlocked(data.get("direction"))
        elif event.topic in {"SIMULATED_TRADE_OPENED", "SIMULATED_TRADE_UPDATED", "SIMULATED_TRADE_CLOSED"}:
            self._count_outcome_record_unlocked(event.topic, data)
        elif event.topic == "AI_LEARNING_UPDATED":
            self.counters["learning_updates"] += 1
            self.professional_counters["successful_learnings"] += 1
        elif event.topic == "SYSTEM_ERROR" or event.topic.endswith("_SERVICE_ERROR"):
            self.counters["error_count"] += 1
            self._count_error_unlocked(event, data, service_error=True)
        elif self._is_data_warning_topic(event.topic):
            self.professional_counters["data_warnings"] += 1
            self._increment_map(self.warning_type_counts, event.topic)
        elif self._is_retry_topic(event.topic):
            self.professional_counters["retry_events"] += 1
        elif event.topic == "TELEGRAM_MESSAGE_SENT":
            self.counters["telegram_messages_sent"] += 1
        elif event.topic.endswith("_REQUEST") or event.topic.endswith("_API_CALL"):
            self.professional_counters["api_calls"] += 1
        elif event.topic.endswith("_WRITTEN") or event.topic.endswith("_SAVED"):
            self.professional_counters["database_writes"] += 1
        else:
            changed = False
        return changed

    def _count_outcome_record_unlocked(self, record_type: str, data: dict[str, Any]) -> None:
        """Count simulated outcome lifecycle records for professional trading stats."""

        normalized = str(record_type or "").upper()
        if normalized == "SIMULATED_TRADE_OPENED":
            self.professional_counters["simulated_trades_opened"] += 1
        elif normalized == "SIMULATED_TRADE_UPDATED":
            self.professional_counters["simulated_trade_updates"] += 1
        elif normalized == "SIMULATED_TRADE_CLOSED":
            self.professional_counters["simulated_trades_closed"] += 1
            result = str(data.get("result_type") or "").upper()
            profit = data.get("gross_profit_percent", data.get("current_profit_percent"))
            holding_seconds = data.get("holding_seconds")
            if result == "WIN":
                self.professional_counters["simulated_wins"] += 1
            elif result == "LOSS":
                self.professional_counters["simulated_losses"] += 1
            elif result == "BREAKEVEN":
                self.professional_counters["simulated_breakeven"] += 1
            else:
                self.professional_counters["simulated_unknown"] += 1
            if isinstance(profit, (int, float)):
                self.professional_counters["outcome_profit_total_bp"] += int(round(float(profit) * 100))
                self.professional_counters["outcome_profit_count"] += 1
            if isinstance(holding_seconds, (int, float)):
                self.professional_counters["outcome_holding_total_seconds"] += int(round(float(holding_seconds)))
                self.professional_counters["outcome_holding_count"] += 1

    def _count_developer_analysis_unlocked(self, data: dict[str, Any]) -> None:
        """Track developer-facing analysis metadata without changing legacy counters."""

        self.professional_counters["analysis_events"] = self.counters["total_analyses"]
        duration = data.get("analysis_time_ms") or data.get("duration_ms")
        if isinstance(duration, (int, float)):
            self.professional_counters["analysis_time_total_ms"] += int(duration)
            self.professional_counters["analysis_time_count"] += 1

    def _count_final_decision_unlocked(self, data: dict[str, Any]) -> None:
        """Count only final DECISION_CREATED outcomes for trading statistics."""

        direction = str(data.get("direction") or data.get("action") or "").upper()
        confidence = data.get("confidence", data.get("probability"))
        self.professional_counters["final_decisions"] += 1
        if direction in {"LONG", "BUY"}:
            self.professional_counters["final_long"] += 1
        elif direction in {"SHORT", "SELL"}:
            self.professional_counters["final_short"] += 1
        elif direction in {"WATCHLIST"}:
            self.professional_counters["watchlist"] += 1
        elif direction in {"HOLD", "WAIT", ""}:
            self.professional_counters["final_hold"] += 1
        if isinstance(confidence, (int, float)):
            normalized_confidence = float(confidence) * 100 if float(confidence) <= 1 else float(confidence)
            self.professional_counters["confidence_total"] += int(round(normalized_confidence * 100))
            self.professional_counters["confidence_count"] += 1

    def _count_error_unlocked(self, event: Event, data: dict[str, Any], *, service_error: bool) -> None:
        """Track developer error detail by type, module, symbol and source."""

        error_type = event.topic
        source = str(event.source or data.get("source") or "unknown")
        symbol = str(data.get("symbol") or event.payload.get("symbol") or "-")
        message = str(data.get("error") or data.get("message") or error_type)
        if service_error:
            self.professional_counters["service_errors"] += 1
        before = self.error_type_counts.get(error_type, 0)
        self._increment_map(self.error_type_counts, error_type)
        self._increment_map(self.error_module_counts, source)
        self._increment_map(self.error_symbol_counts, symbol)
        self._increment_map(self.error_source_counts, source)
        if before:
            self.professional_counters["repeated_errors"] += 1
        self.professional_counters["unique_error_types"] = len(self.error_type_counts)
        self._increment_map(self.warning_type_counts, message[:120]) if not service_error else None

    def _developer_snapshot_unlocked(self) -> dict[str, Any]:
        """Return professional developer statistics."""

        return {
            "analysis_events": self.counters["total_analyses"],
            "brain_updates": self.counters["learning_updates"],
            "api_calls": self.professional_counters["api_calls"],
            "database_writes": self.professional_counters["database_writes"],
            "retry_events": self.professional_counters["retry_events"],
            "service_errors": self.professional_counters["service_errors"],
            "data_warnings": self.professional_counters["data_warnings"],
            "unique_error_types": self.professional_counters["unique_error_types"],
            "repeated_errors": self.professional_counters["repeated_errors"],
            "duplicate_events_ignored": self.counters["duplicate_events_ignored"],
        }

    def _trading_snapshot_unlocked(self) -> dict[str, Any]:
        """Return professional trading statistics based on final decisions only."""

        confidence_count = self.professional_counters["confidence_count"]
        analysis_time_count = self.professional_counters["analysis_time_count"]
        closed = self.professional_counters["simulated_trades_closed"]
        wins = self.professional_counters["simulated_wins"]
        profit_count = self.professional_counters["outcome_profit_count"]
        holding_count = self.professional_counters["outcome_holding_count"]
        open_simulated = max(
            self.professional_counters["simulated_trades_opened"] - self.professional_counters["simulated_trades_closed"],
            0,
        )
        return {
            "analyses_total": self.counters["total_analyses"],
            "final_long": self.professional_counters["final_long"],
            "final_short": self.professional_counters["final_short"],
            "final_hold": self.professional_counters["final_hold"],
            "watchlist": self.professional_counters["watchlist"],
            "active_markets": None,
            "learned_patterns": self.professional_counters["learned_patterns"],
            "hit_rate": round(wins / closed * 100, 2) if closed else None,
            "simulated_open_trades": open_simulated,
            "simulated_closed_trades": closed,
            "simulated_wins": wins,
            "simulated_losses": self.professional_counters["simulated_losses"],
            "simulated_breakeven": self.professional_counters["simulated_breakeven"],
            "simulated_unknown": self.professional_counters["simulated_unknown"],
            "simulated_trade_updates": self.professional_counters["simulated_trade_updates"],
            "average_outcome_profit_percent": round(
                self.professional_counters["outcome_profit_total_bp"] / profit_count / 100,
                4,
            )
            if profit_count
            else None,
            "average_holding_seconds": round(
                self.professional_counters["outcome_holding_total_seconds"] / holding_count,
                2,
            )
            if holding_count
            else None,
            "successful_learnings": self.professional_counters["successful_learnings"],
            "average_confidence": round(self.professional_counters["confidence_total"] / confidence_count / 100, 2)
            if confidence_count
            else None,
            "average_analysis_time_ms": round(self.professional_counters["analysis_time_total_ms"] / analysis_time_count, 2)
            if analysis_time_count
            else None,
        }

    def _error_snapshot_unlocked(self) -> dict[str, Any]:
        """Return error details for diagnostics."""

        return {
            "by_type": dict(sorted(self.error_type_counts.items(), key=lambda item: item[1], reverse=True)),
            "by_module": dict(sorted(self.error_module_counts.items(), key=lambda item: item[1], reverse=True)),
            "by_symbol": dict(sorted(self.error_symbol_counts.items(), key=lambda item: item[1], reverse=True)),
            "by_source": dict(sorted(self.error_source_counts.items(), key=lambda item: item[1], reverse=True)),
            "warnings": dict(sorted(self.warning_type_counts.items(), key=lambda item: item[1], reverse=True)),
            "unique_errors": len(self.error_type_counts),
            "total_error_events": self.counters["error_count"],
        }

    def _is_retry_topic(self, topic: str) -> bool:
        upper = topic.upper()
        return any(marker in upper for marker in RETRY_MARKERS)

    def _is_data_warning_topic(self, topic: str) -> bool:
        upper = topic.upper()
        return "ERROR" not in upper and any(marker in upper for marker in DATA_WARNING_MARKERS)

    def _increment_map(self, target: dict[str, int], key: Any) -> None:
        normalized = str(key or "-")
        target[normalized] = target.get(normalized, 0) + 1

    def _count_direction_unlocked(self, direction: Any) -> None:
        """Count LONG, SHORT or HOLD/WAIT."""

        normalized = str(direction or "").upper()
        if normalized in {"LONG", "BUY", "WATCHLIST"}:
            self.counters["long_count"] += 1
        elif normalized in {"SHORT", "SELL"}:
            self.counters["short_count"] += 1
        elif normalized in {"HOLD", "WAIT"}:
            self.counters["hold_count"] += 1

    def _remember(self, event_id: str, signature: str) -> None:
        """Remember dedupe keys with bounded memory."""

        self.seen_event_ids.add(str(event_id))
        self.seen_signatures.add(signature)
        if len(self.seen_event_ids) > 10000:
            self.seen_event_ids = set(sorted(self.seen_event_ids)[-8000:])
        if len(self.seen_signatures) > 10000:
            self.seen_signatures = set(sorted(self.seen_signatures)[-8000:])

    def _event_signature(self, event: Event) -> str:
        """Build a stable dedupe signature."""

        payload = event.payload if isinstance(event.payload, dict) else {}
        data = payload.get("payload", payload)
        data = data if isinstance(data, dict) else {}
        return "|".join(
            [
                event.topic,
                event.source,
                str(payload.get("symbol") or data.get("symbol")),
                str(payload.get("timeframe") or data.get("timeframe")),
                str(data.get("source_timestamp") or payload.get("timestamp") or event.created_at),
            ]
        )

    def _record_signature(self, record: dict[str, Any]) -> str:
        """Build a stable signature for reconstructed records."""

        return "|".join(
            [
                str(record.get("event_type")),
                str(record.get("source")),
                str(record.get("market_type")),
                str(record.get("symbol")),
                str(record.get("source_timestamp")),
            ]
        )


@dataclass(frozen=True)
class StorageTarget:
    """One configured storage folder or file target."""

    name: str
    path: Path
    root: Path


class StorageStatisticsService:
    """Persistent, single-worker metadata scanner for data folders and files."""

    def __init__(self, config: PlatformConfig, *, scan_interval_seconds: float = 60.0) -> None:
        self.config = config
        self.scan_interval_seconds = max(scan_interval_seconds, 5.0)
        self.scan_timeout_seconds = max(float(config.storage_scan_timeout_seconds), 1.0)
        self.large_file_threshold_bytes = max(int(config.storage_large_file_threshold_bytes), 1)
        self.scan_byte_budget = max(int(config.storage_scan_byte_budget), 1)
        statistics_dir = config.project_root / "storage" / "statistics"
        self.cache_file = statistics_dir / "storage_statistics.json"
        self.index_file = statistics_dir / "storage_file_index.json"
        self._lock = RLock()
        self._scan_lock = Lock()
        self._cancel_event = ThreadEvent()
        self._worker: Thread | None = None
        self._index: dict[str, dict[str, Any]] = self._load_json_file(self.index_file, {}).get("files", {})
        cached = self._load_json_file(self.cache_file, {})
        self._snapshot = cached if self._valid_snapshot(cached) else self._empty_snapshot()
        if cached:
            self._snapshot["scan_status"] = "IDLE"
            self._snapshot.setdefault("scan", self._empty_scan_status())["status"] = "IDLE"

    async def refresh_async(self) -> dict[str, Any]:
        """Run a synchronous compatibility refresh outside the event loop."""

        return await asyncio.to_thread(self.refresh)

    def refresh(self) -> dict[str, Any]:
        """Run one scan synchronously when no background scan is active."""

        if not self._scan_lock.acquire(blocking=False):
            return self.snapshot()
        scan_id = str(uuid4())
        try:
            return self._refresh_acquired(scan_id)
        finally:
            self._scan_lock.release()

    def start_scan(
        self,
        on_complete: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """Start one background scan and return immediately with its identity."""

        if not self._scan_lock.acquire(blocking=False):
            current = self.snapshot()
            return {
                "accepted": False,
                "scan_id": current.get("scan", {}).get("scan_id"),
                "status": "RUNNING",
                "storage": current,
            }

        scan_id = str(uuid4())
        self._cancel_event.clear()
        self._begin_scan(scan_id)
        self._worker = Thread(
            target=self._background_scan,
            args=(scan_id, on_complete),
            name="pandorickki-storage-scanner",
            daemon=True,
        )
        self._worker.start()
        return {
            "accepted": True,
            "scan_id": scan_id,
            "status": "RUNNING",
            "storage": self.snapshot(),
        }

    def cancel_scan(self) -> dict[str, Any]:
        """Request cooperative cancellation of the active scan."""

        self._cancel_event.set()
        current = self.snapshot()
        return {
            "scan_id": current.get("scan", {}).get("scan_id"),
            "status": current.get("scan_status", "IDLE"),
        }

    def close(self) -> None:
        """Request scanner shutdown without delaying platform shutdown."""

        self._cancel_event.set()
        worker = self._worker
        if worker is not None and worker.is_alive():
            worker.join(timeout=1.0)

    def snapshot(self) -> dict[str, Any]:
        """Return the last cached storage snapshot and current scan state."""

        with self._lock:
            return json.loads(json.dumps(self._snapshot, ensure_ascii=True))

    def folder(self, folder_name: str) -> dict[str, Any] | None:
        """Return one cached folder snapshot by name."""

        with self._lock:
            for folder in self._snapshot.get("folders", []):
                if folder.get("name") == folder_name:
                    return json.loads(json.dumps(folder, ensure_ascii=True))
        return None

    def targets(self) -> list[StorageTarget]:
        """Return existing storage targets without inventing missing paths."""

        candidates = [
            ("platform_data", self.config.data_dir, self.config.project_root),
            ("statistics", self.config.project_root / "storage" / "statistics", self.config.project_root),
            ("market_history", self.config.project_root / "storage" / "market_history", self.config.project_root),
            ("calculations", self.config.project_root / "storage" / "calculations", self.config.project_root),
            ("decisions", self.config.project_root / "storage" / "decisions", self.config.project_root),
            ("signals", self.config.project_root / "storage" / "signals", self.config.project_root),
            ("logs", self.config.project_root / "storage" / "logs", self.config.project_root),
            ("crypto_data", self.config.crypto_project_path / "data", self.config.crypto_project_path),
            ("stock_data", self.config.stock_project_path / "data_stock", self.config.stock_project_path),
            ("stock_legacy_data", self.config.stock_project_path / "data", self.config.stock_project_path),
            ("brain_events", self.config.brain_events_file, self.config.project_root),
            ("brain_events_rotated", self.config.brain_events_dir, self.config.project_root),
            ("shared_state", self.config.shared_state_file, self.config.project_root),
            ("telegram_log", self.config.telegram_log_file, self.config.project_root),
        ]
        targets: list[StorageTarget] = []
        seen: set[Path] = set()
        for name, path, root in candidates:
            resolved = path.resolve()
            if path.exists() and resolved not in seen:
                targets.append(StorageTarget(name, path, root))
                seen.add(resolved)
        return targets

    def _background_scan(
        self,
        scan_id: str,
        on_complete: Callable[[dict[str, Any]], None] | None,
    ) -> None:
        """Run a scan in the dedicated daemon worker."""

        try:
            result = self._refresh_acquired(scan_id)
        finally:
            self._scan_lock.release()
        if on_complete is not None:
            try:
                on_complete(result)
            except Exception:
                pass

    def _refresh_acquired(self, scan_id: str) -> dict[str, Any]:
        """Run one cooperatively bounded scan while the single-scan lock is held."""

        self._begin_scan(scan_id)
        started_at = datetime.now(UTC)
        deadline = time.monotonic() + self.scan_timeout_seconds
        progress = {
            "files_total": 0,
            "files_completed": 0,
            "files_failed": 0,
            "bytes_examined": 0,
            "records_added": 0,
        }
        try:
            snapshot = self._scan(deadline, progress)
            status = "DEGRADED" if progress["files_failed"] or snapshot.pop("_partial", False) else "OK"
            finished_at = datetime.now(UTC)
            scan = {
                "scan_id": scan_id,
                "status": status,
                "scan_started_at": started_at.isoformat(),
                "scan_finished_at": finished_at.isoformat(),
                "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
                **progress,
                "last_error": None,
            }
            snapshot["scan_status"] = status
            snapshot["scan"] = scan
            with self._lock:
                self._snapshot = snapshot
            self._persist_index()
            self._atomic_write_json(self.cache_file, snapshot)
            return self.snapshot()
        except StorageScanInterrupted as exc:
            self._persist_index()
            return self._finish_interrupted_scan(scan_id, started_at, progress, exc.status, str(exc))
        except Exception as exc:  # noqa: BLE001 - scanner failure must not affect live services
            self._persist_index()
            return self._finish_interrupted_scan(scan_id, started_at, progress, "ERROR", str(exc))

    def _scan(self, deadline: float, progress: dict[str, int]) -> dict[str, Any]:
        """Scan all targets with one global byte budget."""

        target_files: list[tuple[StorageTarget, list[Path]]] = []
        for target in self.targets():
            self._check_interrupted(deadline)
            files = [target.path] if target.path.is_file() else [
                item for item in target.path.rglob("*") if item.is_file()
            ]
            target_files.append((target, files))
            progress["files_total"] += len(files)

        remaining_budget = [self.scan_byte_budget]
        folders = [
            self._scan_target(target, files, deadline, progress, remaining_budget)
            for target, files in target_files
        ]
        total_files = sum(folder["file_count"] for folder in folders)
        total_records = sum(folder["record_count"] or 0 for folder in folders)
        total_size = sum(folder["total_size_bytes"] for folder in folders)
        return {
            "last_scan": datetime.now(UTC).isoformat(),
            "scan_interval_seconds": self.scan_interval_seconds,
            "total_files": total_files,
            "total_records": total_records,
            "total_size_bytes": total_size,
            "total_size_human": human_size(total_size),
            "folders": folders,
            "_partial": any(folder["status"] == "DEGRADED" for folder in folders),
        }

    def _scan_target(
        self,
        target: StorageTarget,
        files: list[Path],
        deadline: float,
        progress: dict[str, int],
        remaining_budget: list[int],
    ) -> dict[str, Any]:
        """Scan one folder or single file target."""

        file_stats = []
        for path in files:
            self._check_interrupted(deadline)
            try:
                item = self._scan_file(path, target.root, deadline, progress, remaining_budget)
            except OSError as exc:
                item = {
                    "name": path.name,
                    "relative_path": safe_relative(path, target.root),
                    "is_backup": is_backup_path(path),
                    "file_type": path.suffix.lower().lstrip(".") or "unknown",
                    "size_bytes": 0,
                    "size_human": "0 B",
                    "modified_at": None,
                    "record_count": None,
                    "record_count_status": "unavailable",
                    "log_lines": None,
                    "status": "DEGRADED",
                    "error": str(exc),
                }
            file_stats.append(item)
            progress["files_completed"] += 1
            if item.get("error"):
                progress["files_failed"] += 1
        production_errors = [
            item["error"]
            for item in file_stats
            if item.get("error") and not item.get("is_backup")
        ]
        backup_warnings = [
            item["error"]
            for item in file_stats
            if item.get("error") and item.get("is_backup")
        ]
        total_size = sum(item["size_bytes"] for item in file_stats)
        record_counts = [item["record_count"] for item in file_stats if item["record_count"] is not None]
        modified_values = [item["modified_at"] for item in file_stats if item["modified_at"]]
        partial = any(item.get("status") in {"DEGRADED", "REBUILDING", "TIMEOUT", "ERROR"} for item in file_stats)
        type_counts: dict[str, int] = {}
        for item in file_stats:
            type_counts[item["file_type"]] = type_counts.get(item["file_type"], 0) + 1
        return {
            "name": target.name,
            "relative_path": safe_relative(target.path, target.root),
            "file_count": len(file_stats),
            "record_count": sum(record_counts) if record_counts else None,
            "total_size_bytes": total_size,
            "total_size_human": human_size(total_size),
            "last_modified_at": max(modified_values) if modified_values else None,
            "file_types": type_counts,
            "status": "WARN" if production_errors else ("DEGRADED" if partial else "OK"),
            "errors": production_errors[:10],
            "backup_warnings": backup_warnings[:10],
            "files": file_stats,
        }

    def _scan_file(
        self,
        path: Path,
        root: Path,
        deadline: float,
        progress: dict[str, int],
        remaining_budget: list[int],
    ) -> dict[str, Any]:
        """Scan one file without exposing contents."""

        self._check_interrupted(deadline)
        suffix = path.suffix.lower()
        stat = path.stat()
        result = {
            "name": path.name,
            "relative_path": safe_relative(path, root),
            "is_backup": is_backup_path(path),
            "file_type": suffix.lstrip(".") or "unknown",
            "size_bytes": stat.st_size,
            "size_human": human_size(stat.st_size),
            "modified_at": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
            "record_count": None,
            "record_count_status": "unknown",
            "log_lines": None,
            "status": "OK",
            "error": None,
        }
        try:
            if suffix == ".jsonl":
                jsonl = self._scan_jsonl(path, stat, deadline, progress, remaining_budget)
                result.update(jsonl)
            elif suffix == ".csv":
                if stat.st_size > self.large_file_threshold_bytes:
                    result["record_count_status"] = "metadata_only_large_file"
                else:
                    result["record_count"] = count_csv_rows(path)
                    result["record_count_status"] = "counted"
                    progress["bytes_examined"] += stat.st_size
            elif suffix == ".json":
                result["record_count"] = count_json_records(path, stat.st_size)
                result["record_count_status"] = "counted" if result["record_count"] is not None else "not_clear"
                if result["record_count"] is not None:
                    progress["bytes_examined"] += stat.st_size
            elif suffix in {".sqlite", ".sqlite3", ".db"}:
                if stat.st_size > self.large_file_threshold_bytes:
                    result["record_count_status"] = "metadata_only_large_file"
                else:
                    result["record_count"] = count_sqlite_rows(path)
                    result["record_count_status"] = "counted"
            elif suffix in {".log", ".txt"} or "log" in path.name.lower():
                if stat.st_size > self.large_file_threshold_bytes:
                    result["record_count_status"] = "metadata_only_large_file"
                else:
                    result["log_lines"] = count_lines(path)
                    progress["bytes_examined"] += stat.st_size
            self._check_interrupted(deadline)
        except Exception as exc:  # noqa: BLE001 - scanner must not stop on damaged files
            if isinstance(exc, StorageScanInterrupted):
                raise
            result["status"] = "WARN"
            result["error"] = str(exc)
            result["record_count"] = None
        return result

    def _scan_jsonl(
        self,
        path: Path,
        stat: os.stat_result,
        deadline: float,
        progress: dict[str, int],
        remaining_budget: list[int],
    ) -> dict[str, Any]:
        """Incrementally count complete JSONL lines from the persisted byte offset."""

        key = str(path.resolve())
        previous_fingerprint_bytes = int(previous.get("fingerprint_bytes") or 0) if (previous := self._index.get(key, {})) else 0
        fingerprint_bytes = previous_fingerprint_bytes if previous else min(stat.st_size, 4096)
        head_hash = self._file_head_hash(path, fingerprint_bytes)
        file_id = int(getattr(stat, "st_ino", 0) or 0)
        same_identity = bool(previous) and previous.get("head_hash") == head_hash
        previous_file_id = int(previous.get("file_id") or 0)
        if file_id and previous_file_id and file_id != previous_file_id:
            same_identity = False
        previous_offset = int(previous.get("last_offset") or 0)
        if stat.st_size < previous_offset:
            same_identity = False

        offset = previous_offset if same_identity else 0
        record_count = int(previous.get("record_count") or 0) if same_identity else 0
        invalidated = bool(previous) and not same_identity
        unchanged = (
            same_identity
            and int(previous.get("size_bytes") or -1) == stat.st_size
            and int(previous.get("mtime_ns") or -1) == stat.st_mtime_ns
            and previous.get("status") in {"OK", "DEGRADED"}
        )
        if unchanged:
            return {
                "record_count": record_count,
                "record_count_status": "indexed",
                "status": "OK" if previous.get("status") == "OK" else "DEGRADED",
                "error": previous.get("last_error"),
            }

        available = max(stat.st_size - offset, 0)
        allowed = min(available, max(remaining_budget[0], 0))
        if allowed <= 0 and available > 0:
            self._index[key] = self._index_entry(
                path, stat, head_hash, fingerprint_bytes, file_id, offset, record_count, "REBUILDING", None
            )
            return {
                "record_count": record_count if previous else None,
                "record_count_status": "rebuilding",
                "status": "REBUILDING",
                "error": None,
            }

        examined = 0
        added = 0
        invalid_lines = 0
        committed_offset = offset
        carry = b""
        with path.open("rb") as handle:
            handle.seek(offset)
            while examined < allowed:
                self._check_interrupted(deadline)
                chunk = handle.read(min(1024 * 1024, allowed - examined))
                if not chunk:
                    break
                examined += len(chunk)
                data = carry + chunk
                newline = data.rfind(b"\n")
                if newline < 0:
                    carry = data
                    continue
                complete = data[: newline + 1]
                carry = data[newline + 1 :]
                committed_offset = handle.tell() - len(carry)
                for raw_line in complete.splitlines():
                    if not raw_line.strip():
                        continue
                    try:
                        json.loads(raw_line.decode("utf-8"))
                        added += 1
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        invalid_lines += 1

        record_count += added
        progress["bytes_examined"] += examined
        progress["records_added"] += added
        remaining_budget[0] = max(remaining_budget[0] - examined, 0)
        complete_file = committed_offset >= stat.st_size
        status = "DEGRADED" if invalid_lines else ("OK" if complete_file else "REBUILDING")
        error = f"{invalid_lines} invalid JSONL line(s) skipped" if invalid_lines else None
        self._index[key] = self._index_entry(
            path,
            stat,
            head_hash,
            fingerprint_bytes,
            file_id,
            committed_offset,
            record_count,
            status,
            error,
        )
        return {
            "record_count": record_count,
            "record_count_status": "counted" if complete_file else "rebuilding",
            "status": status,
            "error": error,
            "index_invalidated": invalidated,
            "last_offset": committed_offset,
        }

    def _index_entry(
        self,
        path: Path,
        stat: os.stat_result,
        head_hash: str,
        fingerprint_bytes: int,
        file_id: int,
        offset: int,
        record_count: int,
        status: str,
        error: str | None,
    ) -> dict[str, Any]:
        return {
            "path": str(path),
            "size_bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "file_id": file_id,
            "head_hash": head_hash,
            "fingerprint_bytes": fingerprint_bytes,
            "last_offset": offset,
            "record_count": record_count,
            "last_successful_scan": datetime.now(UTC).isoformat() if status in {"OK", "DEGRADED"} else None,
            "status": status,
            "last_error": error,
        }

    def _file_head_hash(self, path: Path, fingerprint_bytes: int) -> str:
        with path.open("rb") as handle:
            return hashlib.sha256(handle.read(max(fingerprint_bytes, 0))).hexdigest()

    def _begin_scan(self, scan_id: str) -> None:
        now = datetime.now(UTC).isoformat()
        with self._lock:
            self._snapshot["scan_status"] = "RUNNING"
            self._snapshot["scan"] = {
                "scan_id": scan_id,
                "status": "RUNNING",
                "scan_started_at": now,
                "scan_finished_at": None,
                "duration_seconds": None,
                "files_total": 0,
                "files_completed": 0,
                "files_failed": 0,
                "bytes_examined": 0,
                "records_added": 0,
                "last_error": None,
            }

    def _finish_interrupted_scan(
        self,
        scan_id: str,
        started_at: datetime,
        progress: dict[str, int],
        status: str,
        error: str,
    ) -> dict[str, Any]:
        finished_at = datetime.now(UTC)
        with self._lock:
            self._snapshot["scan_status"] = status
            self._snapshot["scan"] = {
                "scan_id": scan_id,
                "status": status,
                "scan_started_at": started_at.isoformat(),
                "scan_finished_at": finished_at.isoformat(),
                "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
                **progress,
                "last_error": error,
            }
            snapshot = json.loads(json.dumps(self._snapshot, ensure_ascii=True))
        if self._valid_snapshot(snapshot) and snapshot.get("folders"):
            self._atomic_write_json(self.cache_file, snapshot)
        return snapshot

    def _check_interrupted(self, deadline: float) -> None:
        if self._cancel_event.is_set():
            raise StorageScanInterrupted("CANCELLED", "Storage scan cancelled")
        if time.monotonic() >= deadline:
            raise StorageScanInterrupted("TIMEOUT", "Storage scan timed out")

    def _persist_index(self) -> None:
        self._atomic_write_json(
            self.index_file,
            {"version": 1, "updated_at": datetime.now(UTC).isoformat(), "files": self._index},
        )

    def _atomic_write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        text = json.dumps(payload, indent=2, ensure_ascii=True)
        json.loads(text)
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)

    def _load_json_file(self, path: Path, default: dict[str, Any]) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return dict(default)
        return data if isinstance(data, dict) else dict(default)

    def _valid_snapshot(self, snapshot: dict[str, Any]) -> bool:
        return isinstance(snapshot, dict) and isinstance(snapshot.get("folders"), list)

    def _empty_snapshot(self) -> dict[str, Any]:
        """Return an empty storage snapshot."""

        return {
            "last_scan": None,
            "scan_interval_seconds": self.scan_interval_seconds,
            "total_files": 0,
            "total_records": 0,
            "total_size_bytes": 0,
            "total_size_human": "0 B",
            "folders": [],
            "scan_status": "IDLE",
            "scan": self._empty_scan_status(),
        }

    def _empty_scan_status(self) -> dict[str, Any]:
        return {
            "scan_id": None,
            "status": "IDLE",
            "scan_started_at": None,
            "scan_finished_at": None,
            "duration_seconds": None,
            "files_total": 0,
            "files_completed": 0,
            "files_failed": 0,
            "bytes_examined": 0,
            "records_added": 0,
            "last_error": None,
        }


class StorageScanInterrupted(RuntimeError):
    """Cooperative storage scan cancellation or timeout."""

    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status


def count_jsonl(path: Path) -> int:
    """Count valid non-empty JSON lines."""

    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            json.loads(line)
            count += 1
    return count


def should_skip_large_jsonl_record_scan(path: Path, size_bytes: int) -> bool:
    """Avoid blocking startup on huge legacy append-only JSONL files."""

    return path.name == "brain_events.jsonl" and size_bytes > MAX_JSONL_BYTES_FOR_STARTUP_RECORD_SCAN


def count_csv_rows(path: Path) -> int:
    """Count CSV data rows without the header."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for row in reader if row)


def count_json_records(path: Path, size_bytes: int) -> int | None:
    """Count records in a small JSON file when the structure is clear."""

    if size_bytes > MAX_JSON_BYTES_FOR_RECORD_SCAN:
        return None
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        known_fields = [
            "decisions",
            "signals",
            "history",
            "records",
            "events",
            "logs",
            "data",
            "items",
            "memory",
            "memories",
        ]
        counts = [len(data[field]) for field in known_fields if isinstance(data.get(field), list)]
        if counts:
            return sum(counts)
    return None


def count_sqlite_rows(path: Path) -> int:
    """Count rows in all user tables of a SQLite database."""

    total = 0
    connection = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
    try:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        for (table,) in tables:
            quoted = '"' + str(table).replace('"', '""') + '"'
            total += int(connection.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0])
    finally:
        connection.close()
    return total


def count_lines(path: Path) -> int:
    """Count lines without loading the whole file."""

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for line in handle if line.strip())


def human_size(size: int) -> str:
    """Format bytes as B, KB, MB or GB."""

    value = float(size)
    for unit in ["B", "KB", "MB", "GB"]:
        if value < 1024 or unit == "GB":
            return f"{value:.2f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024


def safe_relative(path: Path, root: Path) -> str:
    """Return a relative path without exposing the Windows user directory."""

    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def is_backup_path(path: Path) -> bool:
    """Return True when a file belongs to a backup directory."""

    return any(part.lower() in {"backup", "backups"} for part in path.parts)
