"""Queued observer-only persistence and reporting for market regime snapshots."""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Event as ThreadEvent
from threading import RLock, Thread
from time import monotonic
from typing import Any, Mapping, Sequence

from event_bus import Event, EventBus
from jsonl_ledger import RotatingJsonlLedger, related_jsonl_files
from market_regime_contract import (
    QUALITY_STATUSES,
    TREND_DIRECTIONS,
    TREND_PHASES,
    VOLATILITY_REGIMES,
    MarketRegimePolicy,
    build_market_regime_snapshot,
)


MARKET_REGIME_OBSERVER_STARTED = "MARKET_REGIME_OBSERVER_STARTED"
MARKET_REGIME_OBSERVED = "MARKET_REGIME_OBSERVED"
MARKET_REGIME_HEARTBEAT = "MARKET_REGIME_HEARTBEAT"
MARKET_REGIME_OBSERVER_ERROR = "MARKET_REGIME_OBSERVER_ERROR"
MARKET_REGIME_OBSERVER_STOPPED = "MARKET_REGIME_OBSERVER_STOPPED"


@dataclass
class MarketRegimeObserverStatus:
    name: str = "market_regime_observer"
    running: bool = False
    healthy: bool = True
    worker_running: bool = False
    submitted: int = 0
    persisted: int = 0
    duplicates_ignored: int = 0
    dropped_inputs: int = 0
    failed_inputs: int = 0
    batches_written: int = 0
    last_batch_size: int = 0
    last_symbol: str | None = None
    last_regime_id: str | None = None
    last_event_at: str | None = None
    last_error: str | None = None


