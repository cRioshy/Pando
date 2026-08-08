import math
import unittest

from feature_data_quality_contract import (
    FEATURE_DATA_QUALITY_SCHEMA,
    FEATURE_DATA_QUALITY_VERSION,
    FeatureDataQualityError,
    FeatureDataQualityPolicy,
    prepare_feature_candles,
)


def candle(timestamp=None, *, close=100.0, **overrides):
    row = {
        "open": close - 0.5,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": 1000.0,
    }
    if timestamp is not None:
        row["timestamp"] = timestamp
    row.update(overrides)
    return row


class FeatureDataQualityContractTest(unittest.TestCase):
    def test_sorts_timestamped_rows_and_keeps_last_duplicate(self) -> None:
        result = prepare_feature_candles(
            [
                candle(3, close=103.0),
                candle(1, close=101.0),
                candle(2, close=102.0),
                candle(2, close=102.5),
            ],
            policy=FeatureDataQualityPolicy(full_warmup_candles=3),
        )

        self.assertEqual([row["close"] for row in result.candles], [101.0, 102.5, 103.0])
        self.assertEqual(result.report["schema_name"], FEATURE_DATA_QUALITY_SCHEMA)
        self.assertEqual(result.report["schema_version"], FEATURE_DATA_QUALITY_VERSION)
        self.assertEqual(result.report["duplicate_rows"], 1)
        self.assertEqual(result.report["status"], "DEGRADED")
        self.assertTrue(result.report["order"]["reordered"])
        self.assertEqual(result.report["order"]["status"], "VERIFIED")
        self.assertEqual(result.report["warmup"]["status"], "READY")

    def test_drops_non_finite_and_inconsistent_ohlcv_rows(self) -> None:
        result = prepare_feature_candles(
            [
                candle(1),
                candle(2, close=math.nan),
                candle(3, close=103.0, high=102.0),
                candle(4, close=104.0, volume=-1.0),
            ]
        )

        self.assertEqual(len(result.candles), 1)
        self.assertEqual(result.report["status"], "DEGRADED")
        self.assertEqual(result.report["dropped_rows"], 3)
        self.assertEqual(result.report["violations"]["non_finite_ohlcv"], 1)
        self.assertEqual(result.report["violations"]["inconsistent_ohlc"], 1)
        self.assertEqual(result.report["violations"]["negative_volume"], 1)

    def test_minimum_valid_candles_is_enforced(self) -> None:
        with self.assertRaisesRegex(FeatureDataQualityError, "minimum 3"):
            prepare_feature_candles(
                [candle(1), candle(2)],
                policy=FeatureDataQualityPolicy(minimum_candles=3),
            )

    def test_missing_timestamps_preserve_provider_order_and_are_explicit(self) -> None:
        result = prepare_feature_candles([candle(close=102.0), candle(close=101.0)])

        self.assertEqual([row["close"] for row in result.candles], [102.0, 101.0])
        self.assertEqual(result.report["order"]["status"], "UNVERIFIED")
        self.assertEqual(result.report["order"]["reason"], "timestamps_missing")
        self.assertEqual(result.report["duplicate_rows"], 0)

    def test_mixed_timestamp_coverage_is_not_silently_sorted(self) -> None:
        result = prepare_feature_candles([candle(2, close=102.0), candle(close=101.0)])

        self.assertEqual([row["close"] for row in result.candles], [102.0, 101.0])
        self.assertEqual(result.report["order"]["status"], "UNVERIFIED")
        self.assertEqual(result.report["order"]["reason"], "timestamps_partial")
        self.assertEqual(result.report["timestamped_rows"], 1)

    def test_timestamp_requirement_can_be_enforced_by_future_gates(self) -> None:
        with self.assertRaisesRegex(FeatureDataQualityError, "requires timestamps"):
            prepare_feature_candles(
                [candle()],
                policy=FeatureDataQualityPolicy(require_timestamps=True),
            )


if __name__ == "__main__":
    unittest.main()
