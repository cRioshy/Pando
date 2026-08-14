"""Async adapter for the existing Pandorick crypto analysis pipeline."""

from __future__ import annotations

import asyncio
import contextlib
import importlib
import io
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Callable
from uuid import uuid4

from adapters.crypto_market_data_service import CryptoMarketDataError, CryptoMarketDataService
from adapters.crypto_price_service import CryptoPriceService
from event_bus import Event, EventBus
from features.feature_engine import FeatureEngine, FeatureEngineError


CRYPTO_SERVICE_STARTED = "CRYPTO_SERVICE_STARTED"
CRYPTO_MARKET_DATA_UPDATED = "CRYPTO_MARKET_DATA_UPDATED"
CRYPTO_ANALYSIS_FINISHED = "CRYPTO_ANALYSIS_FINISHED"
CRYPTO_SERVICE_ERROR = "CRYPTO_SERVICE_ERROR"
CRYPTO_SERVICE_STOPPED = "CRYPTO_SERVICE_STOPPED"
CRYPTO_SERVICE_HEARTBEAT = "CRYPTO_SERVICE_HEARTBEAT"

LEGACY_MODULE_NAMES = {
    "audit_log",
    "brain",
    "decision_core",
    "market",
    "market_state",
    "models",
    "pandorick_pipeline",
    "probability",
    "risk_manager",
    "sensor_engine",
}


@dataclass
class CryptoAdapterStatus:
    """Runtime status of the crypto adapter."""

    name: str = "crypto"
    running: bool = False
    healthy: bool = True
    cycles: int = 0
    last_error: str | None = None
    last_error_details: dict[str, Any] | None = None
    last_event_at: str | None = None
    published_results: int = 0
    test_mode: bool = True
    live_price_display: bool = True
    missing_fields: list[str] = field(default_factory=list)


