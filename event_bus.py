"""Small synchronous event bus for PandorickKi services."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any, Callable
from uuid import uuid4


EventHandler = Callable[["Event"], None]


@dataclass(frozen=True)
class Event:
    """Event exchanged between adapters and platform services."""

    topic: str
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class EventBus:
    """In-process publish/subscribe bus."""

    def __init__(self, *, max_history: int = 2000) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._max_history = max(max_history, 0)
        self._history: deque[Event] = deque(maxlen=self._max_history or None)
        self._published_count = 0
        self._discarded_count = 0
        self._lock = RLock()

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        """Register a handler for one topic."""

        with self._lock:
            self._subscribers[topic].append(handler)

    def unsubscribe(self, topic: str, handler: EventHandler) -> None:
        """Remove a handler from one topic when present."""

        with self._lock:
            if handler in self._subscribers[topic]:
                self._subscribers[topic].remove(handler)

    def publish(self, event: Event) -> None:
        """Publish an event to topic-specific and wildcard subscribers."""

        with self._lock:
            if self._max_history and len(self._history) >= self._max_history:
                self._discarded_count += 1
            self._history.append(event)
            self._published_count += 1
            handlers = [*self._subscribers[event.topic], *self._subscribers["*"]]

        for handler in handlers:
            handler(event)

    def history(self) -> list[Event]:
        """Return a copy of emitted events."""

        with self._lock:
            return list(self._history)

    def queue_size(self) -> int:
        """Return the current in-memory event history size."""

        with self._lock:
            return len(self._history)

    def stats(self) -> dict[str, int]:
        """Return lightweight in-memory event bus metrics."""

        with self._lock:
            return {
                "queue_size": len(self._history),
                "max_history": self._max_history,
                "published_count": self._published_count,
                "discarded_count": self._discarded_count,
            }
