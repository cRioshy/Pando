"""Simulated crypto trade tracking for ControlCenter, Brain and Telegram."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from atomic_json import atomic_write_json
from adapters.crypto_adapter import CRYPTO_ANALYSIS_FINISHED
from adapters.decision_signal_adapter import SIGNAL_CREATED
from event_bus import Event, EventBus


CRYPTO_TRADE_TRACKER_STARTED = "CRYPTO_TRADE_TRACKER_STARTED"
CRYPTO_TRADE_TRACKER_STOPPED = "CRYPTO_TRADE_TRACKER_STOPPED"
CRYPTO_TRADE_TRACKER_HEARTBEAT = "CRYPTO_TRADE_TRACKER_HEARTBEAT"
CRYPTO_TRADE_TRACKER_ERROR = "CRYPTO_TRADE_TRACKER_ERROR"
CRYPTO_TRADE_UPDATED = "CRYPTO_TRADE_UPDATED"


@dataclass
class SimulatedTrade:
    """One simulated active crypto trade."""

    signal_id: str
    symbol: str
    direction: str
    entry_price: float
    entry_time: str
    initial_stop_loss: float
    current_stop_loss: float
    take_profit_1: float
    current_price: float
    current_profit_percent: float
    max_profit_percent: float
    max_drawdown_percent: float
    trade_status: str
    risk_percent: float
    updated_at: str
    source_event_id: str | None = None
    decision_id: str | None = None


@dataclass
class CryptoTradeTrackerStatus:
    """Runtime status for the simulated trade tracker."""

    name: str = "crypto_trade_tracker"
    running: bool = False
    healthy: bool = True
    active_trades: int = 0
    updates: int = 0
    ignored_signals: int = 0
    last_error: str | None = None


class CryptoTradeTracker:
    """Create and update simulated crypto entries from final LONG/SHORT signals."""

    name = "crypto_trade_tracker"

    def __init__(
        self,
        event_bus: EventBus,
        *,
        active_file: Path,
        history_file: Path,
        max_risk_percent: float = 2.0,
        break_even_profit_percent: float = 1.0,
        trailing_start_percent: float = 2.0,
        atr_multiplier: float = 1.5,
    ) -> None:
        self.event_bus = event_bus
        self.active_file = active_file
        self.history_file = history_file
        self.max_risk_percent = max_risk_percent
        self.break_even_profit_percent = break_even_profit_percent
        self.trailing_start_percent = trailing_start_percent
        self.atr_multiplier = atr_multiplier
        self.status = CryptoTradeTrackerStatus()
        self._active: dict[str, SimulatedTrade] = {}
        self._subscribed = False
        self._lock = RLock()

    async def start(self) -> None:
        """Load active simulated trades and subscribe to signal and market updates."""

        self._load_active()
        if not self._subscribed:
            self.event_bus.subscribe(SIGNAL_CREATED, self._handle_signal)
            self.event_bus.subscribe(CRYPTO_ANALYSIS_FINISHED, self._handle_analysis)
            self._subscribed = True
        self.status.running = True
        self.status.healthy = True
        self.status.last_error = None
        self._publish(CRYPTO_TRADE_TRACKER_STARTED, {"status": "started"})

    async def stop(self) -> None:
        """Persist active trades and stop the tracker."""

        self._save_active()
        self.status.running = False
        self._publish(CRYPTO_TRADE_TRACKER_STOPPED, {"status": "stopped"})

    async def run_once(self) -> list[Event]:
        """Emit one heartbeat; trade updates happen through event callbacks."""

        with self._lock:
            active_count = len(self._active)
        return [
            Event(
                topic=CRYPTO_TRADE_TRACKER_HEARTBEAT,
                source=self.name,
                payload={
                    "status": "ok",
                    "active_trades": active_count,
                    "updates": self.status.updates,
                    "ignored_signals": self.status.ignored_signals,
                },
            )
        ]

    async def health(self) -> dict[str, Any]:
        """Return adapter health."""

        with self._lock:
            self.status.active_trades = len(self._active)
        return {
            "name": self.name,
            "running": self.status.running,
            "healthy": self.status.healthy,
            "active_trades": self.status.active_trades,
            "updates": self.status.updates,
            "ignored_signals": self.status.ignored_signals,
            "last_error": self.status.last_error,
        }

    def _handle_signal(self, event: Event) -> None:
        """Create a simulated trade only for valid crypto LONG/SHORT signals."""

        try:
            data = self._payload_data(event)
            if str(data.get("market_type", "")).lower() != "crypto":
                return
            direction = str(data.get("direction") or "").upper()
            if direction not in {"LONG", "SHORT"}:
                self.status.ignored_signals += 1
                return
            symbol = str(data.get("symbol") or "")
            if not symbol:
                self.status.ignored_signals += 1
                return
            with self._lock:
                existing = self._active.get(symbol)
                if existing and existing.trade_status not in {"STOPPED", "TP1_REACHED", "CLOSED", "RESET"}:
                    self.status.ignored_signals += 1
                    return

            entry = as_float(data.get("current_price") or data.get("price"))
            if entry is None or entry <= 0:
                self.status.ignored_signals += 1
                return
            stop = self._calculate_stop(direction, entry, data)
            tp1 = self._calculate_tp1(direction, entry, stop)
            now = datetime.now(UTC).isoformat()
            trade = SimulatedTrade(
                signal_id=str(data.get("signal_id") or event.event_id),
                symbol=symbol,
                direction=direction,
                entry_price=round(entry, 8),
                entry_time=now,
                initial_stop_loss=round(stop, 8),
                current_stop_loss=round(stop, 8),
                take_profit_1=round(tp1, 8),
                current_price=round(entry, 8),
                current_profit_percent=0.0,
                max_profit_percent=0.0,
                max_drawdown_percent=0.0,
                trade_status="ACTIVE",
                risk_percent=round(abs(entry - stop) / entry * 100, 4),
                updated_at=now,
                source_event_id=str(data.get("source_event_id") or event.event_id),
                decision_id=data.get("decision_id"),
            )
            self._store_trade_update(trade)
        except Exception as exc:  # noqa: BLE001
            self._record_error(exc)

    def _handle_analysis(self, event: Event) -> None:
        """Update active trade price, P/L and stop status from fresh analysis."""

        try:
            data = self._payload_data(event)
            symbol = str(data.get("symbol") or "")
            if not symbol:
                return
            price = as_float(data.get("current_price") or data.get("price"))
            if price is None:
                return
            with self._lock:
                trade = self._active.get(symbol)
            if trade is None:
                return
            self._update_trade(trade, price, data)
        except Exception as exc:  # noqa: BLE001
            self._record_error(exc)

    def _update_trade(self, trade: SimulatedTrade, price: float, data: dict[str, Any]) -> None:
        """Apply price movement, break-even and optional trailing stop."""

        if trade.direction == "LONG":
            profit = (price - trade.entry_price) / trade.entry_price * 100
            stopped = price <= trade.current_stop_loss
            tp1_reached = price >= trade.take_profit_1
        else:
            profit = (trade.entry_price - price) / trade.entry_price * 100
            stopped = price >= trade.current_stop_loss
            tp1_reached = price <= trade.take_profit_1

        trade.current_price = round(price, 8)
        trade.current_profit_percent = round(profit, 4)
        trade.max_profit_percent = round(max(trade.max_profit_percent, profit), 4)
        trade.max_drawdown_percent = round(min(trade.max_drawdown_percent, profit), 4)

        if stopped:
            trade.trade_status = "STOPPED"
        elif tp1_reached:
            trade.trade_status = "TP1_REACHED"
        else:
            self._maybe_move_stop(trade, data)
        trade.updated_at = datetime.now(UTC).isoformat()
        self._store_trade_update(trade)

    def _maybe_move_stop(self, trade: SimulatedTrade, data: dict[str, Any]) -> None:
        """Move stop to break-even and then trail it when thresholds are reached."""

        profit = trade.current_profit_percent
        atr = self._atr(data) or abs(trade.entry_price - trade.initial_stop_loss) / self.atr_multiplier
        if profit >= self.break_even_profit_percent:
            if trade.direction == "LONG" and trade.current_stop_loss < trade.entry_price:
                trade.current_stop_loss = round(trade.entry_price, 8)
                trade.trade_status = "BREAK_EVEN"
            elif trade.direction == "SHORT" and trade.current_stop_loss > trade.entry_price:
                trade.current_stop_loss = round(trade.entry_price, 8)
                trade.trade_status = "BREAK_EVEN"

        if profit >= self.trailing_start_percent:
            if trade.direction == "LONG":
                candidate = trade.current_price - atr * self.atr_multiplier
                if candidate > trade.current_stop_loss and candidate < trade.current_price:
                    trade.current_stop_loss = round(candidate, 8)
                    trade.trade_status = "TRAILING"
            else:
                candidate = trade.current_price + atr * self.atr_multiplier
                if candidate < trade.current_stop_loss and candidate > trade.current_price:
                    trade.current_stop_loss = round(candidate, 8)
                    trade.trade_status = "TRAILING"

    def _calculate_stop(self, direction: str, entry: float, data: dict[str, Any]) -> float:
        """Calculate a dynamic stop using risk, ATR, swing and max risk limit."""

        risk_stop = self._risk_stop(data)
        swing = self._swing_price(direction, data)
        atr = self._atr(data) or entry * 0.01
        if direction == "LONG":
            candidates = [
                value
                for value in [
                    risk_stop,
                    swing,
                    entry - atr * self.atr_multiplier,
                    entry * (1 - self.max_risk_percent / 100),
                ]
                if value is not None and value < entry
            ]
            return max(candidates) if candidates else entry * 0.99
        candidates = [
            value
            for value in [
                risk_stop,
                swing,
                entry + atr * self.atr_multiplier,
                entry * (1 + self.max_risk_percent / 100),
            ]
            if value is not None and value > entry
        ]
        return min(candidates) if candidates else entry * 1.01

    def _calculate_tp1(self, direction: str, entry: float, stop: float) -> float:
        """Calculate first take-profit from initial risk."""

        distance = abs(entry - stop)
        if direction == "LONG":
            return entry + distance * 1.5
        return entry - distance * 1.5

    def _risk_stop(self, data: dict[str, Any]) -> float | None:
        """Read an existing risk stop from upstream analysis when available."""

        risk = data.get("risk")
        if not isinstance(risk, dict):
            return None
        return as_float(risk.get("stop_loss") or risk.get("stop"))

    def _atr(self, data: dict[str, Any]) -> float | None:
        """Read ATR from normalized indicators."""

        indicators = data.get("indicators")
        if not isinstance(indicators, dict):
            return None
        return as_float(indicators.get("atr"))

    def _swing_price(self, direction: str, data: dict[str, Any]) -> float | None:
        """Return recent swing low for LONG or swing high for SHORT."""

        context = data.get("market_context")
        if isinstance(context, dict):
            context_key = "recent_swing_low" if direction == "LONG" else "recent_swing_high"
            compact_swing = as_float(context.get(context_key))
            if compact_swing is not None:
                return compact_swing

        raw = data.get("raw_result")
        market_data = raw.get("market_data", {}) if isinstance(raw, dict) else {}
        candles = market_data.get("candles", []) if isinstance(market_data, dict) else []
        if not isinstance(candles, list) or not candles:
            return None
        recent = candles[-20:]
        if direction == "LONG":
            lows = [as_float(candle.get("low")) for candle in recent if isinstance(candle, dict)]
            lows = [value for value in lows if value is not None]
            return min(lows) if lows else None
        highs = [as_float(candle.get("high")) for candle in recent if isinstance(candle, dict)]
        highs = [value for value in highs if value is not None]
        return max(highs) if highs else None

    def _store_trade_update(self, trade: SimulatedTrade) -> None:
        """Persist and publish one timestamped trade update."""

        with self._lock:
            self._active[trade.symbol] = trade
            self.status.active_trades = len(self._active)
            self.status.updates += 1
            self.status.healthy = True
            self.status.last_error = None
            payload = asdict(trade)
            active_payload = {symbol: asdict(item) for symbol, item in self._active.items()}
            self._atomic_write_json(self.active_file, active_payload)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with self.history_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self._publish(CRYPTO_TRADE_UPDATED, payload)

    def _load_active(self) -> None:
        """Load active simulated trades from disk."""

        if not self.active_file.exists():
            return
        try:
            data = json.loads(self.active_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(data, dict):
            return
        with self._lock:
            for symbol, item in data.items():
                if isinstance(item, dict):
                    self._active[str(symbol)] = SimulatedTrade(**item)
            self.status.active_trades = len(self._active)

    def _save_active(self) -> None:
        """Persist active trades."""

        with self._lock:
            payload = {symbol: asdict(trade) for symbol, trade in self._active.items()}
            self._atomic_write_json(self.active_file, payload)

    def _atomic_write_json(self, path: Path, payload: Any) -> None:
        """Write JSON through a validated temporary file and atomic replace."""

        atomic_write_json(path, payload)

    def _payload_data(self, event: Event) -> dict[str, Any]:
        """Return nested event payload data."""

        payload = event.payload if isinstance(event.payload, dict) else {}
        data = payload.get("payload", payload)
        return data if isinstance(data, dict) else {}

    def _record_error(self, exc: Exception) -> None:
        """Record and publish a non-fatal tracker error."""

        self.status.healthy = False
        self.status.last_error = str(exc)
        self._publish(CRYPTO_TRADE_TRACKER_ERROR, {"error": str(exc)})

    def _publish(self, topic: str, payload: dict[str, Any]) -> None:
        """Publish a tracker event."""

        event = Event(
            topic=topic,
            source=self.name,
            payload={
                "event_type": topic,
                "source": self.name,
                "timestamp": datetime.now(UTC).isoformat(),
                "payload": payload,
            },
        )
        event.payload["event_id"] = event.event_id
        self.event_bus.publish(event)


def as_float(value: Any) -> float | None:
    """Return value as float when possible."""

    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
