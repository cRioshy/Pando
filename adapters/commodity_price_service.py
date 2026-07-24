"""Free public commodity price provider for dashboard display."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


UrlOpen = Callable[..., Any]


@dataclass(frozen=True)
class CommodityPriceQuote:
    """Validated commodity quote with basic chart context."""

    symbol: str
    label: str
    price: float
    source: str
    timestamp: int | None = None
    previous_price: float | None = None
    change_percent: float | None = None


class CommodityPriceService:
    """Fetch commodity futures prices from Yahoo Finance without API keys."""

    labels = {
        "GC=F": "Gold",
        "SI=F": "Silver",
        "CL=F": "WTI Oil",
        "BZ=F": "Brent Oil",
    }

    def __init__(self, *, timeout_seconds: float = 5.0, opener: UrlOpen | None = None) -> None:
        self.timeout_seconds = timeout_seconds
        self._opener = opener or urllib.request.urlopen
        self._last_attempts: list[dict[str, str]] = []

    def fetch_price(self, symbol: str) -> CommodityPriceQuote | None:
        """Return the latest Yahoo chart quote for a commodity future."""

        normalized = self._normalize_symbol(symbol)
        self._last_attempts = []
        if not normalized:
            self._record_attempt("yahoo_finance_chart", "unsupported", f"Unsupported symbol: {symbol}")
            return None

        for source, url in self._provider_urls(normalized):
            try:
                data = self._read_json(url)
                quote = self._quote_from_response(normalized, data, source)
                if quote is not None:
                    self._record_attempt(source, "ok", None)
                    return quote
                self._record_attempt(source, "unavailable", "No valid close price in response.")
            except Exception as exc:
                self._record_attempt(source, "error", exc)
        return None

    def _provider_urls(self, normalized: str) -> list[tuple[str, str]]:
        """Return free public quote endpoints in fallback order."""

        encoded = urllib.parse.quote(normalized, safe="")
        suffix = "?range=1d&interval=1m&includePrePost=true"
        return [
            ("yahoo_finance_chart_query1", f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}{suffix}"),
            ("yahoo_finance_chart_query2", f"https://query2.finance.yahoo.com/v8/finance/chart/{encoded}{suffix}"),
        ]

    def _quote_from_response(
        self,
        normalized: str,
        data: dict[str, Any],
        source: str,
    ) -> CommodityPriceQuote | None:
        """Build a quote from one Yahoo chart response."""

        result = data.get("chart", {}).get("result", [])
        if not result:
            return None
        latest = self._latest_and_previous_close(result[0])
        if latest is None:
            return None
        price, timestamp, previous = latest
        change_percent = None
        if previous and previous > 0:
            change_percent = ((price - previous) / previous) * 100
        return self._quote(
            normalized,
            price,
            source=source,
            timestamp=timestamp,
            previous_price=previous,
            change_percent=change_percent,
        )

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
            headers={"User-Agent": "PandorickKi/1.0 local commodity price monitor"},
            method="GET",
        )
        with self._opener(request, timeout=self.timeout_seconds) as response:
            payload = response.read().decode("utf-8")
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("Commodity price response is not a JSON object.")
        return data

    def _latest_and_previous_close(self, result: dict[str, Any]) -> tuple[float, int | None, float | None] | None:
        """Return latest close, timestamp and previous close from the intraday chart."""

        timestamps = result.get("timestamp", [])
        quote_rows = result.get("indicators", {}).get("quote", [])
        if not quote_rows:
            return None
        closes = quote_rows[0].get("close", [])
        latest_index: int | None = None
        latest_price: float | None = None
        previous_price: float | None = None
        for index in range(len(closes) - 1, -1, -1):
            value = closes[index]
            if value is None:
                continue
            if latest_price is None:
                latest_index = index
                latest_price = float(value)
                continue
            previous_price = float(value)
            break
        if latest_price is None:
            return None
        timestamp = timestamps[latest_index] if latest_index is not None and latest_index < len(timestamps) else None
        return latest_price, timestamp, previous_price

    def _quote(
        self,
        symbol: str,
        raw_price: Any,
        *,
        source: str = "yahoo_finance_chart",
        timestamp: Any = None,
        previous_price: float | None = None,
        change_percent: float | None = None,
    ) -> CommodityPriceQuote | None:
        """Validate and normalize one raw Yahoo commodity price."""

        price = float(raw_price)
        if price <= 0:
            return None
        normalized_timestamp = int(timestamp) if timestamp is not None else None
        return CommodityPriceQuote(
            symbol=symbol,
            label=self.labels.get(symbol, symbol),
            price=price,
            source=source,
            timestamp=normalized_timestamp,
            previous_price=previous_price,
            change_percent=change_percent,
        )

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize public commodity symbols."""

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
