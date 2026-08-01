"""Tests for resilient public crypto market data fetching."""

from __future__ import annotations

import json
import unittest

from adapters.crypto_market_data_service import CryptoMarketDataError, CryptoMarketDataService


class _Response:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class CryptoMarketDataServiceTest(unittest.TestCase):
    def test_optional_futures_failures_do_not_discard_candles(self) -> None:
        def opener(request, timeout):
            del timeout
            if "/api/v3/klines" in request.full_url:
                return _Response([[1, "10", "12", "9", "11", "100"]])
            raise OSError("futures endpoint unavailable")

        service = CryptoMarketDataService(opener=opener, retries=0)
        snapshot = service.fetch("BTC/USDT", "15m", 240)

        self.assertEqual(snapshot.symbol, "BTCUSDT")
        self.assertEqual(snapshot.candles[0]["close"], 11.0)
        self.assertIsNone(snapshot.open_interest)
        self.assertIsNone(snapshot.funding_rate)
        self.assertEqual(snapshot.diagnostics["candle_source"], "binance")
        self.assertEqual(snapshot.diagnostics["open_interest_status"], "unavailable")

    def test_bitget_is_used_after_binance_retries_fail(self) -> None:
        sleeps = []

        def opener(request, timeout):
            del timeout
            if "api.binance.com" in request.full_url:
                raise OSError("binance unavailable")
            if "/spot/market/candles" in request.full_url:
                return _Response(
                    {
                        "code": "00000",
                        "data": [
                            ["2", "11", "13", "10", "12", "110"],
                            ["1", "10", "12", "9", "11", "100"],
                        ],
                    }
                )
            raise OSError("optional futures endpoint unavailable")

        service = CryptoMarketDataService(opener=opener, sleeper=sleeps.append, retries=1)
        snapshot = service.fetch("ETHUSDT", "15m", 240)

        self.assertEqual(snapshot.diagnostics["candle_source"], "bitget")
        self.assertEqual([row["close"] for row in snapshot.candles], [11.0, 12.0])
        self.assertEqual(sleeps, [0.25])

    def test_required_candle_failure_contains_provider_diagnostics(self) -> None:
        service = CryptoMarketDataService(
            opener=lambda request, timeout: (_ for _ in ()).throw(OSError("offline")),
            sleeper=lambda seconds: None,
            retries=1,
        )

        with self.assertRaises(CryptoMarketDataError) as caught:
            service.fetch("XRPUSDT", "15m", 240)

        diagnostics = caught.exception.diagnostics
        self.assertEqual(len(diagnostics["attempts"]), 4)
        self.assertEqual(
            {attempt["source"] for attempt in diagnostics["attempts"]},
            {"binance", "bitget"},
        )


if __name__ == "__main__":
    unittest.main()
