"""Persistent read-only comparison of stock Legacy and public Shadow decisions."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import RLock
from typing import Any, Mapping

from adapters.decision_signal_adapter import DECISION_CREATED
from adapters.outcome_tracker import SIMULATED_TRADE_CLOSED
from adapters.stock_adapter import STOCK_ANALYSIS_FINISHED, STOCK_SHADOW_OBSERVED
from event_bus import Event, EventBus
from jsonl_ledger import RotatingJsonlLedger, related_jsonl_files
from stock_shadow_verification_contract import (
    StockShadowVerificationPolicy,
    build_verification_record,
    complete_forward_outcome,
)


STOCK_SHADOW_VERIFICATION_STARTED = "STOCK_SHADOW_VERIFICATION_STARTED"
STOCK_SHADOW_VERIFICATION_UPDATED = "STOCK_SHADOW_VERIFICATION_UPDATED"
STOCK_SHADOW_VERIFICATION_HEARTBEAT = "STOCK_SHADOW_VERIFICATION_HEARTBEAT"
STOCK_SHADOW_VERIFICATION_ERROR = "STOCK_SHADOW_VERIFICATION_ERROR"
STOCK_SHADOW_VERIFICATION_STOPPED = "STOCK_SHADOW_VERIFICATION_STOPPED"


@dataclass
class StockShadowVerificationStatus:
    name: str = "stock_shadow_verification"
    running: bool = False
    healthy: bool = True
    cases: int = 0
    decision_links: int = 0
    tracker_links: int = 0
    completed_outcomes: int = 0
    duplicates_ignored: int = 0
    source_aliases: int = 0
    persisted_records: int = 0
    load_errors: int = 0
    last_symbol: str | None = None
    last_event_at: str | None = None
    last_error: str | None = None


class StockShadowVerificationAdapter:
    """Observe stock comparison events without changing any productive consumer."""

    name = "stock_shadow_verification"

    def __init__(
        self,
        event_bus: EventBus,
        *,
        ledger_file: Path,
        policy: StockShadowVerificationPolicy,
        config_fingerprint: str,
        ledger_rotation_bytes: int = 20 * 1024 * 1024,
        ledger_max_archives: int = 8,
        outcome_batch_size: int = 8,
    ) -> None:
        self.event_bus = event_bus
        self.ledger_file = ledger_file
        self.policy = policy
        self.config_fingerprint = str(config_fingerprint)
        self.outcome_batch_size = max(int(outcome_batch_size), 1)
        self.ledger = RotatingJsonlLedger(
            ledger_file,
            max_bytes=ledger_rotation_bytes,
            max_archives=ledger_max_archives,
        )
        self.status = StockShadowVerificationStatus()
        self._records: dict[str, dict[str, Any]] = {}
        self._source_index: dict[str, str] = {}
        self._decision_index: dict[str, str] = {}
        self._subscribed = False
        self._loaded = False
        self._lock = RLock()
        self._generation = 0
        self._snapshot_cache: dict[tuple[int, int], tuple[int, dict[str, Any]]] = {}

    async def start(self) -> None:
        if not self._loaded:
            self._load_ledger()
            self._loaded = True
        if not self._subscribed:
            self.event_bus.subscribe(STOCK_SHADOW_OBSERVED, self._handle_observation)
            self.event_bus.subscribe(DECISION_CREATED, self._handle_decision)
            self.event_bus.subscribe(SIMULATED_TRADE_CLOSED, self._handle_tracker_outcome)
            self.event_bus.subscribe(STOCK_ANALYSIS_FINISHED, self._handle_stock_price)
            self._subscribed = True
        self.status.running = True
        self.status.healthy = True
        self.status.last_error = None
        self._publish(STOCK_SHADOW_VERIFICATION_STARTED, {"status": "started", "mode": "OBSERVER_ONLY"})

    async def stop(self) -> None:
        if self._subscribed:
            self.event_bus.unsubscribe(STOCK_SHADOW_OBSERVED, self._handle_observation)
            self.event_bus.unsubscribe(DECISION_CREATED, self._handle_decision)
            self.event_bus.unsubscribe(SIMULATED_TRADE_CLOSED, self._handle_tracker_outcome)
            self.event_bus.unsubscribe(STOCK_ANALYSIS_FINISHED, self._handle_stock_price)
            self._subscribed = False
        self.status.running = False
        self._publish(STOCK_SHADOW_VERIFICATION_STOPPED, {"status": "stopped", "mode": "OBSERVER_ONLY"})

    async def run_once(self) -> list[Event]:
        return [
            Event(
                topic=STOCK_SHADOW_VERIFICATION_HEARTBEAT,
                source=self.name,
                payload={
                    "status": "ok" if self.status.healthy else "warning",
                    "mode": "OBSERVER_ONLY",
                    "cases": self.status.cases,
                    "completed_outcomes": self.status.completed_outcomes,
                    "persisted_records": self.status.persisted_records,
                },
            )
        ]

    async def health(self) -> dict[str, Any]:
        with self._lock:
            return {
                "name": self.status.name,
                "running": self.status.running,
                "healthy": self.status.healthy,
                "mode": "OBSERVER_ONLY",
                "asset_scope": "stock",
                "cases": self.status.cases,
                "decision_links": self.status.decision_links,
                "tracker_links": self.status.tracker_links,
                "completed_outcomes": self.status.completed_outcomes,
                "duplicates_ignored": self.status.duplicates_ignored,
                "source_aliases": self.status.source_aliases,
                "persisted_records": self.status.persisted_records,
                "load_errors": self.status.load_errors,
                "last_symbol": self.status.last_symbol,
                "last_event_at": self.status.last_event_at,
                "last_error": self.status.last_error,
                "ledger_file": str(self.ledger_file),
                "observer_version": self.policy.observer_version,
                "config_fingerprint": self.config_fingerprint,
                "ready_for_telegram": False,
                "order_execution_allowed": False,
            }

    def snapshot(self, *, days: int = 7, limit: int = 50) -> dict[str, Any]:
        """Return a compact read-only materialized view for API and UI."""

        days = min(max(int(days), 1), 365)
        limit = min(max(int(limit), 1), 500)
        cutoff = datetime.now(UTC) - timedelta(days=days)
        with self._lock:
            cached = self._snapshot_cache.get((days, limit))
            if cached is not None and cached[0] == self._generation:
                return deepcopy(cached[1])
            generation = self._generation
            records = [deepcopy(record) for record in self._records.values()]
        records = [record for record in records if (_parse(record.get("created_at")) or cutoff) >= cutoff]
        records.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        summary = _summarize(records)
        result = {
            "schema_name": "pandorickki.stock-shadow-verification-summary",
            "schema_version": 1,
            "mode": "OBSERVER_ONLY",
            "asset_scope": "stock",
            "days": days,
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": summary,
            "disagreement_outcome_matrix": _disagreement_matrix(records),
            "records": [_public_record(record) for record in records[:limit]],
            "ready_for_telegram": False,
            "order_execution_allowed": False,
        }
        with self._lock:
            if generation == self._generation:
                self._snapshot_cache[(days, limit)] = (generation, deepcopy(result))
        return result

    def detail(self, verification_id: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._records.get(str(verification_id))
            return _public_record(deepcopy(record)) if record is not None else None

    def _handle_observation(self, event: Event) -> None:
        if not self.status.running:
            return
        try:
            data = _payload_data(event)
            record = build_verification_record(
                data,
                policy=self.policy,
                config_fingerprint=self.config_fingerprint,
            )
            verification_id = str(record["verification_id"])
            source_event_id = str(data.get("source_event_id") or "")
            with self._lock:
                existing = self._records.get(verification_id)
            if existing is not None:
                if source_event_id and source_event_id not in existing.get("source_event_ids", []):
                    entry = {
                        "record_type": "SOURCE_EVENT_LINKED",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "verification_id": verification_id,
                        "source_event_id": source_event_id,
                    }
                    self._append_and_apply(entry)
                    self.status.source_aliases += 1
                else:
                    self.status.duplicates_ignored += 1
                return
            entry = {
                "record_type": "VERIFICATION_CREATED",
                "timestamp": datetime.now(UTC).isoformat(),
                "verification_id": verification_id,
                "payload": record,
            }
            self._append_and_apply(entry)
            self.status.cases = len(self._records)
            self.status.last_symbol = record.get("symbol")
            self.status.last_event_at = entry["timestamp"]
            self._publish(STOCK_SHADOW_VERIFICATION_UPDATED, _public_record(record))
        except Exception as exc:  # noqa: BLE001 - observer failures must not affect market flow
            self._record_error(exc)

    def _handle_decision(self, event: Event) -> None:
        if not self.status.running:
            return
        try:
            data = _payload_data(event)
            if str(data.get("market_type") or "").lower() != "stock":
                return
            source_event_id = str(data.get("source_event_id") or "")
            decision_id = str(data.get("decision_id") or "")
            with self._lock:
                verification_id = self._source_index.get(source_event_id)
                existing_id = (
                    _mapping(self._records.get(verification_id, {}).get("legacy")).get("decision_id")
                    if verification_id
                    else None
                )
            if not verification_id or not decision_id or existing_id == decision_id:
                return
            entry = {
                "record_type": "LEGACY_DECISION_LINKED",
                "timestamp": datetime.now(UTC).isoformat(),
                "verification_id": verification_id,
                "decision_id": decision_id,
                "decision_event_id": event.event_id,
            }
            self._append_and_apply(entry)
            self.status.decision_links += 1
        except Exception as exc:  # noqa: BLE001
            self._record_error(exc)

    def _handle_tracker_outcome(self, event: Event) -> None:
        if not self.status.running:
            return
        try:
            data = _payload_data(event)
            if str(data.get("market_type") or "").lower() != "stock":
                return
            decision_id = str(data.get("decision_id") or "")
            with self._lock:
                verification_id = self._decision_index.get(decision_id)
                tracker = _mapping(_mapping(self._records.get(verification_id, {}).get("outcome")).get("tracker"))
            if not verification_id or tracker:
                return
            projection = {
                "decision_id": decision_id,
                "result_type": data.get("result_type"),
                "gross_profit_percent": data.get("gross_profit_percent"),
                "exit_time": data.get("exit_time"),
                "close_reason": data.get("close_reason"),
            }
            entry = {
                "record_type": "TRACKER_OUTCOME_LINKED",
                "timestamp": datetime.now(UTC).isoformat(),
                "verification_id": verification_id,
                "payload": projection,
            }
            self._append_and_apply(entry)
            self.status.tracker_links += 1
        except Exception as exc:  # noqa: BLE001
            self._record_error(exc)

    def _handle_stock_price(self, event: Event) -> None:
        if not self.status.running:
            return
        try:
            data = _payload_data(event)
            symbol = str(data.get("symbol") or "").upper()
            price = data.get("current_price", data.get("price"))
            quote_timestamp = data.get("price_timestamp")
            now = datetime.now(UTC)
            with self._lock:
                candidates = [
                    deepcopy(record)
                    for record in self._records.values()
                    if record.get("symbol") == symbol
                    and _mapping(record.get("outcome")).get("status") == "PENDING"
                ]
            candidates.sort(key=lambda item: str(item.get("evaluation_due_at") or ""))
            candidates = candidates[: self.outcome_batch_size]
            for record in candidates:
                outcome = complete_forward_outcome(
                    record,
                    exit_price=price,
                    quote_timestamp=quote_timestamp,
                    evaluated_at=now,
                )
                if outcome is None:
                    continue
                entry = {
                    "record_type": "OUTCOME_COMPLETED",
                    "timestamp": now.isoformat(),
                    "verification_id": record["verification_id"],
                    "payload": outcome,
                }
                self._append_and_apply(entry)
                self.status.completed_outcomes += 1
                updated = self.detail(str(record["verification_id"]))
                if updated is not None:
                    self._publish(STOCK_SHADOW_VERIFICATION_UPDATED, updated)
        except Exception as exc:  # noqa: BLE001
            self._record_error(exc)

    def _append_and_apply(self, entry: dict[str, Any]) -> None:
        self.ledger.append(entry)
        with self._lock:
            self._apply_entry(entry)
            self._generation += 1
            self._snapshot_cache.clear()
            self.status.persisted_records += 1
            self.status.healthy = True
            self.status.last_error = None

    def _load_ledger(self) -> None:
        for path in related_jsonl_files(self.ledger_file):
            try:
                with path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        if not line.strip():
                            continue
                        try:
                            entry = json.loads(line)
                            if isinstance(entry, dict):
                                self._apply_entry(entry)
                                self.status.persisted_records += 1
                        except (TypeError, ValueError, json.JSONDecodeError):
                            self.status.load_errors += 1
            except OSError:
                self.status.load_errors += 1
        self.status.cases = len(self._records)
        self.status.completed_outcomes = sum(
            _mapping(record.get("outcome")).get("status") == "COMPLETED"
            for record in self._records.values()
        )
        self._generation += 1
        self._snapshot_cache.clear()
        self.status.healthy = self.status.load_errors == 0

    def _apply_entry(self, entry: Mapping[str, Any]) -> None:
        record_type = str(entry.get("record_type") or "")
        verification_id = str(entry.get("verification_id") or "")
        if record_type == "VERIFICATION_CREATED":
            payload = _mapping(entry.get("payload"))
            if not verification_id or verification_id in self._records or not payload:
                return
            self._records[verification_id] = payload
            for source_id in payload.get("source_event_ids", []):
                if source_id:
                    self._source_index[str(source_id)] = verification_id
            decision_id = _mapping(payload.get("legacy")).get("decision_id")
            if decision_id:
                self._decision_index[str(decision_id)] = verification_id
            return
        record = self._records.get(verification_id)
        if record is None:
            return
        if record_type == "SOURCE_EVENT_LINKED":
            source_id = str(entry.get("source_event_id") or "")
            if source_id and source_id not in record["source_event_ids"]:
                record["source_event_ids"].append(source_id)
                self._source_index[source_id] = verification_id
        elif record_type == "LEGACY_DECISION_LINKED":
            decision_id = str(entry.get("decision_id") or "")
            if decision_id:
                record["legacy"]["decision_id"] = decision_id
                record["legacy"]["decision_event_id"] = entry.get("decision_event_id")
                self._decision_index[decision_id] = verification_id
        elif record_type == "TRACKER_OUTCOME_LINKED":
            record["outcome"]["tracker"] = _mapping(entry.get("payload"))
        elif record_type == "OUTCOME_COMPLETED":
            record["outcome"] = _mapping(entry.get("payload"))

    def _record_error(self, exc: Exception) -> None:
        self.status.healthy = False
        self.status.last_error = str(exc)
        self._publish(
            STOCK_SHADOW_VERIFICATION_ERROR,
            {"error": str(exc), "mode": "OBSERVER_ONLY", "asset_scope": "stock"},
        )

    def _publish(self, topic: str, payload: dict[str, Any]) -> None:
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


def _payload_data(event: Event) -> dict[str, Any]:
    payload = event.payload if isinstance(event.payload, dict) else {}
    data = payload.get("payload", payload)
    return dict(data) if isinstance(data, Mapping) else {}


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _parse(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    except (TypeError, ValueError):
        return None


def _public_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return the explicit browser-safe projection; no candles or raw payloads."""

    return {
        key: deepcopy(record.get(key))
        for key in (
            "schema_name",
            "schema_version",
            "observer_version",
            "mode",
            "verification_id",
            "asset_type",
            "symbol",
            "cycle_id",
            "source_event_ids",
            "analysis_timestamp",
            "source_timestamp",
            "quote_timestamp",
            "latest_candle_timestamp",
            "entry_price",
            "evaluation_due_at",
            "outcome_policy",
            "data_quality",
            "legacy",
            "shadow",
            "comparison",
            "outcome",
            "config_fingerprint",
            "created_at",
            "ready_for_telegram",
            "order_execution_allowed",
            "affects_active_decision",
        )
    }


