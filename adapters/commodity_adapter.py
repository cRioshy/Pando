"""Async adapter for commodity market prices."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from adapters.commodity_price_service import CommodityPriceQuote, CommodityPriceService
from event_bus import Event, EventBus


COMMODITY_SERVICE_STARTED = "COMMODITY_SERVICE_STARTED"
COMMODITY_MARKET_DATA_UPDATED = "COMMODITY_MARKET_DATA_UPDATED"
COMMODITY_ANALYSIS_FINISHED = "COMMODITY_ANALYSIS_FINISHED"
COMMODITY_SERVICE_ERROR = "COMMODITY_SERVICE_ERROR"
COMMODITY_DATA_WARNING = "COMMODITY_DATA_WARNING"
COMMODITY_SERVICE_STOPPED = "COMMODITY_SERVICE_STOPPED"
COMMODITY_SERVICE_HEARTBEAT = "COMMODITY_SERVICE_HEARTBEAT"


@dataclass
class CommodityAdapterStatus:
    """Runtime status of the commodity adapter."""

    name: str = "commodity"
    running: bool = False
    healthy: bool = True
    cycles: int = 0
    last_error: str | None = None
    last_event_at: str | None = None
    published_results: int = 0
    symbols: list[str] = field(default_factory=list)


class CommodityAdapter:
    """Fetch and publish commodity market snapshots without changing trading logic."""

    name = "commodity"

    def __init__(
        self,
        event_bus: EventBus,
        *,
        symbols: list[str] | None = None,
        price_service: CommodityPriceService | None = None,
        symbol_timeout_seconds: float = 8.0,
    ) -> None:
        self.event_bus = event_bus
        self.symbols = symbols or ["GC=F", "SI=F", "CL=F", "BZ=F"]
        self.price_service = price_service or CommodityPriceService()
        self.symbol_timeout_seconds = max(symbol_timeout_seconds, 0.1)
        self.status = CommodityAdapterStatus(symbols=list(self.symbols))
        self._correlation_id: str | None = None
        self._timed_out_symbols: set[str] = set()

    async def start(self) -> None:
        """Start the commodity adapter."""

        self.status.running = True
        self.status.healthy = True
        self.status.last_error = None
        self._publish(COMMODITY_SERVICE_STARTED, {"status": "started", "symbols": list(self.symbols)})

    async def stop(self) -> None:
        """Stop the commodity adapter."""

        self.status.running = False
        self._publish(COMMODITY_SERVICE_STOPPED, {"status": "stopped"})

    async def run_once(self) -> list[dict[str, Any]]:
        """Fetch one commodity cycle and publish normalized events."""

        if not self.status.running:
            await self.start()

        self.status.cycles += 1
        self._correlation_id = str(uuid4())
        self._timed_out_symbols = set()
        results: list[dict[str, Any]] = []

        for symbol in self.symbols:
            try:
                quote = await self._fetch_price_with_timeout(symbol)
                if quote is None:
                    if symbol in self._timed_out_symbols:
                        continue
                    diagnostics = self._price_diagnostics()
                    self._publish(
                        COMMODITY_DATA_WARNING,
                        {
                            "symbol": symbol,
                            "warning": diagnostics.get("last_error") or "No commodity price available.",
                            "price_attempts": diagnostics.get("attempts", []),
                        },
                    )
                    continue
                result = self._normalize_quote(quote)
                results.append(result)
                self._publish(
                    COMMODITY_MARKET_DATA_UPDATED,
                    {
                        "symbol": result["symbol"],
                        "label": result["label"],
                        "price": result["price"],
                        "price_timestamp": result["price_timestamp"],
                    },
                )
                self._publish_analysis_finished(result)
            except Exception as exc:
                self.status.healthy = False
                self.status.last_error = str(exc)
                self._publish(COMMODITY_SERVICE_ERROR, {"symbol": symbol, "error": str(exc)})

        self._publish(
            COMMODITY_SERVICE_HEARTBEAT,
            {"status": "ok" if results else "degraded", "cycle": self.status.cycles},
        )
        if results:
            self.status.healthy = True
            self.status.last_error = None
        return results

    async def _fetch_price_with_timeout(self, symbol: str) -> CommodityPriceQuote | None:
        """Fetch one commodity quote without letting one provider call block the cycle."""

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self.price_service.fetch_price, symbol),
                timeout=self.symbol_timeout_seconds,
            )
        except TimeoutError:
            self._timed_out_symbols.add(symbol)
            self.status.healthy = False
            self.status.last_error = f"Commodity price fetch timed out for {symbol}."
            self._publish(
                COMMODITY_DATA_WARNING,
                {
                    "symbol": symbol,
                    "warning": self.status.last_error,
                    "price_attempts": [{"source": "yahoo_finance_chart", "status": "timeout"}],
                },
            )
            return None

    async def health(self) -> dict[str, Any]:
        """Return adapter health."""

        return {
            "name": self.status.name,
            "running": self.status.running,
            "healthy": self.status.healthy,
            "cycles": self.status.cycles,
            "last_error": self.status.last_error,
            "published_results": self.status.published_results,
            "symbols": list(self.symbols),
        }

    async def get_status(self) -> dict[str, Any]:
        """Return detailed adapter status."""

        data = await self.health()
        data["last_event_at"] = self.status.last_event_at
        return data

    def _normalize_quote(self, quote: CommodityPriceQuote) -> dict[str, Any]:
        """Convert a quote into the shared market format."""

        direction = self._direction_from_change(quote.change_percent)
        probability = self._probability_from_change(quote.change_percent)
        price_timestamp = (
            datetime.fromtimestamp(quote.timestamp, UTC).isoformat()
            if quote.timestamp is not None
            else None
        )
        return {
            "market_type": "commodity",
            "symbol": quote.symbol,
            "label": quote.label,
            "timeframe": "1m",
            "direction": direction,
            "strength": probability,
            "probability": probability,
            "facts": {
                "price_source": quote.source,
                "change_percent": quote.change_percent,
                "previous_price": quote.previous_price,
            },
            "indicators": {
                "change_percent": quote.change_percent,
                "previous_price": quote.previous_price,
            },
            "price": quote.price,
            "current_price": quote.price,
            "price_source": quote.source,
            "price_status": "ok",
            "price_error": None,
            "price_attempts": self._price_diagnostics().get("attempts", []),
            "price_timestamp": price_timestamp,
            "source_timestamp": price_timestamp,
            "received_at": datetime.now(UTC).isoformat(),
            "raw_result": {},
        }

    def _direction_from_change(self, change_percent: float | None) -> str:
        """Map intraday movement to a conservative display direction."""

        if change_percent is None:
            return "HOLD"
        if change_percent >= 0.5:
            return "LONG"
        if change_percent <= -0.5:
            return "SHORT"
        return "HOLD"

    def _probability_from_change(self, change_percent: float | None) -> float:
        """Create a bounded display probability from price movement."""

        if change_percent is None:
            return 50.0
        return round(min(80.0, 50.0 + abs(change_percent) * 10.0), 2)

    def _price_diagnostics(self) -> dict[str, Any]:
        """Return safe provider diagnostics when the price service supports it."""

        diagnostics = getattr(self.price_service, "diagnostics", None)
        if callable(diagnostics):
            return diagnostics()
        return {"attempts": [], "last_error": None}

    def _publish_analysis_finished(self, result: dict[str, Any]) -> None:
        """Publish one normalized commodity analysis event."""

        self.status.published_results += 1
        self.status.last_event_at = datetime.now(UTC).isoformat()
        event = Event(
            topic=COMMODITY_ANALYSIS_FINISHED,
            source=self.name,
            payload={
                "event_type": COMMODITY_ANALYSIS_FINISHED,
                "source": self.name,
                "timestamp": self.status.last_event_at,
                "symbol": result["symbol"],
                "timeframe": result["timeframe"],
                "payload": result,
                "correlation_id": self._correlation_id,
            },
        )
        event.payload["event_id"] = event.event_id
        self.event_bus.publish(event)

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish a commodity service event."""

        event = Event(
            topic=event_type,
            source=self.name,
            payload={
                "event_type": event_type,
                "source": self.name,
                "timestamp": datetime.now(UTC).isoformat(),
                "payload": payload,
                "correlation_id": self._correlation_id,
            },
        )
        event.payload["event_id"] = event.event_id
        self.event_bus.publish(event)
