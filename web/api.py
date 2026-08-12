"""Local web server for the PandorickKi ControlCenter."""

from __future__ import annotations

import asyncio
import ctypes
import json
import os
import time
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any

from config import PlatformConfig
from event_bus import Event
from learning_graph.graph_service import LearningGraphService
from learning_graph.knowledge_graph_service import KnowledgeGraphService
from orchestrator import Orchestrator
from web.learning_report_service import LearningReportPaths, LearningReportService
from web.rick_api_service import RickApiService
from web.routes import RouteMixin
from web.schemas import WebControlState
from web.statistics_service import (
    STATISTICS_UPDATED,
    AnalysisStatisticsService,
    StorageStatisticsService,
)
from web.websocket_manager import WebSocketManager


LIVE_WEB_TOPICS = {
    "CRYPTO_ANALYSIS_FINISHED",
    "STOCK_ANALYSIS_FINISHED",
    "DECISION_CREATED",
    "SIGNAL_CREATED",
    "AI_LEARNING_UPDATED",
    "SERVICE_HEARTBEAT",
    "SERVICE_STATUS_CHANGED",
    "SYSTEM_ERROR",
    "CRYPTO_SERVICE_HEARTBEAT",
    "STOCK_SERVICE_HEARTBEAT",
    "BRAIN_SERVICE_HEARTBEAT",
    "TELEGRAM_SERVICE_HEARTBEAT",
    "BRAIN_DECISION_RECEIVED",
    "TELEGRAM_MESSAGE_READY",
    "TELEGRAM_DRY_RUN_RECORDED",
    "TELEGRAM_MESSAGE_SENT",
    "TELEGRAM_SERVICE_ERROR",
    "CONTROL_STATUS_UPDATED",
    "SIMULATED_TRADE_OPENED",
    "SIMULATED_TRADE_UPDATED",
    "SIMULATED_TRADE_CLOSED",
    "STOCK_SHADOW_VERIFICATION_UPDATED",
    "STOCK_SHADOW_VERIFICATION_HEARTBEAT",
    "MARKET_REGIME_OBSERVED",
    "MARKET_REGIME_HEARTBEAT",
    STATISTICS_UPDATED,
}

LEARNING_GRAPH_SOURCE_TOPICS = {
    "CRYPTO_ANALYSIS_FINISHED",
    "STOCK_ANALYSIS_FINISHED",
    "DECISION_CREATED",
    "SIGNAL_CREATED",
    "AI_LEARNING_UPDATED",
    "BRAIN_DECISION_RECEIVED",
}


