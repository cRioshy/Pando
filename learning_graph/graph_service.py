"""Read-only public service for the Pandorick Learning Graph."""

from __future__ import annotations

import json
from pathlib import Path
from time import monotonic
from typing import Any

from learning_graph.graph_builder import GraphBuilder
from learning_graph.graph_config import LearningGraphConfig
from learning_graph.graph_repository import GraphRepository


class LearningGraphService:
    """Compose repository, builder and cache for the public graph."""

    def __init__(
        self,
        *,
        brain_events_file: Path,
        brain_events_dir: Path | None = None,
        project_root: Path | None = None,
        shared_state_file: Path | None = None,
        stock_project_path: Path | None = None,
        crypto_project_path: Path | None = None,
        config: LearningGraphConfig | None = None,
        repository: GraphRepository | None = None,
        builder: GraphBuilder | None = None,
    ) -> None:
        self.config = config or LearningGraphConfig()
        self.project_root = project_root or brain_events_file.parent.parent
        self.repository = repository or GraphRepository(
            brain_events_file=brain_events_file,
            brain_events_dir=brain_events_dir,
            max_records=self.config.max_node_limit,
            project_root=project_root,
            shared_state_file=shared_state_file,
            stock_project_path=stock_project_path,
            crypto_project_path=crypto_project_path,
        )
        self.builder = builder or GraphBuilder()
        self._cache: dict[str, Any] | None = None
        self._cache_at = 0.0

    def graph(self, *, node_limit: int | None = None, edge_limit: int | None = None) -> dict[str, Any]:
        """Return a cached sanitized graph."""

        now = monotonic()
        if self._cache is not None and now - self._cache_at <= self.config.cache_ttl_seconds:
            return self._cache
        effective_node_limit = self._clamp(
            node_limit or self.config.default_node_limit,
            self.config.max_node_limit,
        )
        effective_edge_limit = self._clamp(
            edge_limit or self.config.default_edge_limit,
            self.config.max_edge_limit,
        )
        records = self.repository.source_records(limit=self.config.max_node_limit)
        graph = self.builder.build(records, node_limit=effective_node_limit, edge_limit=effective_edge_limit)
        self._cache = self._with_persistent_statistics(graph.to_dict())
        self._cache_at = now
        return self._cache

    def nodes(self) -> list[dict[str, Any]]:
        """Return public nodes."""

        return list(self.graph()["nodes"])

    def edges(self) -> list[dict[str, Any]]:
        """Return public edges."""

        return list(self.graph()["edges"])

    def stats(self) -> dict[str, Any]:
        """Return public stats."""

        return dict(self.graph()["stats"])

    def recent(self) -> list[dict[str, Any]]:
        """Return recent public learning or decision nodes."""

        items = [
            node
            for node in self.nodes()
            if node.get("type") in {"LEARNING", "DECISION", "RESULT"}
        ]
        return items[-self.config.recent_limit:]

    def node(self, node_id: str) -> dict[str, Any] | None:
        """Return one public node by id."""

        for node in self.nodes():
            if node.get("id") == node_id:
                return node
        return None

    def invalidate_cache(self) -> None:
        """Clear the in-memory graph cache."""

        self._cache = None
        self._cache_at = 0.0

    def _clamp(self, value: int, maximum: int) -> int:
        """Clamp public limit values."""

        return max(0, min(int(value), maximum))

    def _with_persistent_statistics(self, graph: dict[str, Any]) -> dict[str, Any]:
        """Blend persistent analysis counters into public graph stats."""

        stats_path = self.project_root / "storage" / "statistics" / "system_statistics.json"
        try:
            with stats_path.open("r", encoding="utf-8", errors="replace") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return graph
        counters = payload.get("counters") if isinstance(payload, dict) else {}
        if not isinstance(counters, dict):
            return graph
        stats = graph.setdefault("stats", {})
        if not isinstance(stats, dict):
            return graph
        total = self._safe_int(counters.get("total_analyses"))
        learnings = self._safe_int(counters.get("learning_updates"))
        if total is not None:
            stats["analyses_processed"] = max(int(stats.get("analyses_processed") or 0), total)
        if learnings is not None:
            stats["learning_update_events_total"] = learnings
        return graph

    def _safe_int(self, value: Any) -> int | None:
        """Parse a non-secret public counter."""

        try:
            return int(value)
        except (TypeError, ValueError):
            return None
