"""Shared runtime state for PandorickKi."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any


@dataclass
class ServiceState:
    """Current status of one platform service."""

    name: str
    status: str = "INITIALIZED"
    last_seen: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    details: dict[str, Any] = field(default_factory=dict)


class SharedState:
    """In-memory state with optional JSON persistence."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.services: dict[str, ServiceState] = {}
        self.values: dict[str, Any] = {}
        self._lock = RLock()

    def update_service(
        self,
        name: str,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Update one service status."""

        with self._lock:
            self.services[name] = ServiceState(
                name=name,
                status=status,
                details=details or {},
            )

    def set_value(self, key: str, value: Any) -> None:
        """Store a shared value."""

        with self._lock:
            self.values[key] = value

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable shared state."""

        with self._lock:
            return {
                "services": {name: asdict(state) for name, state in self.services.items()},
                "values": dict(self.values),
            }

    async def get_snapshot(self) -> dict[str, Any]:
        """Return an async-friendly safe snapshot."""

        return self.to_dict()

    def save(self) -> None:
        """Persist state to disk when a path is configured."""

        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=2, ensure_ascii=True)
