"""Explicit learning/outcome metric contract tests."""

from __future__ import annotations

import unittest

from learning_metrics_contract import (
    LEARNING_METRICS_SCHEMA_NAME,
    LEARNING_METRICS_SCHEMA_VERSION,
    build_learning_metrics,
)


class LearningMetricsContractTest(unittest.TestCase):
    def test_rates_publish_their_numerators_and_denominators(self) -> None:
        metrics = build_learning_metrics(
            decisions_total=10,
            outcome_eligible_decisions=6,
            matched_outcomes=3,
            wins=1,
            losses=1,
            breakeven=1,
            unknown=0,
            learning_update_events=12,
            matching_method="decision_id",
        )

        self.assertEqual(metrics["schema_name"], LEARNING_METRICS_SCHEMA_NAME)
        self.assertEqual(metrics["schema_version"], LEARNING_METRICS_SCHEMA_VERSION)
        self.assertEqual(metrics["outcomes"]["closed"], 3)
        self.assertEqual(metrics["outcomes"]["classified_for_hit_rate"], 2)
        self.assertEqual(metrics["rates"]["hit_rate_percent"], 50.0)
        self.assertEqual(metrics["rates"]["hit_rate_numerator"], 1)
        self.assertEqual(metrics["rates"]["hit_rate_denominator"], 2)
        self.assertEqual(metrics["rates"]["outcome_coverage_percent"], 50.0)
        self.assertEqual(metrics["rates"]["outcome_coverage_numerator"], 3)
        self.assertEqual(metrics["rates"]["outcome_coverage_denominator"], 6)
        self.assertEqual(metrics["learning"]["update_events"], 12)
        self.assertIsNone(metrics["learning"]["successful_model_updates"])
        self.assertFalse(metrics["ml_training"]["active"])
        self.assertEqual(metrics["ml_training"]["model_updates"], 0)

    def test_incompatible_counter_scopes_do_not_invent_coverage(self) -> None:
        metrics = build_learning_metrics(
            decisions_total=4,
            outcome_eligible_decisions=2,
            matched_outcomes=3,
            wins=2,
            losses=1,
        )

        self.assertFalse(metrics["rates"]["outcome_coverage_scope_consistent"])
        self.assertIsNone(metrics["rates"]["outcome_coverage_percent"])


if __name__ == "__main__":
    unittest.main()
