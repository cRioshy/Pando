"""Read-only NeuroBrain receiver for PandorickKi event coexistence."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from queue import Empty, Full, Queue
from threading import Event as ThreadEvent
from threading import RLock, Thread
from time import monotonic
from typing import Any

from atomic_json import atomic_write_json
from event_bus import Event, EventBus
from event_payload_contract import compact_market_payload, compact_observer_payload
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

OBSERVER_TOPICS = frozenset({"AI_LEARNING_UPDATED", "STOCK_MARKET_DATA_UPDATED"})
MARKET_TYPE_BY_TOPIC = {
    "CRYPTO_MARKET_DATA_UPDATED": "crypto",
    "COMMODITY_MARKET_DATA_UPDATED": "commodity",
}


@dataclass
class NeuroBrainReceiverStatus:
    """Runtime state for the read-only NeuroBrain receiver."""

    name: str = "neurobrain_receiver"
    running: bool = False
    healthy: bool = True
    received_events: int = 0
    ignored_events: int = 0
    duplicate_events: int = 0
    dropped_events: int = 0
    failed_events: int = 0
    status_write_failures: int = 0
    notification_failures: int = 0
    batches_written: int = 0
    last_batch_size: int = 0
    worker_running: bool = False
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
        queue_capacity: int = 2048,
        batch_size: int = 64,
        flush_interval_seconds: float = 0.25,
    ) -> None:
        self.event_bus = event_bus
        self.inbox_file = inbox_file
        self.status_file = status_file
        self.allowed_topics = frozenset(allowed_topics or DEFAULT_NEUROBRAIN_TOPICS)
        self.ledger = RotatingJsonlLedger(inbox_file, max_bytes=ledger_rotation_bytes)
        self.queue_capacity = max(int(queue_capacity), 1)
        self.batch_size = max(int(batch_size), 1)
        self.flush_interval_seconds = max(float(flush_interval_seconds), 0.01)
        self._queue: Queue[dict[str, Any]] = Queue(maxsize=self.queue_capacity)
        self._stop_worker = ThreadEvent()
        self._worker: Thread | None = None
        self._accepting = False
        self.status = NeuroBrainReceiverStatus(
            inbox_path=str(inbox_file),
            status_path=str(status_file),
        )
        self._subscribed = False
        self._lock = RLock()
        self._seen_event_ids: set[str] = set()

    async def start(self) -> None:
        """Start receiving selected EventBus events."""

        with self._lock:
            if self.status.running:
                return
            self._stop_worker.clear()
            self._accepting = True
            self.status.running = True
            self.status.worker_running = True
            self.status.healthy = self._is_healthy_locked()
            if self.status.healthy:
                self.status.last_error = None
            self._worker = Thread(
                target=self._worker_loop,
                name="pandorickki:neurobrain-writer",
                daemon=False,
            )
            worker = self._worker
        worker.start()
        if not self._subscribed:
            self.event_bus.subscribe("*", self._handle_event)
            self._subscribed = True
        self._write_status()
        self._publish(
            NEUROBRAIN_RECEIVER_STARTED,
            {
                "status": "started",
                "mode": "read_only_queued",
                "queue_capacity": self.queue_capacity,
                "batch_size": self.batch_size,
            },
        )

    async def stop(self) -> None:
        """Stop receiving events and persist the latest status."""

        with self._lock:
            if not self.status.running and self._worker is None and not self._subscribed:
                return
        if self._subscribed:
            self.event_bus.unsubscribe("*", self._handle_event)
            self._subscribed = False
        with self._lock:
            self._accepting = False
            worker = self._worker
        self._stop_worker.set()
        if worker is not None and worker.is_alive():
            await asyncio.to_thread(worker.join)
        with self._lock:
            self.status.running = False
            self.status.worker_running = False
            self._worker = None
        self._write_status()
        self._publish(
            NEUROBRAIN_RECEIVER_STOPPED,
            {
                "status": "stopped",
                "queue_depth": self._queue.qsize(),
                "dropped_events": self.status.dropped_events,
            },
        )

    async def run_once(self) -> list[Event]:
        """Emit a lightweight heartbeat; event capture happens in callbacks."""

        with self._lock:
            payload = {
                "status": "ok" if self.status.healthy else "warning",
                "received_events": self.status.received_events,
                "ignored_events": self.status.ignored_events,
                "duplicate_events": self.status.duplicate_events,
                "dropped_events": self.status.dropped_events,
                "failed_events": self.status.failed_events,
                "status_write_failures": self.status.status_write_failures,
                "notification_failures": self.status.notification_failures,
                "queue_depth": self._queue.qsize(),
                "queue_capacity": self.queue_capacity,
                "batches_written": self.status.batches_written,
                "worker_running": self.status.worker_running,
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
                "dropped_events": self.status.dropped_events,
                "failed_events": self.status.failed_events,
                "status_write_failures": self.status.status_write_failures,
                "notification_failures": self.status.notification_failures,
                "queue_depth": self._queue.qsize(),
                "queue_capacity": self.queue_capacity,
                "batch_size": self.batch_size,
                "batches_written": self.status.batches_written,
                "last_batch_size": self.status.last_batch_size,
                "worker_running": self.status.worker_running,
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
            if not self._accepting:
                self.status.ignored_events += 1
                return
            if event.event_id in self._seen_event_ids:
                self.status.duplicate_events += 1
                return
            try:
                record = self._to_record(event)
            except Exception as exc:
                self.status.failed_events += 1
                self.status.healthy = False
                self.status.last_error = f"projection failed: {exc}"
                return
            try:
                self._queue.put_nowait(record)
            except Full:
                self.status.dropped_events += 1
                self.status.healthy = False
                self.status.last_error = f"queue full; newest event dropped: {event.topic}"
                return
            self._seen_event_ids.add(event.event_id)

    def _worker_loop(self) -> None:
        """Drain accepted records in FIFO batches until shutdown is complete."""

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
                    self._persist_batch(batch)
                finally:
                    for _ in batch:
                        self._queue.task_done()
        finally:
            with self._lock:
                self.status.worker_running = False

    def _persist_batch(self, batch: list[dict[str, Any]]) -> None:
        """Persist one accepted FIFO batch and publish compact receipts."""

        try:
            self.ledger.append_many(batch)
        except Exception as exc:
            with self._lock:
                self.status.failed_events += len(batch)
                self.status.healthy = False
                self.status.last_error = str(exc)
            self._write_status_from_worker()
            self._publish_worker_event(
                NEUROBRAIN_RECEIVER_ERROR,
                {"error": str(exc), "topic": batch[0].get("topic"), "batch_size": len(batch)},
            )
            return

        with self._lock:
            first_received = self.status.received_events + 1
            self.status.received_events += len(batch)
            self.status.batches_written += 1
            self.status.last_batch_size = len(batch)
            last = batch[-1]
            self.status.last_topic = last.get("topic")
            self.status.last_symbol = last.get("symbol")
            self.status.last_event_at = last["received_at"]
            self.status.healthy = self._is_healthy_locked()
            if self.status.healthy:
                self.status.last_error = None
        self._write_status_from_worker()
        for index, record in enumerate(batch):
            self._publish_worker_event(
                NEUROBRAIN_EVENT_RECEIVED,
                {
                    "source_event_id": record["source_event_id"],
                    "topic": record["topic"],
                    "symbol": record.get("symbol"),
                    "market_type": record.get("market_type"),
                    "received_events": first_received + index,
                },
            )

    def _to_record(self, event: Event) -> dict[str, Any]:
        """Convert an EventBus event to a stable NeuroBrain inbox record."""

        payload = event.payload if isinstance(event.payload, dict) else {"raw_payload": event.payload}
        if event.topic in OBSERVER_TOPICS:
            observer_source = payload
            if not isinstance(payload.get("event_type"), str):
                observer_source = {"event_type": event.topic, "payload": payload}
            compact_payload = compact_observer_payload(observer_source)
        else:
            compact_payload = compact_market_payload(payload)
            inferred_market_type = MARKET_TYPE_BY_TOPIC.get(event.topic)
            if inferred_market_type and not compact_payload.get("market_type"):
                compact_payload["market_type"] = inferred_market_type
        return {
            "received_at": datetime.now(UTC).isoformat(),
            "source_event_id": event.event_id,
            "topic": event.topic,
            "source": event.source,
            "source_created_at": event.created_at,
            "event_type": compact_payload.get("event_type", event.topic),
            "market_type": compact_payload.get("market_type"),
            "symbol": compact_payload.get("symbol"),
            "decision_id": compact_payload.get("decision_id"),
            "signal_id": compact_payload.get("signal_id"),
            "direction": compact_payload.get("direction"),
            "probability": compact_payload.get("probability"),
            "source_timestamp": compact_payload.get("source_timestamp"),
            "payload": compact_payload,
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
                "dropped_events": self.status.dropped_events,
                "failed_events": self.status.failed_events,
                "status_write_failures": self.status.status_write_failures,
                "notification_failures": self.status.notification_failures,
                "queue_depth": self._queue.qsize(),
                "queue_capacity": self.queue_capacity,
                "batch_size": self.batch_size,
                "batches_written": self.status.batches_written,
                "last_batch_size": self.status.last_batch_size,
                "worker_running": self.status.worker_running,
                "last_topic": self.status.last_topic,
                "last_symbol": self.status.last_symbol,
                "last_error": self.status.last_error,
                "last_event_at": self.status.last_event_at,
                "inbox_path": str(self.inbox_file),
                "updated_at": datetime.now(UTC).isoformat(),
            }
            atomic_write_json(self.status_file, payload)

    def _write_status_from_worker(self) -> None:
        """Keep a transient status-file failure from terminating the writer."""

        try:
            self._write_status()
        except Exception as exc:
            with self._lock:
                self.status.status_write_failures += 1
                self.status.healthy = False
                self.status.last_error = f"status write failed: {exc}"
            self._publish_worker_event(
                NEUROBRAIN_RECEIVER_ERROR,
                {"error": str(exc), "stage": "status_write"},
            )

    def _publish_worker_event(self, topic: str, payload: dict[str, Any]) -> None:
        """Keep receipt subscribers from terminating the persistence worker."""

        try:
            self._publish(topic, payload)
        except Exception as exc:
            with self._lock:
                self.status.notification_failures += 1
                self.status.healthy = False
                self.status.last_error = f"notification failed: {exc}"

    def _is_healthy_locked(self) -> bool:
        """Return whether the current session has persisted without loss/failure."""

        return not any(
            (
                self.status.dropped_events,
                self.status.failed_events,
                self.status.status_write_failures,
                self.status.notification_failures,
            )
        )

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
