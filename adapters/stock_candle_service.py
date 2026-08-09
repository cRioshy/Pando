"""Read-only public daily stock candles with bounded in-memory caching."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


UrlOpen = Callable[..., Any]


@dataclass(frozen=True)
class StockCandleSnapshot:
    """Normalized provider response before feature-quality validation."""

    symbol: str
    timeframe: str
    candles: list[dict[str, Any]]
    source: str


class StockCandleService:
    """Fetch public Yahoo daily chart data without API keys or write access."""

    unsupported_symbols = {"SPCX", "SPACEX"}

    def __init__(
        self,
        *,
        timeout_seconds: float = 8.0,
        cache_ttl_seconds: float = 900.0,
        opener: UrlOpen | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.timeout_seconds = max(float(timeout_seconds), 0.1)
        self.cache_ttl_seconds = max(float(cache_ttl_seconds), 0.0)
        self._opener = opener or urllib.request.urlopen
        self._clock = clock or time.monotonic
        self._cache: dict[tuple[str, int], tuple[float, StockCandleSnapshot]] = {}
        self._last_attempts: list[dict[str, str]] = []

    def fetch_daily_candles(self, symbol: str, *, limit: int = 260) -> StockCandleSnapshot | None:
        """Return up to ``limit`` daily candles with query1/query2 fallback."""

        normalized = str(symbol or "").upper().strip()
        normalized_limit = max(int(limit), 1)
        self._last_attempts = []
        if not normalized or normalized in self.unsupported_symbols:
            self._record("yahoo_finance_chart", "unsupported", f"Unsupported symbol: {symbol}")
            return None

        cache_key = (normalized, normalized_limit)
        cached = self._cache.get(cache_key)
        now = self._clock()
        if cached is not None and now - cached[0] <= self.cache_ttl_seconds:
            self._record(cached[1].source, "cache", None)
            return cached[1]

        encoded = urllib.parse.quote(normalized, safe="")
        query = "range=2y&interval=1d&events=history&includeAdjustedClose=true"
        for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
            source = f"yahoo_finance_chart:{host.split('.')[0]}"
            url = f"https://{host}/v8/finance/chart/{encoded}?{query}"
            try:
                snapshot = self._parse_snapshot(normalized, self._read_json(url), normalized_limit, source)
                self._cache[cache_key] = (now, snapshot)
                self._record(source, "ok", None)
                return snapshot
            except Exception as exc:  # noqa: BLE001 - fallback records safe diagnostics
                self._record(source, "error", exc)
        return None

    def diagnostics(self) -> dict[str, Any]:
        """Return safe diagnostics for the latest fetch."""

        error = next(
            (item.get("error") for item in reversed(self._last_attempts) if item.get("error")),
            None,
        )
        return {"attempts": list(self._last_attempts), "last_error": error}

    def _read_json(self, url: str) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "PandorickKi/1.0 local read-only stock candle observer"},
            method="GET",
        )
        with self._opener(request, timeout=self.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Stock candle response is not a JSON object.")
        return data

    def _parse_snapshot(
        self,
        symbol: str,
        data: dict[str, Any],
        limit: int,
        source: str,
    ) -> StockCandleSnapshot:
        chart = data.get("chart", {})
        if chart.get("error"):
            raise ValueError(f"Yahoo chart error: {chart.get('error')}")
        results = chart.get("result") or []
        if not results or not isinstance(results[0], dict):
            raise ValueError("No stock chart result.")
        result = results[0]
        timestamps = result.get("timestamp") or []
        indicators = result.get("indicators") or {}
        quotes = indicators.get("quote") or []
        if not timestamps or not quotes or not isinstance(quotes[0], dict):
            raise ValueError("Stock chart contains no timestamped OHLCV rows.")
        quote = quotes[0]
        adjusted_rows = indicators.get("adjclose") or []
        adjusted = adjusted_rows[0].get("adjclose", []) if adjusted_rows and isinstance(adjusted_rows[0], dict) else []
        candles: list[dict[str, Any]] = []
        for index, timestamp in enumerate(timestamps):
            candles.append(
                {
                    "timestamp": timestamp,
                    "open": _at(quote.get("open"), index),
                    "high": _at(quote.get("high"), index),
                    "low": _at(quote.get("low"), index),
                    "close": _at(quote.get("close"), index),
                    "adj_close": _at(adjusted, index),
                    "volume": _at(quote.get("volume"), index),
                }
            )
        if not candles:
            raise ValueError("Stock chart contains no candles.")
        return StockCandleSnapshot(
            symbol=symbol,
            timeframe="1d",
            candles=candles[-limit:],
            source=source,
        )

    def _record(self, source: str, status: str, error: Any) -> None:
        item = {"source": source, "status": status}
        if error is not None:
            item["error"] = str(error)
        self._last_attempts.append(item)


def _at(values: Any, index: int) -> Any:
    return values[index] if isinstance(values, list) and index < len(values) else None
