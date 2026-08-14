"""Tests for the public-data stock shadow candidate."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from stock_shadow_candidate import StockShadowPolicy, build_stock_shadow_candidate


def candles(step: float, count: int = 220) -> list[dict]:
    start = datetime.now(UTC) - timedelta(days=count - 1)
    rows = []
    for index in range(count):
        close = 100.0 + step * index
        rows.append(
            {
                "timestamp": (start + timedelta(days=index)).isoformat(),
                "open": close - 0.2,
                "high": close + 0.5,
                "low": close - 0.5,
                "close": close,
                "volume": 1_000_000 + index,
            }
        )
    return rows


class StockShadowCandidateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = StockShadowPolicy(minimum_candles=200, full_warmup_candles=200)

    def build(self, rows: list[dict], price: float) -> dict:
        return build_stock_shadow_candidate(
            symbol="AAPL",
            candles=rows,
            current_price=price,
            price_source="yahoo_finance_chart",
            price_timestamp=datetime.now(UTC).isoformat(),
            candle_source="yahoo_finance_chart_query1",
            policy=self.policy,
        )

    def test_uptrend_creates_compact_long_observer(self) -> None:
        candidate = self.build(candles(0.2), 144.0)
        self.assertEqual(candidate["status"], "CALCULATED")
        self.assertEqual(candidate["direction"], "LONG")
        self.assertGreaterEqual(candidate["probability"], 60)
        self.assertEqual(candidate["probability_kind"], "UNVALIDATED_HEURISTIC_SCORE")
        self.assertNotIn("candles", candidate)
        self.assertIsNone(candidate["risk"])
        self.assertFalse(candidate["ready_for_telegram"])
        self.assertFalse(candidate["order_execution_allowed"])

    def test_downtrend_creates_short_observer(self) -> None:
        candidate = self.build(candles(-0.2), 56.0)
        self.assertEqual(candidate["direction"], "SHORT")
        self.assertGreaterEqual(candidate["probability"], 60)

    def test_flat_series_is_neutral_hold(self) -> None:
        candidate = self.build(candles(0.0), 100.0)
        self.assertEqual(candidate["direction"], "HOLD")
        self.assertEqual(candidate["bullish_score"], 50.0)
        self.assertEqual(candidate["probability"], 50.0)

    def test_invalid_series_fails_closed(self) -> None:
        candidate = self.build(candles(0.1, 30), 103.0)
        self.assertEqual(candidate["status"], "BLOCKED")
        self.assertEqual(candidate["reason_codes"], ["SS_CANDLES_INVALID"])
        self.assertIsNone(candidate["direction"])

    def test_policy_requires_sma200_history(self) -> None:
        with self.assertRaises(ValueError):
            StockShadowPolicy(minimum_candles=199, full_warmup_candles=200)


if __name__ == "__main__":
    unittest.main()
