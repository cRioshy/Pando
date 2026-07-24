"""Tests for public crypto spot price fallback providers."""

from __future__ import annotations

import unittest

from adapters.crypto_price_service import CryptoPriceService


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


class CryptoPriceServiceTest(unittest.TestCase):
    def test_binance_price_is_used_first_for_supported_symbols(self) -> None:
        calls: list[str] = []

        def opener(request: object, *, timeout: float) -> FakeResponse:
            calls.append(request.full_url)  # type: ignore[attr-defined]
            return FakeResponse('{"symbol":"BTCUSDT","price":"118000.50"}')

        service = CryptoPriceService(opener=opener)
        quote = service.fetch_price("BTCUSDT")

        self.assertIsNotNone(quote)
        assert quote is not None
        self.assertEqual(quote.symbol, "BTCUSDT")
        self.assertEqual(quote.price, 118000.50)
        self.assertEqual(quote.source, "binance")
        self.assertEqual(len(calls), 1)
        self.assertIn("api.binance.com", calls[0])

    def test_bitget_is_used_when_binance_fails(self) -> None:
        calls: list[str] = []

        def opener(request: object, *, timeout: float) -> FakeResponse:
            url = request.full_url  # type: ignore[attr-defined]
            calls.append(url)
            if "api.binance.com" in url:
                raise OSError("blocked")
            return FakeResponse('{"code":"00000","data":[{"symbol":"ETHUSDT","lastPr":"3650.25"}]}')

        service = CryptoPriceService(opener=opener)
        quote = service.fetch_price("ETHUSDT")

        self.assertIsNotNone(quote)
        assert quote is not None
        self.assertEqual(quote.symbol, "ETHUSDT")
        self.assertEqual(quote.price, 3650.25)
        self.assertEqual(quote.source, "bitget")
        self.assertIn("api.binance.com", calls[0])
        self.assertIn("api.bitget.com", calls[1])
        diagnostics = service.diagnostics()
        self.assertEqual(diagnostics["attempts"][0]["source"], "binance")
        self.assertEqual(diagnostics["attempts"][0]["status"], "error")
        self.assertEqual(diagnostics["attempts"][1]["source"], "bitget")
        self.assertEqual(diagnostics["attempts"][1]["status"], "ok")

    def test_returns_none_when_all_sources_fail(self) -> None:
        def opener(request: object, *, timeout: float) -> FakeResponse:
            raise OSError("network down")

        service = CryptoPriceService(opener=opener)

        self.assertIsNone(service.fetch_price("XRPUSDT"))
        diagnostics = service.diagnostics()
        self.assertEqual(len(diagnostics["attempts"]), 2)
        self.assertIn("network down", diagnostics["last_error"])


if __name__ == "__main__":
    unittest.main()
