"""Live ControlCenter adapter for the PandorickKi platform."""

from __future__ import annotations

import asyncio
import os
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from time import monotonic
from typing import Any

from event_bus import Event, EventBus
from shared_state import SharedState


CONTROL_CENTER_STARTED = "CONTROL_CENTER_STARTED"
CONTROL_CENTER_STOPPED = "CONTROL_CENTER_STOPPED"
CONTROL_STATUS_UPDATED = "CONTROL_STATUS_UPDATED"
CONTROL_CENTER_ERROR = "CONTROL_CENTER_ERROR"

LIVE_EVENT_TOPICS = {
    "CRYPTO_MARKET_DATA_UPDATED",
    "STOCK_MARKET_DATA_UPDATED",
    "COMMODITY_MARKET_DATA_UPDATED",
    "CRYPTO_ANALYSIS_FINISHED",
    "STOCK_ANALYSIS_FINISHED",
    "COMMODITY_ANALYSIS_FINISHED",
    "DECISION_CREATED",
    "SIGNAL_CREATED",
    "AI_LEARNING_UPDATED",
    "SERVICE_HEARTBEAT",
    "SERVICE_STATUS_CHANGED",
    "SYSTEM_ERROR",
    "CRYPTO_SERVICE_HEARTBEAT",
    "STOCK_SERVICE_HEARTBEAT",
    "BRAIN_SERVICE_HEARTBEAT",
    "BRAIN_DECISION_RECEIVED",
    "CRYPTO_SERVICE_STARTED",
    "STOCK_SERVICE_STARTED",
    "COMMODITY_SERVICE_STARTED",
    "BRAIN_SERVICE_STARTED",
    "CONTROL_CENTER_STARTED",
    "CRYPTO_SERVICE_STOPPED",
    "STOCK_SERVICE_STOPPED",
    "COMMODITY_SERVICE_STOPPED",
    "BRAIN_SERVICE_STOPPED",
    "CONTROL_CENTER_STOPPED",
    "CRYPTO_SERVICE_ERROR",
    "STOCK_SERVICE_ERROR",
    "COMMODITY_SERVICE_ERROR",
    "COMMODITY_DATA_WARNING",
    "BRAIN_SERVICE_ERROR",
    "CONTROL_CENTER_ERROR",
    "TELEGRAM_SERVICE_STARTED",
    "TELEGRAM_SERVICE_STOPPED",
    "TELEGRAM_SERVICE_ERROR",
    "TELEGRAM_SERVICE_HEARTBEAT",
    "TELEGRAM_MESSAGE_READY",
    "TELEGRAM_DRY_RUN_RECORDED",
    "TELEGRAM_MESSAGE_SENT",
    "CRYPTO_TRADE_UPDATED",
    "CRYPTO_TRADE_TRACKER_STARTED",
    "CRYPTO_TRADE_TRACKER_STOPPED",
    "CRYPTO_TRADE_TRACKER_HEARTBEAT",
    "CRYPTO_TRADE_TRACKER_ERROR",
    "COMMODITY_SERVICE_HEARTBEAT",
    CONTROL_STATUS_UPDATED,
}


@dataclass
class LiveControlState:
    """Thread-safe serializable live view state."""

    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    started_monotonic: float = field(default_factory=monotonic)
    last_crypto_price: dict[str, Any] = field(default_factory=dict)
    last_crypto_analysis: dict[str, Any] = field(default_factory=dict)
    last_stock_price: dict[str, Any] = field(default_factory=dict)
    last_stock_analysis: dict[str, Any] = field(default_factory=dict)
    last_commodity_price: dict[str, Any] = field(default_factory=dict)
    last_commodity_analysis: dict[str, Any] = field(default_factory=dict)
    last_brain_decision: dict[str, Any] = field(default_factory=dict)
    last_learning_update: dict[str, Any] = field(default_factory=dict)
    telegram_status: dict[str, Any] = field(default_factory=dict)
    service_status: dict[str, str] = field(default_factory=dict)
    service_heartbeats: dict[str, str] = field(default_factory=dict)
    error_count: int = 0
    last_update_at: str | None = None
    events_received: int = 0
    event_counts: Counter[str] = field(default_factory=Counter)
    latest_events: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=12))
    event_bus_queue_size: int = 0


