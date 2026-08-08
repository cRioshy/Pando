"""Small serializable models for the local web ControlCenter."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any


ALLOWED_CONTROL_ACTIONS = {
    "start",
    "stop",
    "restart",
    "pause",
    "resume",
    "restart/crypto",
    "restart/stocks",
    "restart/brain",
    "restart/telegram",
}


@dataclass
class WebControlState:
    """Thread-safe browser control state."""

    running: bool = True
    paused: bool = False
    stop_requested: bool = False
    restart_requested: bool = False
    last_command: dict[str, Any] | None = None
    commands: list[dict[str, Any]] = field(default_factory=list)
    _lock: RLock = field(default_factory=RLock, repr=False)

    def apply(self, action: str, source: str) -> dict[str, Any]:
        """Validate and apply one local control action."""

        if action not in ALLOWED_CONTROL_ACTIONS:
            raise ValueError(f"Unsupported control action: {action}")

        command = {
            "action": action,
            "source": source,
            "accepted_at": datetime.now(UTC).isoformat(),
            "status": "ACCEPTED",
        }
        with self._lock:
            if action == "start":
                self.running = True
                self.paused = False
                self.stop_requested = False
            elif action == "stop":
                self.stop_requested = True
                self.running = False
            elif action == "restart":
                self.restart_requested = True
                self.stop_requested = False
                self.running = True
                self.paused = False
            elif action == "pause":
                self.paused = True
            elif action == "resume":
                self.paused = False
                self.running = True
                self.stop_requested = False
            elif action.startswith("restart/"):
                command["note"] = "Service restart was accepted as a safe local control event."
            self.last_command = command
            self.commands.append(command)
            self.commands = self.commands[-50:]
        return dict(command)

    def snapshot(self) -> dict[str, Any]:
        """Return a safe JSON snapshot."""

        with self._lock:
            return {
                "running": self.running,
                "paused": self.paused,
                "stop_requested": self.stop_requested,
                "restart_requested": self.restart_requested,
                "last_command": dict(self.last_command) if self.last_command else None,
                "commands": [dict(command) for command in self.commands],
            }

    def is_paused(self) -> bool:
        """Return whether orchestration cycles should pause."""

        with self._lock:
            return self.paused

    def should_stop(self) -> bool:
        """Return whether continuous orchestration should stop."""

        with self._lock:
            return self.stop_requested

    def take_restart_request(self) -> bool:
        """Atomically consume one pending platform restart request."""

        with self._lock:
            if not self.restart_requested:
                return False
            self.restart_requested = False
            completed_at = datetime.now(UTC).isoformat()
            if self.last_command and self.last_command.get("action") == "restart":
                self.last_command["status"] = "APPLIED"
                self.last_command["completed_at"] = completed_at
            return True
