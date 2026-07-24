"""Phase 7.3 tests for polished Learning Graph interactions."""

from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_ROOT / "web" / "static"


class LearningGraphUiPhase73Test(unittest.TestCase):
    """Verify graph polish, search and interaction hooks."""

    def test_search_controls_are_present(self) -> None:
        html = (STATIC_DIR / "control_center.html").read_text(encoding="utf-8")

        self.assertIn("learningGraphSearch", html)
        self.assertIn("searchLearningGraph", html)
        self.assertIn("learningGraphSearchStatus", html)

    def test_polished_layout_functions_are_present(self) -> None:
        script = (STATIC_DIR / "control_center.js").read_text(encoding="utf-8")

        self.assertIn("clusterKey", script)
        self.assertIn("clusterCenters", script)
        self.assertIn("runForceSimulation", script)
        self.assertIn("initializeGraphPositions", script)
        self.assertIn("boundGraphPositions", script)
        self.assertIn("connectedNodeIds", script)
        self.assertIn("relaxGraphCollisions", script)
        self.assertIn("displayNodeLabel", script)
        self.assertIn("state.layoutPositions", script)

    def test_force_layout_separates_clusters_and_keeps_limits(self) -> None:
        script = (STATIC_DIR / "control_center.js").read_text(encoding="utf-8")

        self.assertIn("GRAPH_WIDTH = 1600", script)
        self.assertIn("GRAPH_HEIGHT = 980", script)
        self.assertIn("GRAPH_MIN_ZOOM = 0.25", script)
        self.assertIn("GRAPH_MAX_ZOOM = 4.0", script)
        self.assertIn("unconnected", script)
        self.assertIn("connectedIds.has(node.id) ? clusterKey(node) : \"unconnected\"", script)
        self.assertIn("nodeRadius(aNode) + nodeRadius(bNode)", script)

    def test_focus_search_and_dragging_are_present(self) -> None:
        script = (STATIC_DIR / "control_center.js").read_text(encoding="utf-8")

        self.assertIn("focusLearningGraphNode", script)
        self.assertIn("searchLearningGraph", script)
        self.assertIn("startNodeDrag", script)
        self.assertIn("updateNodeDrag", script)
        self.assertIn("stopNodeDrag", script)
        self.assertIn("dblclick", script)
        self.assertIn("mouseenter", script)
        self.assertIn("mouseleave", script)
        self.assertIn("hoveredNodeId", script)

    def test_resize_and_fit_behaviour_are_present(self) -> None:
        script = (STATIC_DIR / "control_center.js").read_text(encoding="utf-8")

        self.assertIn("enableGraphResize", script)
        self.assertIn("fitLearningGraphView", script)
        self.assertIn("window.addEventListener(\"resize\"", script)
        self.assertIn("Math.min(GRAPH_WIDTH / width, GRAPH_HEIGHT / height)", script)
        self.assertIn("graphPointFromEvent(event)", script)

    def test_visual_polish_css_is_present(self) -> None:
        css = (STATIC_DIR / "control_center.css").read_text(encoding="utf-8")

        self.assertIn(".graph-tools", css)
        self.assertIn(".graph-node:hover", css)
        self.assertIn("@keyframes graphNodeIn", css)
        self.assertIn(".graph-edge.neighbor", css)
        self.assertIn("rgba(154, 168, 178, 0.18)", css)
        self.assertIn(".graph-label-bg", css)
        self.assertIn(".graph-cluster-label", css)

    def test_labels_are_reduced_and_tooltips_keep_full_names(self) -> None:
        script = (STATIC_DIR / "control_center.js").read_text(encoding="utf-8")

        self.assertIn("shouldShowNodeLabel", script)
        self.assertIn("type === \"MARKET\" || type === \"SYSTEM\"", script)
        self.assertIn("state.svgZoom >= 1.35", script)
        self.assertIn("svgElement(\"title\"", script)
        self.assertIn("replace(/^Connected To Source$/i", script)

    def test_no_secret_or_demo_data_was_added(self) -> None:
        combined = (
            (STATIC_DIR / "control_center.html").read_text(encoding="utf-8")
            + "\n"
            + (STATIC_DIR / "control_center.js").read_text(encoding="utf-8")
        ).lower()

        for forbidden in (
            "demo",
            "sample graph",
            "brain_events.jsonl",
            "raw_result",
            "reasoning",
            "calculation",
            "api_key",
            "telegram_bot_token",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
