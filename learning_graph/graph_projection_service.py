"""Projection layer for readable public Knowledge Graph views."""

from __future__ import annotations

import math
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any


FORCEATLAS2_ITERATIONS = 350
FORCEATLAS2_SETTINGS = {
    "linLogMode": True,
    "outboundAttractionDistribution": True,
    "adjustSizes": True,
    "edgeWeightInfluence": 0.7,
    "scalingRatio": 7.5,
    "strongGravityMode": False,
    "gravity": 0.045,
    "slowDown": 18.0,
}

GROUP_ANCHORS = {
    "brain": (0.0, 0.0),
    "crypto": (-17.0, -2.0),
    "stocks": (17.0, -2.0),
    "learning": (0.0, 14.0),
    "patterns": (-10.0, 12.0),
    "decisions": (10.0, 12.0),
    "indicators": (0.0, -15.0),
    "infrastructure": (0.0, -21.0),
    "errors": (-18.0, 14.0),
    "warnings": (18.0, 14.0),
}

TYPE_PRIORITY = {
    "brain": 34,
    "project": 30,
    "market": 24,
    "cluster": 22,
    "crypto": 18,
    "stock": 18,
    "learning": 16,
    "decision": 15,
    "signal": 14,
    "indicator": 13,
    "pattern": 12,
    "data_source": 11,
    "bot": 10,
    "service": 9,
    "memory": 9,
    "warning": 8,
    "error": 8,
}


