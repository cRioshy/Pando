"""Public Knowledge Graph models for the Pandorick Control Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from hashlib import sha1
from typing import Any


def _safe_slug(value: str) -> str:
    """Return a stable public slug."""

    text = "".join(char.lower() if char.isalnum() else "_" for char in str(value)).strip("_")
    while "__" in text:
        text = text.replace("__", "_")
    return text or "unknown"


def stable_knowledge_node_id(node_type: str, group: str, label: str) -> str:
    """Create a stable public node id."""

    return f"{_safe_slug(node_type)}:{_safe_slug(group)}:{_safe_slug(label)}"


def stable_knowledge_edge_id(source: str, relation: str, target: str) -> str:
    """Create a stable public edge id."""

    digest = sha1(f"{source}|{relation}|{target}".encode("utf-8")).hexdigest()[:16]
    return f"edge:{digest}"


@dataclass(frozen=True)
class KnowledgeNode:
    """One browser-safe knowledge node."""

    id: str
    label: str
    type: str
    group: str
    importance: float
    confidence: float | None = None
    count: int = 1
    status: str = "ACTIVE"
    last_updated: str | None = None
    health: str = "OK"
    metadata: dict[str, str | int | float | bool | None] = field(default_factory=dict)
    details_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dictionary."""

        payload = asdict(self)
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True)
class KnowledgeEdge:
    """One browser-safe knowledge edge."""

    id: str
    source: str
    target: str
    relation: str
    weight: float
    confidence: float | None = None
    event_count: int = 1
    last_updated: str | None = None
    direction: str = "directed"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dictionary."""

        payload = asdict(self)
        return {key: value for key, value in payload.items() if value is not None}


@dataclass(frozen=True)
class KnowledgeGraph:
    """One public Knowledge Graph response."""

    generated_at: str
    node_count: int
    edge_count: int
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]

    @classmethod
    def empty(cls) -> "KnowledgeGraph":
        """Return an empty graph."""

        return cls(
            generated_at=datetime.now(UTC).isoformat(),
            node_count=0,
            edge_count=0,
            nodes=[],
            edges=[],
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dictionary."""

        return asdict(self)
