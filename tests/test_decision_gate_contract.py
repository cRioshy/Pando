"""Tests for the observer-only Decision Gate contract."""

from __future__ import annotations

import unittest

from decision_gate_contract import (
    DECISION_GATE_SCHEMA,
    DECISION_GATE_VERSION,
    DecisionGatePolicy,
    evaluate_decision_gate,
    project_feature_quality,
)


def _quality(*, status: str = "PASS", order: str = "VERIFIED", warmup: str = "READY") -> dict:
    return {
        "schema_name": "pandorickki.feature-data-quality",
        "schema_version": 1,
        "status": status,
        "input_rows": 240,
        "accepted_rows": 240,
        "output_rows": 240,
        "dropped_rows": 0,
        "duplicate_rows": 0,
        "timestamped_rows": 240,
        "violations": {},
        "order": {"status": order, "reason": "timestamps_sorted_ascending"},
        "warmup": {"status": warmup, "available_candles": 240},
        "warnings": [],
    }


def _candidate() -> dict:
    return {
        "market_type": "crypto",
        "symbol": "BTCUSDT",
        "direction": "LONG",
        "probability": 74.0,
        "confidence": 74.0,
        "price": 64_260.0,
        "facts": {"trend": "bullish"},
        "risk": {
            "action": "LONG",
            "stop_loss": 63_000.0,
            "take_profit": [66_000.0],
        },
        "features": {"metadata": {"data_quality": _quality()}},
        "source_event_id": "analysis-1",
    }


class DecisionGateContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = DecisionGatePolicy(
            minimum_probability=60.0,
            minimum_confidence=60.0,
        )

    def test_qualified_candidate_stays_observer_only(self) -> None:
        result = evaluate_decision_gate(_candidate(), policy=self.policy)

        self.assertEqual(result["schema_name"], DECISION_GATE_SCHEMA)
        self.assertEqual(result["schema_version"], DECISION_GATE_VERSION)
        self.assertEqual(result["gate_status"], "QUALIFIED")
        self.assertTrue(result["qualified"])
        self.assertFalse(result["ready_for_telegram"])
        self.assertEqual(result["release_status"], "OBSERVER_ONLY")
        self.assertEqual(result["reason_codes"], ["DG_QUALIFIED"])

    def test_missing_quality_is_fail_closed(self) -> None:
        candidate = _candidate()
        candidate.pop("features")

        result = evaluate_decision_gate(candidate, policy=self.policy)

        self.assertEqual(result["gate_status"], "BLOCKED")
        self.assertIn("DG_QUALITY_MISSING", result["reason_codes"])

    def test_unverified_warming_stock_snapshot_is_blocked(self) -> None:
        candidate = _candidate()
        candidate["market_type"] = "stock"
        candidate["symbol"] = "AAPL"
        candidate["features"]["metadata"]["data_quality"] = _quality(
            status="WARN", order="UNVERIFIED", warmup="WARMING"
        )

        result = evaluate_decision_gate(candidate, policy=self.policy)

        self.assertEqual(result["gate_status"], "BLOCKED")
        self.assertIn("DG_QUALITY_STATUS_NOT_ALLOWED", result["reason_codes"])
        self.assertIn("DG_ORDER_NOT_VERIFIED", result["reason_codes"])
        self.assertIn("DG_WARMUP_NOT_READY", result["reason_codes"])

    def test_hold_or_wait_never_qualifies(self) -> None:
        for direction in ("HOLD", "WAIT", None):
            with self.subTest(direction=direction):
                candidate = _candidate()
                candidate["direction"] = direction
                result = evaluate_decision_gate(candidate, policy=self.policy)
                self.assertIn("DG_DIRECTION_NOT_ELIGIBLE", result["reason_codes"])
                self.assertFalse(result["qualified"])

    def test_conflicting_confidence_and_risk_action_are_blocked(self) -> None:
        candidate = _candidate()
        candidate["confidence"] = 68.0
        candidate["risk"]["action"] = "SHORT"

        result = evaluate_decision_gate(candidate, policy=self.policy)

        self.assertIn("DG_CONFIDENCE_CONFLICT", result["reason_codes"])
        self.assertIn("DG_RISK_DIRECTION_CONFLICT", result["reason_codes"])

    def test_directional_risk_plan_is_required(self) -> None:
        candidate = _candidate()
        candidate["risk"]["stop_loss"] = 65_000.0
        candidate["risk"]["take_profit"] = [63_000.0]

        result = evaluate_decision_gate(candidate, policy=self.policy)

        self.assertIn("DG_STOP_LOSS_INVALID", result["reason_codes"])
        self.assertIn("DG_TAKE_PROFIT_INVALID", result["reason_codes"])

    def test_explicit_zero_current_price_or_stop_is_not_hidden_by_fallback(self) -> None:
        candidate = _candidate()
        candidate["current_price"] = 0
        candidate["risk"]["stop_loss"] = 0
        candidate["risk"]["stop"] = 63_000.0

        result = evaluate_decision_gate(candidate, policy=self.policy)

        self.assertIn("DG_PRICE_INVALID", result["reason_codes"])
        self.assertIn("DG_STOP_LOSS_INVALID", result["reason_codes"])

    def test_feature_error_blocks_even_with_valid_report(self) -> None:
        candidate = _candidate()
        candidate["feature_error"] = "provider failed"

        result = evaluate_decision_gate(candidate, policy=self.policy)

        self.assertIn("DG_FEATURE_ERROR", result["reason_codes"])

    def test_missing_facts_are_blocked(self) -> None:
        candidate = _candidate()
        candidate["facts"] = {}

        result = evaluate_decision_gate(candidate, policy=self.policy)

        self.assertIn("DG_FACTS_MISSING", result["reason_codes"])

    def test_quality_projection_is_compact_and_accepts_preprojected_input(self) -> None:
        projection = project_feature_quality(_candidate())
        self.assertEqual(projection["status"], "PASS")
        self.assertNotIn("violations", projection)
        self.assertNotIn("warnings", projection)

        candidate = _candidate()
        candidate.pop("features")
        candidate["feature_quality"] = projection
        result = evaluate_decision_gate(candidate, policy=self.policy)
        self.assertTrue(result["qualified"])


if __name__ == "__main__":
    unittest.main()
