"""Serializable models for the public Pandorick Learning Graph."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class GraphNode:
    """One public graph node."""

    id: str
    label: str
    type: str
    status: str = "ACTIVE"
    market: str | None = None
    timestamp: str | None = None
    data_quality: str | None = None
    similar_cases: int | None = None
    public_confidence: str | None = None
    public_result: str | None = None
    analysis_count: int | None = None
    last_seen: str | None = None
    activity_count: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe node dictionary."""

        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True)
class GraphEdge:
    """One public graph edge."""

    id: str
    source: str
    target: str
    type: str
    label: str | None = None
    count: int = 1
    last_seen: str | None = None
    status: str = "OBSERVED"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe edge dictionary."""

        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True)
class GraphStats:
    """Public graph statistics."""

    visible_nodes: int = 0
    visible_edges: int = 0
    analyses_processed: int = 0
    patterns_recognized: int = 0
    new_learnings_today: int = 0
    pattern_buckets: int = 0
    learning_projection_records_today: int = 0
    learning_update_events_total: int = 0
    ml_training_active: bool = False
    model_updates: int = 0
    active_markets: int = 0
    last_update: str | None = None
    system_status: str = "PENDING"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe stats dictionary."""

        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True)
class LearningGraph:
    """A sanitized public graph snapshot."""

    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return graph as JSON-safe dictionary."""

        return {"nodes": self.nodes, "edges": self.edges, "stats": self.stats}


def stable_node_id(node_type: str, label: str) -> str:
    """Create a stable public node id."""

    safe_label = "".join(char.lower() if char.isalnum() else "_" for char in str(label)).strip("_")
    safe_type = "".join(char.lower() if char.isalnum() else "_" for char in str(node_type)).strip("_")
    return f"{safe_type}:{safe_label}"


def stable_edge_id(source: str, edge_type: str, target: str) -> str:
    """Create a stable public edge id."""

    return f"{source}|{edge_type}|{target}"
