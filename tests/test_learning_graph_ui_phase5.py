"""Phase 5 UI tests for the Pandorick Learning Graph dashboard."""

from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_ROOT / "web" / "static"


class LearningGraphUiPhase5Test(unittest.TestCase):
    """Verify that the ControlCenter exposes the Learning Graph UI safely."""

    def test_control_center_contains_learning_graph_section(self) -> None:
        html = (STATIC_DIR / "control_center.html").read_text(encoding="utf-8")

        self.assertIn("Learning Graph", html)
        self.assertIn("graphNodeCount", html)
        self.assertIn("learningGraphNodes", html)
        self.assertIn("learningGraphEdges", html)
        self.assertIn("learningGraphDetails", html)
        self.assertIn("refreshLearningGraph", html)

    def test_javascript_uses_public_learning_graph_api(self) -> None:
        script = (STATIC_DIR / "control_center.js").read_text(encoding="utf-8")

        self.assertIn("/api/v1/learning-graph", script)
        self.assertIn("/api/v1/learning-graph/node/", script)
        self.assertIn("renderLearningGraph", script)
        self.assertIn("loadLearningGraphNode", script)

    def test_javascript_does_not_fetch_internal_graph_files(self) -> None:
        script = (STATIC_DIR / "control_center.js").read_text(encoding="utf-8").lower()

        self.assertNotIn("brain_events.jsonl", script)
        self.assertNotIn("brain.jsonl", script)
        self.assertNotIn("raw_result", script)
        self.assertNotIn("telegram_bot_token", script)


if __name__ == "__main__":
    unittest.main()
