"""Resilient public crypto market data fetching without third-party HTTP clients."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


UrlOpen = Callable[..., Any]
Sleeper = Callable[[float], None]


class CryptoMarketDataError(RuntimeError):
    """Raised when no provider can supply the required candle data."""

    def __init__(self, message: str, *, diagnostics: dict[str, Any]) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics


@dataclass(frozen=True)
class CryptoMarketDataSnapshot:
    """Normalized inputs accepted by the external read-only analysis pipeline."""

    symbol: str
    timeframe: str
    candles: list[dict[str, float]]
    open_interest: float | None
    funding_rate: float | None
    diagnostics: dict[str, Any]


class CryptoMarketDataService:
    """Fetch required candles with fallback and optional futures context."""

    _BITGET_GRANULARITIES = {
        "1m": "1min",
        "3m": "3min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1h",
        "4h": "4h",
        "6h": "6h",
        "12h": "12h",
        "1d": "1day",
    }

    def __init__(
        self,
        *,
        timeout_seconds: float = 6.0,
        retries: int = 1,
        retry_backoff_seconds: float = 0.25,
        opener: UrlOpen | None = None,
        sleeper: Sleeper | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.retries = max(int(retries), 0)
        self.retry_backoff_seconds = max(float(retry_backoff_seconds), 0.0)
        self._opener = opener or urllib.request.urlopen
        self._sleep = sleeper or time.sleep

    def fetch(self, symbol: str, timeframe: str, limit: int) -> CryptoMarketDataSnapshot:
        """Return candles and best-effort futures context for one symbol."""

        normalized_symbol = self._normalize_symbol(symbol)
        normalized_limit = min(max(int(limit), 1), 1000)
        attempts: list[dict[str, Any]] = []
        candles: list[dict[str, float]] | None = None
        candle_source: str | None = None

        providers = (
            ("binance", lambda: self._fetch_binance_candles(normalized_symbol, timeframe, normalized_limit)),
            ("bitget", lambda: self._fetch_bitget_candles(normalized_symbol, timeframe, normalized_limit)),
        )
        for source, provider in providers:
            candles = self._attempt_required(source, "candles", provider, attempts)
            if candles:
                candle_source = source
                break

        if not candles:
            diagnostics = {
                "candle_source": None,
                "open_interest_status": "not_attempted",
                "funding_rate_status": "not_attempted",
                "attempts": attempts,
            }
            raise CryptoMarketDataError(
                f"No candle provider available for {normalized_symbol} {timeframe}.",
                diagnostics=diagnostics,
            )

        open_interest = self._attempt_optional(
            "binance_futures", "open_interest", lambda: self._fetch_open_interest(normalized_symbol), attempts
        )
        funding_rate = self._attempt_optional(
            "binance_futures", "funding_rate", lambda: self._fetch_funding_rate(normalized_symbol), attempts
        )
        diagnostics = {
            "candle_source": candle_source,
            "open_interest_status": "ok" if open_interest is not None else "unavailable",
            "funding_rate_status": "ok" if funding_rate is not None else "unavailable",
            "attempts": attempts,
        }
        return CryptoMarketDataSnapshot(
            symbol=normalized_symbol,
            timeframe=timeframe,
            candles=candles,
            open_interest=open_interest,
            funding_rate=funding_rate,
            diagnostics=diagnostics,
        )

    def _attempt_required(
        self,
        source: str,
        data_type: str,
        operation: Callable[[], Any],
        attempts: list[dict[str, Any]],
    ) -> Any | None:
        for attempt_number in range(1, self.retries + 2):
            try:
                result = operation()
                if not result:
                    raise ValueError("Provider returned no usable data.")
                attempts.append(
                    {"source": source, "data_type": data_type, "status": "ok", "attempt": attempt_number}
                )
                return result
            except Exception as exc:  # noqa: BLE001 - provider fallback must continue
                attempts.append(
                    {
                        "source": source,
                        "data_type": data_type,
                        "status": "error",
                        "attempt": attempt_number,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                if attempt_number <= self.retries and self.retry_backoff_seconds:
                    self._sleep(self.retry_backoff_seconds * attempt_number)
        return None

    def _attempt_optional(
        self,
        source: str,
        data_type: str,
        operation: Callable[[], Any],
        attempts: list[dict[str, Any]],
    ) -> float | None:
        try:
            value = operation()
            attempts.append({"source": source, "data_type": data_type, "status": "ok", "attempt": 1})
            return float(value)
        except Exception as exc:  # noqa: BLE001 - optional context must not stop candles
            attempts.append(
                {
                    "source": source,
                    "data_type": data_type,
                    "status": "error",
                    "attempt": 1,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            return None

    def _fetch_binance_candles(
        self, symbol: str, timeframe: str, limit: int
    ) -> list[dict[str, float]]:
        query = urllib.parse.urlencode({"symbol": symbol, "interval": timeframe, "limit": limit})
        rows = self._read_json(f"https://api.binance.com/api/v3/klines?{query}")
        if not isinstance(rows, list):
            raise ValueError("Binance candle response is not a list.")
        return [self._normalize_candle(row) for row in rows]

    def _fetch_bitget_candles(
        self, symbol: str, timeframe: str, limit: int
    ) -> list[dict[str, float]]:
        granularity = self._BITGET_GRANULARITIES.get(timeframe)
        if granularity is None:
            raise ValueError(f"Bitget does not support configured timeframe {timeframe!r}.")
        query = urllib.parse.urlencode(
            {"symbol": symbol, "granularity": granularity, "limit": min(limit, 1000)}
        )
        payload = self._read_json(f"https://api.bitget.com/api/v2/spot/market/candles?{query}")
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise ValueError("Bitget candle response does not contain a data list.")
        rows = sorted(payload["data"], key=lambda row: int(row[0]))
        return [self._normalize_candle(row) for row in rows]

    def _fetch_open_interest(self, symbol: str) -> float:
        query = urllib.parse.urlencode({"symbol": symbol})
        payload = self._read_json(f"https://fapi.binance.com/fapi/v1/openInterest?{query}")
        if not isinstance(payload, dict):
            raise ValueError("Open-interest response is not an object.")
        return float(payload["openInterest"])

    def _fetch_funding_rate(self, symbol: str) -> float:
        query = urllib.parse.urlencode({"symbol": symbol, "limit": 1})
        payload = self._read_json(f"https://fapi.binance.com/fapi/v1/fundingRate?{query}")
        if not isinstance(payload, list) or not payload:
            raise ValueError("Funding-rate response is empty.")
        return float(payload[0]["fundingRate"])

    def _read_json(self, url: str) -> Any:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "PandorickKi/1.0 local market monitor"},
            method="GET",
        )
        with self._opener(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _normalize_candle(row: Any) -> dict[str, float]:
        if not isinstance(row, (list, tuple)) or len(row) < 6:
            raise ValueError("Candle row has fewer than six fields.")
        return {
            "timestamp": float(row[0]),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
        }

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        normalized = str(symbol or "").upper().replace("-", "").replace("/", "")
        if not normalized:
            raise ValueError("Crypto symbol must not be empty.")
        return normalized
