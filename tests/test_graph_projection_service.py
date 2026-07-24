"""Tests for readable Knowledge Graph projections."""

from __future__ import annotations

import unittest

from learning_graph.graph_projection_service import GraphProjectionService


def sample_graph(node_count: int = 90) -> dict:
    """Build a dense public graph with one super-node."""

    groups = ("crypto", "stocks", "brain", "patterns", "decisions", "infrastructure")
    nodes = [
        {
            "id": "project:pandorick",
            "label": "Pandorick",
            "type": "project",
            "group": "infrastructure",
            "importance": 100,
            "count": 1,
        },
        {
            "id": "brain:core",
            "label": "Brain",
            "type": "brain",
            "group": "brain",
            "importance": 98,
            "count": 400,
        },
    ]
    for index in range(node_count):
        group = groups[index % len(groups)]
        node_type = {
            "crypto": "crypto",
            "stocks": "stock",
            "brain": "learning",
            "patterns": "pattern",
            "decisions": "decision",
            "infrastructure": "service",
        }[group]
        nodes.append(
            {
                "id": f"{group}:node:{index}",
                "label": f"{group}-{index}",
                "type": node_type,
                "group": group,
                "importance": 40 + (index % 50),
                "count": index + 1,
            }
        )
    edges = []
    for index, node in enumerate(nodes[2:], start=1):
        edges.append(
            {
                "id": f"brain-edge-{index}",
                "source": "brain:core",
                "target": node["id"],
                "relation": "learned_from",
                "weight": 1 + (index % 7),
                "event_count": index + 2,
            }
        )
        if index > 1:
            edges.append(
                {
                    "id": f"group-edge-{index}",
                    "source": nodes[index]["id"],
                    "target": node["id"],
                    "relation": "belongs_to",
                    "weight": 2,
                    "event_count": 3,
                }
            )
    return {"generated_at": "2026-07-21T10:00:00+00:00", "version": 7, "nodes": nodes, "edges": edges}


class GraphProjectionServiceTest(unittest.TestCase):
    """Verify projection limits and metadata."""

    def setUp(self) -> None:
        self.service = GraphProjectionService()
        self.graph = sample_graph()

    def test_overview_limits_nodes_and_adds_layout_metadata(self) -> None:
        projection = self.service.overview_projection(self.graph, node_limit=50)

        self.assertLessEqual(projection["node_count"], 50)
        self.assertEqual(projection["mode"], "overview")
        for node in projection["nodes"]:
            self.assertIn("community", node)
            self.assertIn("degree", node)
            self.assertIn("size", node)
            self.assertIn("label_visible", node)
            self.assertIsInstance(node["x"], float)
            self.assertIsInstance(node["y"], float)

    def test_overview_reduces_super_node_edges(self) -> None:
        projection = self.service.overview_projection(self.graph, node_limit=50)
        incident_to_brain = [
            edge
            for edge in projection["edges"]
            if edge["source"] == "brain:core" or edge["target"] == "brain:core"
        ]

        self.assertLessEqual(len(incident_to_brain), 8)

    def test_cluster_projection_returns_only_requested_group_or_community(self) -> None:
        projection = self.service.cluster_projection(self.graph, "crypto")

        self.assertGreater(projection["node_count"], 0)
        self.assertEqual(projection["mode"], "cluster")
        self.assertTrue(all(node["group"] == "crypto" or node["community"] == "crypto" for node in projection["nodes"]))

    def test_neighborhood_projection_returns_focus_and_neighbors(self) -> None:
        projection = self.service.neighborhood_projection(self.graph, "brain:core", max_neighbors=12)

        self.assertIsNotNone(projection)
        assert projection is not None
        self.assertEqual(projection["focus_node_id"], "brain:core")
        self.assertEqual(projection["node"]["id"], "brain:core")
        self.assertLessEqual(len(projection["neighbors"]), 12)
        self.assertTrue(all(edge["source"] == "brain:core" or edge["target"] == "brain:core" for edge in projection["edges"]))

    def test_full_projection_filters_edges_by_weight(self) -> None:
        projection = self.service.full_projection(self.graph, node_limit=500, min_edge_weight=6)

        self.assertEqual(projection["mode"], "full")
        self.assertEqual(projection["min_edge_weight"], 6)
        self.assertTrue(all(float(edge.get("weight") or 0) >= 6 for edge in projection["edges"]))

    def test_projection_removes_edges_with_missing_nodes(self) -> None:
        graph = sample_graph(10)
        graph["edges"].append(
            {
                "id": "broken",
                "source": "missing",
                "target": "brain:core",
                "relation": "broken",
                "weight": 99,
            }
        )
        projection = self.service.overview_projection(graph, node_limit=20)
        node_ids = {node["id"] for node in projection["nodes"]}

        self.assertTrue(all(edge["source"] in node_ids and edge["target"] in node_ids for edge in projection["edges"]))

    def test_overview_keeps_brain_central_and_visually_dominant(self) -> None:
        projection = self.service.overview_projection(self.graph, node_limit=50)
        nodes = {node["id"]: node for node in projection["nodes"]}
        brain = nodes["brain:core"]
        largest_size = max(float(node["size"]) for node in projection["nodes"])

        self.assertAlmostEqual(float(brain["x"]), 0.0, delta=0.001)
        self.assertAlmostEqual(float(brain["y"]), 0.0, delta=0.001)
        self.assertEqual(float(brain["size"]), largest_size)
        self.assertTrue(brain["label_visible"])
        self.assertTrue(projection["diagnostics"]["brain_centered"])

    def test_overview_edges_include_visual_metadata(self) -> None:
        projection = self.service.overview_projection(self.graph, node_limit=50)

        self.assertGreater(projection["edge_count"], 0)
        for edge in projection["edges"]:
            self.assertIn("visual_weight", edge)
            self.assertIn("visual_opacity", edge)
            self.assertIn("cross_cluster", edge)
            self.assertGreaterEqual(float(edge["visual_opacity"]), 0.06)
            self.assertLessEqual(float(edge["visual_opacity"]), 0.42)


if __name__ == "__main__":
    unittest.main()
