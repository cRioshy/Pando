"""Tests for observer-only stock shadow risk levels."""

from __future__ import annotations

import unittest

from stock_shadow_risk import StockShadowRiskPolicy, build_stock_shadow_risk


POLICY = StockShadowRiskPolicy(
    atr_multiplier=1.0,
    minimum_distance_percent=0.5,
    take_profit_multiples=(1.0, 2.0, 3.0),
    price_decimals=4,
)


def candidate(direction: str = "LONG", *, price: float = 100.0, atr: float = 2.0) -> dict:
    return {
        "schema_name": "pandorickki.stock-shadow-candidate",
        "schema_version": 1,
        "status": "CALCULATED",
        "symbol": "AAPL",
        "direction": direction,
        "source_kind": "PUBLIC_LIVE",
        "current_price": price,
        "indicators": {"atr14": atr},
    }


class StockShadowRiskTest(unittest.TestCase):
    def test_long_plan_uses_public_entry_atr_and_three_targets(self) -> None:
        plan = build_stock_shadow_risk(candidate(), policy=POLICY)
        self.assertEqual(plan["status"], "CALCULATED")
        self.assertEqual(plan["risk"]["entry_price"], 100.0)
        self.assertEqual(plan["risk"]["stop_loss"], 98.0)
        self.assertEqual(plan["risk"]["take_profit"], [102.0, 104.0, 106.0])
        self.assertEqual(plan["reward_risk_multiples"], [1.0, 2.0, 3.0])
        self.assertFalse(plan["affects_active_decision"])
        self.assertFalse(plan["ready_for_telegram"])
        self.assertFalse(plan["order_execution_allowed"])

    def test_short_plan_reverses_levels(self) -> None:
        plan = build_stock_shadow_risk(candidate("SHORT"), policy=POLICY)
        self.assertEqual(plan["risk"]["stop_loss"], 102.0)
        self.assertEqual(plan["risk"]["take_profit"], [98.0, 96.0, 94.0])

    def test_minimum_half_percent_distance_applies(self) -> None:
        plan = build_stock_shadow_risk(candidate(atr=0.1), policy=POLICY)
        self.assertEqual(plan["risk_distance"], 0.5)
        self.assertEqual(plan["risk"]["stop_loss"], 99.5)

    def test_hold_and_uncalculated_shadow_fail_closed(self) -> None:
        hold = build_stock_shadow_risk(candidate("HOLD"), policy=POLICY)
        self.assertEqual(hold["reason_codes"], ["SSR_DIRECTION_NOT_ELIGIBLE"])
        blocked_candidate = candidate()
        blocked_candidate["status"] = "BLOCKED"
        blocked = build_stock_shadow_risk(blocked_candidate, policy=POLICY)
        self.assertEqual(blocked["reason_codes"], ["SSR_SHADOW_NOT_CALCULATED"])
        self.assertIsNone(blocked["risk"])

    def test_invalid_atr_and_impossible_long_stop_fail_closed(self) -> None:
        invalid_atr = build_stock_shadow_risk(candidate(atr=0.0), policy=POLICY)
        self.assertEqual(invalid_atr["reason_codes"], ["SSR_ATR_INVALID"])
        impossible = build_stock_shadow_risk(candidate(price=1.0, atr=2.0), policy=POLICY)
        self.assertEqual(impossible["reason_codes"], ["SSR_STOP_INVALID"])

    def test_policy_is_explicit_and_validated(self) -> None:
        with self.assertRaises(ValueError):
            StockShadowRiskPolicy(0.0, 0.5, (1.0,), 4)
        with self.assertRaises(ValueError):
            StockShadowRiskPolicy(1.0, 0.5, (2.0, 1.0), 4)
        with self.assertRaises(ValueError):
            StockShadowRiskPolicy(1.0, 0.5, (1.0,), 9)


if __name__ == "__main__":
    unittest.main()
