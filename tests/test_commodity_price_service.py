"""Tests for free Yahoo Finance commodity price provider."""

from __future__ import annotations

import unittest

from adapters.commodity_price_service import CommodityPriceService


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


class CommodityPriceServiceTest(unittest.TestCase):
    def test_latest_yahoo_chart_price_is_used(self) -> None:
        calls: list[str] = []

        def opener(request: object, *, timeout: float) -> FakeResponse:
            calls.append(request.full_url)  # type: ignore[attr-defined]
            return FakeResponse(
                '{"chart":{"result":[{"timestamp":[1784780400,1784780460],'
                '"indicators":{"quote":[{"close":[2420.5,2421.75]}]}}]}}'
            )

        service = CommodityPriceService(opener=opener)
        quote = service.fetch_price("GC=F")

        self.assertIsNotNone(quote)
        assert quote is not None
        self.assertEqual(quote.symbol, "GC=F")
        self.assertEqual(quote.label, "Gold")
        self.assertEqual(quote.price, 2421.75)
        self.assertEqual(quote.previous_price, 2420.5)
        self.assertEqual(quote.timestamp, 1784780460)
        self.assertEqual(quote.source, "yahoo_finance_chart_query1")
        self.assertIn("includePrePost=true", calls[0])
        self.assertEqual(service.diagnostics()["attempts"][0]["status"], "ok")

    def test_query2_is_used_when_query1_fails(self) -> None:
        calls: list[str] = []

        def opener(request: object, *, timeout: float) -> FakeResponse:
            calls.append(request.full_url)  # type: ignore[attr-defined]
            if "query1.finance.yahoo.com" in request.full_url:  # type: ignore[attr-defined]
                raise OSError("query1 down")
            return FakeResponse(
                '{"chart":{"result":[{"timestamp":[1784780400,1784780460],'
                '"indicators":{"quote":[{"close":[89.5,90.25]}]}}]}}'
            )

        service = CommodityPriceService(opener=opener)
        quote = service.fetch_price("CL=F")

        self.assertIsNotNone(quote)
        assert quote is not None
        self.assertEqual(quote.price, 90.25)
        self.assertEqual(quote.source, "yahoo_finance_chart_query2")
        self.assertEqual(service.diagnostics()["attempts"][0]["status"], "error")
        self.assertEqual(service.diagnostics()["attempts"][1]["status"], "ok")
        self.assertEqual(len(calls), 2)

    def test_returns_none_when_provider_fails(self) -> None:
        def opener(request: object, *, timeout: float) -> FakeResponse:
            raise OSError("network down")

        service = CommodityPriceService(opener=opener)

        self.assertIsNone(service.fetch_price("CL=F"))
        diagnostics = service.diagnostics()
        self.assertEqual(diagnostics["attempts"][0]["status"], "error")
        self.assertEqual(diagnostics["attempts"][1]["status"], "error")
        self.assertIn("network down", diagnostics["last_error"])


if __name__ == "__main__":
    unittest.main()
