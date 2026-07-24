"""Tests for the free Yahoo Finance stock price provider."""

from __future__ import annotations

import unittest

from adapters.stock_price_service import StockPriceService


class FakeResponse:
    """Tiny context manager for urllib-style tests."""

    def __init__(self, payload: str) -> None:
        self.payload = payload.encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class StockPriceServiceTest(unittest.TestCase):
    def test_yahoo_regular_market_price_is_used(self) -> None:
        calls: list[str] = []

        def opener(request: object, *, timeout: float) -> FakeResponse:
            calls.append(request.full_url)  # type: ignore[attr-defined]
            return FakeResponse(
                '{"chart":{"result":[{"meta":{"symbol":"AAPL","regularMarketPrice":214.25},'
                '"timestamp":[1784780400,1784780460],'
                '"indicators":{"quote":[{"close":[214.25,215.75]}]}}]}}'
            )

        service = StockPriceService(opener=opener)
        quote = service.fetch_price("AAPL")

        self.assertIsNotNone(quote)
        assert quote is not None
        self.assertEqual(quote.symbol, "AAPL")
        self.assertEqual(quote.price, 215.75)
        self.assertEqual(quote.source, "yahoo_finance_chart")
        self.assertEqual(quote.timestamp, 1784780460)
        self.assertEqual(len(calls), 1)
        self.assertIn("query1.finance.yahoo.com", calls[0])
        self.assertIn("includePrePost=true", calls[0])
        self.assertEqual(service.diagnostics()["attempts"][0]["status"], "ok")

    def test_latest_close_is_used_when_meta_price_is_missing(self) -> None:
        def opener(request: object, *, timeout: float) -> FakeResponse:
            return FakeResponse(
                '{"chart":{"result":[{"meta":{"symbol":"MSFT"},'
                '"timestamp":[1784780400,1784780460,1784780520],'
                '"indicators":{"quote":[{"close":[null,444.1,445.2]}]}}]}}'
            )

        service = StockPriceService(opener=opener)
        quote = service.fetch_price("MSFT")

        self.assertIsNotNone(quote)
        assert quote is not None
        self.assertEqual(quote.price, 445.2)
        self.assertEqual(quote.timestamp, 1784780520)

    def test_private_spacex_alias_is_not_requested(self) -> None:
        def opener(request: object, *, timeout: float) -> FakeResponse:
            raise AssertionError("SPCX should not call Yahoo.")

        service = StockPriceService(opener=opener)

        self.assertIsNone(service.fetch_price("SPCX"))
        self.assertEqual(service.diagnostics()["attempts"][0]["status"], "unsupported")

    def test_returns_none_when_yahoo_fails(self) -> None:
        def opener(request: object, *, timeout: float) -> FakeResponse:
            raise OSError("network down")

        service = StockPriceService(opener=opener)

        self.assertIsNone(service.fetch_price("NVDA"))
        diagnostics = service.diagnostics()
        self.assertEqual(diagnostics["attempts"][0]["status"], "error")
        self.assertIn("network down", diagnostics["last_error"])


if __name__ == "__main__":
    unittest.main()