class GraphProjectionService:
    """Create readable graph projections from the full public graph."""

    def overview_projection(self, graph: dict[str, Any], *, node_limit: int = 30) -> dict[str, Any]:
        """Return a compact aggregated overview with super-node edges reduced."""

        full = self._with_communities_without_positions(graph)
        nodes = self._overview_nodes(full, node_limit=min(node_limit, 30))
        edges = self._aggregate_overview_edges(full, nodes, edge_limit=40)
        overview_communities = {node["id"]: str(node.get("community") or node.get("group") or "overview") for node in nodes}
        positions, diagnostics = self._forceatlas2_positions(nodes, edges, overview_communities)
        for node in nodes:
            node.update(positions.get(node["id"], {}))
        full["diagnostics"] = diagnostics
        projected = self._finalize(full, nodes, edges, mode="overview")
        projected["mode"] = "overview"
        projected["max_nodes"] = min(node_limit, 30)
        projected["max_edges"] = 40
        return projected

    def _legacy_overview_projection(self, graph: dict[str, Any], *, node_limit: int = 30) -> dict[str, Any]:
        """Return the previous compact overview shape for regression comparison."""

        full = self._with_communities_and_positions(graph)
        nodes = list(full.get("nodes", []))
        edges = list(full.get("edges", []))
        ranked = sorted(nodes, key=self._node_rank, reverse=True)
        keep: list[dict[str, Any]] = []
        seen: set[str] = set()

        for node_type in ("project", "brain", "market", "data_source", "bot"):
            for node in ranked:
                if node.get("type") == node_type and node["id"] not in seen:
                    keep.append(node)
                    seen.add(node["id"])
                    if len(keep) >= node_limit:
                        break
            if len(keep) >= node_limit:
                break

        for group in ("crypto", "stocks", "indicators", "decisions", "patterns", "infrastructure"):
            group_nodes = [node for node in ranked if node.get("group") == group and node["id"] not in seen]
            for node in group_nodes[: self._group_quota(group)]:
                keep.append(node)
                seen.add(node["id"])
                if len(keep) >= node_limit:
                    break
            if len(keep) >= node_limit:
                break

        if len(keep) < node_limit:
            for node in ranked:
                if node["id"] in seen:
                    continue
                keep.append(node)
                seen.add(node["id"])
                if len(keep) >= node_limit:
                    break

        node_ids = {node["id"] for node in keep}
        visible_edges = [
            edge for edge in edges if edge.get("source") in node_ids and edge.get("target") in node_ids
        ]
        visible_edges = self._limit_edges_per_node(visible_edges, max_edges=8)
        projected = self._finalize(full, keep, visible_edges, mode="overview")
        projected["mode"] = "overview"
        projected["max_nodes"] = node_limit
        return projected

    def cluster_projection(self, graph: dict[str, Any], cluster_id: str, *, node_limit: int = 120) -> dict[str, Any]:
        """Return nodes belonging to one group or community."""

        full = self._with_communities_and_positions(graph)
        cluster = str(cluster_id or "").lower()
        nodes = [
            node
            for node in full.get("nodes", [])
            if str(node.get("group", "")).lower() == cluster
            or str(node.get("community", "")).lower() == cluster
        ]
        nodes = sorted(nodes, key=self._node_rank, reverse=True)[:node_limit]
        node_ids = {node["id"] for node in nodes}
        edges = [
            edge
            for edge in full.get("edges", [])
            if edge.get("source") in node_ids and edge.get("target") in node_ids
        ]
        projected = self._finalize(full, nodes, self._limit_edges_per_node(edges, max_edges=12), mode="cluster")
        projected["cluster_id"] = cluster
        return projected

    def neighborhood_projection(self, graph: dict[str, Any], node_id: str, *, max_neighbors: int = 30) -> dict[str, Any] | None:
        """Return one node plus its strongest direct neighbors."""

        full = self._with_communities_and_positions(graph)
        nodes_by_id = {node["id"]: node for node in full.get("nodes", [])}
        if node_id not in nodes_by_id:
            return None
        incident = [
            edge
            for edge in full.get("edges", [])
            if edge.get("source") == node_id or edge.get("target") == node_id
        ]
        incident = sorted(incident, key=self._edge_rank, reverse=True)[:max_neighbors]
        neighbor_ids = {
            value
            for edge in incident
            for value in (edge.get("source"), edge.get("target"))
            if isinstance(value, str)
        }
        nodes = [nodes_by_id[item] for item in neighbor_ids if item in nodes_by_id]
        projected = self._finalize(full, nodes, incident, mode="neighborhood")
        projected["focus_node_id"] = node_id
        projected["node"] = nodes_by_id[node_id]
        projected["neighbors"] = [node for node in nodes if node.get("id") != node_id]
        return projected

    def full_projection(self, graph: dict[str, Any], *, node_limit: int = 500, min_edge_weight: float = 0.0) -> dict[str, Any]:
        """Return a developer full graph projection."""

        full = self._with_communities_and_positions(graph)
        nodes = sorted(full.get("nodes", []), key=self._node_rank, reverse=True)[:node_limit]
        node_ids = {node["id"] for node in nodes}
        edges = [
            edge
            for edge in full.get("edges", [])
            if edge.get("source") in node_ids
            and edge.get("target") in node_ids
            and float(edge.get("weight") or 0) >= min_edge_weight
        ]
        projected = self._finalize(full, nodes, edges[:2000], mode="full")
        projected["min_edge_weight"] = min_edge_weight
        return projected

    def _with_communities_and_positions(self, graph: dict[str, Any]) -> dict[str, Any]:
        """Add public community and stable initial position metadata."""

        full = self._with_communities_without_positions(graph)
        nodes = full["nodes"]
        edges = full["edges"]
        communities = {node["id"]: node.get("community", "community_0") for node in nodes}
        positions, layout_diagnostics = self._forceatlas2_positions(nodes, edges, communities)
        for node in nodes:
            node.update(positions.get(node["id"], {}))
        full["diagnostics"] = layout_diagnostics
        return full

    def _with_communities_without_positions(self, graph: dict[str, Any]) -> dict[str, Any]:
        """Add public community metadata without running the layout."""

        nodes = [dict(node) for node in graph.get("nodes", []) if isinstance(node, dict)]
        edges = [dict(edge) for edge in graph.get("edges", []) if isinstance(edge, dict)]
        communities = self._detect_communities(nodes, edges)
        degree = Counter()
        weighted = Counter()
        for edge in edges:
            weight = self._edge_rank(edge)
            degree[edge.get("source")] += 1
            degree[edge.get("target")] += 1
            weighted[edge.get("source")] += weight
            weighted[edge.get("target")] += weight
        for node in nodes:
            node_id = node["id"]
            node["community"] = communities.get(node_id, "community_0")
            node["degree"] = int(degree[node_id])
            node["size"] = self._size(node, degree[node_id], weighted[node_id])
            node["label_visible"] = self._label_visible(node, degree[node_id])
        edges = self._decorate_edges(nodes, edges)
        return {
            "generated_at": graph.get("generated_at") or datetime.now(UTC).isoformat(),
            "version": graph.get("version"),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "diagnostics": {},
        }

    def _detect_communities(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, str]:
        """Run deterministic weighted label propagation as a Louvain-style lightweight pass."""

        nodes_by_id = {node["id"]: node for node in nodes}
        labels = {node["id"]: str(node.get("group") or node.get("type") or "community") for node in nodes}
        neighbors: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if not isinstance(source, str) or not isinstance(target, str):
                continue
            weight = self._edge_rank(edge)
            source_group = nodes_by_id.get(source, {}).get("group")
            target_group = nodes_by_id.get(target, {}).get("group")
            if source_group and target_group and source_group != target_group:
                weight *= 0.25
            neighbors[source].append((target, weight))
            neighbors[target].append((source, weight))
        for _ in range(8):
            changed = False
            for node_id in sorted(labels):
                scores: Counter[str] = Counter()
                for neighbor, weight in neighbors.get(node_id, []):
                    scores[labels.get(neighbor, "unknown")] += weight
                if not scores:
                    continue
                best = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[0][0]
                if labels[node_id] != best:
                    labels[node_id] = best
                    changed = True
            if not changed:
                break
        mapping = {label: f"community_{index + 1}" for index, label in enumerate(sorted(set(labels.values())))}
        return {node_id: mapping[label] for node_id, label in labels.items()}

    def _forceatlas2_positions(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        communities: dict[str, str],
    ) -> tuple[dict[str, dict[str, float]], dict[str, Any]]:
        """Run a deterministic ForceAtlas2-style layout and return diagnostics."""

        started_at = time.perf_counter()
        positions = self._community_positions(nodes, communities)
        nodes_by_id = {node["id"]: node for node in nodes}
        degree = Counter()
        for edge in edges:
            degree[edge.get("source")] += 1
            degree[edge.get("target")] += 1
        displacements = {node["id"]: [0.0, 0.0] for node in nodes}
        node_ids = sorted(nodes_by_id)
        valid_edges = [
            edge
            for edge in edges
            if edge.get("source") in nodes_by_id and edge.get("target") in nodes_by_id
        ]

        for _ in range(FORCEATLAS2_ITERATIONS):
            for node_id in node_ids:
                displacements[node_id][0] = 0.0
                displacements[node_id][1] = 0.0

            for index, source in enumerate(node_ids):
                sx, sy = positions[source]["x"], positions[source]["y"]
                source_mass = 1.0 + math.sqrt(max(0, degree[source]))
                for target in node_ids[index + 1 :]:
                    tx, ty = positions[target]["x"], positions[target]["y"]
                    dx = sx - tx
                    dy = sy - ty
                    distance2 = max(0.08, dx * dx + dy * dy)
                    target_mass = 1.0 + math.sqrt(max(0, degree[target]))
                    force = FORCEATLAS2_SETTINGS["scalingRatio"] * source_mass * target_mass / distance2
                    distance = math.sqrt(distance2)
                    ux = dx / distance
                    uy = dy / distance
                    displacements[source][0] += ux * force
                    displacements[source][1] += uy * force
                    displacements[target][0] -= ux * force
                    displacements[target][1] -= uy * force

            for edge in valid_edges:
                source = edge["source"]
                target = edge["target"]
                sx, sy = positions[source]["x"], positions[source]["y"]
                tx, ty = positions[target]["x"], positions[target]["y"]
                dx = sx - tx
                dy = sy - ty
                distance = max(0.1, math.sqrt(dx * dx + dy * dy))
                weight = max(0.1, float(edge.get("weight") or 1.0))
                attraction = math.log1p(distance) * (weight ** FORCEATLAS2_SETTINGS["edgeWeightInfluence"])
                if FORCEATLAS2_SETTINGS["outboundAttractionDistribution"]:
                    attraction /= max(1.0, math.sqrt(degree[source] + 1))
                ux = dx / distance
                uy = dy / distance
                displacements[source][0] -= ux * attraction
                displacements[source][1] -= uy * attraction
                displacements[target][0] += ux * attraction
                displacements[target][1] += uy * attraction

            for node_id in node_ids:
                x, y = positions[node_id]["x"], positions[node_id]["y"]
                distance = max(0.1, math.sqrt(x * x + y * y))
                gravity = FORCEATLAS2_SETTINGS["gravity"] * distance
                displacements[node_id][0] -= (x / distance) * gravity
                displacements[node_id][1] -= (y / distance) * gravity
                positions[node_id]["x"] = x + displacements[node_id][0] / FORCEATLAS2_SETTINGS["slowDown"]
                positions[node_id]["y"] = y + displacements[node_id][1] / FORCEATLAS2_SETTINGS["slowDown"]

        normalized, _ = self._normalize_positions(positions)
        normalized = self._center_brain_positions(nodes, normalized)
        bounds = self._position_bounds(normalized)
        runtime_ms = round((time.perf_counter() - started_at) * 1000, 2)
        diagnostics = {
            "layout_engine": "server_forceatlas2_style",
            "forceatlas2_started": True,
            "forceatlas2_finished": True,
            "forceatlas2_iterations": FORCEATLAS2_ITERATIONS,
            "forceatlas2_runtime_ms": runtime_ms,
            "forceatlas2_settings": dict(FORCEATLAS2_SETTINGS),
            "communities": len(set(communities.values())),
            "bounds": bounds,
            "duplicate_positions": self._duplicate_positions(normalized),
            "overlapping_nodes": self._overlapping_nodes(nodes, normalized),
            "isolated_nodes": sum(1 for node in nodes if degree[node["id"]] == 0),
            "brain_centered": bool(self._brain_node_ids(nodes)),
            "brain_nodes": len(self._brain_node_ids(nodes)),
        }
        return normalized, diagnostics

    def _community_positions(self, nodes: list[dict[str, Any]], communities: dict[str, str]) -> dict[str, dict[str, float]]:
        """Set unique stable community-based initial positions."""

        by_community: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for node in nodes:
            by_community[communities.get(node["id"], "community_0")].append(node)
        community_ids = sorted(by_community)
        community_centers: dict[str, tuple[float, float]] = {}
        for index, community in enumerate(community_ids):
            anchor = self._community_anchor(by_community[community])
            if anchor is None:
                angle = (math.tau * index) / max(1, len(community_ids))
                radius = 18.0
                anchor = (math.cos(angle) * radius, math.sin(angle) * radius)
            community_centers[community] = anchor

        positions: dict[str, dict[str, float]] = {}
        for community, items in by_community.items():
            cx, cy = community_centers[community]
            ranked = sorted(items, key=self._node_rank, reverse=True)
            for index, node in enumerate(ranked):
                if self._is_brain_node(node):
                    positions[node["id"]] = {"x": 0.0, "y": 0.0}
                    continue
                if index == 0:
                    positions[node["id"]] = {"x": round(cx, 4), "y": round(cy, 4)}
                    continue
                angle = (math.tau * index) / max(1, len(ranked) - 1) + self._seeded_angle(node["id"]) * 0.08
                local_radius = 1.8 + math.sqrt(index) * 0.9
                positions[node["id"]] = {
                    "x": round(cx + math.cos(angle) * local_radius, 4),
                    "y": round(cy + math.sin(angle) * local_radius, 4),
                }
        return positions

    def _overview_nodes(self, full: dict[str, Any], *, node_limit: int) -> list[dict[str, Any]]:
        """Build high-level overview nodes and synthetic group clusters."""

        nodes = list(full.get("nodes", []))
        ranked = sorted(nodes, key=self._node_rank, reverse=True)
        keep: list[dict[str, Any]] = []
        seen: set[str] = set()
        for node in ranked:
            if node.get("type") in {"project", "brain", "market", "data_source", "bot"}:
                item = dict(node)
                item["label_visible"] = True
                keep.append(item)
                seen.add(item["id"])
            if len(keep) >= node_limit:
                return keep[:node_limit]

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for node in nodes:
            group = str(node.get("group") or "other")
            if node["id"] not in seen:
                grouped[group].append(node)

        for group in ("crypto", "stocks", "indicators", "decisions", "patterns", "learning", "infrastructure", "errors", "warnings"):
            items = grouped.get(group) or []
            if not items:
                continue
            aggregate_id = f"cluster:{group}"
            best = max(items, key=self._node_rank)
            keep.append(
                {
                    "id": aggregate_id,
                    "label": self._cluster_label(group),
                    "type": "cluster",
                    "group": group,
                    "community": best.get("community"),
                    "importance": max(float(item.get("importance") or 0) for item in items),
                    "count": sum(int(float(item.get("count") or 1)) for item in items),
                    "degree": sum(int(item.get("degree") or 0) for item in items),
                    "size": min(22.0, max(9.0, 8.0 + math.sqrt(len(items)) * 2.4)),
                    "label_visible": True,
                    "status": "AGGREGATED",
                    "health": "OK",
                    "aggregated": True,
                    "aggregated_nodes": len(items),
                    "x": best.get("x", 0.0),
                    "y": best.get("y", 0.0),
                }
            )
            if len(keep) >= node_limit:
                break

        return self._normalize_node_list_positions(keep[:node_limit])

    def _aggregate_overview_edges(
        self,
        full: dict[str, Any],
        visible_nodes: list[dict[str, Any]],
        *,
        edge_limit: int,
    ) -> list[dict[str, Any]]:
        """Aggregate raw edges into high-level overview relations."""

        visible_ids = {node["id"] for node in visible_nodes}
        raw_nodes = {node["id"]: node for node in full.get("nodes", [])}
        representative = {}
        for raw_id, node in raw_nodes.items():
            if raw_id in visible_ids:
                representative[raw_id] = raw_id
            else:
                cluster_id = f"cluster:{node.get('group') or 'other'}"
                representative[raw_id] = cluster_id if cluster_id in visible_ids else None

        aggregates: dict[tuple[str, str], dict[str, Any]] = {}
        for edge in full.get("edges", []):
            source = representative.get(edge.get("source"))
            target = representative.get(edge.get("target"))
            if not source or not target or source == target:
                continue
            key = tuple(sorted((source, target)))
            item = aggregates.setdefault(
                key,
                {
                    "id": f"aggregate:{key[0]}->{key[1]}",
                    "source": key[0],
                    "target": key[1],
                    "relation": "aggregated",
                    "weight": 0.0,
                    "event_count": 0,
                    "aggregated": True,
                    "relations": set(),
                },
            )
            item["weight"] += float(edge.get("weight") or 1)
            item["event_count"] += int(float(edge.get("event_count") or 1))
            if edge.get("relation"):
                item["relations"].add(str(edge["relation"]))

        edges = []
        for item in aggregates.values():
            item["weight"] = round(math.log1p(item["weight"]) * 2.0, 3)
            item["relations"] = sorted(item["relations"])[:5]
            edges.append(item)
        return sorted(edges, key=self._edge_rank, reverse=True)[:edge_limit]

    def _decorate_edges(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Add display-only edge metadata used by the web renderer."""

        by_id = {node["id"]: node for node in nodes}
        decorated: list[dict[str, Any]] = []
        for edge in edges:
            item = dict(edge)
            source = by_id.get(str(item.get("source")))
            target = by_id.get(str(item.get("target")))
            source_group = str(source.get("group") or source.get("community") or "") if source else ""
            target_group = str(target.get("group") or target.get("community") or "") if target else ""
            cross_cluster = bool(source_group and target_group and source_group != target_group)
            raw_weight = max(0.1, float(item.get("weight") or 1.0))
            event_count = max(1.0, float(item.get("event_count") or 1.0))
            confidence = float(item.get("confidence") or 0.0)
            visual_weight = math.log1p(raw_weight) + math.log10(event_count + 1.0) * 0.7 + confidence / 180.0
            if cross_cluster:
                visual_weight *= 0.72
            item["cross_cluster"] = cross_cluster
            item["visual_weight"] = round(max(0.2, min(5.0, visual_weight)), 3)
            item["visual_opacity"] = round(0.12 if cross_cluster else min(0.36, 0.16 + visual_weight * 0.045), 3)
            decorated.append(item)
        return decorated

    def _community_anchor(self, nodes: list[dict[str, Any]]) -> tuple[float, float] | None:
        groups = Counter(str(node.get("group") or node.get("type") or "other") for node in nodes)
        if not groups:
            return None
        group = sorted(groups.items(), key=lambda item: (-item[1], item[0]))[0][0]
        return GROUP_ANCHORS.get(group)

    def _center_brain_positions(
        self,
        nodes: list[dict[str, Any]],
        positions: dict[str, dict[str, float]],
    ) -> dict[str, dict[str, float]]:
        """Keep the public Brain node readable and move nearby nodes away from it."""

        brain_ids = self._brain_node_ids(nodes)
        if not brain_ids:
            return positions
        adjusted = {node_id: dict(point) for node_id, point in positions.items()}
        primary = brain_ids[0]
        adjusted[primary] = {"x": 0.0, "y": 0.0}
        min_distance = 3.2
        for node_id, point in list(adjusted.items()):
            if node_id in brain_ids:
                continue
            x = float(point.get("x") or 0.0)
            y = float(point.get("y") or 0.0)
            distance = math.sqrt(x * x + y * y)
            if distance >= min_distance:
                continue
            angle = self._seeded_angle(node_id)
            if distance > 0.001:
                angle = math.atan2(y, x)
            adjusted[node_id] = {
                "x": round(math.cos(angle) * min_distance, 4),
                "y": round(math.sin(angle) * min_distance, 4),
            }
        return adjusted

    def _brain_node_ids(self, nodes: list[dict[str, Any]]) -> list[str]:
        return [str(node["id"]) for node in nodes if self._is_brain_node(node)]

    def _is_brain_node(self, node: dict[str, Any]) -> bool:
        node_type = str(node.get("type") or "").lower()
        node_id = str(node.get("id") or "").lower()
        return node_type == "brain" or node_id.startswith("brain:")

    def _normalize_node_list_positions(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        positions = {node["id"]: {"x": float(node.get("x") or 0), "y": float(node.get("y") or 0)} for node in nodes}
        normalized, _ = self._normalize_positions(positions)
        for node in nodes:
            node.update(normalized.get(node["id"], {}))
        return nodes

    def _limit_edges_per_node(self, edges: list[dict[str, Any]], *, max_edges: int) -> list[dict[str, Any]]:
        """Keep only strongest edges around super-nodes."""

        result: list[dict[str, Any]] = []
        counts: Counter[str] = Counter()
        for edge in sorted(edges, key=self._edge_rank, reverse=True):
            source = str(edge.get("source"))
            target = str(edge.get("target"))
            if counts[source] >= max_edges or counts[target] >= max_edges:
                continue
            result.append(edge)
            counts[source] += 1
            counts[target] += 1
        return result

    def _finalize(
        self,
        full: dict[str, Any],
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        *,
        mode: str,
    ) -> dict[str, Any]:
        """Return one projection response."""

        edges = self._decorate_edges(nodes, edges)
        return {
            "generated_at": full.get("generated_at") or datetime.now(UTC).isoformat(),
            "version": full.get("version"),
            "mode": mode,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "diagnostics": self._projection_diagnostics(full, nodes, edges, mode),
        }

    def _projection_diagnostics(
        self,
        full: dict[str, Any],
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        mode: str,
    ) -> dict[str, Any]:
        base = dict(full.get("diagnostics") or {})
        positions = {node["id"]: {"x": float(node.get("x") or 0), "y": float(node.get("y") or 0)} for node in nodes}
        _, bounds = self._normalize_positions(positions)
        base.update(
            {
                "projection": mode,
                "nodes": len(nodes),
                "edges": len(edges),
                "bounds": bounds,
                "duplicate_positions": self._duplicate_positions(positions),
                "overlapping_nodes": self._overlapping_nodes(nodes, positions),
                "isolated_nodes": self._isolated_count(nodes, edges),
                "aggregated_edges": sum(1 for edge in edges if edge.get("aggregated")),
                "aggregated_nodes": sum(1 for node in nodes if node.get("aggregated")),
            }
        )
        return base

    def _normalize_positions(self, positions: dict[str, dict[str, float]]) -> tuple[dict[str, dict[str, float]], dict[str, float]]:
        if not positions:
            return {}, {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0}
        min_x = min(point["x"] for point in positions.values())
        max_x = max(point["x"] for point in positions.values())
        min_y = min(point["y"] for point in positions.values())
        max_y = max(point["y"] for point in positions.values())
        width = max(0.001, max_x - min_x)
        height = max(0.001, max_y - min_y)
        target = 24.0
        margin = 1.2
        normalized = {}
        for node_id, point in positions.items():
            x = ((point["x"] - min_x) / width) * (target - margin * 2) - (target / 2 - margin)
            y = ((point["y"] - min_y) / height) * (target - margin * 2) - (target / 2 - margin)
            normalized[node_id] = {"x": round(x, 4), "y": round(y, 4)}
        bounds = {
            "min_x": round(min(point["x"] for point in normalized.values()), 4),
            "max_x": round(max(point["x"] for point in normalized.values()), 4),
            "min_y": round(min(point["y"] for point in normalized.values()), 4),
            "max_y": round(max(point["y"] for point in normalized.values()), 4),
        }
        return normalized, bounds

    def _position_bounds(self, positions: dict[str, dict[str, float]]) -> dict[str, float]:
        if not positions:
            return {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0}
        return {
            "min_x": round(min(point["x"] for point in positions.values()), 4),
            "max_x": round(max(point["x"] for point in positions.values()), 4),
            "min_y": round(min(point["y"] for point in positions.values()), 4),
            "max_y": round(max(point["y"] for point in positions.values()), 4),
        }

    def _duplicate_positions(self, positions: dict[str, dict[str, float]]) -> int:
        seen = Counter((round(point["x"], 3), round(point["y"], 3)) for point in positions.values())
        return sum(count - 1 for count in seen.values() if count > 1)

    def _overlapping_nodes(self, nodes: list[dict[str, Any]], positions: dict[str, dict[str, float]]) -> int:
        count = 0
        for index, source in enumerate(nodes):
            source_pos = positions.get(source["id"])
            if not source_pos:
                continue
            for target in nodes[index + 1 :]:
                target_pos = positions.get(target["id"])
                if not target_pos:
                    continue
                dx = source_pos["x"] - target_pos["x"]
                dy = source_pos["y"] - target_pos["y"]
                if math.sqrt(dx * dx + dy * dy) < 0.75:
                    count += 1
        return count

    def _isolated_count(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> int:
        connected = {value for edge in edges for value in (edge.get("source"), edge.get("target"))}
        return sum(1 for node in nodes if node["id"] not in connected)

    def _cluster_label(self, group: str) -> str:
        return {
            "crypto": "Crypto Cluster",
            "stocks": "Stock Cluster",
            "indicators": "Indicator Cluster",
            "decisions": "Decision Cluster",
            "patterns": "Pattern Cluster",
            "learning": "Learning Cluster",
            "infrastructure": "Infrastructure",
            "errors": "Error Cluster",
            "warnings": "Warning Cluster",
        }.get(group, f"{group.title()} Cluster")

    def _seeded_angle(self, value: str) -> float:
        seed = 0
        for char in str(value):
            seed = (seed * 31 + ord(char)) % 360
        return math.radians(seed)

    def _node_rank(self, node: dict[str, Any]) -> float:
        priority = TYPE_PRIORITY.get(str(node.get("type") or ""), 5)
        confidence = float(node.get("confidence") or 0) * 0.08
        count = math.log10(float(node.get("count") or 1) + 1) * 4
        degree = float(node.get("degree") or 0) * 2
        return priority + float(node.get("importance") or 0) * 0.08 + confidence + count + degree

    def _edge_rank(self, edge: dict[str, Any]) -> float:
        return float(edge.get("weight") or 1) * math.log10(float(edge.get("event_count") or 1) + 1)

    def _size(self, node: dict[str, Any], degree: int, weighted: float) -> float:
        priority = {
            "brain": 23,
            "project": 17,
            "market": 14,
            "cluster": 13,
            "crypto": 11,
            "stock": 11,
            "learning": 10,
            "decision": 9,
            "signal": 9,
            "indicator": 8,
            "pattern": 8,
            "bot": 8,
            "data_source": 8,
            "service": 7,
        }.get(str(node.get("type") or ""), 6)
        confidence = float(node.get("confidence") or 0) / 100
        recency_bonus = 1.0 if node.get("last_updated") else 0.0
        degree_bonus = math.sqrt(max(0, degree)) * (1.45 if self._is_brain_node(node) else 1.25)
        size = priority + degree_bonus + math.log10(weighted + 1) * 1.55 + confidence * 2.4 + recency_bonus
        return round(max(6.0, min(28.0, size)), 2)

    def _label_visible(self, node: dict[str, Any], degree: int) -> bool:
        return (
            str(node.get("type")) in {"brain", "project", "market", "cluster"}
            or degree >= 10
            or float(node.get("importance") or 0) >= 98
        )

    def _group_quota(self, group: str) -> int:
        return {
            "crypto": 8,
            "stocks": 9,
            "indicators": 8,
            "decisions": 6,
            "patterns": 8,
            "infrastructure": 7,
        }.get(group, 4)
