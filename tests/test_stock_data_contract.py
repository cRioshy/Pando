"""Tests for the reference-only stock data contract."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from stock_data_contract import StockDataPolicy, evaluate_stock_data


NOW = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)


def candidate(count: int = 200) -> dict:
    start = NOW - timedelta(days=count)
    candles = []
    for index in range(count):
        close = 100.0 + index * 0.1
        candles.append({
            "timestamp": (start + timedelta(days=index)).isoformat(),
            "open": close - 0.2, "high": close + 0.5, "low": close - 0.5,
            "close": close, "volume": 1_000_000 + index,
        })
    return {
        "market_type": "stock", "symbol": "AAPL", "timeframe": "1d",
        "source_kind": "PUBLIC_LIVE", "direction": "LONG", "candles": candles,
        "current_price": 120.0, "price_source": "yahoo_finance_chart",
        "price_timestamp": (NOW - timedelta(minutes=2)).isoformat(),
        "risk": {"action": "LONG", "entry_price": 120.0, "stop_loss": 117.0, "take_profit": [123.0, 126.0]},
    }


def policy() -> StockDataPolicy:
    return StockDataPolicy(
        minimum_candles=200,
        full_warmup_candles=200,
        maximum_candle_age_seconds=4 * 24 * 60 * 60,
        maximum_quote_age_seconds=900,
    )


class StockDataContractTest(unittest.TestCase):
    def test_complete_live_input_is_ready_but_never_released(self) -> None:
        result = evaluate_stock_data(candidate(), policy=policy(), evaluated_at=NOW)
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["reason_codes"], ["SD_READY"])
        self.assertEqual(result["feature_quality"]["status"], "PASS")
        self.assertTrue(result["usable_for_decision_gate"])
        self.assertFalse(result["ready_for_telegram"])
        self.assertFalse(result["order_execution_allowed"])

    def test_current_single_snapshot_fallback_is_blocked(self) -> None:
        result = evaluate_stock_data(candidate(count=1), policy=policy(), evaluated_at=NOW)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("SD_CANDLES_INVALID", result["reason_codes"])

    def test_placeholder_source_missing_quote_and_risk_are_blocked(self) -> None:
        item = candidate()
        item.update(source_kind="PLACEHOLDER", current_price=None,
                    price_source="live_unavailable_placeholder_hidden", price_timestamp=None, risk=None)
        result = evaluate_stock_data(item, policy=policy(), evaluated_at=NOW)
        expected = {"SD_SOURCE_NOT_LIVE", "SD_PRICE_INVALID", "SD_PRICE_SOURCE_NOT_ALLOWED",
                    "SD_PRICE_TIMESTAMP_INVALID", "SD_RISK_MISSING"}
        self.assertTrue(expected.issubset(result["reason_codes"]))

    def test_stale_quote_and_directionally_invalid_risk_are_blocked(self) -> None:
        item = candidate()
        item["price_timestamp"] = (NOW - timedelta(hours=1)).isoformat()
        item["risk"] = {"action": "SHORT", "entry_price": 100.0,
                        "stop_loss": 125.0, "take_profit": [115.0]}
        result = evaluate_stock_data(item, policy=policy(), evaluated_at=NOW)
        for reason in ("SD_PRICE_STALE", "SD_RISK_DIRECTION_CONFLICT",
                       "SD_RISK_ENTRY_PRICE_MISMATCH", "SD_STOP_LOSS_INVALID",
                       "SD_TAKE_PROFIT_INVALID"):
            self.assertIn(reason, result["reason_codes"])

    def test_stale_candle_history_is_blocked(self) -> None:
        item = candidate()
        for candle in item["candles"]:
            timestamp = datetime.fromisoformat(candle["timestamp"])
            candle["timestamp"] = (timestamp - timedelta(days=30)).isoformat()
        result = evaluate_stock_data(item, policy=policy(), evaluated_at=NOW)
        self.assertIn("SD_CANDLES_STALE", result["reason_codes"])

    def test_policy_has_no_hidden_minimum_or_quote_age(self) -> None:
        with self.assertRaises(TypeError):
            StockDataPolicy()  # type: ignore[call-arg]


if __name__ == "__main__":
    unittest.main()