def _summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    comparable = [record for record in records if _mapping(record.get("comparison")).get("decisions_match") is not None]
    agreement = sum(_mapping(record.get("comparison")).get("decisions_match") is True for record in comparable)
    disagreement = len(comparable) - agreement
    quality = {name: 0 for name in ("OK", "DEGRADED", "REJECTED")}
    gates = {name: 0 for name in ("PASS", "BLOCK", "HOLD", "UNKNOWN")}
    outcomes = {name: 0 for name in ("PENDING", "COMPLETED", "UNKNOWN")}
    for record in records:
        quality_status = str(_mapping(record.get("data_quality")).get("status") or "REJECTED")
        quality[quality_status] = quality.get(quality_status, 0) + 1
        gate_status = str(_mapping(record.get("shadow")).get("gate_status") or "UNKNOWN")
        gates[gate_status] = gates.get(gate_status, 0) + 1
        outcome_status = str(_mapping(record.get("outcome")).get("status") or "UNKNOWN")
        outcomes[outcome_status] = outcomes.get(outcome_status, 0) + 1
    return {
        "shadow_cases": len(records),
        "comparable_cases": len(comparable),
        "agreement": agreement,
        "disagreement": disagreement,
        "agreement_rate_percent": round(agreement / len(comparable) * 100.0, 4) if comparable else None,
        "disagreement_rate_percent": round(disagreement / len(comparable) * 100.0, 4) if comparable else None,
        "gate_blocks": gates.get("BLOCK", 0),
        "data_quality": quality,
        "shadow_gate": gates,
        "outcomes": outcomes,
    }


def _disagreement_matrix(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        comparison = _mapping(record.get("comparison"))
        if comparison.get("decisions_match") is not False:
            continue
        legacy = str(_mapping(record.get("legacy")).get("decision") or "UNKNOWN")
        shadow = str(_mapping(record.get("shadow")).get("decision") or "UNKNOWN")
        key = (legacy, shadow)
        bucket = buckets.setdefault(
            key,
            {
                "legacy_decision": legacy,
                "shadow_decision": shadow,
                "count": 0,
                "shadow_outcomes": {name: 0 for name in ("PENDING", "WIN", "LOSS", "NEUTRAL", "UNKNOWN")},
            },
        )
        bucket["count"] += 1
        outcome = _mapping(_mapping(record.get("outcome")).get("shadow"))
        status = str(outcome.get("status") or "UNKNOWN")
        bucket["shadow_outcomes"][status] = bucket["shadow_outcomes"].get(status, 0) + 1
    return sorted(buckets.values(), key=lambda item: (-item["count"], item["legacy_decision"], item["shadow_decision"]))
