import unittest

from features.feature_engine import FeatureEngine, FeatureEngineError


def candles(count: int = 60) -> list[dict[str, float]]:
    rows = []
    for index in range(count):
        close = 100.0 + index * 0.5
        rows.append(
            {
                "open": close - 0.2,
                "high": close + 0.8,
                "low": close - 0.7,
                "close": close,
                "volume": 1000.0 + index * 10.0,
            }
        )
    return rows


class FeatureEngineTest(unittest.TestCase):
    def test_compute_live_features_without_targets(self) -> None:
        result = FeatureEngine().compute(
            candles(),
            symbol="BTCUSDT",
            market_type="crypto",
            optional_context={"funding_rate": 0.0001, "secret": None},
        ).to_dict()

        self.assertEqual(result["metadata"]["symbol"], "BTCUSDT")
        self.assertTrue(result["metadata"]["live_safe"])
        self.assertEqual(result["training_only"], {})
        live = result["live_features"]
        self.assertIn("price", live)
        self.assertIn("trend", live)
        self.assertIn("volatility", live)
        self.assertIn("volume", live)
        self.assertIn("candles", live)
        self.assertIn("technical_indicators", live)
        self.assertIn("rsi", live["technical_indicators"])
        self.assertIn("macd", live["technical_indicators"])
        self.assertIn("adx", live["technical_indicators"])
        self.assertEqual(live["optional_context"]["funding_rate"], 0.0001)
        self.assertNotIn("target_direction", live)

    def test_training_targets_are_separated(self) -> None:
        result = FeatureEngine(target_horizon=1).compute(
            candles(20),
            include_targets=True,
        ).to_dict()

        self.assertFalse(result["metadata"]["live_safe"])
        self.assertIn("target_direction", result["training_only"])
        self.assertIn("target_future_return", result["training_only"])
        self.assertNotIn("target_direction", result["live_features"])

    def test_invalid_candles_raise_clear_error(self) -> None:
        with self.assertRaises(FeatureEngineError):
            FeatureEngine().compute([{"close": None}])


if __name__ == "__main__":
    unittest.main()
