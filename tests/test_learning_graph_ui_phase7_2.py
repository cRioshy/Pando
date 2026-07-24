"""Phase 7.2 tests for the interactive Learning Graph network view."""

from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_ROOT / "web" / "static"


class LearningGraphUiPhase72Test(unittest.TestCase):
    """Verify the network view shell without touching trading logic."""

    def test_list_view_is_still_present(self) -> None:
        html = (STATIC_DIR / "control_center.html").read_text(encoding="utf-8")

        self.assertIn("learningGraphListView", html)
        self.assertIn("learningGraphNodes", html)
        self.assertIn("learningGraphEdges", html)
        self.assertIn("learningGraphDetails", html)

    def test_network_view_shell_is_loaded(self) -> None:
        html = (STATIC_DIR / "control_center.html").read_text(encoding="utf-8")

        self.assertIn("data-graph-view=\"list\"", html)
        self.assertIn("data-graph-view=\"graph\"", html)
        self.assertIn("learningGraphGraphView", html)
        self.assertIn("learningGraphSvg", html)
        self.assertIn("fitLearningGraph", html)
        self.assertIn("resetLearningGraph", html)
        self.assertIn("learningGraphLegend", html)

    def test_javascript_renders_real_nodes_and_edges(self) -> None:
        script = (STATIC_DIR / "control_center.js").read_text(encoding="utf-8")

        self.assertIn("renderLearningGraphNetwork", script)
        self.assertIn("visibleGraphData", script)
        self.assertIn("graph.edges", script)
        self.assertIn("graph.nodes", script)
        self.assertIn("source", script)
        self.assertIn("target", script)

    def test_javascript_supports_interaction(self) -> None:
        script = (STATIC_DIR / "control_center.js").read_text(encoding="utf-8")

        self.assertIn("setLearningGraphView", script)
        self.assertIn("selectLearningGraphNode", script)
        self.assertIn("enableGraphPanZoom", script)
        self.assertIn("selectedNeighborIds", script)
        self.assertIn("renderLearningGraphDetails", script)

    def test_graph_limits_and_deduplication_are_present(self) -> None:
        script = (STATIC_DIR / "control_center.js").read_text(encoding="utf-8")

        self.assertIn("GRAPH_NODE_LIMIT = 300", script)
        self.assertIn("GRAPH_EDGE_LIMIT = 800", script)
        self.assertIn("dedupeById", script)
        self.assertIn("Showing the most relevant", script)

    def test_network_view_has_no_demo_or_secret_data(self) -> None:
        html = (STATIC_DIR / "control_center.html").read_text(encoding="utf-8").lower()
        script = (STATIC_DIR / "control_center.js").read_text(encoding="utf-8").lower()
        combined = html + "\n" + script

        for forbidden in (
            "demo",
            "sample graph",
            "brain_events.jsonl",
            "raw_result",
            "reasoning",
            "calculation",
            "telegram_bot_token",
            "api_key",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
