"""Read-only service for the interactive Pandorick Knowledge Graph."""

from __future__ import annotations

from pathlib import Path
from time import monotonic
from typing import Any

from learning_graph.graph_config import LearningGraphConfig
from learning_graph.graph_repository import GraphRepository
from learning_graph.graph_projection_service import GraphProjectionService
from learning_graph.knowledge_graph_builder import KnowledgeGraphBuilder


class KnowledgeGraphService:
    """Serve cached public graph views from existing Pandorick data."""

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
        builder: KnowledgeGraphBuilder | None = None,
        projector: GraphProjectionService | None = None,
    ) -> None:
        self.config = config or LearningGraphConfig()
        self.repository = repository or GraphRepository(
            brain_events_file=brain_events_file,
            brain_events_dir=brain_events_dir,
            max_records=self.config.max_node_limit,
            project_root=project_root,
            shared_state_file=shared_state_file,
            stock_project_path=stock_project_path,
            crypto_project_path=crypto_project_path,
        )
        self.builder = builder or KnowledgeGraphBuilder()
        self.projector = projector or GraphProjectionService()
        self._cache: dict[str, Any] | None = None
        self._cache_at = 0.0
        self._full_cache: dict[str, Any] | None = None
        self._full_cache_at = 0.0
        self._cache_dirty = False
        self._full_cache_dirty = False
        self._min_rebuild_interval_seconds = max(20.0, self.config.cache_ttl_seconds)
        self._version = 0

    def full(self, *, node_limit: int | None = None, min_edge_weight: float = 0.0) -> dict[str, Any]:
        """Return the developer full graph projection."""

        graph = self._full_graph()
        return self.projector.full_projection(
            graph,
            node_limit=self._clamp(node_limit or 500, self.config.max_node_limit),
            min_edge_weight=min_edge_weight,
        )

    def overview(self, *, node_limit: int | None = None, edge_limit: int | None = None) -> dict[str, Any]:
        """Return the compact public overview projection."""

        now = monotonic()
        if self._cache is not None and self._can_reuse_cache(
            now=now,
            cached_at=self._cache_at,
            dirty=self._cache_dirty,
        ):
            return self._cache
        graph = self._full_graph()
        self._cache = self.projector.overview_projection(
            graph,
            node_limit=self._clamp(node_limit or 30, 30),
        )
        self._cache_at = now
        self._cache_dirty = False
        return self._cache

    def _full_graph(self) -> dict[str, Any]:
        """Return a cached full graph before projection."""

        now = monotonic()
        if self._full_cache is not None and self._can_reuse_cache(
            now=now,
            cached_at=self._full_cache_at,
            dirty=self._full_cache_dirty,
        ):
            return self._full_cache
        graph = self.builder.build(
            self.repository.source_records(limit=self.config.max_node_limit),
            node_limit=self.config.max_node_limit,
            edge_limit=self.config.max_edge_limit,
        ).to_dict()
        self._version += 1
        graph["version"] = self._version
        self._full_cache = graph
        self._full_cache_at = now
        self._full_cache_dirty = False
        return self._full_cache

    def cluster(self, cluster_id: str) -> dict[str, Any]:
        """Return one projected cluster."""

        return self.projector.cluster_projection(self._full_graph(), cluster_id)

    def node(self, node_id: str) -> dict[str, Any] | None:
        """Return one node and its strongest direct neighborhood."""

        return self.projector.neighborhood_projection(self._full_graph(), node_id)

    def search(self, query: str, *, limit: int = 25) -> dict[str, Any]:
        """Search visible nodes by public text fields."""

        graph = self.projector.full_projection(self._full_graph(), node_limit=self.config.max_node_limit)
        q = str(query or "").strip().lower()
        if not q:
            matches: list[dict[str, Any]] = []
        else:
            matches = [
                node
                for node in graph["nodes"]
                if q
                in " ".join(
                    str(node.get(field, ""))
                    for field in ("id", "label", "type", "group", "status", "health")
                ).lower()
            ][: max(0, limit)]
        return {
            "generated_at": graph["generated_at"],
            "query": query,
            "node_count": len(matches),
            "edge_count": 0,
            "nodes": matches,
            "edges": [],
        }

    def changes(self, *, since_version: int | None = None) -> dict[str, Any]:
        """Return a lightweight change marker for future live updates."""

        graph = self.overview()
        current_version = int(graph.get("version") or self._version)
        changed = since_version is None or int(since_version) < current_version
        return {
            "generated_at": graph["generated_at"],
            "version": current_version,
            "changed": changed,
            "node_count": graph["node_count"] if changed else 0,
            "edge_count": graph["edge_count"] if changed else 0,
            "nodes": graph["nodes"] if changed else [],
            "edges": graph["edges"] if changed else [],
        }

    def invalidate_cache(self) -> None:
        """Mark cached graph data stale without forcing a rebuild storm."""

        self._cache_dirty = True
        self._full_cache_dirty = True
        if self._cache is None:
            self._cache_at = 0.0
        if self._full_cache is None:
            self._full_cache_at = 0.0

    def _can_reuse_cache(self, *, now: float, cached_at: float, dirty: bool) -> bool:
        """Return whether a cached graph is fresh enough for live rendering."""

        age = now - cached_at
        if dirty:
            return age < self._min_rebuild_interval_seconds
        return age <= self.config.cache_ttl_seconds

    def _clamp(self, value: int, maximum: int) -> int:
        """Clamp public limits."""

        return max(0, min(int(value), maximum))