class MarketRegimeObserverAdapter:
    """Classify in a bounded worker and publish only compact snapshots."""

    name = "market_regime_observer"

    def __init__(
        self,
        event_bus: EventBus,
        *,
        ledger_file: Path,
        policy: MarketRegimePolicy | None = None,
        ledger_rotation_bytes: int = 20 * 1024 * 1024,
        ledger_max_archives: int = 8,
        queue_capacity: int = 512,
        batch_size: int = 32,
        flush_interval_seconds: float = 0.25,
    ) -> None:
        self.event_bus = event_bus
        self.ledger_file = ledger_file
        self.policy = policy or MarketRegimePolicy()
        self.ledger = RotatingJsonlLedger(
            ledger_file,
            max_bytes=ledger_rotation_bytes,
            max_archives=ledger_max_archives,
        )
        self.queue_capacity = max(int(queue_capacity), 1)
        self.batch_size = max(int(batch_size), 1)
        self.flush_interval_seconds = max(float(flush_interval_seconds), 0.01)
        self._queue: Queue[dict[str, Any]] = Queue(maxsize=self.queue_capacity)
        self._stop_worker = ThreadEvent()
        self._worker: Thread | None = None
        self._accepting = False
        self._lock = RLock()
        self._seen_regime_ids: set[str] = set()
        self._records: list[dict[str, Any]] = []
        self._latest: dict[tuple[str, str], dict[str, Any]] = {}
        self.status = MarketRegimeObserverStatus()

    async def start(self) -> None:
        """Rebuild the materialized view and start the bounded worker."""

        with self._lock:
            if self.status.running:
                return
            self._load_existing_locked()
            self._stop_worker.clear()
            self._accepting = True
            self.status.running = True
            self.status.worker_running = True
            self.status.healthy = True
            self.status.last_error = None
            self._worker = Thread(
                target=self._worker_loop,
                name="pandorickki:market-regime-observer",
                daemon=False,
            )
            worker = self._worker
        worker.start()
        self._publish(
            MARKET_REGIME_OBSERVER_STARTED,
            {
                "status": "started",
                "mode": "OBSERVER_ONLY",
                "queue_capacity": self.queue_capacity,
                "batch_size": self.batch_size,
                "known_snapshots": len(self._seen_regime_ids),
            },
        )

    async def stop(self) -> None:
        """Stop accepting, drain every accepted input and join the worker."""

        with self._lock:
            if not self.status.running and self._worker is None:
                return
            self._accepting = False
            worker = self._worker
        self._stop_worker.set()
        if worker is not None and worker.is_alive():
            await asyncio.to_thread(worker.join)
        with self._lock:
            self.status.running = False
            self.status.worker_running = False
            self._worker = None
        self._publish(
            MARKET_REGIME_OBSERVER_STOPPED,
            {
                "status": "stopped",
                "queue_depth": self._queue.qsize(),
                "persisted": self.status.persisted,
                "dropped_inputs": self.status.dropped_inputs,
            },
        )

    def submit(
        self,
        *,
        symbol: Any,
        asset_type: Any,
        timeframe: Any,
        candles: Sequence[Mapping[str, Any]] | None,
        source_event_id: Any,
    ) -> bool:
        """Queue one in-memory feature input without blocking a source adapter."""

        with self._lock:
            if not self._accepting:
                return False
        item = {
            "symbol": str(symbol or ""),
            "asset_type": str(asset_type or ""),
            "timeframe": str(timeframe or ""),
            "source_event_id": str(source_event_id or ""),
            "candles": [dict(row) for row in (candles or []) if isinstance(row, Mapping)],
        }
        try:
            self._queue.put_nowait(item)
        except Full:
            with self._lock:
                self.status.dropped_inputs += 1
                self.status.healthy = False
                self.status.last_error = "market regime queue full; newest input dropped"
            return False
        with self._lock:
            self.status.submitted += 1
        return True

    async def run_once(self) -> list[Event]:
        """Return one lightweight lifecycle heartbeat."""

        with self._lock:
            payload = {
                "status": "ok" if self.status.healthy else "warning",
                "mode": "OBSERVER_ONLY",
                "submitted": self.status.submitted,
                "persisted": self.status.persisted,
                "duplicates_ignored": self.status.duplicates_ignored,
                "dropped_inputs": self.status.dropped_inputs,
                "failed_inputs": self.status.failed_inputs,
                "queue_depth": self._queue.qsize(),
                "queue_capacity": self.queue_capacity,
                "worker_running": self.status.worker_running,
            }
        return [Event(topic=MARKET_REGIME_HEARTBEAT, source=self.name, payload=payload)]

    async def health(self) -> dict[str, Any]:
        with self._lock:
            return {
                "name": self.status.name,
                "running": self.status.running,
                "healthy": self.status.healthy,
                "mode": "OBSERVER_ONLY",
                "submitted": self.status.submitted,
                "persisted": self.status.persisted,
                "duplicates_ignored": self.status.duplicates_ignored,
                "dropped_inputs": self.status.dropped_inputs,
                "failed_inputs": self.status.failed_inputs,
                "queue_depth": self._queue.qsize(),
                "queue_capacity": self.queue_capacity,
                "batch_size": self.batch_size,
                "batches_written": self.status.batches_written,
                "last_batch_size": self.status.last_batch_size,
                "worker_running": self.status.worker_running,
                "last_symbol": self.status.last_symbol,
                "last_regime_id": self.status.last_regime_id,
                "last_event_at": self.status.last_event_at,
                "last_error": self.status.last_error,
                "ledger_file": str(self.ledger_file),
            }

    async def get_status(self) -> dict[str, Any]:
        return await self.health()

    def current(self, *, asset_type: str | None = None, symbol: str | None = None) -> dict[str, Any]:
        normalized_asset = str(asset_type or "").strip().lower()
        normalized_symbol = str(symbol or "").strip().upper()
        with self._lock:
            records = [dict(record) for record in self._latest.values()]
        if normalized_asset:
            records = [record for record in records if str(record.get("asset_type") or "").lower() == normalized_asset]
        if normalized_symbol:
            records = [record for record in records if str(record.get("symbol") or "").upper() == normalized_symbol]
        records.sort(key=lambda item: str(item.get("timestamp") or item.get("created_at") or ""), reverse=True)
        return {
            "schema_name": "pandorickki.market-regime-current",
            "schema_version": 1,
            "items": records,
            "count": len(records),
            "read_only": True,
        }

    def history(
        self,
        *,
        asset_type: str | None = None,
        symbol: str | None = None,
        days: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        records = self._filtered_records(asset_type=asset_type, symbol=symbol, days=days)
        normalized_limit = max(1, min(int(limit), 500))
        normalized_offset = max(int(offset), 0)
        page = records[normalized_offset : normalized_offset + normalized_limit]
        return {
            "schema_name": "pandorickki.market-regime-history",
            "schema_version": 1,
            "items": page,
            "pagination": {
                "offset": normalized_offset,
                "limit": normalized_limit,
                "returned": len(page),
                "total": len(records),
                "has_more": normalized_offset + len(page) < len(records),
            },
            "read_only": True,
        }

    def statistics(
        self,
        *,
        asset_type: str | None = None,
        symbol: str | None = None,
        days: int | None = None,
    ) -> dict[str, Any]:
        records = self._filtered_records(asset_type=asset_type, symbol=symbol, days=days)
        trends = Counter(str(item.get("trend_direction") or "UNKNOWN") for item in records)
        volatility = Counter(str(item.get("volatility_regime") or "UNKNOWN") for item in records)
        phases = Counter(str(item.get("trend_phase") or "UNKNOWN") for item in records)
        quality = Counter(str(item.get("data_quality_status") or "REJECTED") for item in records)
        combinations = Counter(
            f"{item.get('trend_direction', 'UNKNOWN')} + {item.get('volatility_regime', 'UNKNOWN')} + {item.get('trend_phase', 'UNKNOWN')}"
            for item in records
        )
        by_asset: dict[str, int] = dict(Counter(str(item.get("asset_type") or "unknown") for item in records))
        return {
            "schema_name": "pandorickki.market-regime-statistics",
            "schema_version": 1,
            "count": len(records),
            "trend": {value: trends[value] for value in sorted(TREND_DIRECTIONS)},
            "volatility": {value: volatility[value] for value in sorted(VOLATILITY_REGIMES)},
            "phase": {value: phases[value] for value in sorted(TREND_PHASES)},
            "quality": {value: quality[value] for value in sorted(QUALITY_STATUSES)},
            "common_combinations": [
                {"combination": value, "count": count}
                for value, count in combinations.most_common(20)
            ],
            "by_asset_type": by_asset,
            "filters": {"asset_type": asset_type, "symbol": symbol, "days": days},
            "legacy_labels_included": False,
            "read_only": True,
        }

    def _worker_loop(self) -> None:
        try:
            while not self._stop_worker.is_set() or not self._queue.empty():
                try:
                    first = self._queue.get(timeout=self.flush_interval_seconds)
                except Empty:
                    continue
                batch = [first]
                deadline = monotonic() + self.flush_interval_seconds
                while len(batch) < self.batch_size:
                    try:
                        if self._stop_worker.is_set():
                            batch.append(self._queue.get_nowait())
                        else:
                            remaining = deadline - monotonic()
                            if remaining <= 0:
                                break
                            batch.append(self._queue.get(timeout=remaining))
                    except Empty:
                        break
                try:
                    self._process_batch(batch)
                finally:
                    for _ in batch:
                        self._queue.task_done()
        finally:
            with self._lock:
                self.status.worker_running = False

    def _process_batch(self, inputs: list[dict[str, Any]]) -> None:
        snapshots: list[dict[str, Any]] = []
        for item in inputs:
            try:
                snapshot = build_market_regime_snapshot(policy=self.policy, **item)
            except Exception as exc:  # noqa: BLE001 - observer failure must stay isolated
                with self._lock:
                    self.status.failed_inputs += 1
                    self.status.healthy = False
                    self.status.last_error = f"classification failed: {exc}"
                self._publish_worker_event(MARKET_REGIME_OBSERVER_ERROR, {"error": str(exc), "stage": "classify"})
                continue
            with self._lock:
                if snapshot["regime_id"] in self._seen_regime_ids:
                    self.status.duplicates_ignored += 1
                    continue
                self._seen_regime_ids.add(snapshot["regime_id"])
            snapshots.append(snapshot)
        if not snapshots:
            return
        try:
            self.ledger.append_many(snapshots)
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                for snapshot in snapshots:
                    self._seen_regime_ids.discard(snapshot["regime_id"])
                self.status.failed_inputs += len(snapshots)
                self.status.healthy = False
                self.status.last_error = f"persist failed: {exc}"
            self._publish_worker_event(MARKET_REGIME_OBSERVER_ERROR, {"error": str(exc), "stage": "persist"})
            return
        with self._lock:
            self._records.extend(snapshots)
            for snapshot in snapshots:
                self._latest[(snapshot["asset_type"], snapshot["symbol"])] = snapshot
            self.status.persisted += len(snapshots)
            self.status.batches_written += 1
            self.status.last_batch_size = len(snapshots)
            self.status.last_symbol = snapshots[-1]["symbol"]
            self.status.last_regime_id = snapshots[-1]["regime_id"]
            self.status.last_event_at = snapshots[-1]["created_at"]
            self.status.healthy = not (self.status.dropped_inputs or self.status.failed_inputs)
            if self.status.healthy:
                self.status.last_error = None
        for snapshot in snapshots:
            self._publish_worker_event(MARKET_REGIME_OBSERVED, snapshot)

    def _load_existing_locked(self) -> None:
        self._seen_regime_ids.clear()
        self._records.clear()
        self._latest.clear()
        for path in related_jsonl_files(self.ledger_file):
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for line in lines:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, dict) or record.get("schema_name") != "pandorickki.market-regime-snapshot":
                    continue
                regime_id = str(record.get("regime_id") or "")
                if not regime_id or regime_id in self._seen_regime_ids:
                    continue
                self._seen_regime_ids.add(regime_id)
                self._records.append(record)
                self._latest[(str(record.get("asset_type")), str(record.get("symbol")))] = record

    def _filtered_records(
        self,
        *,
        asset_type: str | None = None,
        symbol: str | None = None,
        days: int | None = None,
    ) -> list[dict[str, Any]]:
        normalized_asset = str(asset_type or "").strip().lower()
        normalized_symbol = str(symbol or "").strip().upper()
        cutoff = datetime.now(UTC) - timedelta(days=max(int(days), 0)) if days is not None else None
        with self._lock:
            records = list(self._records)
        filtered: list[dict[str, Any]] = []
        for record in reversed(records):
            if normalized_asset and str(record.get("asset_type") or "").lower() != normalized_asset:
                continue
            if normalized_symbol and str(record.get("symbol") or "").upper() != normalized_symbol:
                continue
            if cutoff is not None:
                created = _parse_datetime(record.get("created_at"))
                if created is None or created < cutoff:
                    continue
            filtered.append(dict(record))
        return filtered

    def _publish_worker_event(self, topic: str, payload: dict[str, Any]) -> None:
        try:
            self._publish(topic, payload)
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self.status.failed_inputs += 1
                self.status.healthy = False
                self.status.last_error = f"notification failed: {exc}"

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


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