@dataclass
class ControlCenterAdapter:
    """Collect platform events and render a non-blocking live terminal view."""

    event_bus: EventBus
    shared_state: SharedState
    print_output: bool = True
    name: str = "control_center"
    _running: bool = False
    _subscribed_topics: set[str] = field(default_factory=set)
    _stop_live_view: asyncio.Event | None = None
    _lock: RLock = field(default_factory=RLock)
    _state: LiveControlState = field(default_factory=LiveControlState)

    async def start(self) -> None:
        """Start event observation."""

        self._running = True
        self._subscribe_live_events()
        self.event_bus.publish(
            Event(
                topic=CONTROL_CENTER_STARTED,
                source=self.name,
                payload={"status": "STARTED"},
            )
        )

    async def stop(self) -> None:
        """Stop the adapter and close event subscriptions."""

        await self.stop_live_view()
        if self._running:
            self.event_bus.publish(
                Event(
                    topic=CONTROL_CENTER_STOPPED,
                    source=self.name,
                    payload={"status": "STOPPED"},
                )
            )
        self._running = False
        self._unsubscribe_live_events()

    async def run_once(self) -> list[Event]:
        """Create one control-center snapshot event."""

        snapshot = await self.get_snapshot()
        if self.print_output:
            self._print_snapshot(snapshot)
        return [
            Event(
                topic=CONTROL_STATUS_UPDATED,
                source=self.name,
                payload=snapshot,
            )
        ]

    async def run_live_view(self, refresh_seconds: float = 1.0) -> None:
        """Refresh the terminal view until stopped."""

        self._stop_live_view = asyncio.Event()
        refresh_seconds = max(refresh_seconds, 0.1)
        while not self._stop_live_view.is_set():
            if self.print_output:
                self._render_live_snapshot(await self.get_snapshot())
            try:
                await asyncio.wait_for(self._stop_live_view.wait(), timeout=refresh_seconds)
            except asyncio.TimeoutError:
                continue

    async def stop_live_view(self) -> None:
        """Request live-view shutdown."""

        if self._stop_live_view is not None:
            self._stop_live_view.set()

    async def health(self) -> dict[str, Any]:
        """Return current ControlCenter health."""

        snapshot = await self.get_snapshot()
        return {
            "name": self.name,
            "running": self._running,
            "healthy": self._running,
            "total_events": snapshot["events_received"],
            "event_counts": snapshot["event_counts"],
            "errors": snapshot["error_count"],
        }

    async def get_snapshot(self) -> dict[str, Any]:
        """Return an async serializable runtime status snapshot."""

        return await self._build_snapshot()

    def get_status(self) -> dict[str, Any]:
        """Return a status snapshot for synchronous tests or reports."""

        return self._build_snapshot_sync(self.shared_state.to_dict())

    def _subscribe_live_events(self) -> None:
        """Subscribe to all live topics once."""

        for topic in LIVE_EVENT_TOPICS:
            if topic in self._subscribed_topics:
                continue
            self.event_bus.subscribe(topic, self._record_event)
            self._subscribed_topics.add(topic)

    def _unsubscribe_live_events(self) -> None:
        """Remove all live subscriptions."""

        for topic in list(self._subscribed_topics):
            self.event_bus.unsubscribe(topic, self._record_event)
            self._subscribed_topics.remove(topic)

    def _record_event(self, event: Event) -> None:
        """Update live state immediately when an event arrives."""

        try:
            self._update_live_state(event)
        except Exception:
            with self._lock:
                self._state.error_count += 1
                self._state.last_update_at = datetime.now(UTC).isoformat()

    def _update_live_state(self, event: Event) -> None:
        """Apply one event to the live state without blocking producers."""

        payload = event.payload if isinstance(event.payload, dict) else {}
        data = payload.get("payload", payload) if isinstance(payload.get("payload", payload), dict) else {}
        now = datetime.now(UTC).isoformat()
        source = str(payload.get("source") or event.source)

        with self._lock:
            self._state.events_received += 1
            self._state.event_counts[event.topic] += 1
            self._state.event_bus_queue_size = self.event_bus.queue_size()
            self._state.last_update_at = now
            self._state.latest_events.append(
                {
                    "topic": event.topic,
                    "source": event.source,
                    "created_at": event.created_at,
                }
            )

            if "ERROR" in event.topic.upper() or event.topic == "SYSTEM_ERROR":
                self._state.error_count += 1

            if event.topic.endswith("HEARTBEAT") or event.topic == "SERVICE_HEARTBEAT":
                self._state.service_heartbeats[source] = now

            if event.topic.endswith("STARTED"):
                self._state.service_status[source] = "STARTED"
            elif event.topic.endswith("STOPPED"):
                self._state.service_status[source] = "STOPPED"
            elif event.topic.endswith("ERROR") or event.topic == "SYSTEM_ERROR":
                self._state.service_status[source] = "ERROR"
            elif event.topic == "SERVICE_STATUS_CHANGED":
                service = str(data.get("service") or source)
                self._state.service_status[service] = str(data.get("status", "UNKNOWN"))

            self._apply_market_event(event.topic, payload, data)

    def _apply_market_event(
        self,
        topic: str,
        payload: dict[str, Any],
        data: dict[str, Any],
    ) -> None:
        """Update market, decision, signal and learning fields."""

        symbol = payload.get("symbol") or data.get("symbol")
        price = data.get("price") or payload.get("price")

        if topic == "CRYPTO_MARKET_DATA_UPDATED":
            self._state.last_crypto_price[str(symbol)] = price
        elif topic == "STOCK_MARKET_DATA_UPDATED":
            for item in data.get("symbols", []):
                self._state.last_stock_price[str(item)] = None
            if symbol:
                self._state.last_stock_price[str(symbol)] = price
        elif topic == "COMMODITY_MARKET_DATA_UPDATED":
            if symbol:
                self._state.last_commodity_price[str(symbol)] = price
        elif topic == "CRYPTO_ANALYSIS_FINISHED":
            existing = self._state.last_crypto_analysis.get(str(symbol), {})
            self._state.last_crypto_analysis[str(symbol)] = {
                **self._compact_decision(data),
                **self._trade_fields(existing),
            }
        elif topic == "STOCK_ANALYSIS_FINISHED":
            self._state.last_stock_analysis[str(symbol)] = self._compact_decision(data)
            if data.get("current_price") is not None:
                self._state.last_stock_price[str(symbol)] = data.get("current_price")
        elif topic == "COMMODITY_ANALYSIS_FINISHED":
            self._state.last_commodity_analysis[str(symbol)] = self._compact_decision(data)
            if data.get("current_price") is not None:
                self._state.last_commodity_price[str(symbol)] = data.get("current_price")
        elif topic in {"DECISION_CREATED", "SIGNAL_CREATED"}:
            market_type = str(data.get("market_type", "")).lower()
            if market_type == "crypto" and symbol:
                self._state.last_crypto_analysis[str(symbol)] = self._compact_decision(data)
            elif market_type == "stock" and symbol:
                self._state.last_stock_analysis[str(symbol)] = self._compact_decision(data)
            elif market_type == "commodity" and symbol:
                self._state.last_commodity_analysis[str(symbol)] = self._compact_decision(data)
        elif topic == "CRYPTO_TRADE_UPDATED" and symbol:
            existing = self._state.last_crypto_analysis.get(str(symbol), {})
            merged = {**existing, **self._compact_trade(data)}
            self._state.last_crypto_analysis[str(symbol)] = merged
        elif topic == "BRAIN_DECISION_RECEIVED":
            self._state.last_brain_decision = dict(data)
        elif topic == "AI_LEARNING_UPDATED":
            self._state.last_learning_update = dict(data)
        elif topic.startswith("TELEGRAM_"):
            self._apply_telegram_event(topic, data)

    def _apply_telegram_event(self, topic: str, data: dict[str, Any]) -> None:
        """Update Telegram status fields."""

        status = self._state.telegram_status
        status["last_topic"] = topic
        status["last_update_at"] = datetime.now(UTC).isoformat()
        if topic == "TELEGRAM_SERVICE_STARTED":
            status["enabled"] = data.get("enabled", False)
            status["dry_run"] = data.get("dry_run", True)
            status["running"] = True
        elif topic == "TELEGRAM_SERVICE_HEARTBEAT":
            status["enabled"] = data.get("enabled", status.get("enabled", False))
            status["dry_run"] = data.get("dry_run", status.get("dry_run", True))
            status["messages_ready"] = data.get("messages_ready", status.get("messages_ready", 0))
            status["messages_sent"] = data.get("messages_sent", status.get("messages_sent", 0))
            status["dry_run_records"] = data.get("dry_run_records", status.get("dry_run_records", 0))
            status["running"] = True
        elif topic == "TELEGRAM_SERVICE_STOPPED":
            status["running"] = False
        elif topic == "TELEGRAM_MESSAGE_READY":
            status["messages_ready"] = status.get("messages_ready", 0) + 1
            status["last_message"] = data.get("message")
        elif topic == "TELEGRAM_DRY_RUN_RECORDED":
            status["dry_run_records"] = status.get("dry_run_records", 0) + 1
            status["last_message"] = data.get("message")
        elif topic == "TELEGRAM_MESSAGE_SENT":
            status["messages_sent"] = status.get("messages_sent", 0) + 1
            status["last_message"] = data.get("message")
        elif topic == "TELEGRAM_SERVICE_ERROR":
            status["errors"] = status.get("errors", 0) + 1
            status["last_error"] = data.get("error")

    def _compact_decision(self, data: dict[str, Any]) -> dict[str, Any]:
        """Return the subset needed by the terminal view."""

        return {
            "symbol": data.get("symbol"),
            "label": data.get("label"),
            "direction": data.get("direction"),
            "probability": data.get("probability"),
            "price": data.get("current_price", data.get("price")),
            "current_price": data.get("current_price", data.get("price")),
            "price_source": data.get("price_source"),
            "price_status": data.get("price_status"),
            "price_error": data.get("price_error"),
            "price_attempts": data.get("price_attempts", []),
            "price_timestamp": data.get("price_timestamp"),
            "entry_price": data.get("entry_price"),
            "current_stop_loss": data.get("current_stop_loss"),
            "take_profit_1": data.get("take_profit_1"),
            "current_profit_percent": data.get("current_profit_percent"),
            "trade_status": data.get("trade_status"),
            "risk_percent": data.get("risk_percent"),
            "received_at": data.get("received_at"),
        }

    def _compact_trade(self, data: dict[str, Any]) -> dict[str, Any]:
        """Return the subset needed for simulated crypto trade display."""

        return {
            "symbol": data.get("symbol"),
            "direction": data.get("direction"),
            "entry_price": data.get("entry_price"),
            "current_stop_loss": data.get("current_stop_loss"),
            "take_profit_1": data.get("take_profit_1"),
            "current_profit_percent": data.get("current_profit_percent"),
            "trade_status": data.get("trade_status"),
            "risk_percent": data.get("risk_percent"),
            "price": data.get("current_price"),
            "current_price": data.get("current_price"),
            "received_at": data.get("updated_at"),
        }

    def _trade_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """Keep simulated trade fields across ordinary market refreshes."""

        keys = {
            "entry_price",
            "current_stop_loss",
            "take_profit_1",
            "current_profit_percent",
            "trade_status",
            "risk_percent",
        }
        return {key: data.get(key) for key in keys if data.get(key) is not None}

    async def _build_snapshot(self) -> dict[str, Any]:
        """Build a live snapshot from ControlCenter state and SharedState."""

        return self._build_snapshot_sync(await self.shared_state.get_snapshot())

    def _build_snapshot_sync(self, shared_snapshot: dict[str, Any]) -> dict[str, Any]:
        """Build a serializable snapshot."""

        services = {
            name: {
                "status": service.get("status", "UNKNOWN"),
                "last_seen": service.get("last_seen"),
                "details": service.get("details", {}),
            }
            for name, service in shared_snapshot.get("services", {}).items()
        }
        last_health = shared_snapshot.get("values", {}).get("last_health", {})
        platform_health = last_health.get("status") or self._infer_health(services)

        with self._lock:
            state = self._state
            merged_status = {
                **state.service_status,
                **{name: service["status"] for name, service in services.items()},
            }
            return {
                "running": self._running,
                "platform_health": platform_health,
                "runtime_seconds": round(monotonic() - state.started_monotonic, 2),
                "services": services,
                "service_status": merged_status,
                "service_heartbeats": dict(state.service_heartbeats),
                "last_crypto_price": dict(state.last_crypto_price),
                "last_crypto_analysis": dict(state.last_crypto_analysis),
                "last_stock_price": dict(state.last_stock_price),
                "last_stock_analysis": dict(state.last_stock_analysis),
                "last_commodity_price": dict(state.last_commodity_price),
                "last_commodity_analysis": dict(state.last_commodity_analysis),
                "last_brain_decision": dict(state.last_brain_decision),
                "last_learning_update": dict(state.last_learning_update),
                "telegram_status": dict(state.telegram_status),
                "error_count": state.error_count,
                "last_update_at": state.last_update_at,
                "events_received": state.events_received,
                "total_events": state.events_received,
                "event_counts": dict(state.event_counts),
                "latest_events": list(state.latest_events),
                "event_bus_queue_size": self.event_bus.queue_size(),
            }

    def _infer_health(self, services: dict[str, dict[str, Any]]) -> str:
        """Infer a live status before the HealthMonitor creates its report."""

        statuses = [service["status"].upper() for service in services.values()]
        if any(status in {"ERROR", "FAILED"} for status in statuses):
            return "DEGRADED"
        if not statuses:
            return "PENDING"
        return "OK"

    def _print_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Print a PowerShell-friendly final status panel."""

        print(self._format_view(snapshot))

    def _render_live_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Redraw the live terminal view in-place."""

        print("\033[2J\033[H", end="")
        print(self._format_view(snapshot), end="", flush=True)

    def _format_view(self, snapshot: dict[str, Any]) -> str:
        """Format the current live state for terminal output."""

        lines = [
            "",
            "PANDORICK CONTROL CENTER",
            "-" * 44,
            f"System Health: {snapshot['platform_health']}",
            f"Runtime: {self._format_runtime(snapshot['runtime_seconds'])}",
            f"Events received: {snapshot['events_received']}",
            f"EventBus queue size: {snapshot['event_bus_queue_size']}",
            f"Errors: {snapshot['error_count']}",
            "",
            "SERVICES",
        ]
        service_status = snapshot["service_status"]
        heartbeats = snapshot["service_heartbeats"]
        for name in sorted(service_status):
            heartbeat_text = self._heartbeat_age(heartbeats.get(name))
            lines.append(f"{name:<16} {service_status[name]:<10} Heartbeat {heartbeat_text}")

        lines.extend(["", "CRYPTO"])
        lines.extend(self._format_market_rows(snapshot["last_crypto_analysis"]))
        lines.extend(["", "STOCKS"])
        lines.extend(self._format_market_rows(snapshot["last_stock_analysis"]))

        brain = snapshot["last_brain_decision"]
        learning = snapshot["last_learning_update"]
        telegram = snapshot["telegram_status"]
        lines.extend(
            [
                "",
                "BRAIN",
                f"Last decision: {brain.get('symbol', '-')}",
                f"Confidence: {brain.get('probability', '-')}",
                f"Learning updates: {learning.get('updates', 0) if learning else 0}",
                "",
                "TELEGRAM",
                f"Enabled: {telegram.get('enabled', False)}",
                f"Dry run: {telegram.get('dry_run', True)}",
                f"Messages ready: {telegram.get('messages_ready', 0)}",
                f"Dry-run records: {telegram.get('dry_run_records', 0)}",
                f"Messages sent: {telegram.get('messages_sent', 0)}",
                "",
                f"Last update: {self._format_clock(snapshot['last_update_at'])}",
                "",
            ]
        )
        return os.linesep.join(lines)

    def _format_market_rows(self, data: dict[str, dict[str, Any]]) -> list[str]:
        """Format compact market rows."""

        if not data:
            return ["-"]
        rows = []
        for symbol, item in sorted(data.items()):
            direction = str(item.get("direction") or "-")
            probability = item.get("probability")
            price = item.get("price")
            entry = item.get("entry_price")
            stop = item.get("current_stop_loss")
            tp1 = item.get("take_profit_1")
            profit = item.get("current_profit_percent")
            trade_status = item.get("trade_status") or "-"
            probability_text = "-" if probability is None else f"{float(probability):.2f}%"
            price_text = "-" if price is None else f"{float(price):,.4f}"
            entry_text = "-" if entry is None else f"{float(entry):,.4f}"
            stop_text = "-" if stop is None else f"{float(stop):,.4f}"
            tp1_text = "-" if tp1 is None else f"{float(tp1):,.4f}"
            profit_text = "-" if profit is None else f"{float(profit):+.2f}%"
            rows.append(
                f"{symbol:<10} {direction:<8} {probability_text:>8} "
                f"{entry_text:>12} {stop_text:>12} {tp1_text:>12} "
                f"{profit_text:>9} {price_text:>14} {trade_status:<12}"
            )
        return rows

    def _heartbeat_age(self, timestamp: str | None) -> str:
        """Return a small heartbeat age string."""

        if timestamp is None:
            return "-"
        try:
            happened = datetime.fromisoformat(timestamp)
            seconds = max(0, int((datetime.now(UTC) - happened).total_seconds()))
        except ValueError:
            return "?"
        return f"{seconds}s"

    def _format_runtime(self, seconds: float) -> str:
        """Format runtime seconds as HH:MM:SS."""

        total = int(seconds)
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _format_clock(self, timestamp: str | None) -> str:
        """Format an ISO timestamp for display."""

        if timestamp is None:
            return "-"
        try:
            return datetime.fromisoformat(timestamp).astimezone().strftime("%H:%M:%S")
        except ValueError:
            return timestamp
