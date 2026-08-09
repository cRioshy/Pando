"""Async adapter for the existing Pandorick stock bot."""

from __future__ import annotations

import asyncio
import contextlib
import importlib.util
import io
import sys
from dataclasses import dataclass, field
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any
from uuid import uuid4

from adapters.stock_price_service import StockPriceService
from adapters.stock_candle_service import StockCandleService
from event_bus import Event, EventBus
from features.feature_engine import FeatureEngine, FeatureEngineError
from stock_data_contract import StockDataPolicy, evaluate_stock_data
from stock_shadow_candidate import StockShadowPolicy, build_stock_shadow_candidate
from stock_shadow_risk import StockShadowRiskPolicy, build_stock_shadow_risk


STOCK_SERVICE_STARTED = "STOCK_SERVICE_STARTED"
STOCK_MARKET_DATA_UPDATED = "STOCK_MARKET_DATA_UPDATED"
STOCK_ANALYSIS_FINISHED = "STOCK_ANALYSIS_FINISHED"
STOCK_SERVICE_ERROR = "STOCK_SERVICE_ERROR"
STOCK_SERVICE_STOPPED = "STOCK_SERVICE_STOPPED"
SERVICE_HEARTBEAT = "SERVICE_HEARTBEAT"

LEGACY_STOCK_MODULE_NAMES = {
    "brain",
    "brain_learning",
    "config",
    "control_unit",
    "decision_core",
    "market",
    "market_state",
    "probability",
    "risk_manager",
    "sensor_engine",
    "statistics",
    "stock_analyse",
    "stock_brain",
    "stock_brain_knowledge",
    "stock_data",
    "stock_fundamentals",
    "stock_market_context",
    "stock_monitor",
    "stock_patterns",
    "stock_precedence",
    "stock_probability",
    "stock_risk",
    "stock_storage",
    "stock_strategy",
    "telegram",
    "trade_manager",
}


@dataclass
class StockAdapterStatus:
    """Runtime status of the stock adapter."""

    name: str = "stock"
    running: bool = False
    healthy: bool = True
    cycles: int = 0
    last_error: str | None = None
    last_event_at: str | None = None
    published_results: int = 0
    duplicate_results: int = 0
    test_mode: bool = False
    live_price_display: bool = False
    stock_data_audits: int = 0
    stock_data_ready: int = 0
    stock_data_blocked: int = 0
    stock_candle_successes: int = 0
    stock_candle_failures: int = 0
    last_stock_data_status: str | None = None
    last_stock_data_reason_codes: list[str] = field(default_factory=list)
    stock_shadow_candidates: int = 0
    stock_shadow_long: int = 0
    stock_shadow_short: int = 0
    stock_shadow_hold: int = 0
    last_stock_shadow_direction: str | None = None
    last_stock_shadow_probability: float | None = None
    stock_shadow_risk_plans: int = 0
    stock_shadow_risk_blocked: int = 0
    last_stock_shadow_risk_status: str | None = None
    last_stock_shadow_risk_reason_codes: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)


