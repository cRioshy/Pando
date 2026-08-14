"""Tests for the read-only daily stock candle provider."""

from __future__ import annotations

import json
import unittest

from adapters.stock_candle_service import StockCandleService


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def chart_payload() -> dict:
    return {
        "chart": {
            "result": [{
                "timestamp": [1000, 2000, 3000],
                "indicators": {
                    "quote": [{
                        "open": [10.0, 11.0, 12.0], "high": [11.0, 12.0, 13.0],
                        "low": [9.0, 10.0, 11.0], "close": [10.5, 11.5, 12.5],
                        "volume": [100, 200, 300],
                    }],
                    "adjclose": [{"adjclose": [10.4, 11.4, 12.4]}],
                },
            }],
            "error": None,
        }
    }


class StockCandleServiceTest(unittest.TestCase):
    def test_daily_rows_are_normalized_and_limited(self) -> None:
        calls: list[str] = []

        def opener(request: object, *, timeout: float) -> FakeResponse:
            calls.append(request.full_url)  # type: ignore[attr-defined]
            return FakeResponse(chart_payload())

        snapshot = StockCandleService(opener=opener).fetch_daily_candles("aapl", limit=2)
        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual(snapshot.symbol, "AAPL")
        self.assertEqual(snapshot.timeframe, "1d")
        self.assertEqual([row["close"] for row in snapshot.candles], [11.5, 12.5])
        self.assertIn("range=2y", calls[0])
        self.assertIn("interval=1d", calls[0])

    def test_query2_is_used_after_query1_failure(self) -> None:
        calls: list[str] = []

        def opener(request: object, *, timeout: float) -> FakeResponse:
            calls.append(request.full_url)  # type: ignore[attr-defined]
            if "query1" in request.full_url:  # type: ignore[attr-defined]
                raise OSError("query1 unavailable")
            return FakeResponse(chart_payload())

        service = StockCandleService(opener=opener)
        snapshot = service.fetch_daily_candles("MSFT")
        self.assertIsNotNone(snapshot)
        self.assertEqual(len(calls), 2)
        self.assertIn("query2.finance.yahoo.com", calls[1])
        self.assertEqual([item["status"] for item in service.diagnostics()["attempts"]], ["error", "ok"])

    def test_cache_avoids_repeated_provider_requests(self) -> None:
        calls = 0

        def opener(request: object, *, timeout: float) -> FakeResponse:
            nonlocal calls
            calls += 1
            return FakeResponse(chart_payload())

        service = StockCandleService(opener=opener, cache_ttl_seconds=900)
        first = service.fetch_daily_candles("NVDA")
        second = service.fetch_daily_candles("NVDA")
        self.assertIs(first, second)
        self.assertEqual(calls, 1)
        self.assertEqual(service.diagnostics()["attempts"][0]["status"], "cache")

    def test_private_symbol_is_not_requested(self) -> None:
        def opener(request: object, *, timeout: float) -> FakeResponse:
            raise AssertionError("unsupported ticker must not be requested")

        service = StockCandleService(opener=opener)
        self.assertIsNone(service.fetch_daily_candles("SPCX"))
        self.assertEqual(service.diagnostics()["attempts"][0]["status"], "unsupported")

    def test_both_provider_failures_return_none_with_diagnostics(self) -> None:
        def opener(request: object, *, timeout: float) -> FakeResponse:
            raise OSError("network down")

        service = StockCandleService(opener=opener)
        self.assertIsNone(service.fetch_daily_candles("TSLA"))
        self.assertEqual(len(service.diagnostics()["attempts"]), 2)
        self.assertIn("network down", service.diagnostics()["last_error"])


if __name__ == "__main__":
    unittest.main()
