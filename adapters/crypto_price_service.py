"""Live crypto spot price providers for dashboard display."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


UrlOpen = Callable[..., Any]


@dataclass(frozen=True)
class CryptoPriceQuote:
    """Validated spot price with provider metadata."""

    symbol: str
    price: float
    source: str


class CryptoPriceService:
    """Fetch spot prices from Binance with Bitget as a public fallback."""

    def __init__(self, *, timeout_seconds: float = 5.0, opener: UrlOpen | None = None) -> None:
        self.timeout_seconds = timeout_seconds
        self._opener = opener or urllib.request.urlopen
        self._last_attempts: list[dict[str, str]] = []

    def fetch_price(self, symbol: str) -> CryptoPriceQuote | None:
        """Return the first valid quote from Binance or Bitget."""

        normalized = self._normalize_symbol(symbol)
        self._last_attempts = []
        for source, provider in (("binance", self._fetch_binance), ("bitget", self._fetch_bitget)):
            try:
                quote = provider(normalized)
            except Exception as exc:
                self._record_attempt(source, "error", exc)
                continue
            if quote is None:
                self._record_attempt(source, "unavailable", "No valid price in response.")
                continue
            self._record_attempt(source, "ok", None)
            return quote
        return None

    def diagnostics(self) -> dict[str, Any]:
        """Return safe provider diagnostics for the latest fetch."""

        return {
            "attempts": list(self._last_attempts),
            "last_error": self._last_error_summary(),
        }

    def _fetch_binance(self, symbol: str) -> CryptoPriceQuote | None:
        """Fetch a public Binance spot ticker price."""

        query = urllib.parse.urlencode({"symbol": symbol})
        url = f"https://api.binance.com/api/v3/ticker/price?{query}"
        data = self._read_json(url)
        return self._quote(symbol, data.get("price"), "binance")

    def _fetch_bitget(self, symbol: str) -> CryptoPriceQuote | None:
        """Fetch a public Bitget spot ticker price."""

        query = urllib.parse.urlencode({"symbol": symbol})
        url = f"https://api.bitget.com/api/v2/spot/market/tickers?{query}"
        data = self._read_json(url)
        rows = data.get("data", [])
        if isinstance(rows, dict):
            rows = [rows]
        if not rows:
            return None
        row = rows[0]
        if not isinstance(row, dict):
            return None
        price = (
            row.get("lastPr")
            or row.get("last")
            or row.get("close")
            or row.get("price")
        )
        return self._quote(symbol, price, "bitget")

    def _read_json(self, url: str) -> dict[str, Any]:
        """Read one JSON response using a browser-like user agent."""

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "PandorickKi/1.0 local price monitor"},
            method="GET",
        )
        with self._opener(request, timeout=self.timeout_seconds) as response:
            payload = response.read().decode("utf-8")
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("Price response is not a JSON object.")
        return data

    def _quote(self, symbol: str, raw_price: Any, source: str) -> CryptoPriceQuote | None:
        """Validate and normalize a raw provider price."""

        price = float(raw_price)
        if price <= 0:
            return None
        return CryptoPriceQuote(symbol=symbol, price=price, source=source)

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize supported dashboard symbols."""

        return str(symbol or "").upper().replace("-", "").replace("/", "")

    def _record_attempt(self, source: str, status: str, error: Any) -> None:
        """Store one safe provider attempt."""

        item = {"source": source, "status": status}
        if error is not None:
            item["error"] = str(error)
        self._last_attempts.append(item)

    def _last_error_summary(self) -> str | None:
        """Return a compact latest error message when all providers failed."""

        for attempt in reversed(self._last_attempts):
            if attempt.get("status") != "ok" and attempt.get("error"):
                return f"{attempt.get('source')}: {attempt.get('error')}"
        return None
