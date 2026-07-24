"""Health monitoring for PandorickKi services."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shared_state import SharedState


@dataclass(frozen=True)
class HealthReport:
    """Snapshot of platform health."""

    status: str
    created_at: str
    services: dict[str, str]
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable health data."""

        return asdict(self)


class HealthMonitor:
    """Build lightweight health reports from shared state and paths."""

    def __init__(self, required_paths: list[Path] | None = None) -> None:
        self.required_paths = required_paths or []

    def check(self, state: SharedState) -> HealthReport:
        """Create a health report without touching external services."""

        warnings: list[str] = []
        for path in self.required_paths:
            if not path.exists():
                warnings.append(f"Missing path: {path}")

        service_statuses = {
            name: service.status for name, service in state.services.items()
        }
        if any(status.upper() in {"ERROR", "FAILED"} for status in service_statuses.values()):
            platform_status = "DEGRADED"
        elif warnings:
            platform_status = "WARNING"
        else:
            platform_status = "OK"

        return HealthReport(
            status=platform_status,
            created_at=datetime.now(UTC).isoformat(),
            services=service_statuses,
            warnings=warnings,
            details={"service_count": len(service_statuses)},
        )
