"""Phase 3 tests for the Knowledge Graph Control Center UI."""

from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_ROOT / "web" / "static"


class KnowledgeGraphUiPhase3Test(unittest.TestCase):
    """Verify the browser shell for the public Knowledge Graph engine."""

    def test_control_center_loads_knowledge_graph_assets(self) -> None:
        html = (STATIC_DIR / "control_center.html").read_text(encoding="utf-8")

        self.assertIn("/knowledge_graph.css", html)
        self.assertIn("/vendor/graphology.umd.min.js", html)
        self.assertIn("/vendor/sigma.min.js", html)
        self.assertIn("/knowledge_graph.js", html)
        self.assertIn("/knowledge_graph_bootstrap.js", html)
        self.assertIn("Knowledge Graph", html)
        self.assertIn("knowledgeGraphSvg", html)
        self.assertIn("knowledgeGraphDetails", html)

    def test_knowledge_graph_controls_are_present(self) -> None:
        html = (STATIC_DIR / "control_center.html").read_text(encoding="utf-8")

        for expected in (
            "fitKnowledgeGraph",
            "resetKnowledgeGraph",
            "refreshKnowledgeGraph",
            "toggleKnowledgeFullscreen",
            "knowledgeOverviewMode",
            "knowledgeFullMode",
            "knowledge2DMode",
            "knowledge3DMode",
            "knowledgeMinEdgeWeight",
            "knowledgeGraphSearch",
            "knowledgeGraphTypeFilter",
            "knowledgeGraphGroupFilter",
            "knowledgeGraphNeighborsOnly",
        ):
            self.assertIn(expected, html)

    def test_javascript_uses_read_only_projection_api(self) -> None:
        script = (STATIC_DIR / "knowledge_graph.js").read_text(encoding="utf-8")

        for expected in (
            "/api/v1/graph/overview",
            "/api/v1/graph/search",
            "/api/v1/graph/node/",
            "/api/v1/graph/cluster/",
            "/api/v1/graph/full?min_edge_weight=",
        ):
            self.assertIn(expected, script)
        self.assertNotIn("/api/control/", script)

    def test_sigma_engine_and_interactions_are_present(self) -> None:
        script = (STATIC_DIR / "knowledge_graph.js").read_text(encoding="utf-8")

        for expected in (
            "window.graphology.Graph",
            "new window.Sigma",
            "replaceSvgWithContainer",
            "renderSigma",
            "enterNode",
            "leaveNode",
            "clickNode",
            "doubleClickNode",
            "highlight",
            "fitCamera",
            "minEdgeWeight",
        ):
            self.assertIn(expected, script)

    def test_optional_3d_knowledge_graph_mode_is_present(self) -> None:
        script = (STATIC_DIR / "knowledge_graph.js").read_text(encoding="utf-8")
        css = (STATIC_DIR / "knowledge_graph.css").read_text(encoding="utf-8")

        for expected in (
            "renderKnowledgeGraph3D",
            "projectLayout3D",
            "bind3DControls",
            "knowledge-graph-3d",
            "knowledge-3d-node",
        ):
            self.assertIn(expected, script + "\n" + css)

    def test_graph_initializes_after_late_script_load(self) -> None:
        script = (STATIC_DIR / "knowledge_graph.js").read_text(encoding="utf-8")

        self.assertIn('document.readyState === "loading"', script)
        self.assertIn("init();", script)
        self.assertIn("Sigma laedt zu lange", script)

    def test_graph_uses_visual_edge_and_node_metadata(self) -> None:
        script = (STATIC_DIR / "knowledge_graph.js").read_text(encoding="utf-8")

        for expected in (
            "nodeColorFromData",
            "edgeColor(edge)",
            "edgeSize(edge)",
            "baseColor",
            "baseSize",
            "visual_weight",
            "cross_cluster",
            "requestJson",
            "XMLHttpRequest",
        ):
            self.assertIn(expected, script)

    def test_old_svg_force_engine_is_no_longer_active(self) -> None:
        script = (STATIC_DIR / "knowledge_graph.js").read_text(encoding="utf-8")

        for removed in (
            "runForces",
            "runForceDirectedSimulation",
            "SVG_NS",
            "state.velocities",
        ):
            self.assertNotIn(removed, script)

    def test_legacy_fallback_files_are_kept(self) -> None:
        self.assertTrue((STATIC_DIR / "knowledge_graph_legacy.js").exists())
        self.assertTrue((STATIC_DIR / "knowledge_graph_legacy.css").exists())
        self.assertTrue((STATIC_DIR / "knowledge_graph_bootstrap.js").exists())

    def test_css_contains_dark_graph_visuals_and_canvas_container(self) -> None:
        css = (STATIC_DIR / "knowledge_graph.css").read_text(encoding="utf-8")

        for expected in (
            ".knowledge-graph-shell",
            ".knowledge-graph-canvas",
            ".knowledge-graph-canvas canvas",
            ".knowledge-panel.fullscreen",
            "@keyframes knowledgeNodeIn",
        ):
            self.assertIn(expected, css)

    def test_vendor_assets_exist(self) -> None:
        self.assertGreater((STATIC_DIR / "vendor" / "sigma.min.js").stat().st_size, 100_000)
        self.assertGreater((STATIC_DIR / "vendor" / "graphology.umd.min.js").stat().st_size, 50_000)

    def test_no_demo_or_secret_data_in_frontend_assets(self) -> None:
        combined = (
            (STATIC_DIR / "control_center.html").read_text(encoding="utf-8")
            + "\n"
            + (STATIC_DIR / "knowledge_graph.js").read_text(encoding="utf-8")
            + "\n"
            + (STATIC_DIR / "knowledge_graph.css").read_text(encoding="utf-8")
        ).lower()

        for forbidden in (
            "sample graph",
            "brain_events.jsonl",
            "raw_result",
            "calculation",
            "api_key",
            "telegram_bot_token",
            "secret-token",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
