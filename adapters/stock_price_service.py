"""Free public stock price provider for dashboard display."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


UrlOpen = Callable[..., Any]


@dataclass(frozen=True)
class StockPriceQuote:
    """Validated stock price with provider metadata."""

    symbol: str
    price: float
    source: str
    timestamp: int | None = None


class StockPriceService:
    """Fetch public stock prices from Yahoo Finance without API keys."""

    unsupported_symbols = {"SPCX", "SPACEX"}

    def __init__(self, *, timeout_seconds: float = 5.0, opener: UrlOpen | None = None) -> None:
        self.timeout_seconds = timeout_seconds
        self._opener = opener or urllib.request.urlopen
        self._last_attempts: list[dict[str, str]] = []

    def fetch_price(self, symbol: str) -> StockPriceQuote | None:
        """Return the current Yahoo Finance price for a listed stock symbol."""

        normalized = self._normalize_symbol(symbol)
        self._last_attempts = []
        if not normalized or normalized in self.unsupported_symbols:
            self._record_attempt("yahoo_finance_chart", "unsupported", f"Unsupported symbol: {symbol}")
            return None

        encoded = urllib.parse.quote(normalized, safe="")
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}"
            "?range=1d&interval=1m&includePrePost=true"
        )
        try:
            data = self._read_json(url)
            result = data.get("chart", {}).get("result", [])
            if not result:
                self._record_attempt("yahoo_finance_chart", "unavailable", "No chart result in response.")
                return None
            latest = self._latest_chart_close(result[0])
            if latest is not None:
                price, timestamp = latest
                quote = self._quote(normalized, price, timestamp=timestamp)
                self._record_attempt("yahoo_finance_chart", "ok" if quote else "unavailable", None)
                return quote
            meta = result[0].get("meta", {})
            timestamp = (
                meta.get("regularMarketTime")
                or meta.get("postMarketTime")
                or meta.get("preMarketTime")
            )
            price = meta.get("regularMarketPrice") or meta.get("postMarketPrice") or meta.get("preMarketPrice")
            quote = self._quote(normalized, price, timestamp=timestamp)
            self._record_attempt("yahoo_finance_chart", "ok" if quote else "unavailable", None)
            return quote
        except Exception as exc:
            self._record_attempt("yahoo_finance_chart", "error", exc)
            return None

    def diagnostics(self) -> dict[str, Any]:
        """Return safe provider diagnostics for the latest fetch."""

        return {
            "attempts": list(self._last_attempts),
            "last_error": self._last_error_summary(),
        }

    def _read_json(self, url: str) -> dict[str, Any]:
        """Read one Yahoo Finance JSON response."""

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "PandorickKi/1.0 local stock price monitor"},
            method="GET",
        )
        with self._opener(request, timeout=self.timeout_seconds) as response:
            payload = response.read().decode("utf-8")
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("Stock price response is not a JSON object.")
        return data

    def _latest_chart_close(self, result: dict[str, Any]) -> tuple[Any, int | None] | None:
        """Return the latest close value and timestamp from the intraday chart."""

        timestamps = result.get("timestamp", [])
        indicators = result.get("indicators", {})
        quote_rows = indicators.get("quote", [])
        if not quote_rows:
            return None
        closes = quote_rows[0].get("close", [])
        for index in range(len(closes) - 1, -1, -1):
            value = closes[index]
            if value is not None:
                timestamp = timestamps[index] if index < len(timestamps) else None
                return value, timestamp
        return None

    def _quote(
        self,
        symbol: str,
        raw_price: Any,
        *,
        timestamp: Any = None,
    ) -> StockPriceQuote | None:
        """Validate and normalize a raw Yahoo price."""

        price = float(raw_price)
        if price <= 0:
            return None
        normalized_timestamp = int(timestamp) if timestamp is not None else None
        return StockPriceQuote(
            symbol=symbol,
            price=price,
            source="yahoo_finance_chart",
            timestamp=normalized_timestamp,
        )

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize public stock symbols."""

        return str(symbol or "").upper().strip()

    def _record_attempt(self, source: str, status: str, error: Any) -> None:
        """Store one safe provider attempt."""

        item = {"source": source, "status": status}
        if error is not None:
            item["error"] = str(error)
        self._last_attempts.append(item)

    def _last_error_summary(self) -> str | None:
        """Return a compact latest error message when the provider failed."""

        for attempt in reversed(self._last_attempts):
            if attempt.get("status") != "ok" and attempt.get("error"):
                return f"{attempt.get('source')}: {attempt.get('error')}"
        return None
