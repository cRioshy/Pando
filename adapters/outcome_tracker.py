"""Persistent simulated trade outcome foundation for PandorickKi."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any

from adapters.crypto_trade_tracker import CRYPTO_TRADE_UPDATED
from adapters.decision_signal_adapter import DECISION_CREATED, SIGNAL_CREATED
from event_bus import Event, EventBus
from jsonl_ledger import RotatingJsonlLedger


OUTCOME_TRACKER_STARTED = "OUTCOME_TRACKER_STARTED"
OUTCOME_TRACKER_STOPPED = "OUTCOME_TRACKER_STOPPED"
OUTCOME_TRACKER_HEARTBEAT = "OUTCOME_TRACKER_HEARTBEAT"
OUTCOME_TRACKER_ERROR = "OUTCOME_TRACKER_ERROR"
SIMULATED_TRADE_OPENED = "SIMULATED_TRADE_OPENED"
SIMULATED_TRADE_UPDATED = "SIMULATED_TRADE_UPDATED"
SIMULATED_TRADE_CLOSED = "SIMULATED_TRADE_CLOSED"

TERMINAL_TRADE_STATUSES = {"STOPPED", "TP1_REACHED", "CLOSED", "RESET"}


@dataclass
class OutcomeStatus:
    """Runtime status for simulated outcome tracking."""

    name: str = "outcome_tracker"
    running: bool = False
    healthy: bool = True
    open_trades: int = 0
    opened_trades: int = 0
    closed_trades: int = 0
    updated_trades: int = 0
    market_price_updates: int = 0
    ignored_decisions: int = 0
    ignored_trade_updates: int = 0
    duplicates_ignored: int = 0
    linked_signals: int = 0
    last_error: str | None = None


@dataclass
class SimulatedOutcomeTrade:
    """One open simulated trade connected to a final decision."""

    decision_id: str
    symbol: str
    market_type: str
    direction: str
    entry_price: float | None
    entry_time: str
    initial_stop_loss: float | None
    current_stop_loss: float | None
    take_profit_1: float | None
    current_price: float | None
    current_profit_percent: float | None
    max_profit_percent: float | None
    max_drawdown_percent: float | None
    trade_status: str
    updated_at: str
    source_event_id: str | None = None
    signal_id: str | None = None
    outcome_status: str = "OPEN"
    fees_percent: float | None = None
    slippage_percent: float | None = None
    exit_price: float | None = None
    exit_time: str | None = None
    result_type: str | None = None
    gross_profit_percent: float | None = None
    holding_seconds: float | None = None
    close_reason: str | None = None


class OutcomeTracker:
    """Open simulated trade records from final LONG/SHORT decisions.

    This adapter does not execute orders and does not change trading logic. It only
    creates a persistent audit trail that later outcome evaluation can close.
    """

    name = "outcome_tracker"

    def __init__(
        self,
        event_bus: EventBus,
        *,
        open_trades_file: Path,
        outcomes_file: Path,
        evaluation_horizon_seconds: float = 3600.0,
        ledger_rotation_bytes: int = 128 * 1024 * 1024,
    ) -> None:
        self.event_bus = event_bus
        self.open_trades_file = open_trades_file
        self.outcomes_file = outcomes_file
        self.evaluation_horizon_seconds = max(float(evaluation_horizon_seconds), 1.0)
        self.ledger_rotation_bytes = ledger_rotation_bytes
        self.status = OutcomeStatus()
        self._open_trades: dict[str, SimulatedOutcomeTrade] = {}
        self._closed_decision_ids: set[str] = set()
        self._subscribed = False
        self._lock = RLock()

    async def start(self) -> None:
        """Load open trades and subscribe to final decisions."""

        self._load_open_trades()
        if not self._subscribed:
            self.event_bus.subscribe(DECISION_CREATED, self._handle_decision)
            self.event_bus.subscribe(SIGNAL_CREATED, self._handle_signal)
            self.event_bus.subscribe(CRYPTO_TRADE_UPDATED, self._handle_trade_update)
            self.event_bus.subscribe("CRYPTO_ANALYSIS_FINISHED", self._handle_market_price_update)
            self.event_bus.subscribe("STOCK_ANALYSIS_FINISHED", self._handle_market_price_update)
            self.event_bus.subscribe("COMMODITY_ANALYSIS_FINISHED", self._handle_market_price_update)
            self._subscribed = True
        self.status.running = True
        self.status.healthy = True
        self.status.last_error = None
        self._publish(OUTCOME_TRACKER_STARTED, {"status": "started"})

    async def stop(self) -> None:
        """Persist current state and stop the tracker."""

        self._save_open_trades()
        self.status.running = False
        self._publish(OUTCOME_TRACKER_STOPPED, {"status": "stopped"})

    async def run_once(self) -> list[Event]:
        """Emit one heartbeat; tracking is event-driven."""

        with self._lock:
            open_count = len(self._open_trades)
        return [
            Event(
                topic=OUTCOME_TRACKER_HEARTBEAT,
                source=self.name,
                payload={
                    "status": "ok",
                    "open_trades": open_count,
                    "opened_trades": self.status.opened_trades,
                    "closed_trades": self.status.closed_trades,
                    "updated_trades": self.status.updated_trades,
                    "market_price_updates": self.status.market_price_updates,
                    "ignored_decisions": self.status.ignored_decisions,
                    "ignored_trade_updates": self.status.ignored_trade_updates,
                    "duplicates_ignored": self.status.duplicates_ignored,
                    "linked_signals": self.status.linked_signals,
                },
            )
        ]

    async def health(self) -> dict[str, Any]:
        """Return adapter health."""

        with self._lock:
            self.status.open_trades = len(self._open_trades)
        return asdict(self.status)

    def _handle_decision(self, event: Event) -> None:
        """Create one open simulated trade for valid final LONG/SHORT decisions."""

        try:
            data = self._payload_data(event)
            decision_id = str(data.get("decision_id") or event.event_id)
            direction = str(data.get("direction") or "").upper()
            symbol = str(data.get("symbol") or "")
            if direction not in {"LONG", "SHORT"} or not symbol:
                self.status.ignored_decisions += 1
                return
            entry_price = as_float(data.get("entry_price") or data.get("current_price") or data.get("price"))
            if entry_price is None:
                self.status.ignored_decisions += 1
                return

            now = datetime.now(UTC).isoformat()
            trade = SimulatedOutcomeTrade(
                decision_id=decision_id,
                symbol=symbol,
                market_type=str(data.get("market_type") or data.get("market") or "unknown"),
                direction=direction,
                entry_price=entry_price,
                entry_time=str(data.get("created_at") or now),
                initial_stop_loss=as_float(data.get("initial_stop_loss") or _nested(data, "risk", "stop_loss")),
                current_stop_loss=as_float(data.get("current_stop_loss") or _nested(data, "risk", "stop_loss")),
                take_profit_1=as_float(data.get("take_profit_1") or _nested(data, "risk", "take_profit_1")),
                current_price=as_float(data.get("current_price") or data.get("price")),
                current_profit_percent=0.0,
                max_profit_percent=0.0,
                max_drawdown_percent=0.0,
                trade_status="OPEN",
                updated_at=now,
                source_event_id=str(data.get("source_event_id") or event.event_id),
                signal_id=data.get("signal_id"),
            )

            with self._lock:
                if decision_id in self._open_trades:
                    self.status.duplicates_ignored += 1
                    return
                self._open_trades[decision_id] = trade
                self.status.open_trades = len(self._open_trades)
                self.status.opened_trades += 1
                self.status.healthy = True
                self.status.last_error = None

            self._save_open_trades()
            self._append_outcome_record("SIMULATED_TRADE_OPENED", asdict(trade))
            self._publish(SIMULATED_TRADE_OPENED, asdict(trade))
        except Exception as exc:  # noqa: BLE001 - platform services must stay alive
            self._record_error(exc)

    def _handle_market_price_update(self, event: Event) -> None:
        """Update open simulated outcomes from normal market analysis prices."""

        try:
            data = self._payload_data(event)
            symbol = str(data.get("symbol") or "")
            market_type = str(data.get("market_type") or "").lower()
            price = as_float(data.get("current_price") or data.get("price"))
            if not symbol or price is None:
                self.status.ignored_trade_updates += 1
                return

            matching: list[SimulatedOutcomeTrade] = []
            with self._lock:
                for trade in self._open_trades.values():
                    if trade.symbol == symbol and _market_matches(trade.market_type, market_type):
                        matching.append(trade)
            if not matching:
                return

            for trade in matching:
                if trade.entry_price is None:
                    self.status.ignored_trade_updates += 1
                    continue
                self._apply_market_price_update(trade, price, data)
                close_status = self._close_status_from_market_update(trade)
                if close_status:
                    self._close_trade(trade, close_status)
                    continue
                with self._lock:
                    self._open_trades[trade.decision_id] = trade
                    self.status.updated_trades += 1
                    self.status.market_price_updates += 1
                    self.status.healthy = True
                    self.status.last_error = None
                self._append_outcome_record("SIMULATED_TRADE_UPDATED", asdict(trade))
                self._publish(SIMULATED_TRADE_UPDATED, asdict(trade))
            self._save_open_trades()
        except Exception as exc:  # noqa: BLE001 - platform services must stay alive
            self._record_error(exc)

    def _handle_signal(self, event: Event) -> None:
        """Link a final signal id to an already opened simulated outcome."""

        try:
            data = self._payload_data(event)
            decision_id = str(data.get("decision_id") or "")
            signal_id = data.get("signal_id")
            if not decision_id or not signal_id:
                return
            with self._lock:
                trade = self._open_trades.get(decision_id)
                if trade is None:
                    return
                if trade.signal_id == signal_id:
                    return
                trade.signal_id = str(signal_id)
                trade.updated_at = datetime.now(UTC).isoformat()
                self._open_trades[decision_id] = trade
                self.status.linked_signals += 1
            self._save_open_trades()
            self._append_outcome_record("SIMULATED_TRADE_SIGNAL_LINKED", asdict(trade))
        except Exception as exc:  # noqa: BLE001 - platform services must stay alive
            self._record_error(exc)

    def _handle_trade_update(self, event: Event) -> None:
        """Update or close open simulated outcomes from simulated trade updates."""

        try:
            data = self._payload_data(event)
            trade = self._find_open_trade(data)
            if trade is None:
                self.status.ignored_trade_updates += 1
                return

            self._apply_trade_update(trade, data)
            trade_status = str(data.get("trade_status") or trade.trade_status).upper()
            if trade_status in TERMINAL_TRADE_STATUSES:
                self._close_trade(trade, trade_status)
                return

            with self._lock:
                self._open_trades[trade.decision_id] = trade
                self.status.updated_trades += 1
                self.status.healthy = True
                self.status.last_error = None
            self._save_open_trades()
            self._append_outcome_record("SIMULATED_TRADE_UPDATED", asdict(trade))
            self._publish(SIMULATED_TRADE_UPDATED, asdict(trade))
        except Exception as exc:  # noqa: BLE001 - platform services must stay alive
            self._record_error(exc)

    def _load_open_trades(self) -> None:
        """Load open simulated trades from disk."""

        if not self.open_trades_file.exists():
            return
        try:
            data = json.loads(self.open_trades_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self._record_error(exc)
            return
        if not isinstance(data, dict):
            return
        with self._lock:
            for decision_id, item in data.items():
                if isinstance(item, dict):
                    self._open_trades[str(decision_id)] = SimulatedOutcomeTrade(**item)
            self.status.open_trades = len(self._open_trades)

    def _find_open_trade(self, data: dict[str, Any]) -> SimulatedOutcomeTrade | None:
        """Find an open outcome trade by decision id or symbol fallback."""

        decision_id = data.get("decision_id")
        symbol = str(data.get("symbol") or "")
        with self._lock:
            if decision_id and str(decision_id) in self._open_trades:
                return self._open_trades[str(decision_id)]
            for trade in self._open_trades.values():
                if trade.symbol == symbol and trade.outcome_status == "OPEN":
                    return trade
        return None

    def _apply_trade_update(self, trade: SimulatedOutcomeTrade, data: dict[str, Any]) -> None:
        """Copy measured simulated trade values onto an outcome trade."""

        trade.current_price = as_float(data.get("current_price")) or trade.current_price
        if data.get("signal_id"):
            trade.signal_id = str(data.get("signal_id"))
        trade.current_stop_loss = as_float(data.get("current_stop_loss")) or trade.current_stop_loss
        trade.initial_stop_loss = as_float(data.get("initial_stop_loss")) or trade.initial_stop_loss
        trade.take_profit_1 = as_float(data.get("take_profit_1")) or trade.take_profit_1
        trade.current_profit_percent = as_float(data.get("current_profit_percent"))
        trade.max_profit_percent = as_float(data.get("max_profit_percent"))
        trade.max_drawdown_percent = as_float(data.get("max_drawdown_percent"))
        trade.trade_status = str(data.get("trade_status") or trade.trade_status)
        trade.updated_at = str(data.get("updated_at") or datetime.now(UTC).isoformat())

    def _apply_market_price_update(self, trade: SimulatedOutcomeTrade, price: float, data: dict[str, Any]) -> None:
        """Calculate simulated P/L from a later market price."""

        profit_percent = _profit_percent(trade.direction, trade.entry_price, price)
        trade.current_price = price
        trade.current_profit_percent = profit_percent
        trade.max_profit_percent = max(
            as_float(trade.max_profit_percent) or 0.0,
            profit_percent if profit_percent is not None else 0.0,
        )
        trade.max_drawdown_percent = min(
            as_float(trade.max_drawdown_percent) or 0.0,
            profit_percent if profit_percent is not None else 0.0,
        )
        trade.trade_status = str(data.get("trade_status") or "OPEN")
        trade.updated_at = str(data.get("source_timestamp") or data.get("received_at") or datetime.now(UTC).isoformat())

    def _close_status_from_market_update(self, trade: SimulatedOutcomeTrade) -> str | None:
        """Return a simulated close status when stop, TP1 or horizon is reached."""

        if trade.current_price is None:
            return None
        if _stop_hit(trade.direction, trade.current_price, trade.current_stop_loss):
            return "STOPPED"
        if _take_profit_hit(trade.direction, trade.current_price, trade.take_profit_1):
            return "TP1_REACHED"
        elapsed = _duration_seconds(trade.entry_time, trade.updated_at)
        if elapsed is not None and elapsed >= self.evaluation_horizon_seconds:
            return "CLOSED"
        return None

    def _close_trade(self, trade: SimulatedOutcomeTrade, trade_status: str) -> None:
        """Close one simulated outcome and persist final result fields."""

        now = datetime.now(UTC).isoformat()
        with self._lock:
            if trade.decision_id in self._closed_decision_ids:
                self.status.duplicates_ignored += 1
                return
            self._closed_decision_ids.add(trade.decision_id)

        trade.trade_status = trade_status
        trade.outcome_status = "CLOSED"
        trade.exit_price = trade.current_price
        trade.exit_time = now
        trade.gross_profit_percent = trade.current_profit_percent
        trade.holding_seconds = _duration_seconds(trade.entry_time, now)
        trade.close_reason = trade_status
        trade.result_type = _result_type(trade.current_profit_percent, trade_status)
        trade.updated_at = now

        with self._lock:
            self._open_trades.pop(trade.decision_id, None)
            self.status.open_trades = len(self._open_trades)
            self.status.closed_trades += 1
            self.status.updated_trades += 1
            self.status.healthy = True
            self.status.last_error = None

        payload = asdict(trade)
        self._save_open_trades()
        self._append_outcome_record("SIMULATED_TRADE_CLOSED", payload)
        self._publish(SIMULATED_TRADE_CLOSED, payload)

    def _save_open_trades(self) -> None:
        """Atomically persist open simulated trades."""

        with self._lock:
            payload = {decision_id: asdict(trade) for decision_id, trade in self._open_trades.items()}
        self._atomic_write_json(self.open_trades_file, payload)

    def _append_outcome_record(self, record_type: str, payload: dict[str, Any]) -> None:
        """Append one JSONL outcome lifecycle record and fsync it."""

        record = {
            "record_type": record_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "payload": payload,
        }
        self.outcomes_file.parent.mkdir(parents=True, exist_ok=True)
        RotatingJsonlLedger(self.outcomes_file, max_bytes=self.ledger_rotation_bytes).append(record)

    def _atomic_write_json(self, path: Path, payload: Any) -> None:
        """Write JSON through a validated temporary file and atomic replace."""

        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f"{path.name}.tmp")
        text = json.dumps(payload, indent=2, ensure_ascii=True)
        json.loads(text)
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)

    def _payload_data(self, event: Event) -> dict[str, Any]:
        """Return nested event payload data."""

        payload = event.payload if isinstance(event.payload, dict) else {}
        data = payload.get("payload", payload)
        return data if isinstance(data, dict) else {}

    def _record_error(self, exc: Exception) -> None:
        """Record and publish one non-fatal outcome tracker error."""

        self.status.healthy = False
        self.status.last_error = str(exc)
        self._publish(OUTCOME_TRACKER_ERROR, {"error": str(exc)})

    def _publish(self, topic: str, payload: dict[str, Any]) -> None:
        """Publish one outcome tracker event."""

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


def _nested(data: dict[str, Any], key: str, nested_key: str) -> Any:
    """Return one nested value when the parent is a dictionary."""

    parent = data.get(key)
    if not isinstance(parent, dict):
        return None
    return parent.get(nested_key)


def _duration_seconds(start: str | None, end: str | None) -> float | None:
    """Return elapsed seconds between two ISO timestamps."""

    if not start or not end:
        return None
    try:
        start_time = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(end.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max((end_time - start_time).total_seconds(), 0.0)


def _result_type(profit_percent: float | None, trade_status: str) -> str:
    """Classify one completed simulated outcome."""

    if trade_status == "TP1_REACHED":
        return "WIN"
    if profit_percent is None:
        return "UNKNOWN"
    if profit_percent > 0:
        return "WIN"
    if profit_percent < 0:
        return "LOSS"
    return "BREAKEVEN"


def _market_matches(left: str | None, right: str | None) -> bool:
    """Return True when market names are compatible."""

    normalized_left = str(left or "").lower()
    normalized_right = str(right or "").lower()
    return not normalized_right or normalized_left == normalized_right


def _profit_percent(direction: str, entry_price: float | None, current_price: float | None) -> float | None:
    """Calculate simulated profit percent for LONG or SHORT."""

    if entry_price is None or current_price is None or entry_price <= 0:
        return None
    normalized = str(direction or "").upper()
    if normalized == "SHORT":
        return round((entry_price - current_price) / entry_price * 100, 6)
    return round((current_price - entry_price) / entry_price * 100, 6)


def _stop_hit(direction: str, price: float, stop_loss: float | None) -> bool:
    """Return True when a simulated stop is hit."""

    if stop_loss is None:
        return False
    return price <= stop_loss if str(direction or "").upper() == "LONG" else price >= stop_loss


def _take_profit_hit(direction: str, price: float, take_profit: float | None) -> bool:
    """Return True when a simulated first take-profit is hit."""

    if take_profit is None:
        return False
    return price >= take_profit if str(direction or "").upper() == "LONG" else price <= take_profit
