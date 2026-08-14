"""Orchestration layer for the PandorickKi ground system."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from adapters.brain_adapter import BrainAdapter
from adapters.commodity_adapter import CommodityAdapter
from adapters.control_center_adapter import ControlCenterAdapter
from adapters.crypto_adapter import CryptoAdapter
from adapters.crypto_trade_tracker import CryptoTradeTracker
from adapters.decision_signal_adapter import DecisionSignalAdapter
from adapters.decision_gate_audit_adapter import DecisionGateAuditAdapter
from adapters.market_regime_observer_adapter import MarketRegimeObserverAdapter
from adapters.neurobrain_receiver_adapter import NeuroBrainReceiverAdapter
from adapters.outcome_tracker import OutcomeTracker
from adapters.stock_adapter import StockAdapter
from adapters.stock_shadow_verification_adapter import StockShadowVerificationAdapter
from adapters.telegram_adapter import TelegramAdapter
from config import PlatformConfig
from decision_gate_contract import DecisionGatePolicy
from event_bus import Event, EventBus
from health_monitor import HealthMonitor, HealthReport
from service_error_journal import ServiceErrorJournal
from shared_state import SharedState
from stock_data_contract import StockDataPolicy
from stock_shadow_candidate import StockShadowPolicy
from stock_shadow_risk import StockShadowRiskPolicy
from stock_shadow_verification_contract import (
    StockShadowVerificationPolicy,
    configuration_fingerprint,
)


class ServiceAdapter(Protocol):
    """Minimal adapter contract for existing systems."""

    name: str

    async def start(self) -> None:
        """Start the adapter."""

    async def stop(self) -> None:
        """Stop the adapter."""

    async def run_once(self) -> list[Event] | list[dict]:
        """Run one non-blocking service cycle and return emitted events."""

    async def health(self) -> dict:
        """Return health information."""


@dataclass(frozen=True)
class NoopAdapter:
    """Safe adapter placeholder that never imports legacy bot loops."""

    name: str
    reason: str

    async def start(self) -> None:
        """Start the no-op service."""

    async def stop(self) -> None:
        """Stop the no-op service."""

    async def health(self) -> dict:
        """Return no-op health."""

        return {"name": self.name, "running": True, "healthy": True}

    async def run_once(self) -> list[Event]:
        """Emit one heartbeat event."""

        return [
            Event(
                topic="service.heartbeat",
                source=self.name,
                payload={"status": "READY", "reason": self.reason},
            )
        ]


class Orchestrator:
    """Coordinates adapters, event bus, shared state and health reports."""

    def __init__(
        self,
        *,
        event_bus: EventBus | None = None,
        shared_state: SharedState | None = None,
        health_monitor: HealthMonitor | None = None,
        adapters: list[ServiceAdapter] | None = None,
        config: PlatformConfig | None = None,
        error_journal: ServiceErrorJournal | None = None,
    ) -> None:
        self.config = config or PlatformConfig.from_env()
        self.event_bus = event_bus or EventBus(max_history=self.config.event_bus_max_history)
        self.shared_state = shared_state or SharedState(self.config.shared_state_file)
        self.health_monitor = health_monitor or HealthMonitor()
        self.adapters = adapters or self._default_adapters()
        self.error_journal = error_journal
        if self.error_journal is None and adapters is None and self.config.service_error_journal_enabled:
            self.error_journal = ServiceErrorJournal(
                self.event_bus,
                journal_file=self.config.service_error_journal_file,
                summary_file=self.config.service_error_summary_file,
                rotation_bytes=self.config.service_error_rotation_bytes,
                max_archives=self.config.service_error_max_archives,
                max_summary_entries=self.config.service_error_max_summary_entries,
            )
        self._live_control_task: asyncio.Task | None = None
        self.event_bus.subscribe("*", self._record_event)

    async def start(self) -> None:
        """Start all adapters."""

        if self.error_journal is not None:
            self.error_journal.start()
            self._sync_error_journal_health()
        for adapter in self.adapters:
            try:
                await adapter.start()
                self.shared_state.update_service(adapter.name, "STARTED")
            except Exception as exc:
                self.shared_state.update_service(adapter.name, "ERROR", {"error": str(exc)})
                self.event_bus.publish(
                    Event(topic="service.error", source=adapter.name, payload={"error": str(exc)})
                )

    async def stop(self) -> None:
        """Stop all adapters."""

        await self.stop_live_control()
        for adapter in self.adapters:
            try:
                await adapter.stop()
                self.shared_state.update_service(adapter.name, "STOPPED")
            except Exception as exc:
                self.shared_state.update_service(adapter.name, "ERROR", {"error": str(exc)})
                self.event_bus.publish(
                    Event(
                        topic="service.error",
                        source=adapter.name,
                        payload={"error": str(exc)},
                    )
                )
        if self.error_journal is not None:
            self._sync_error_journal_health()
            self.error_journal.stop()
            self.shared_state.update_service(self.error_journal.name, "STOPPED")

    async def run_once(self, *, final_control_snapshot: bool = True) -> HealthReport:
        """Run one orchestration cycle with real asyncio service tasks."""

        tasks = [
            asyncio.create_task(
                self._run_adapter_task(adapter),
                name=f"pandorickki:{adapter.name}",
            )
            for adapter in self.adapters
        ]
        await asyncio.gather(*tasks)

        self._sync_error_journal_health()

        if final_control_snapshot:
            await self._publish_final_control_snapshot()

        report = self.health_monitor.check(self.shared_state)
        self.shared_state.set_value("last_health", report.to_dict())
        self.shared_state.save()
        return report

    async def run_continuous(
        self,
        *,
        cycle_interval: float = 60.0,
        live_control: bool = False,
        refresh_seconds: float = 1.0,
        final_control_snapshot: bool = False,
        max_cycles: int | None = None,
        should_pause: Callable[[], bool] | None = None,
        should_stop: Callable[[], bool] | None = None,
        take_restart_request: Callable[[], bool] | None = None,
    ) -> HealthReport | None:
        """Run orchestration cycles until cancelled or max_cycles is reached."""

        if live_control:
            await self.start_live_control(refresh_seconds=refresh_seconds)

        cycles = 0
        last_report: HealthReport | None = None
        while max_cycles is None or cycles < max_cycles:
            if should_stop is not None and should_stop():
                break
            if take_restart_request is not None and take_restart_request():
                await self._restart_adapters(
                    restart_live_control=live_control,
                    refresh_seconds=refresh_seconds,
                )
                continue
            if should_pause is not None and should_pause():
                action = await self._wait_for_control_action(
                    min(max(cycle_interval, 0.1), 1.0),
                    should_stop=should_stop,
                    take_restart_request=take_restart_request,
                )
                if action == "stop":
                    break
                if action == "restart":
                    await self._restart_adapters(
                        restart_live_control=live_control,
                        refresh_seconds=refresh_seconds,
                    )
                continue
            last_report = await self.run_once(final_control_snapshot=final_control_snapshot)
            cycles += 1
            if max_cycles is not None and cycles >= max_cycles:
                break
            action = await self._wait_for_control_action(
                max(cycle_interval, 0.1),
                should_stop=should_stop,
                take_restart_request=take_restart_request,
            )
            if action == "stop":
                break
            if action == "restart":
                await self._restart_adapters(
                    restart_live_control=live_control,
                    refresh_seconds=refresh_seconds,
                )
        if live_control:
            await self.stop_live_control()
            await self._publish_final_control_snapshot()
        return last_report

    async def _wait_for_control_action(
        self,
        delay: float,
        *,
        should_stop: Callable[[], bool] | None,
        take_restart_request: Callable[[], bool] | None,
    ) -> str | None:
        """Wait interruptibly so stop and restart do not wait for the next cycle."""

        loop = asyncio.get_running_loop()
        deadline = loop.time() + max(delay, 0.0)
        while True:
            if should_stop is not None and should_stop():
                return "stop"
            if take_restart_request is not None and take_restart_request():
                return "restart"
            remaining = deadline - loop.time()
            if remaining <= 0:
                return None
            await asyncio.sleep(min(remaining, 0.1))

    async def _restart_adapters(
        self,
        *,
        restart_live_control: bool,
        refresh_seconds: float,
    ) -> None:
        """Restart the existing adapter set without replacing the web process."""

        await self.stop()
        await self.start()
        if restart_live_control:
            await self.start_live_control(refresh_seconds=refresh_seconds)

    async def start_live_control(self, refresh_seconds: float = 1.0) -> None:
        """Start the ControlCenter live view as a background task."""

        if self._live_control_task is not None and not self._live_control_task.done():
            return
        control = self._control_adapter()
        if control is None or not hasattr(control, "run_live_view"):
            return
        self._live_control_task = asyncio.create_task(
            control.run_live_view(refresh_seconds=refresh_seconds),
            name="pandorickki:control_center_live_view",
        )

    async def stop_live_control(self) -> None:
        """Stop the ControlCenter live task cleanly."""

        if self._live_control_task is None:
            return
        control = self._control_adapter()
        if control is not None and hasattr(control, "stop_live_view"):
            await control.stop_live_view()
        try:
            await asyncio.wait_for(self._live_control_task, timeout=self.config.stop_timeout_seconds)
        except asyncio.TimeoutError:
            self._live_control_task.cancel()
            await asyncio.gather(self._live_control_task, return_exceptions=True)
        self._live_control_task = None

    async def _run_adapter_task(self, adapter: ServiceAdapter) -> None:
        """Run one adapter in an isolated task and keep platform state consistent."""

        self.shared_state.update_service(adapter.name, "RUNNING")
        try:
            results = await self._run_adapter_once(adapter)
        except Exception as exc:
            self.shared_state.update_service(
                adapter.name,
                "ERROR",
                {"error": str(exc)},
            )
            self.event_bus.publish(
                Event(
                    topic="service.error",
                    source=adapter.name,
                    payload={"error": str(exc)},
                )
            )
            return

        event_count = self._publish_adapter_results(adapter.name, results)
        adapter_health = await adapter.health()
        healthy = adapter_health.get("healthy")
        if healthy is False:
            service_status = "DEGRADED" if results else "ERROR"
        else:
            service_status = "OK"
        health_details = {
            key: value
            for key, value in adapter_health.items()
            if key
            in {
                "healthy",
                "last_error",
                "last_error_details",
                "cycles",
                "published_results",
                "test_mode",
                "stock_data_observer_enabled",
                "stock_data_audits",
                "stock_data_ready",
                "stock_data_blocked",
                "stock_candle_successes",
                "stock_candle_failures",
                "last_stock_data_status",
                "last_stock_data_reason_codes",
                "stock_shadow_candidates",
                "stock_shadow_long",
                "stock_shadow_short",
                "stock_shadow_hold",
                "last_stock_shadow_direction",
                "last_stock_shadow_probability",
                "stock_shadow_risk_plans",
                "stock_shadow_risk_blocked",
                "last_stock_shadow_risk_status",
                "last_stock_shadow_risk_reason_codes",
                "queue_depth",
                "queue_capacity",
                "batch_size",
                "batches_written",
                "dropped_events",
                "failed_events",
                "status_write_failures",
                "notification_failures",
                "worker_running",
            }
        }
        self.shared_state.update_service(
            adapter.name,
            service_status,
            {"results": len(results), "events": event_count, **health_details},
        )

    async def _run_adapter_once(self, adapter: ServiceAdapter) -> list[Any]:
        """Run one adapter while keeping noisy parallel snapshots quiet."""

        if adapter.name != "control_center" or not hasattr(adapter, "print_output"):
            return await adapter.run_once()

        previous = getattr(adapter, "print_output")
        setattr(adapter, "print_output", False)
        try:
            return await adapter.run_once()
        finally:
            setattr(adapter, "print_output", previous)

    def _publish_adapter_results(self, adapter_name: str, results: list[Any]) -> int:
        """Publish Event results returned by an adapter."""

        event_count = 0
        for result in results:
            if isinstance(result, Event):
                self.event_bus.publish(result)
                event_count += 1
        return event_count

    async def _publish_final_control_snapshot(self) -> None:
        """Let ControlCenter emit a final cycle snapshot after parallel workers finish."""

        adapter = self._control_adapter()
        if adapter is None:
            return
        try:
            results = await adapter.run_once()
        except Exception as exc:
            self.shared_state.update_service(
                adapter.name,
                "ERROR",
                {"error": str(exc)},
            )
            self.event_bus.publish(
                Event(
                    topic="service.error",
                    source=adapter.name,
                    payload={"error": str(exc)},
                )
            )
            return
        event_count = self._publish_adapter_results(adapter.name, results)
        self.shared_state.update_service(
            adapter.name,
            "OK",
            {"results": len(results), "events": event_count, "final_snapshot": True},
        )

    def _control_adapter(self) -> ServiceAdapter | None:
        """Return the configured ControlCenter adapter when present."""

        for adapter in self.adapters:
            if adapter.name == "control_center":
                return adapter
        return None

    def _record_event(self, event: Event) -> None:
        """Record latest event metadata without persisting full payload history yet."""

        self.shared_state.set_value(
            "last_event",
            {
                "topic": event.topic,
                "source": event.source,
                "created_at": event.created_at,
            },
        )

    def _sync_error_journal_health(self) -> None:
        """Project journal health into shared state without exposing local paths."""

        if self.error_journal is None:
            return
        health = self.error_journal.health()
        status = "OK" if health.get("healthy") else "ERROR"
        self.shared_state.update_service(
            self.error_journal.name,
            status,
            {
                key: health.get(key)
                for key in ("running", "healthy", "events_recorded", "unique_errors", "failed_writes", "last_error")
            },
        )

    def _default_adapters(self) -> list[ServiceAdapter]:
        """Return safe placeholders for Phase 3 ground-system validation."""

        verification_policy = StockShadowVerificationPolicy(
            horizon_seconds=self.config.stock_shadow_verification_horizon_seconds,
            neutral_band_percent=self.config.stock_shadow_verification_neutral_band_percent,
        )
        verification_fingerprint = configuration_fingerprint(
            {
                "stock_data_minimum_candles": self.config.stock_data_minimum_candles,
                "stock_data_full_warmup_candles": self.config.stock_data_full_warmup_candles,
                "stock_data_maximum_candle_age_seconds": self.config.stock_data_maximum_candle_age_seconds,
                "stock_data_maximum_quote_age_seconds": self.config.stock_data_maximum_quote_age_seconds,
                "stock_data_maximum_future_skew_seconds": self.config.stock_data_maximum_future_skew_seconds,
                "stock_data_maximum_entry_deviation_percent": self.config.stock_data_maximum_entry_deviation_percent,
                "stock_shadow_long_bullish_score": self.config.stock_shadow_long_bullish_score,
                "stock_shadow_short_bullish_score": self.config.stock_shadow_short_bullish_score,
                "stock_shadow_risk_atr_multiplier": self.config.stock_shadow_risk_atr_multiplier,
                "stock_shadow_risk_minimum_distance_percent": self.config.stock_shadow_risk_minimum_distance_percent,
                "stock_shadow_risk_targets": [
                    self.config.stock_shadow_risk_target_1_multiple,
                    self.config.stock_shadow_risk_target_2_multiple,
                    self.config.stock_shadow_risk_target_3_multiple,
                ],
                "stock_shadow_risk_price_decimals": self.config.stock_shadow_risk_price_decimals,
                "verification_observer_version": verification_policy.observer_version,
                "verification_horizon_seconds": verification_policy.horizon_seconds,
                "verification_neutral_band_percent": verification_policy.neutral_band_percent,
            }
        )
        regime_observer = (
            MarketRegimeObserverAdapter(
                self.event_bus,
                ledger_file=self.config.market_regime_file,
                ledger_rotation_bytes=self.config.market_regime_rotation_bytes,
                ledger_max_archives=self.config.market_regime_max_archives,
                queue_capacity=self.config.market_regime_queue_capacity,
                batch_size=self.config.market_regime_batch_size,
                flush_interval_seconds=self.config.market_regime_flush_interval_seconds,
            )
            if self.config.market_regime_observer_enabled
            else None
        )
        return [
            *([regime_observer] if regime_observer is not None else []),
            CryptoAdapter(
                self.event_bus,
                self.config.crypto_project_path,
                symbols=self.config.crypto_symbols,
                timeframe=self.config.crypto_timeframe,
                candle_limit=self.config.crypto_candle_limit,
                test_mode=not self.config.live_crypto,
                live_price_display=self.config.crypto_live_price_display,
                regime_submitter=regime_observer.submit if regime_observer is not None else None,
            ),
            BrainAdapter(
                self.event_bus,
                self.config.brain_events_file,
                event_root=self.config.brain_events_dir,
                rotation_bytes=self.config.brain_event_rotation_bytes,
                day_warning_bytes=self.config.brain_event_day_warning_bytes,
            ),
            *(
                [
                    DecisionGateAuditAdapter(
                        self.event_bus,
                        policy=DecisionGatePolicy(
                            minimum_probability=self.config.decision_gate_minimum_probability,
                            minimum_confidence=self.config.decision_gate_minimum_confidence,
                            confidence_tolerance=self.config.decision_gate_confidence_tolerance,
                        ),
                        audit_file=self.config.decision_gate_audit_file,
                        ledger_rotation_bytes=self.config.decision_gate_audit_rotation_bytes,
                        ledger_max_archives=self.config.decision_gate_audit_max_archives,
                    )
                ]
                if self.config.decision_gate_observer_enabled
                else []
            ),
            DecisionSignalAdapter(
                self.event_bus,
                decisions_file=self.config.platform_decisions_file,
                signals_file=self.config.platform_signals_file,
                ledger_rotation_bytes=self.config.jsonl_ledger_rotation_bytes,
            ),
            OutcomeTracker(
                self.event_bus,
                open_trades_file=self.config.simulated_open_trades_file,
                outcomes_file=self.config.trade_outcomes_file,
                evaluation_horizon_seconds=self.config.simulated_outcome_horizon_seconds,
                ledger_rotation_bytes=self.config.jsonl_ledger_rotation_bytes,
            ),
            *(
                [
                    StockShadowVerificationAdapter(
                        self.event_bus,
                        ledger_file=self.config.stock_shadow_verification_file,
                        policy=verification_policy,
                        config_fingerprint=verification_fingerprint,
                        ledger_rotation_bytes=self.config.stock_shadow_verification_rotation_bytes,
                        ledger_max_archives=self.config.stock_shadow_verification_max_archives,
                    )
                ]
                if self.config.stock_shadow_verification_enabled
                else []
            ),
            *(
                [
                    NeuroBrainReceiverAdapter(
                        self.event_bus,
                        inbox_file=self.config.neurobrain_inbox_file,
                        status_file=self.config.neurobrain_status_file,
                        ledger_rotation_bytes=self.config.jsonl_ledger_rotation_bytes,
                        queue_capacity=self.config.neurobrain_queue_capacity,
                        batch_size=self.config.neurobrain_batch_size,
                        flush_interval_seconds=self.config.neurobrain_flush_interval_seconds,
                    )
                ]
                if self.config.neurobrain_receiver_enabled
                else []
            ),
            CryptoTradeTracker(
                self.event_bus,
                active_file=self.config.data_dir / "crypto_active_trades.json",
                history_file=self.config.data_dir / "crypto_trade_history.jsonl",
            ),
            StockAdapter(
                self.event_bus,
                self.config.stock_project_path,
                test_mode=self.config.stock_test_mode,
                live_price_display=self.config.stock_live_price_display,
                stock_data_observer_enabled=self.config.stock_data_observer_enabled,
                daily_candle_limit=self.config.stock_daily_candle_limit,
                candle_cache_ttl_seconds=self.config.stock_candle_cache_ttl_seconds,
                stock_data_policy=StockDataPolicy(
                    minimum_candles=self.config.stock_data_minimum_candles,
                    full_warmup_candles=self.config.stock_data_full_warmup_candles,
                    maximum_candle_age_seconds=self.config.stock_data_maximum_candle_age_seconds,
                    maximum_quote_age_seconds=self.config.stock_data_maximum_quote_age_seconds,
                    maximum_future_skew_seconds=self.config.stock_data_maximum_future_skew_seconds,
                    maximum_entry_deviation_percent=self.config.stock_data_maximum_entry_deviation_percent,
                ),
                stock_shadow_policy=StockShadowPolicy(
                    minimum_candles=self.config.stock_data_minimum_candles,
                    full_warmup_candles=self.config.stock_data_full_warmup_candles,
                    long_bullish_score=self.config.stock_shadow_long_bullish_score,
                    short_bullish_score=self.config.stock_shadow_short_bullish_score,
                ),
                stock_shadow_risk_policy=StockShadowRiskPolicy(
                    atr_multiplier=self.config.stock_shadow_risk_atr_multiplier,
                    minimum_distance_percent=self.config.stock_shadow_risk_minimum_distance_percent,
                    take_profit_multiples=(
                        self.config.stock_shadow_risk_target_1_multiple,
                        self.config.stock_shadow_risk_target_2_multiple,
                        self.config.stock_shadow_risk_target_3_multiple,
                    ),
                    price_decimals=self.config.stock_shadow_risk_price_decimals,
                ),
                cycle_timeout_seconds=self.config.adapter_cycle_timeout_seconds,
                nonblocking_cycle=True,
                regime_submitter=regime_observer.submit if regime_observer is not None else None,
            ),
            *(
                [CommodityAdapter(self.event_bus, symbols=list(self.config.commodity_symbols))]
                if self.config.commodities_enabled
                else []
            ),
            TelegramAdapter(self.event_bus, **self.config.telegram_settings()),
            *(
                [ControlCenterAdapter(self.event_bus, self.shared_state)]
                if self.config.control_center_enabled
                else []
            ),
        ]