class CryptoAdapter:
    """Connect the existing crypto pipeline without importing its endless bot.py."""

    name = "crypto"

    def __init__(
        self,
        event_bus: EventBus,
        crypto_project_path: Path,
        *,
        symbols: list[str] | None = None,
        timeframe: str = "15m",
        candle_limit: int = 240,
        test_mode: bool = True,
        live_price_display: bool = False,
        persist_existing: bool = False,
        load_existing_brain: bool = False,
        suppress_output: bool = True,
        market_data_service: CryptoMarketDataService | None = None,
        regime_submitter: Callable[..., bool] | None = None,
    ) -> None:
        self.event_bus = event_bus
        self.crypto_project_path = crypto_project_path
        self.symbols = symbols or ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
        self.timeframe = timeframe
        self.candle_limit = candle_limit
        self.test_mode = test_mode
        self.live_price_display = live_price_display
        self.persist_existing = persist_existing
        self.load_existing_brain = load_existing_brain
        self.suppress_output = suppress_output
        self.status = CryptoAdapterStatus(test_mode=test_mode, live_price_display=live_price_display)
        self._pipeline: ModuleType | None = None
        self._models: ModuleType | None = None
        self._brain: ModuleType | None = None
        self._correlation_id: str | None = None
        self._previous_modules: dict[str, ModuleType | None] = {}
        self._price_service = CryptoPriceService()
        self._market_data_service = market_data_service or CryptoMarketDataService()
        self._regime_submitter = regime_submitter
        self._feature_engine = FeatureEngine()
        self._last_live_price_source: str | None = None
        self._last_price_diagnostics: dict[str, Any] = {}
        self._market_diagnostics: dict[str, dict[str, Any]] = {}

    async def start(self) -> None:
        """Load safe crypto modules and optional brain state."""

        try:
            self._load_crypto_modules()
            if (
                self.load_existing_brain
                and self._brain is not None
                and hasattr(self._brain, "load_brain")
            ):
                self._brain.load_brain()
            self.status.running = True
            self.status.healthy = True
            self.status.last_error = None
            self.status.last_error_details = None
            self._publish(CRYPTO_SERVICE_STARTED, {"status": "started", "test_mode": self.test_mode})
        except Exception as exc:
            self.status.running = False
            self.status.healthy = False
            self.status.last_error = str(exc)
            self._publish(CRYPTO_SERVICE_ERROR, {"error": str(exc)})
            raise

    async def stop(self) -> None:
        """Stop the adapter without touching the legacy bot loop."""

        self.status.running = False
        self._publish(CRYPTO_SERVICE_STOPPED, {"status": "stopped"})

    async def run_once(self) -> list[dict[str, Any]]:
        """Run one crypto analysis cycle and publish normalized events."""

        if not self.status.running:
            await self.start()

        self.status.cycles += 1
        self._correlation_id = str(uuid4())
        results: list[dict[str, Any]] = []
        cycle_errors: list[dict[str, Any]] = []

        for symbol in self.symbols:
            try:
                record = await asyncio.to_thread(self._analyse_symbol_sync, symbol)
                normalized = self._normalize_record(record)
                results.append(normalized)
                self._publish(
                    CRYPTO_MARKET_DATA_UPDATED,
                    {
                        "symbol": symbol,
                        "timeframe": self.timeframe,
                        "price": normalized.get("price"),
                    },
                )
                self._publish_analysis_finished(normalized)
            except Exception as exc:
                diagnostics = getattr(exc, "diagnostics", None)
                error = {
                    "symbol": symbol,
                    "stage": "market_data" if isinstance(exc, CryptoMarketDataError) else "analysis",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                if diagnostics:
                    error["diagnostics"] = diagnostics
                cycle_errors.append(error)
                self._publish(CRYPTO_SERVICE_ERROR, error)

        self.status.healthy = bool(results) and not cycle_errors
        if cycle_errors:
            self.status.last_error = cycle_errors[-1]["error"]
            self.status.last_error_details = cycle_errors[-1]
        else:
            self.status.last_error = None
            self.status.last_error_details = None
        self._publish(
            CRYPTO_SERVICE_HEARTBEAT,
            {
                "status": "ok" if self.status.healthy else ("degraded" if results else "error"),
                "cycle": self.status.cycles,
                "results": len(results),
                "errors": len(cycle_errors),
            },
        )
        return results

    async def health(self) -> dict[str, Any]:
        """Return adapter health."""

        return {
            "name": self.status.name,
            "running": self.status.running,
            "healthy": self.status.healthy,
            "cycles": self.status.cycles,
            "last_error": self.status.last_error,
            "last_error_details": self.status.last_error_details,
            "published_results": self.status.published_results,
            "test_mode": self.status.test_mode,
            "live_price_display": self.status.live_price_display,
        }

    async def get_status(self) -> dict[str, Any]:
        """Return detailed adapter status."""

        data = await self.health()
        data["last_event_at"] = self.status.last_event_at
        data["symbols"] = list(self.symbols)
        data["timeframe"] = self.timeframe
        data["missing_fields"] = list(self.status.missing_fields)
        return data

    def _load_crypto_modules(self) -> None:
        """Load existing crypto modules through their project path."""

        if self._pipeline is not None:
            return
        if not (self.crypto_project_path / "pandorick_pipeline.py").exists():
            raise FileNotFoundError(f"Crypto pipeline not found: {self.crypto_project_path}")

        crypto_path = str(self.crypto_project_path)
        inserted = False
        self._previous_modules = {
            name: sys.modules.get(name) for name in LEGACY_MODULE_NAMES
        }
        for name in LEGACY_MODULE_NAMES:
            sys.modules.pop(name, None)

        if crypto_path not in sys.path:
            sys.path.insert(0, crypto_path)
            inserted = True

        try:
            self._pipeline = importlib.import_module("pandorick_pipeline")
            self._models = importlib.import_module("models")
            self._brain = importlib.import_module("brain")
        finally:
            if inserted:
                try:
                    sys.path.remove(crypto_path)
                except ValueError:
                    pass
            self._restore_previous_modules()

    def _restore_previous_modules(self) -> None:
        """Restore module names so stock and platform imports are not polluted."""

        for name in LEGACY_MODULE_NAMES:
            previous = self._previous_modules.get(name)
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous

    def _analyse_symbol_sync(self, symbol: str) -> Any:
        """Analyze one symbol with live data or deterministic test candles."""

        assert self._pipeline is not None
        if self.test_mode:
            market_data = self._build_test_market_data(symbol)
        else:
            assert self._models is not None
            snapshot = self._market_data_service.fetch(symbol, self.timeframe, self.candle_limit)
            self._market_diagnostics[symbol] = snapshot.diagnostics
            market_data = self._models.MarketData(
                symbol=snapshot.symbol,
                timeframe=snapshot.timeframe,
                candles=snapshot.candles,
                open_interest=snapshot.open_interest,
                funding_rate=snapshot.funding_rate,
            )

        if not self.suppress_output:
            return self._analyse_with_brain_guard(market_data)

        with contextlib.redirect_stdout(io.StringIO()):
            return self._analyse_with_brain_guard(market_data)

    def _analyse_with_brain_guard(self, market_data: Any) -> Any:
        """Run analysis while keeping legacy brain files untouched by default."""

        assert self._pipeline is not None
        if self.load_existing_brain:
            return self._pipeline.analyse_market(market_data, persist=self.persist_existing)

        original_finder = self._pipeline.find_similar_market_states
        self._pipeline.find_similar_market_states = (
            lambda market_state: self._pipeline.empty_brain_result(market_state.symbol)
        )
        try:
            return self._pipeline.analyse_market(market_data, persist=False)
        finally:
            self._pipeline.find_similar_market_states = original_finder

    def _build_test_market_data(self, symbol: str) -> Any:
        """Create deterministic candles for tests and offline platform runs."""

        assert self._models is not None
        base = 100.0 + (sum(ord(char) for char in symbol) % 50)
        candles = []
        for index in range(self.candle_limit):
            trend = index * 0.08
            wave = ((index % 9) - 4) * 0.15
            close = base + trend + wave
            open_price = close - 0.25
            high = close + 0.9
            low = close - 0.9
            candles.append(
                {
                    "open": round(open_price, 6),
                    "high": round(high, 6),
                    "low": round(low, 6),
                    "close": round(close, 6),
                    "volume": round(1000 + index * 4 + (index % 5) * 20, 6),
                }
            )

        return self._models.MarketData(
            symbol=symbol,
            timeframe=self.timeframe,
            candles=candles,
            open_interest=1_000_000 + len(symbol) * 1000,
            funding_rate=0.0001,
        )

    def _normalize_record(self, record: Any) -> dict[str, Any]:
        """Convert an AnalysisRecord into the shared market event format."""

        raw = record.to_dict() if hasattr(record, "to_dict") else {}
        market_data = raw.get("market_data", {}) if isinstance(raw, dict) else {}
        decision = raw.get("decision", {}) if isinstance(raw, dict) else {}
        risk = raw.get("risk", {}) if isinstance(raw, dict) else {}
        sensors = raw.get("sensors", {}) if isinstance(raw, dict) else {}
        sensor_values = sensors.get("values", {}) if isinstance(sensors, dict) else {}
        candle_close = sensor_values.get("close")
        live_price = self._fetch_live_spot_price(market_data.get("symbol") or decision.get("symbol"))
        if live_price is not None:
            display_price = live_price
            price_source = self._last_live_price_source or "live_spot_ticker"
            price_status = "ok"
        elif self.test_mode:
            display_price = None
            price_source = "live_unavailable_offline_test_hidden"
            price_status = "unavailable" if self.live_price_display else "disabled"
        else:
            display_price = candle_close
            price_source = "analysis_close"
            price_status = "fallback_analysis_close"
        price_diagnostics = dict(self._last_price_diagnostics)
        feature_payload = self._build_feature_payload(
            market_data=market_data,
            sensor_values=sensor_values,
            symbol=market_data.get("symbol") or decision.get("symbol"),
            optional_context={
                "open_interest": market_data.get("open_interest"),
                "funding_rate": market_data.get("funding_rate"),
                "timeframe": market_data.get("timeframe"),
                "price_source": price_source,
            },
        )
        missing: list[str] = []

        def required(name: str, value: Any) -> Any:
            if value is None:
                missing.append(name)
            return value

        result = {
            "market_type": "crypto",
            "symbol": required("symbol", market_data.get("symbol") or decision.get("symbol")),
            "timeframe": required("timeframe", market_data.get("timeframe")),
            "direction": decision.get("action"),
            "strength": decision.get("confidence"),
            "probability": decision.get("confidence"),
            "facts": raw.get("market_state", {}).get("facts", {}),
            "indicators": sensor_values,
            "price": display_price,
            "current_price": display_price,
            "analysis_close": candle_close,
            "price_source": price_source,
            "price_status": price_status,
            "price_error": price_diagnostics.get("last_error"),
            "price_attempts": price_diagnostics.get("attempts", []),
            "market_data_diagnostics": dict(
                self._market_diagnostics.get(str(market_data.get("symbol") or decision.get("symbol")), {})
            ),
            "features": feature_payload.get("features"),
            "feature_error": feature_payload.get("feature_error"),
            "risk": risk,
            "source_timestamp": required("source_timestamp", raw.get("timestamp")),
            "received_at": datetime.now(UTC).isoformat(),
            "raw_result": raw,
        }
        if missing:
            self.status.missing_fields.extend(missing)
        return result

    def _build_feature_payload(
        self,
        *,
        market_data: dict[str, Any],
        sensor_values: dict[str, Any],
        symbol: Any,
        optional_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Create additive feature data without affecting legacy decisions."""

        candles = market_data.get("candles")
        if not isinstance(candles, list) or not candles:
            candles = [
                {
                    "open": sensor_values.get("open") or sensor_values.get("close"),
                    "high": sensor_values.get("high") or sensor_values.get("close"),
                    "low": sensor_values.get("low") or sensor_values.get("close"),
                    "close": sensor_values.get("close"),
                    "volume": sensor_values.get("volume", 0.0),
                }
            ]
        else:
            candles = candles[-500:]
        try:
            features = self._feature_engine.compute(
                candles,
                symbol=str(symbol) if symbol else None,
                market_type="crypto",
                optional_context=optional_context,
                include_targets=False,
            )
        except FeatureEngineError as exc:
            return {"features": None, "feature_error": str(exc)}
        except Exception as exc:
            return {"features": None, "feature_error": f"Feature engine failed: {exc}"}
        return {"features": features.to_dict(), "feature_error": None}

    def _fetch_live_spot_price(self, symbol: Any) -> float | None:
        """Fetch current public spot ticker price for dashboard display."""

        self._last_live_price_source = None
        self._last_price_diagnostics = {}
        if not self.live_price_display or not symbol:
            self._last_price_diagnostics = {
                "attempts": [],
                "last_error": "Live crypto price display is disabled.",
            }
            return None
        quote = self._price_service.fetch_price(str(symbol))
        self._last_price_diagnostics = self._price_service.diagnostics()
        if quote is None:
            return None
        self._last_live_price_source = quote.source
        return quote.price

    def _publish_analysis_finished(self, result: dict[str, Any]) -> None:
        """Publish one normalized CRYPTO_ANALYSIS_FINISHED event."""

        self.status.published_results += 1
        self.status.last_event_at = datetime.now(UTC).isoformat()
        event = Event(
            topic=CRYPTO_ANALYSIS_FINISHED,
            source=self.name,
            payload={
                "event_type": CRYPTO_ANALYSIS_FINISHED,
                "source": self.name,
                "timestamp": self.status.last_event_at,
                "symbol": result["symbol"],
                "timeframe": result["timeframe"],
                "payload": result,
                "correlation_id": self._correlation_id,
            },
        )
        event.payload["event_id"] = event.event_id
        if self._regime_submitter is not None:
            raw = result.get("raw_result")
            market_data = raw.get("market_data") if isinstance(raw, dict) else None
            candles = market_data.get("candles") if isinstance(market_data, dict) else None
            self._regime_submitter(
                symbol=result.get("symbol"),
                asset_type="crypto",
                timeframe=result.get("timeframe") or self.timeframe,
                candles=candles,
                source_event_id=event.event_id,
            )
        self.event_bus.publish(event)

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish a crypto service event."""

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
