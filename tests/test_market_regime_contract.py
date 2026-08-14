"""Tests for the observer-only market regime contract."""

from __future__ import annotations

import json
import math
import unittest

from market_regime_contract import (
    CLASSIFIER_VERSION,
    MarketRegimePolicy,
    build_market_regime_snapshot,
    classify_phase,
    classify_trend,
    classify_volatility,
    configuration_fingerprint,
)


def row(
    close: float,
    *,
    sma20: float | None = None,
    sma50: float | None = None,
    sma200: float | None = None,
    ema20: float | None = None,
    ema50: float | None = None,
    atr: float = 1.0,
    adx: float = 30.0,
    macd: float = 1.0,
    roc: float = 1.0,
    momentum: float = 1.0,
    percent_return: float = 0.5,
    volume_ratio: float = 1.0,
) -> dict:
    return {
        "price": {
            "open": close - 0.2,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "momentum": momentum,
            "percent_return": percent_return,
        },
        "trend": {
            "sma": {"20": sma20, "50": sma50, "200": sma200},
            "ema": {"20": ema20, "50": ema50},
        },
        "volatility": {"atr": atr},
        "volume": {"volume_ratio": volume_ratio},
        "technical_indicators": {
            "adx": adx,
            "macd_histogram": macd,
            "roc": roc,
            "kama": close - (0.5 if roc >= 0 else -0.5),
        },
    }


def trend_rows(direction: int, *, adx: float = 35.0) -> list[dict]:
    result = []
    for index in range(220):
        close = 100.0 + direction * index * 0.4
        result.append(
            row(
                close,
                sma20=close - direction * 2.0,
                sma50=close - direction * 5.0,
                sma200=close - direction * 10.0,
                ema20=close - direction * 1.5,
                ema50=close - direction * 4.0,
                adx=adx,
                macd=float(direction),
                roc=2.0 * direction,
                momentum=4.0 * direction,
                percent_return=0.4 * direction,
            )
        )
    return result


def candles(count: int = 220, *, direction: int = 1) -> list[dict]:
    result = []
    for index in range(count):
        close = 100.0 + direction * index * 0.25 + math.sin(index / 7.0) * 0.2
        result.append(
            {
                "timestamp": 1_700_000_000 + index * 900,
                "open": close - 0.15 * direction,
                "high": close + 0.8,
                "low": close - 0.8,
                "close": close,
                "volume": 1_000 + index,
            }
        )
    return result


class MarketRegimeContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = MarketRegimePolicy()

    def test_trend_classes_cover_strong_up_up_down_and_strong_down(self) -> None:
        self.assertEqual(classify_trend(trend_rows(1), quality_status="OK", policy=self.policy)["value"], "STRONG_UP")
        self.assertEqual(classify_trend(trend_rows(1, adx=15.0), quality_status="OK", policy=self.policy)["value"], "UP")
        self.assertEqual(classify_trend(trend_rows(-1, adx=15.0), quality_status="OK", policy=self.policy)["value"], "DOWN")
        self.assertEqual(classify_trend(trend_rows(-1), quality_status="OK", policy=self.policy)["value"], "STRONG_DOWN")

    def test_sideways_is_independent_and_unknown_is_fail_closed(self) -> None:
        rows = []
        for index in range(220):
            close = 100.0 + (0.3 if index % 2 else -0.3)
            rows.append(
                row(
                    close,
                    sma20=100.0,
                    sma50=100.0,
                    sma200=100.0,
                    ema20=100.0,
                    ema50=100.0,
                    adx=8.0,
                    macd=0.0,
                    roc=0.0,
                    momentum=0.0,
                    percent_return=0.0,
                )
            )
        self.assertEqual(classify_trend(rows, quality_status="OK", policy=self.policy)["value"], "SIDEWAYS")
        self.assertEqual(classify_trend(rows[:5], quality_status="OK", policy=self.policy)["value"], "UNKNOWN")
        self.assertEqual(classify_trend(rows, quality_status="REJECTED", policy=self.policy)["value"], "UNKNOWN")

    def test_degraded_quality_caps_confidence_and_forbids_strong_class(self) -> None:
        result = classify_trend(trend_rows(1), quality_status="DEGRADED", policy=self.policy)
        self.assertEqual(result["value"], "UP")
        self.assertLessEqual(result["confidence"], self.policy.degraded_confidence_cap)

    def test_volatility_classes_use_backward_normalized_percentiles(self) -> None:
        baseline = [row(100.0, atr=1.0 + index / 100.0) for index in range(60)]
        cases = ((0.5, "LOW"), (1.3, "MEDIUM"), (1.55, "HIGH"), (3.0, "EXTREME"))
        for current, expected in cases:
            with self.subTest(expected=expected):
                result = classify_volatility(
                    [*baseline, row(100.0, atr=current)],
                    quality_status="OK",
                    policy=self.policy,
                )
                self.assertEqual(result["value"], expected)
                self.assertGreaterEqual(result["score"], 0.0)
                self.assertLessEqual(result["score"], 1.0)
        self.assertEqual(
            classify_volatility(baseline[:20], quality_status="OK", policy=self.policy)["value"],
            "UNKNOWN",
        )

    def test_phase_classes_cover_stable_weakening_reversal_breakout_unknown(self) -> None:
        stable = trend_rows(1)
        self.assertEqual(
            classify_phase(stable, trend_direction="UP", quality_status="OK", policy=self.policy)["value"],
            "STABLE",
        )

        weakening = trend_rows(1)
        weakening[-2]["price"]["momentum"] = 8.0
        weakening[-1]["price"]["momentum"] = 2.0
        weakening[-2]["technical_indicators"]["macd_histogram"] = 2.0
        weakening[-1]["technical_indicators"]["macd_histogram"] = 0.5
        weakening[-2]["technical_indicators"]["adx"] = 35.0
        weakening[-1]["technical_indicators"]["adx"] = 25.0
        self.assertEqual(
            classify_phase(weakening, trend_direction="UP", quality_status="OK", policy=self.policy)["value"],
            "WEAKENING",
        )

        reversal = trend_rows(1)
        for item in reversal[-3:]:
            item["price"]["momentum"] = -2.0
            item["price"]["percent_return"] = -1.0
            item["technical_indicators"]["roc"] = -2.0
        reversal[-2]["technical_indicators"]["macd_histogram"] = 0.5
        reversal[-1]["technical_indicators"]["macd_histogram"] = -0.5
        self.assertEqual(
            classify_phase(reversal, trend_direction="UP", quality_status="OK", policy=self.policy)["value"],
            "REVERSAL",
        )

        breakout = []
        for index in range(220):
            close = 100.0 + (0.15 if index % 2 else -0.15)
            breakout.append(row(close, sma20=100.0, sma50=100.0, sma200=100.0, ema20=100.0, ema50=100.0, adx=12.0))
        breakout[-1] = row(103.0, sma20=100.0, sma50=100.0, sma200=100.0, ema20=100.0, ema50=100.0, atr=1.0, adx=25.0, volume_ratio=1.5)
        self.assertEqual(
            classify_phase(breakout, trend_direction="UP", quality_status="OK", policy=self.policy)["value"],
            "BREAKOUT",
        )
        self.assertEqual(
            classify_phase(stable, trend_direction="UP", quality_status="REJECTED", policy=self.policy)["value"],
            "UNKNOWN",
        )

    def test_snapshot_identity_is_restart_stable_and_source_event_is_not_primary(self) -> None:
        kwargs = {
            "symbol": "BTCUSDT",
            "asset_type": "crypto",
            "timeframe": "15m",
            "candles": candles(),
            "policy": self.policy,
            "created_at": "2026-08-12T20:00:00+00:00",
        }
        first = build_market_regime_snapshot(source_event_id="event-before-restart", **kwargs)
        second = build_market_regime_snapshot(source_event_id="event-after-restart", **kwargs)
        self.assertEqual(first["feature_snapshot_id"], second["feature_snapshot_id"])
        self.assertEqual(first["regime_id"], second["regime_id"])
        self.assertNotEqual(first["source_event_id"], second["source_event_id"])
        self.assertEqual(first["classifier_version"], CLASSIFIER_VERSION)

    def test_config_fingerprint_changes_with_relevant_policy(self) -> None:
        changed = MarketRegimePolicy(trend_score_threshold=0.35)
        self.assertNotEqual(configuration_fingerprint(self.policy), configuration_fingerprint(changed))

    def test_quality_ok_degraded_and_rejected_are_explicit(self) -> None:
        valid = candles()
        ok = build_market_regime_snapshot(
            symbol="AAPL", asset_type="stock", timeframe="1d", candles=valid, source_event_id="event-1"
        )
        duplicated = [*valid, dict(valid[-1])]
        degraded = build_market_regime_snapshot(
            symbol="AAPL", asset_type="stock", timeframe="1d", candles=duplicated, source_event_id="event-2"
        )
        rejected = build_market_regime_snapshot(
            symbol="AAPL", asset_type="stock", timeframe="1d", candles=valid[:20], source_event_id="event-3"
        )
        self.assertEqual(ok["data_quality_status"], "OK")
        self.assertEqual(degraded["data_quality_status"], "DEGRADED")
        self.assertEqual(rejected["data_quality_status"], "REJECTED")
        self.assertEqual(rejected["trend_direction"], "UNKNOWN")
        self.assertEqual(rejected["volatility_regime"], "UNKNOWN")
        self.assertEqual(rejected["trend_phase"], "UNKNOWN")

    def test_non_finite_null_and_negative_prices_fail_closed(self) -> None:
        for invalid in (float("nan"), float("inf"), None, -1.0):
            broken = candles()
            broken[-1]["close"] = invalid
            result = build_market_regime_snapshot(
                symbol="BTCUSDT",
                asset_type="crypto",
                timeframe="15m",
                candles=broken,
                source_event_id="invalid",
            )
            self.assertEqual(result["data_quality_status"], "REJECTED")
            self.assertEqual(result["trend_direction"], "UNKNOWN")

    def test_public_snapshot_is_compact_neutral_and_finite(self) -> None:
        result = build_market_regime_snapshot(
            symbol="BTCUSDT",
            asset_type="crypto",
            timeframe="15m",
            candles=candles(),
            source_event_id="source-1",
        )
        encoded = json.dumps(result, allow_nan=False)
        self.assertNotIn("candles", encoded)
        self.assertNotIn("raw_result", encoded)
        self.assertNotIn("live_features", encoded)
        self.assertFalse(result["affects_active_decision"])
        self.assertFalse(result["ready_for_telegram"])
        self.assertFalse(result["order_execution_allowed"])
        self.assertEqual(result["timeframes_used"], ["15m"])
        self.assertIn("1h", result["missing_timeframes"])

        stock_result = build_market_regime_snapshot(
            symbol="AAPL",
            asset_type="stock",
            timeframe="1d",
            candles=candles(),
            source_event_id="source-stock",
        )
        self.assertEqual(stock_result["timeframes_used"], ["1d"])
        self.assertEqual(stock_result["missing_timeframes"], ["1m", "5m", "15m", "1h", "4h"])


if __name__ == "__main__":
    unittest.main()
