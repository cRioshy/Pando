"""Whitelist sanitizer for public Learning Graph data."""

from __future__ import annotations

from typing import Any

from learning_graph.graph_config import (
    ALLOWED_EDGE_FIELDS,
    ALLOWED_NODE_FIELDS,
    EDGE_TYPES,
    NODE_TYPES,
    SECRET_FIELD_MARKERS,
)


class GraphSanitizer:
    """Remove non-public fields before data reaches the browser."""

    def sanitize_node(self, node: dict[str, Any]) -> dict[str, Any]:
        """Return a whitelisted public node."""

        clean = self._whitelist(node, ALLOWED_NODE_FIELDS)
        if clean.get("type") not in NODE_TYPES:
            clean["type"] = "SYSTEM"
        return clean

    def sanitize_edge(self, edge: dict[str, Any]) -> dict[str, Any]:
        """Return a whitelisted public edge."""

        clean = self._whitelist(edge, ALLOWED_EDGE_FIELDS)
        if clean.get("type") not in EDGE_TYPES:
            clean["type"] = "RELATED_MARKET"
        return clean

    def sanitize_graph(self, graph: dict[str, Any]) -> dict[str, Any]:
        """Sanitize a complete graph payload."""

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        stats = graph.get("stats", {})
        return {
            "nodes": [self.sanitize_node(node) for node in nodes if isinstance(node, dict)],
            "edges": [self.sanitize_edge(edge) for edge in edges if isinstance(edge, dict)],
            "stats": self.sanitize_public_stats(stats if isinstance(stats, dict) else {}),
        }

    def sanitize_public_stats(self, stats: dict[str, Any]) -> dict[str, Any]:
        """Return public stats without paths or secret-like fields."""

        allowed = {
            "visible_nodes",
            "visible_edges",
            "analyses_processed",
            "patterns_recognized",
            "new_learnings_today",
            "pattern_buckets",
            "learning_projection_records_today",
            "learning_update_events_total",
            "ml_training_active",
            "model_updates",
            "active_markets",
            "last_update",
            "system_status",
        }
        return self._whitelist(stats, allowed)

    def _whitelist(self, data: dict[str, Any], allowed: set[str]) -> dict[str, Any]:
        """Whitelist keys and strip secret-looking values."""

        clean: dict[str, Any] = {}
        for key, value in data.items():
            key_text = str(key).lower()
            if key not in allowed:
                continue
            if any(marker in key_text for marker in SECRET_FIELD_MARKERS):
                continue
            if self._looks_secret(value):
                continue
            clean[key] = value
        return clean

    def _looks_secret(self, value: Any) -> bool:
        """Detect values that look like paths, tokens or raw internals."""

        if isinstance(value, (dict, list, tuple, set)):
            return True
        text = str(value)
        lower = text.lower()
        if "c:\\users\\" in lower or "/users/" in lower:
            return True
        if any(marker in lower for marker in ("api_key", "token=", "password", "secret")):
            return True
        return False
