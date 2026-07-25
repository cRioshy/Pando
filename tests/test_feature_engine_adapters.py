import unittest
from pathlib import Path

from adapters.crypto_adapter import CryptoAdapter
from adapters.stock_adapter import StockAdapter
from event_bus import EventBus


class FeatureEngineAdapterTest(unittest.TestCase):
    def test_crypto_adapter_builds_additive_features(self) -> None:
        adapter = CryptoAdapter(EventBus(), Path("."), symbols=["BTCUSDT"])
        payload = adapter._build_feature_payload(
            market_data={
                "symbol": "BTCUSDT",
                "timeframe": "15m",
                "candles": [
                    {"open": 100 + i, "high": 101 + i, "low": 99 + i, "close": 100.5 + i, "volume": 1000 + i}
                    for i in range(30)
                ],
                "open_interest": 123.0,
                "funding_rate": 0.0002,
            },
            sensor_values={},
            symbol="BTCUSDT",
            optional_context={"open_interest": 123.0, "funding_rate": 0.0002},
        )

        self.assertIsNone(payload["feature_error"])
        features = payload["features"]
        self.assertEqual(features["metadata"]["market_type"], "crypto")
        self.assertEqual(features["live_features"]["optional_context"]["funding_rate"], 0.0002)
        self.assertIn("technical_indicators", features["live_features"])
        self.assertEqual(features["training_only"], {})

    def test_stock_adapter_builds_features_from_latest_facts(self) -> None:
        adapter = StockAdapter(EventBus(), Path("."))
        payload = adapter._build_feature_payload(
            raw={"symbol": "AAPL"},
            facts={
                "open_price": 100.0,
                "high_price": 104.0,
                "low_price": 99.0,
                "close_price": 103.0,
                "volume": 5000,
                "earnings_flag": False,
            },
            symbol="AAPL",
            optional_context={"earnings_flag": False, "price_source": "test"},
        )

        self.assertIsNone(payload["feature_error"])
        features = payload["features"]
        self.assertEqual(features["metadata"]["market_type"], "stock")
        self.assertEqual(features["live_features"]["price"]["close"], 103.0)
        self.assertFalse(features["live_features"]["optional_context"]["earnings_flag"])
        self.assertEqual(features["training_only"], {})


if __name__ == "__main__":
    unittest.main()