class WebControlServer:
    """Non-blocking local HTTP/WebSocket server around an Orchestrator."""

    def __init__(
        self,
        orchestrator: Orchestrator,
        *,
        host: str = "127.0.0.1",
        port: int = 8000,
        command_log_file: Path | None = None,
        warm_learning_report: bool = True,
    ) -> None:
        self.orchestrator = orchestrator
        self.host = host
        self.port = port
        self.command_log_file = command_log_file or orchestrator.config.data_dir / "web_control_commands.jsonl"
        self.warm_learning_report = warm_learning_report
        self.websocket_manager = WebSocketManager()
        self.control_state = WebControlState()
        self.analysis_statistics = AnalysisStatisticsService(
            orchestrator.config.project_root / "storage" / "statistics" / "system_statistics.json"
        )
        self.storage_statistics = StorageStatisticsService(
            orchestrator.config,
            scan_interval_seconds=orchestrator.config.storage_scan_interval_seconds,
        )
        self.learning_graph = LearningGraphService(
            brain_events_file=orchestrator.config.brain_events_file,
            brain_events_dir=orchestrator.config.brain_events_dir,
            project_root=orchestrator.config.project_root,
            shared_state_file=orchestrator.config.shared_state_file,
            stock_project_path=orchestrator.config.stock_project_path,
            crypto_project_path=orchestrator.config.crypto_project_path,
        )
        self.knowledge_graph = KnowledgeGraphService(
            brain_events_file=orchestrator.config.brain_events_file,
            brain_events_dir=orchestrator.config.brain_events_dir,
            project_root=orchestrator.config.project_root,
            shared_state_file=orchestrator.config.shared_state_file,
            stock_project_path=orchestrator.config.stock_project_path,
            crypto_project_path=orchestrator.config.crypto_project_path,
        )
        self.learning_report = LearningReportService(LearningReportPaths.from_config(orchestrator.config))
        self.rick_api = RickApiService(
            self,
            audit_log_file=orchestrator.config.rick_api_audit_log_file,
        )
        self._server: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None
        self._storage_scan_task: asyncio.Task | None = None
        self._running = False
        self._last_error: dict[str, Any] | None = None
        self._event_count = 0
        self._started_at = time.monotonic()
        self._last_cpu_probe: tuple[float, float] | None = None
        self._last_live_broadcast_at = 0.0
        self._last_statistics_broadcast_at = 0.0
        self._live_broadcast_interval_seconds = 0.5
        self._statistics_broadcast_interval_seconds = 1.0

    def start(self) -> None:
        """Start the local web server on a background thread."""

        if self._running:
            return

        self.analysis_statistics.start(self.orchestrator.config)
        app = self

        class Handler(RouteMixin, BaseHTTPRequestHandler):
            pass

        class LocalHTTPServer(ThreadingHTTPServer):
            daemon_threads = True
            web_running = True

        server = LocalHTTPServer((self.host, self.port), Handler)
        server.app = app  # type: ignore[attr-defined]
        self._server = server
        self.port = int(server.server_address[1])
        self.orchestrator.event_bus.subscribe("*", self._handle_event)
        self._running = True
        self._thread = Thread(target=server.serve_forever, name="pandorickki-web", daemon=True)
        self._thread.start()
        if self.warm_learning_report:
            self.learning_report.report_cached()
        self._start_storage_scan_task()

    def stop(self) -> None:
        """Stop web server, unsubscribe and close browser sockets."""

        if not self._running:
            return
        self._running = False
        self.orchestrator.event_bus.unsubscribe("*", self._handle_event)
        self.websocket_manager.close_all()
        if self._server is not None:
            self._server.web_running = False  # type: ignore[attr-defined]
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self.storage_statistics.close()
        self._server = None
        self._thread = None
        if self._storage_scan_task is not None:
            self._storage_scan_task.cancel()
            self._storage_scan_task = None

    @property
    def url(self) -> str:
        """Return the browser URL."""

        return f"http://{self.host}:{self.port}"

    def is_paused(self) -> bool:
        """Return whether orchestration should pause."""

        return self.control_state.is_paused()

    def should_stop(self) -> bool:
        """Return whether orchestration should stop."""

        return self.control_state.should_stop()

    def take_restart_request(self) -> bool:
        """Consume one browser-requested in-process platform restart."""

        return self.control_state.take_restart_request()

    def is_local_address(self, address: str) -> bool:
        """Allow only local browser/API access."""

        return address in {"127.0.0.1", "::1", "localhost"}

    def apply_control(self, action: str, source: str) -> dict[str, Any]:
        """Validate, apply and log one safe control command."""

        command = self.control_state.apply(action, source)
        self._log_command(command)
        self.orchestrator.event_bus.publish(
            Event(
                topic="CONTROL_COMMAND_APPLIED",
                source="web_control_center",
                payload={
                    "action": action,
                    "command": command,
                },
            )
        )
        self.websocket_manager.broadcast_json(
            {"type": "control", "command": command, "snapshot": self.snapshot()}
        )
        return command

    def snapshot(self) -> dict[str, Any]:
        """Build a browser-safe snapshot from ControlCenter and SharedState."""

        control = self.orchestrator._control_adapter()
        if control is not None and hasattr(control, "get_status"):
            base = control.get_status()
        else:
            shared = self.orchestrator.shared_state.to_dict()
            base = {
                "running": True,
                "platform_health": shared.get("values", {}).get("last_health", {}).get("status", "PENDING"),
                "runtime_seconds": 0,
                "services": shared.get("services", {}),
                "service_status": {
                    name: data.get("status", "UNKNOWN")
                    for name, data in shared.get("services", {}).items()
                },
                "service_heartbeats": {},
                "last_crypto_price": {},
                "last_crypto_analysis": {},
                "last_stock_price": {},
                "last_stock_analysis": {},
                "last_commodity_price": {},
                "last_commodity_analysis": {},
                "last_brain_decision": {},
                "last_learning_update": {},
                "telegram_status": {},
                "error_count": 0,
                "last_update_at": None,
                "events_received": 0,
                "latest_events": [],
                "event_bus_queue_size": self.orchestrator.event_bus.queue_size(),
            }

        self._apply_stale_heartbeats(base)
        base["shadow_verification"] = self.api_shadow_verification_summary(days=7, limit=50)
        base["market_regime"] = self.api_market_regime_current()
        base["web"] = {
            "running": self._running,
            "url": self.url,
            "websocket_clients": self.websocket_manager.count(),
            "events_broadcast": self._event_count,
            "event_bus": self.orchestrator.event_bus.stats(),
            "control": self.control_state.snapshot(),
        }
        base["statistics"] = self.api_statistics()
        base["last_error"] = self._last_error
        return self._sanitize(base)

    def _apply_stale_heartbeats(self, snapshot: dict[str, Any]) -> None:
        """Mark services with an old known heartbeat as STALE in API snapshots."""

        threshold = max(float(self.orchestrator.config.service_heartbeat_stale_seconds), 1.0)
        now = datetime.now(UTC)
        statuses = dict(snapshot.get("service_status") or {})
        heartbeats = snapshot.get("service_heartbeats") or {}
        ages: dict[str, float] = {}
        stale_services: list[str] = []
        for name, value in heartbeats.items():
            try:
                heartbeat = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                if heartbeat.tzinfo is None:
                    heartbeat = heartbeat.replace(tzinfo=UTC)
                age = max(0.0, (now - heartbeat.astimezone(UTC)).total_seconds())
            except (TypeError, ValueError):
                continue
            ages[str(name)] = round(age, 2)
            status = str(statuses.get(name, "UNKNOWN")).upper()
            if age > threshold and status not in {"ERROR", "STOPPED", "DISABLED"}:
                statuses[name] = "STALE"
                stale_services.append(str(name))
        snapshot["service_status"] = statuses
        snapshot["service_heartbeat_age_seconds"] = ages
        snapshot["service_heartbeat_stale_after_seconds"] = threshold
        snapshot["stale_services"] = sorted(stale_services)

    def api_health(self) -> dict[str, Any]:
        """Return compact web/platform health."""

        snapshot = self.snapshot()
        return {
            "status": snapshot.get("platform_health", "PENDING"),
            "web_running": self._running,
            "websocket_active": True,
            "statistics_active": True,
            "last_update_at": snapshot.get("last_update_at"),
        }

    def api_status(self) -> dict[str, Any]:
        """Return full safe status."""

        return self.snapshot()

    def api_services(self) -> dict[str, Any]:
        """Return service states."""

        snapshot = self.snapshot()
        return {
            "services": snapshot.get("services", {}),
            "service_status": snapshot.get("service_status", {}),
            "service_heartbeats": snapshot.get("service_heartbeats", {}),
            "telegram": snapshot.get("telegram_status", {}),
        }

    def api_crypto(self) -> dict[str, Any]:
        """Return latest crypto data."""

        snapshot = self.snapshot()
        return {
            "prices": snapshot.get("last_crypto_price", {}),
            "analyses": snapshot.get("last_crypto_analysis", {}),
        }

    def api_stocks(self) -> dict[str, Any]:
        """Return latest stock data."""

        snapshot = self.snapshot()
        return {
            "prices": snapshot.get("last_stock_price", {}),
            "analyses": snapshot.get("last_stock_analysis", {}),
        }

    def api_shadow_verification_summary(self, *, days: int = 7, limit: int = 50) -> dict[str, Any]:
        """Return the compact stock-only observer summary."""

        adapter = self._shadow_verification_adapter()
        if adapter is not None and hasattr(adapter, "snapshot"):
            result = adapter.snapshot(days=days, limit=limit)
            result["enabled"] = True
            return result
        return {
            "schema_name": "pandorickki.stock-shadow-verification-summary",
            "schema_version": 1,
            "mode": "OBSERVER_ONLY",
            "asset_scope": "stock",
            "enabled": False,
            "days": min(max(int(days), 1), 365),
            "summary": {
                "shadow_cases": 0,
                "comparable_cases": 0,
                "agreement": 0,
                "disagreement": 0,
                "agreement_rate_percent": None,
                "disagreement_rate_percent": None,
                "gate_blocks": 0,
                "data_quality": {"OK": 0, "DEGRADED": 0, "REJECTED": 0},
                "shadow_gate": {"PASS": 0, "BLOCK": 0, "HOLD": 0, "UNKNOWN": 0},
                "outcomes": {"PENDING": 0, "COMPLETED": 0, "UNKNOWN": 0},
            },
            "disagreement_outcome_matrix": [],
            "records": [],
            "ready_for_telegram": False,
            "order_execution_allowed": False,
        }

    def api_shadow_verification_detail(self, verification_id: str) -> dict[str, Any]:
        """Return one read-only stock verification record."""

        adapter = self._shadow_verification_adapter()
        if adapter is None or not hasattr(adapter, "detail"):
            raise KeyError(verification_id)
        record = adapter.detail(verification_id)
        if record is None:
            raise KeyError(verification_id)
        return {
            "mode": "OBSERVER_ONLY",
            "asset_scope": "stock",
            "record": record,
            "ready_for_telegram": False,
            "order_execution_allowed": False,
        }

    def api_market_regime_current(
        self, *, asset_type: str | None = None, symbol: str | None = None
    ) -> dict[str, Any]:
        adapter = self._market_regime_adapter()
        if adapter is None:
            return {
                "schema_name": "pandorickki.market-regime-current",
                "schema_version": 1,
                "enabled": False,
                "items": [],
                "count": 0,
                "read_only": True,
            }
        result = adapter.current(asset_type=asset_type, symbol=symbol)
        result["enabled"] = True
        return result

    def api_market_regime_history(
        self,
        *,
        asset_type: str | None = None,
        symbol: str | None = None,
        days: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        adapter = self._market_regime_adapter()
        if adapter is None:
            return {
                "schema_name": "pandorickki.market-regime-history",
                "schema_version": 1,
                "enabled": False,
                "items": [],
                "pagination": {"offset": 0, "limit": max(1, min(limit, 500)), "returned": 0, "total": 0, "has_more": False},
                "read_only": True,
            }
        result = adapter.history(
            asset_type=asset_type,
            symbol=symbol,
            days=days,
            limit=limit,
            offset=offset,
        )
        result["enabled"] = True
        return result

    def api_market_regime_statistics(
        self, *, asset_type: str | None = None, symbol: str | None = None, days: int | None = None
    ) -> dict[str, Any]:
        adapter = self._market_regime_adapter()
        if adapter is None:
            return {
                "schema_name": "pandorickki.market-regime-statistics",
                "schema_version": 1,
                "enabled": False,
                "count": 0,
                "trend": {},
                "volatility": {},
                "phase": {},
                "quality": {},
                "common_combinations": [],
                "by_asset_type": {},
                "legacy_labels_included": False,
                "read_only": True,
            }
        result = adapter.statistics(asset_type=asset_type, symbol=symbol, days=days)
        result["enabled"] = True
        return result

    def api_commodities(self) -> dict[str, Any]:
        """Return latest commodity data."""

        snapshot = self.snapshot()
        return {
            "prices": snapshot.get("last_commodity_price", {}),
            "analyses": snapshot.get("last_commodity_analysis", {}),
        }

    def api_brain(self) -> dict[str, Any]:
        """Return latest brain data."""

        snapshot = self.snapshot()
        return {
            "last_decision": snapshot.get("last_brain_decision", {}),
            "last_learning_update": snapshot.get("last_learning_update", {}),
        }

    def api_signals(self) -> dict[str, Any]:
        """Return recent signal-like events."""

        events = [
            event
            for event in self.snapshot().get("latest_events", [])
            if "SIGNAL" in str(event.get("topic", "")) or "DECISION" in str(event.get("topic", ""))
        ]
        return {"signals": events[-20:]}

    def api_errors(self) -> dict[str, Any]:
        """Return error counters and latest error."""

        snapshot = self.snapshot()
        return {
            "error_count": snapshot.get("error_count", 0),
            "last_error": snapshot.get("last_error"),
            "error_events": [
                event
                for event in snapshot.get("latest_events", [])
                if "ERROR" in str(event.get("topic", "")).upper()
            ],
        }

    def api_events(self) -> dict[str, Any]:
        """Return event counters and queue size."""

        snapshot = self.snapshot()
        bus_stats = self.orchestrator.event_bus.stats()
        return {
            "events_received": snapshot.get("events_received", 0),
            "event_counts": snapshot.get("event_counts", {}),
            "latest_events": snapshot.get("latest_events", []),
            "queue_size": snapshot.get("event_bus_queue_size", 0),
            "event_bus": bus_stats,
            "discarded_events": bus_stats["discarded_count"],
        }

    def api_public_config(self) -> dict[str, Any]:
        """Return only non-secret public configuration."""

        config = self.orchestrator.config
        return {
            "project_root": str(config.project_root),
            "crypto_symbols": list(config.crypto_symbols),
            "crypto_timeframe": config.crypto_timeframe,
            "cycle_interval": config.cycle_interval,
            "control_center_enabled": config.control_center_enabled,
            "service_heartbeat_stale_seconds": config.service_heartbeat_stale_seconds,
            "telegram_enabled": config.telegram_enabled,
            "telegram_dry_run": config.telegram_dry_run,
            "live_crypto": config.live_crypto,
            "web_host": self.host,
            "web_port": self.port,
            "storage_scan_interval_seconds": config.storage_scan_interval_seconds,
            "stock_shadow_verification_enabled": config.stock_shadow_verification_enabled,
            "market_regime_observer_enabled": config.market_regime_observer_enabled,
        }

    def api_statistics(self) -> dict[str, Any]:
        """Return combined analysis and storage statistics."""

        analyses = self.analysis_statistics.snapshot()
        storage = self.storage_statistics.snapshot()
        developer = dict(analyses.get("developer", {}))
        developer.update(
            {
                "system_runtime_seconds": round(time.monotonic() - self._started_at, 2),
                "cpu_percent": self._process_cpu_percent(),
                "ram_mb": self._process_ram_mb(),
            }
        )
        trading = dict(analyses.get("trading", {}))
        trading["active_markets"] = self._active_market_count()
        return {
            "analyses": {
                "total": analyses["total_analyses"],
                "crypto": analyses["crypto_analyses"],
                "stocks": analyses["stock_analyses"],
                "brain_evaluations": analyses["brain_evaluations"],
                "decisions": analyses["decisions_created"],
                "signals": analyses["signals_created"],
                "long": analyses["long_count"],
                "short": analyses["short_count"],
                "hold": analyses["hold_count"],
                "errors": analyses["error_count"],
                "duplicate_events_ignored": analyses["duplicate_events_ignored"],
                "telegram_messages_sent": analyses["telegram_messages_sent"],
                "learning_updates": analyses["learning_updates"],
                "reconstructed": analyses["reconstructed"],
                "reconstructed_at": analyses["reconstructed_at"],
                "last_update_at": analyses["last_update_at"],
            },
            "developer": developer,
            "trading": trading,
            "errors_detail": analyses.get("errors_detail", {}),
            "storage": {
                "total_files": storage["total_files"],
                "total_records": storage["total_records"],
                "total_size_bytes": storage["total_size_bytes"],
                "total_size_human": storage["total_size_human"],
                "totals_status": storage.get("totals_status"),
                "physical_total_files": storage.get("physical_total_files"),
                "physical_total_records": storage.get("physical_total_records"),
                "physical_total_size_bytes": storage.get("physical_total_size_bytes"),
                "physical_total_size_human": storage.get("physical_total_size_human"),
                "logical_total_files": storage.get("logical_total_files"),
                "logical_total_records": storage.get("logical_total_records"),
                "logical_total_size_bytes": storage.get("logical_total_size_bytes"),
                "logical_total_size_human": storage.get("logical_total_size_human"),
                "overlapping_file_references": storage.get("overlapping_file_references"),
                "last_scan": storage["last_scan"],
                "scan_interval_seconds": storage["scan_interval_seconds"],
            },
        }

    def api_statistics_analyses(self) -> dict[str, Any]:
        """Return analysis counters."""

        return {"analyses": self.api_statistics()["analyses"]}

    def api_statistics_storage(self) -> dict[str, Any]:
        """Return cached storage statistics."""

        return {"storage": self.storage_statistics.snapshot()}

    def api_statistics_storage_folder(self, folder_name: str) -> dict[str, Any]:
        """Return one storage folder by name."""

        folder = self.storage_statistics.folder(folder_name)
        if folder is None:
            raise KeyError(folder_name)
        return {"folder": folder}

    def api_learning_graph(self) -> dict[str, Any]:
        """Return the full public read-only learning graph."""

        return {"learning_graph": self.learning_graph.graph()}

    def api_learning_graph_nodes(self) -> dict[str, Any]:
        """Return public learning graph nodes."""

        return {"nodes": self.learning_graph.nodes()}

    def api_learning_graph_edges(self) -> dict[str, Any]:
        """Return public learning graph edges."""

        return {"edges": self.learning_graph.edges()}

    def api_learning_graph_stats(self) -> dict[str, Any]:
        """Return public learning graph statistics."""

        return {"stats": self.learning_graph.stats()}

    def api_learning_graph_recent(self) -> dict[str, Any]:
        """Return recent public learning graph nodes."""

        return {"recent": self.learning_graph.recent()}

    def api_learning_graph_node(self, node_id: str) -> dict[str, Any]:
        """Return one public learning graph node."""

        node = self.learning_graph.node(node_id)
        if node is None:
            raise KeyError(node_id)
        return {"node": node}

    def api_knowledge_graph_overview(self) -> dict[str, Any]:
        """Return the interactive public Knowledge Graph overview."""

        return self.knowledge_graph.overview()

    def api_knowledge_graph_full(self, min_edge_weight: float = 0.0) -> dict[str, Any]:
        """Return the developer full Knowledge Graph projection."""

        return self.knowledge_graph.full(min_edge_weight=min_edge_weight)

    def api_knowledge_graph_cluster(self, cluster_id: str) -> dict[str, Any]:
        """Return one public Knowledge Graph cluster."""

        result = self.knowledge_graph.cluster(cluster_id)
        if result["node_count"] <= 0:
            raise KeyError(cluster_id)
        return result

    def api_knowledge_graph_node(self, node_id: str) -> dict[str, Any]:
        """Return one public Knowledge Graph node with direct neighbors."""

        result = self.knowledge_graph.node(node_id)
        if result is None:
            raise KeyError(node_id)
        return result

    def api_knowledge_graph_search(self, query: str) -> dict[str, Any]:
        """Search public Knowledge Graph nodes."""

        return self.knowledge_graph.search(query)

    def api_knowledge_graph_changes(self, since_version: int | None = None) -> dict[str, Any]:
        """Return public Knowledge Graph changes."""

        return self.knowledge_graph.changes(since_version=since_version)

    def api_learning_report(self) -> dict[str, Any]:
        """Return objective read-only learning performance metrics."""

        return {"learning_report": self.learning_report.report_cached()}

    def refresh_storage_statistics(self) -> dict[str, Any]:
        """Queue a storage scan without blocking the HTTP request."""

        result = self.storage_statistics.start_scan(self._storage_scan_completed)
        return {"ok": True, **result}

    def _handle_event(self, event: Event) -> None:
        """Broadcast live events to connected browsers."""

        try:
            if event.topic in LEARNING_GRAPH_SOURCE_TOPICS:
                self.learning_graph.invalidate_cache()
                self.knowledge_graph.invalidate_cache()
            stats_changed = self.analysis_statistics.apply_event(event)
            if stats_changed:
                self._broadcast_statistics_update()
            if event.topic not in LIVE_WEB_TOPICS and not event.topic.endswith(("HEARTBEAT", "ERROR")):
                return
            now = time.monotonic()
            throttle_event = event.topic.endswith("HEARTBEAT") or event.topic.endswith("MARKET_DATA_UPDATED")
            if throttle_event and now - self._last_live_broadcast_at < self._live_broadcast_interval_seconds:
                return
            self._last_live_broadcast_at = now
            self._event_count += 1
            self.websocket_manager.broadcast_json(
                {
                    "type": "event",
                    "event": {
                        "topic": event.topic,
                        "source": event.source,
                        "created_at": event.created_at,
                    },
                    "snapshot": self.live_event_snapshot(),
                }
            )
        except Exception as exc:
            self._last_error = {
                "error": str(exc),
                "created_at": datetime.now(UTC).isoformat(),
            }

    def _broadcast_statistics_update(self) -> None:
        """Publish and broadcast current statistics."""

        now = time.monotonic()
        if now - self._last_statistics_broadcast_at < self._statistics_broadcast_interval_seconds:
            return
        self._last_statistics_broadcast_at = now
        payload = self.api_statistics()
        self.websocket_manager.broadcast_json(
            {
                "type": "event",
                "event": {
                    "topic": STATISTICS_UPDATED,
                    "source": "web_statistics",
                    "created_at": datetime.now(UTC).isoformat(),
                },
                "payload": payload,
                "snapshot": self.live_event_snapshot(),
            }
        )

    def _active_market_count(self) -> int:
        """Return how many market groups currently have visible data."""

        snapshot = self.snapshot_without_statistics()
        active = 0
        if snapshot.get("last_crypto_analysis") or snapshot.get("last_crypto_price"):
            active += 1
        if snapshot.get("last_stock_analysis") or snapshot.get("last_stock_price"):
            active += 1
        return active

    def snapshot_without_statistics(self) -> dict[str, Any]:
        """Build a lightweight snapshot without recursively attaching statistics."""

        control = self.orchestrator._control_adapter()
        if control is not None and hasattr(control, "get_status"):
            snapshot = control.get_status()
            self._apply_stale_heartbeats(snapshot)
            snapshot["shadow_verification"] = self.api_shadow_verification_summary(days=7, limit=50)
            snapshot["market_regime"] = self.api_market_regime_current()
            return self._sanitize(snapshot)
        shared = self.orchestrator.shared_state.to_dict()
        snapshot = {
            "last_crypto_price": shared.get("values", {}).get("last_crypto_price", {}),
            "last_crypto_analysis": shared.get("values", {}).get("last_crypto_analysis", {}),
            "last_stock_price": shared.get("values", {}).get("last_stock_price", {}),
            "last_stock_analysis": shared.get("values", {}).get("last_stock_analysis", {}),
            "shadow_verification": self.api_shadow_verification_summary(days=7, limit=50),
            "market_regime": self.api_market_regime_current(),
        }
        return self._sanitize(snapshot)

    def _shadow_verification_adapter(self) -> Any | None:
        """Return the optional stock-only verification observer."""

        for adapter in self.orchestrator.adapters:
            if getattr(adapter, "name", None) == "stock_shadow_verification":
                return adapter
        return None

    def _market_regime_adapter(self) -> Any | None:
        for adapter in self.orchestrator.adapters:
            if getattr(adapter, "name", None) == "market_regime_observer":
                return adapter
        return None

    def live_event_snapshot(self) -> dict[str, Any]:
        """Build a lightweight browser snapshot for high-frequency events."""

        snapshot = self.snapshot_without_statistics()
        snapshot["web"] = {
            "running": self._running,
            "url": self.url,
            "websocket_clients": self.websocket_manager.count(),
            "events_broadcast": self._event_count,
            "event_bus": self.orchestrator.event_bus.stats(),
            "control": self.control_state.snapshot(),
        }
        snapshot["last_error"] = self._last_error
        return self._sanitize(snapshot)

    def _process_cpu_percent(self) -> float | None:
        """Return approximate process CPU usage since the previous probe."""

        now = time.monotonic()
        cpu_now = time.process_time()
        if self._last_cpu_probe is None:
            self._last_cpu_probe = (now, cpu_now)
            return None
        previous_wall, previous_cpu = self._last_cpu_probe
        self._last_cpu_probe = (now, cpu_now)
        wall_delta = now - previous_wall
        if wall_delta <= 0:
            return None
        return round(max(0.0, (cpu_now - previous_cpu) / wall_delta * 100), 2)

    def _process_ram_mb(self) -> float | None:
        """Return process working set on Windows without adding a dependency."""

        if os.name != "nt":
            return None

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(ProcessMemoryCounters)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
        if not ok:
            return None
        return round(counters.WorkingSetSize / 1024 / 1024, 2)

    def _start_storage_scan_task(self) -> None:
        """Start periodic async storage scanning when an event loop is running."""

        if self.warm_learning_report:
            self.storage_statistics.start_scan(self._storage_scan_completed)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        self._storage_scan_task = loop.create_task(
            self._periodic_storage_scan(),
            name="pandorickki:storage_statistics_scan",
        )

    async def _periodic_storage_scan(self) -> None:
        """Refresh storage statistics periodically without blocking the loop."""

        while self._running:
            await asyncio.sleep(self.storage_statistics.scan_interval_seconds)
            if not self._running:
                break
            self.storage_statistics.start_scan(self._storage_scan_completed)

    def _storage_scan_completed(self, _storage: dict[str, Any]) -> None:
        """Broadcast a completed background scan while the web server is active."""

        if self._running:
            self._broadcast_statistics_update()

    def _log_command(self, command: dict[str, Any]) -> None:
        """Append one local control command to JSONL."""

        self.command_log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.command_log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(command, ensure_ascii=True) + "\n")

    def _sanitize(self, value: Any) -> Any:
        """Remove secret-looking values recursively before API output."""

        if isinstance(value, dict):
            clean: dict[str, Any] = {}
            for key, item in value.items():
                key_text = str(key).lower()
                if any(secret in key_text for secret in ("token", "password", "secret", "api_key")):
                    continue
                if key_text in {"raw_result", "features", "training_only", "steps", "candles"}:
                    continue
                clean[key] = self._sanitize(item)
            return clean
        if isinstance(value, list):
            return [self._sanitize(item) for item in value]
        return value


async def run_standalone() -> None:
    """Start the platform and local web server from ``python -m web.api``."""

    config = PlatformConfig.from_env().with_control_center(True)
    orchestrator = Orchestrator(config=config)
    server = WebControlServer(orchestrator)
    await orchestrator.start()
    server.start()
    print(f"PandorickKi Web ControlCenter: {server.url}")
    try:
        await orchestrator.run_continuous(
            cycle_interval=config.cycle_interval,
            live_control=False,
            final_control_snapshot=False,
            should_pause=server.is_paused,
            should_stop=server.should_stop,
        )
    finally:
        server.stop()
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(run_standalone())