class StockAdapter:
    """Connect the existing stock bot to the PandorickKi event bus."""

    name = "stock"

    def __init__(
        self,
        event_bus: EventBus,
        stock_project_path: Path,
        *,
        test_mode: bool = False,
        live_price_display: bool = False,
        stock_data_observer_enabled: bool = False,
        daily_candle_limit: int = 260,
        candle_cache_ttl_seconds: float = 900.0,
        stock_data_policy: StockDataPolicy | None = None,
        stock_shadow_policy: StockShadowPolicy | None = None,
        stock_shadow_risk_policy: StockShadowRiskPolicy | None = None,
        candle_service: StockCandleService | None = None,
        suppress_output: bool = True,
        cycle_timeout_seconds: float = 45.0,
    ) -> None:
        self.event_bus = event_bus
        self.stock_project_path = stock_project_path
        self.status = StockAdapterStatus()
        self.status.test_mode = test_mode
        self.status.live_price_display = live_price_display
        self.test_mode = test_mode
        self.live_price_display = live_price_display
        self.stock_data_observer_enabled = stock_data_observer_enabled
        self.daily_candle_limit = max(int(daily_candle_limit), 1)
        if stock_data_observer_enabled and stock_data_policy is None:
            raise ValueError("stock_data_policy is required when the stock data observer is enabled")
        if stock_data_observer_enabled and stock_shadow_policy is None:
            raise ValueError("stock_shadow_policy is required when the stock data observer is enabled")
        if stock_data_observer_enabled and stock_shadow_risk_policy is None:
            raise ValueError("stock_shadow_risk_policy is required when the stock data observer is enabled")
        self.stock_data_policy = stock_data_policy
        self.stock_shadow_policy = stock_shadow_policy
        self.stock_shadow_risk_policy = stock_shadow_risk_policy
        self.suppress_output = suppress_output
        self.cycle_timeout_seconds = max(cycle_timeout_seconds, 0.01)
        self._stock_main: ModuleType | None = None
        self._config: Any = None
        self._provider: Any = None
        self._sensor: Any = None
        self._temp_dir: TemporaryDirectory[str] | None = None
        self._seen_keys: set[tuple[str, str, str]] = set()
        self._correlation_id: str | None = None
        self._previous_modules: dict[str, ModuleType | None] = {}
        self._cycle_task: asyncio.Task[list[Any]] | None = None
        self._price_service = StockPriceService()
        self._candle_service = candle_service or StockCandleService(
            cache_ttl_seconds=candle_cache_ttl_seconds
        )
        self._feature_engine = FeatureEngine()
        self._last_live_price_source: str | None = None
        self._last_live_price_timestamp: str | None = None
        self._last_price_diagnostics: dict[str, Any] = {}

    async def start(self) -> None:
        """Load stock bot functions without starting its endless loop."""

        try:
            self._load_stock_module()
            self._config = self._build_config()
            self._provider = self._stock_main.PlaceholderStockDataProvider()
            self._sensor = self._stock_main.SensorEngine(self._provider)
            self.status.running = True
            self.status.healthy = True
            self.status.last_error = None
            self._publish(STOCK_SERVICE_STARTED, {"status": "started"})
        except Exception as exc:
            self.status.running = False
            self.status.healthy = False
            self.status.last_error = str(exc)
            self._publish(STOCK_SERVICE_ERROR, {"error": str(exc)})
            raise

    async def stop(self) -> None:
        """Stop the adapter without touching the existing stock bot files."""

        self.status.running = False
        self._publish(STOCK_SERVICE_STOPPED, {"status": "stopped"})
        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None

    async def run_once(self) -> list[dict[str, Any]]:
        """Run one stock cycle and publish normalized analysis events."""

        if not self.status.running:
            await self.start()

        assert self._stock_main is not None
        assert self._config is not None
        assert self._sensor is not None
        self.status.cycles += 1
        self._correlation_id = str(uuid4())

        try:
            decisions = await self._run_stock_with_timeout()
            if decisions is None:
                return []
        except Exception as exc:
            self.status.healthy = False
            self.status.last_error = str(exc)
            self._publish(STOCK_SERVICE_ERROR, {"error": str(exc)})
            return []

        normalized_results = [self._normalize_decision(decision) for decision in decisions]
        self._publish(
            STOCK_MARKET_DATA_UPDATED,
            {
                "count": len(normalized_results),
                "symbols": [item["symbol"] for item in normalized_results],
            },
        )

        for result in normalized_results:
            self._publish_analysis_if_new(result)

        self._publish(SERVICE_HEARTBEAT, {"status": "ok", "cycle": self.status.cycles})
        self.status.healthy = True
        self.status.last_error = None
        return normalized_results

    async def _run_stock_with_timeout(self) -> list[Any] | None:
        """Run the stock bot without letting slow JSON writes freeze PandorickKi."""

        if self._cycle_task is not None:
            if not self._cycle_task.done():
                message = (
                    "Previous stock cycle is still running; skipping this platform cycle "
                    "to avoid overlapping stock JSON writes."
                )
                self.status.healthy = False
                self.status.last_error = message
                self._publish(STOCK_SERVICE_ERROR, {"error": message})
                return None
            try:
                decisions = self._cycle_task.result()
            finally:
                self._cycle_task = None
            return decisions

        self._cycle_task = asyncio.create_task(
            asyncio.to_thread(self._run_stock_once_sync),
            name="pandorickki:stock_legacy_run_once",
        )
        done, _pending = await asyncio.wait({self._cycle_task}, timeout=self.cycle_timeout_seconds)
        if not done:
            message = f"Stock cycle exceeded {self.cycle_timeout_seconds:.1f}s and continues in background."
            self.status.healthy = False
            self.status.last_error = message
            self._publish(STOCK_SERVICE_ERROR, {"error": message})
            return None
        try:
            decisions = self._cycle_task.result()
        finally:
            self._cycle_task = None
        return decisions

    async def health(self) -> dict[str, Any]:
        """Return adapter health."""

        return {
            "name": self.status.name,
            "running": self.status.running,
            "healthy": self.status.healthy,
            "cycles": self.status.cycles,
            "last_error": self.status.last_error,
            "published_results": self.status.published_results,
            "duplicate_results": self.status.duplicate_results,
            "test_mode": self.status.test_mode,
            "live_price_display": self.status.live_price_display,
            "stock_data_observer_enabled": self.stock_data_observer_enabled,
            "stock_data_audits": self.status.stock_data_audits,
            "stock_data_ready": self.status.stock_data_ready,
            "stock_data_blocked": self.status.stock_data_blocked,
            "stock_candle_successes": self.status.stock_candle_successes,
            "stock_candle_failures": self.status.stock_candle_failures,
            "last_stock_data_status": self.status.last_stock_data_status,
            "last_stock_data_reason_codes": list(self.status.last_stock_data_reason_codes),
            "stock_shadow_candidates": self.status.stock_shadow_candidates,
            "stock_shadow_long": self.status.stock_shadow_long,
            "stock_shadow_short": self.status.stock_shadow_short,
            "stock_shadow_hold": self.status.stock_shadow_hold,
            "last_stock_shadow_direction": self.status.last_stock_shadow_direction,
            "last_stock_shadow_probability": self.status.last_stock_shadow_probability,
            "stock_shadow_risk_plans": self.status.stock_shadow_risk_plans,
            "stock_shadow_risk_blocked": self.status.stock_shadow_risk_blocked,
            "last_stock_shadow_risk_status": self.status.last_stock_shadow_risk_status,
            "last_stock_shadow_risk_reason_codes": list(
                self.status.last_stock_shadow_risk_reason_codes
            ),
        }

    async def get_status(self) -> dict[str, Any]:
        """Return current adapter status."""

        data = await self.health()
        data["last_event_at"] = self.status.last_event_at
        data["missing_fields"] = list(self.status.missing_fields)
        return data

    def _load_stock_module(self) -> None:
        """Load the existing stock main module with its own path priority."""

        if self._stock_main is not None:
            return
        main_path = self.stock_project_path / "main.py"
        if not main_path.exists():
            raise FileNotFoundError(f"Stock main.py not found: {main_path}")

        inserted = False
        stock_path = str(self.stock_project_path)
        self._previous_modules = {
            name: sys.modules.get(name) for name in LEGACY_STOCK_MODULE_NAMES
        }
        for name in LEGACY_STOCK_MODULE_NAMES:
            sys.modules.pop(name, None)

        if stock_path not in sys.path:
            sys.path.insert(0, stock_path)
            inserted = True

        try:
            spec = importlib.util.spec_from_file_location(
                "pandorick_stock_bot_main_adapter",
                main_path,
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load stock module from {main_path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._stock_main = module
        finally:
            if inserted:
                try:
                    sys.path.remove(stock_path)
                except ValueError:
                    pass
            self._restore_previous_modules()

    def _restore_previous_modules(self) -> None:
        """Restore module names after stock imports are bound in the loaded module."""

        for name in LEGACY_STOCK_MODULE_NAMES:
            previous = self._previous_modules.get(name)
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous

    def _build_config(self) -> Any:
        """Build the stock config for real or test-mode execution."""

        assert self._stock_main is not None
        if not self.test_mode:
            return self._stock_main.CONFIG

        self._temp_dir = TemporaryDirectory(prefix="pandorickki_stock_adapter_")
        data_dir = Path(self._temp_dir.name) / "data_stock"
        return replace(
            self._stock_main.CONFIG,
            history_file=data_dir / "stock_history.json",
            brain_file=data_dir / "stock_brain.json",
            decisions_file=data_dir / "stock_decisions.json",
            logs_file=data_dir / "stock_logs.json",
            precedence_file=data_dir / "stock_precedence.json",
            knowledge_file=data_dir / "stock_knowledge.json",
            patterns_file=data_dir / "stock_patterns.json",
            weights_file=data_dir / "stock_weights.json",
            sqlite_file=data_dir / "pandorick_stock.sqlite",
            sqlite_migration_report_file=data_dir / "sqlite_migration_report.json",
            use_sqlite_storage=True,
            backups_dir=data_dir / "backups",
        )

    def _run_stock_once_sync(self) -> list[Any]:
        """Run stock `run_once` synchronously with optional output suppression."""

        assert self._stock_main is not None
        assert self._config is not None
        assert self._sensor is not None
        if not self.suppress_output:
            return self._stock_main.run_once(
                self._config,
                self._sensor,
                self.status.cycles,
                None,
            )
        with contextlib.redirect_stdout(io.StringIO()):
            return self._stock_main.run_once(
                self._config,
                self._sensor,
                self.status.cycles,
                None,
            )

    def _normalize_decision(self, decision: Any) -> dict[str, Any]:
        """Convert a stock Decision object into the shared market format."""

        raw = decision.to_dict() if hasattr(decision, "to_dict") else {}
        state = raw.get("state", {}) if isinstance(raw, dict) else {}
        facts = state.get("facts", {}) if isinstance(state, dict) else {}
        missing: list[str] = []

        def required(name: str, value: Any) -> Any:
            if value is None:
                missing.append(name)
            return value

        direction = self._map_direction(raw.get("action"))
        analysis_close = facts.get("close_price") if isinstance(facts, dict) else None
        display_price = self._fetch_live_stock_price(raw.get("symbol"))
        price_source = self._last_live_price_source if display_price is not None else "live_unavailable_placeholder_hidden"
        price_status = "ok" if display_price is not None else ("unavailable" if self.live_price_display else "disabled")
        price_diagnostics = dict(self._last_price_diagnostics)
        source_timestamp = required("source_timestamp", raw.get("timestamp"))
        feature_payload = self._build_feature_payload(
            raw=raw,
            facts=facts if isinstance(facts, dict) else {},
            symbol=raw.get("symbol"),
            optional_context={
                "price_source": price_source,
                "earnings_flag": facts.get("earnings_flag") if isinstance(facts, dict) else None,
                "news_impact": facts.get("news_impact") if isinstance(facts, dict) else None,
                "sector_impact": facts.get("sector_impact") if isinstance(facts, dict) else None,
                "market_impact": facts.get("market_impact") if isinstance(facts, dict) else None,
            },
        )
        stock_data_audit = self._build_stock_data_audit(
            symbol=raw.get("symbol"),
            direction=direction,
            legacy_probability=raw.get("final_probability"),
            current_price=display_price,
            price_source=price_source,
            price_timestamp=self._last_live_price_timestamp,
        )
        result = {
            "market_type": "stock",
            "symbol": required("symbol", raw.get("symbol")),
            "timeframe": None,
            "direction": direction,
            "strength": raw.get("final_probability"),
            "probability": raw.get("final_probability"),
            "facts": state.get("labels", []) if isinstance(state, dict) else [],
            "indicators": facts if isinstance(facts, dict) else {},
            "price": display_price,
            "current_price": display_price,
            "analysis_close": analysis_close,
            "price_source": price_source,
            "price_status": price_status,
            "price_error": price_diagnostics.get("last_error"),
            "price_attempts": price_diagnostics.get("attempts", []),
            "price_timestamp": self._last_live_price_timestamp,
            "features": feature_payload.get("features"),
            "feature_error": feature_payload.get("feature_error"),
            "stock_data_audit": stock_data_audit.get("audit"),
            "stock_shadow_candidate": stock_data_audit.get("shadow_candidate"),
            "stock_shadow_comparison": stock_data_audit.get("comparison"),
            "stock_shadow_risk": stock_data_audit.get("shadow_risk"),
            "stock_candle_source": stock_data_audit.get("candle_source"),
            "stock_candle_count": stock_data_audit.get("candle_count", 0),
            "stock_candle_error": stock_data_audit.get("candle_error"),
            "source_timestamp": source_timestamp,
            "received_at": datetime.now(UTC).isoformat(),
            "raw_result": raw,
        }
        if missing:
            self.status.missing_fields.extend(missing)
        return result

    def _build_feature_payload(
        self,
        *,
        raw: dict[str, Any],
        facts: dict[str, Any],
        symbol: Any,
        optional_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Create additive feature data from stock candles or latest facts."""

        candles = raw.get("candles") or raw.get("history") or raw.get("price_history")
        if not isinstance(candles, list) or not candles:
            close = facts.get("close_price")
            candles = [
                {
                    "open": facts.get("open_price") or close,
                    "high": facts.get("high_price") or close,
                    "low": facts.get("low_price") or close,
                    "close": close,
                    "volume": facts.get("volume", 0.0),
                }
            ]
        else:
            candles = candles[-500:]
        try:
            features = self._feature_engine.compute(
                candles,
                symbol=str(symbol) if symbol else None,
                market_type="stock",
                optional_context=optional_context,
                include_targets=False,
            )
        except FeatureEngineError as exc:
            return {"features": None, "feature_error": str(exc)}
        except Exception as exc:
            return {"features": None, "feature_error": f"Feature engine failed: {exc}"}
        return {"features": features.to_dict(), "feature_error": None}

    def _build_stock_data_audit(
        self,
        *,
        symbol: Any,
        direction: str | None,
        legacy_probability: Any,
        current_price: float | None,
        price_source: str,
        price_timestamp: str | None,
    ) -> dict[str, Any]:
        """Evaluate public daily candles separately from the active legacy decision path."""

        if (
            not self.stock_data_observer_enabled
            or self.stock_data_policy is None
            or self.stock_shadow_policy is None
            or self.stock_shadow_risk_policy is None
        ):
            return {
                "audit": None,
                "shadow_candidate": None,
                "comparison": None,
                "shadow_risk": None,
                "candle_source": None,
                "candle_count": 0,
                "candle_error": None,
            }
        snapshot = self._candle_service.fetch_daily_candles(
            str(symbol or ""),
            limit=self.daily_candle_limit,
        )
        diagnostics = self._candle_service.diagnostics()
        candles = snapshot.candles if snapshot is not None else None
        shadow = build_stock_shadow_candidate(
            symbol=symbol,
            candles=candles,
            current_price=current_price,
            price_source=price_source,
            price_timestamp=price_timestamp,
            candle_source=snapshot.source if snapshot is not None else None,
            timeframe=snapshot.timeframe if snapshot is not None else "1d",
            policy=self.stock_shadow_policy,
        )
        shadow_risk = build_stock_shadow_risk(
            shadow,
            policy=self.stock_shadow_risk_policy,
        )
        shadow["risk"] = shadow_risk.get("risk")
        audit = evaluate_stock_data(
            {
                "market_type": "stock",
                "symbol": symbol,
                "timeframe": snapshot.timeframe if snapshot is not None else "1d",
                # This audit evaluates only the separated public-data shadow candidate.
                "source_kind": shadow.get("source_kind"),
                "direction": shadow.get("direction"),
                "candles": candles,
                "current_price": current_price,
                "price_source": price_source,
                "price_timestamp": price_timestamp,
                "risk": shadow_risk.get("risk"),
            },
            policy=self.stock_data_policy,
        )
        self.status.stock_data_audits += 1
        if audit["status"] == "READY":
            self.status.stock_data_ready += 1
        else:
            self.status.stock_data_blocked += 1
        if snapshot is None:
            self.status.stock_candle_failures += 1
        else:
            self.status.stock_candle_successes += 1
        self.status.last_stock_data_status = str(audit["status"])
        self.status.last_stock_data_reason_codes = list(audit["reason_codes"])
        if shadow.get("status") == "CALCULATED":
            self.status.stock_shadow_candidates += 1
            shadow_direction = str(shadow.get("direction") or "HOLD")
            if shadow_direction == "LONG":
                self.status.stock_shadow_long += 1
            elif shadow_direction == "SHORT":
                self.status.stock_shadow_short += 1
            else:
                self.status.stock_shadow_hold += 1
            self.status.last_stock_shadow_direction = shadow_direction
            probability = shadow.get("probability")
            self.status.last_stock_shadow_probability = (
                float(probability) if isinstance(probability, (int, float)) else None
            )
        if shadow_risk.get("status") == "CALCULATED":
            self.status.stock_shadow_risk_plans += 1
        else:
            self.status.stock_shadow_risk_blocked += 1
        self.status.last_stock_shadow_risk_status = str(shadow_risk.get("status") or "BLOCKED")
        self.status.last_stock_shadow_risk_reason_codes = list(
            shadow_risk.get("reason_codes") or []
        )
        return {
            "audit": audit,
            "shadow_candidate": shadow,
            "shadow_risk": shadow_risk,
            "comparison": {
                "mode": "OBSERVER",
                "legacy": {
                    "source_kind": "LEGACY_PLACEHOLDER",
                    "direction": direction,
                    "probability": legacy_probability,
                },
                "public_shadow": {
                    "source_kind": "PUBLIC_LIVE",
                    "direction": shadow.get("direction"),
                    "probability": shadow.get("probability"),
                    "probability_kind": shadow.get("probability_kind"),
                },
                "direction_matches": (
                    direction == shadow.get("direction")
                    if direction in {"LONG", "SHORT", "HOLD"} and shadow.get("direction") is not None
                    else None
                ),
                "affects_active_decision": False,
            },
            "candle_source": snapshot.source if snapshot is not None else None,
            "candle_count": len(snapshot.candles) if snapshot is not None else 0,
            "candle_error": diagnostics.get("last_error"),
        }

    def _fetch_live_stock_price(self, symbol: Any) -> float | None:
        """Fetch a public stock quote for dashboard display."""

        self._last_live_price_source = None
        self._last_live_price_timestamp = None
        self._last_price_diagnostics = {}
        if not self.live_price_display or not symbol:
            self._last_price_diagnostics = {
                "attempts": [],
                "last_error": "Live stock price display is disabled.",
            }
            return None
        quote = self._price_service.fetch_price(str(symbol))
        self._last_price_diagnostics = self._price_service.diagnostics()
        if quote is None:
            return None
        self._last_live_price_source = quote.source
        if quote.timestamp is not None:
            self._last_live_price_timestamp = datetime.fromtimestamp(quote.timestamp, UTC).isoformat()
        return quote.price

    def _publish_analysis_finished(self, result: dict[str, Any]) -> None:
        """Publish one normalized STOCK_ANALYSIS_FINISHED event."""

        observer_only_fields = {
            "stock_data_audit",
            "stock_shadow_candidate",
            "stock_shadow_comparison",
            "stock_shadow_risk",
            "stock_candle_source",
            "stock_candle_count",
            "stock_candle_error",
        }
        active_result = {
            key: value for key, value in result.items() if key not in observer_only_fields
        }
        event = Event(
            topic=STOCK_ANALYSIS_FINISHED,
            source=self.name,
            payload={
                "event_type": STOCK_ANALYSIS_FINISHED,
                "source": self.name,
                "timestamp": datetime.now(UTC).isoformat(),
                "symbol": result["symbol"],
                "timeframe": result["timeframe"],
                "payload": active_result,
                "correlation_id": self._correlation_id,
            },
        )
        event.payload["event_id"] = event.event_id
        self.event_bus.publish(event)

    def _publish_analysis_if_new(self, result: dict[str, Any]) -> bool:
        """Publish a normalized result unless its dedupe key was already seen."""

        key = (
            str(result["symbol"]),
            str(result["timeframe"]),
            str(result["source_timestamp"]),
        )
        if key in self._seen_keys:
            self.status.duplicate_results += 1
            return False
        self._seen_keys.add(key)
        self.status.published_results += 1
        self.status.last_event_at = datetime.now(UTC).isoformat()
        self._publish_analysis_finished(result)
        return True

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish a stock service event."""

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

    def _map_direction(self, action: Any) -> str | None:
        """Map stock bot actions to the shared direction vocabulary."""

        normalized = str(action or "").upper()
        if normalized in {"BUY", "WATCHLIST"}:
            return "LONG"
        if normalized in {"SELL", "SHORT"}:
            return "SHORT"
        if normalized in {"WAIT", "HOLD"}:
            return "HOLD"
        return None
