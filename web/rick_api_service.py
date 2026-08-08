"""Read-only versioned API facade for future Rick integration."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


RICK_API_VERSION = "v1"
SOURCE = "pandoriki"
SECRET_MARKERS = ("token", "password", "secret", "api_key", "authorization")


class RickApiService:
    """Build browser-safe read-only API responses from existing platform services."""

    def __init__(self, app: Any, *, audit_log_file: Path) -> None:
        self.app = app
        self.audit_log_file = audit_log_file

    def envelope(self, data: dict[str, Any], *, status: str = "ok", generated_at: str | None = None) -> dict[str, Any]:
        """Wrap data in the stable Rick response format."""

        timestamp = generated_at or datetime.now(UTC).isoformat()
        return {
            "status": status,
            "generated_at": timestamp,
            "data_age_seconds": self._age_seconds(timestamp),
            "source": SOURCE,
            "version": RICK_API_VERSION,
            "data": self._sanitize(data),
        }

    def audit(self, *, path: str, client: str, status: str) -> None:
        """Append one minimal Rick API access audit record."""

        record = {
            "created_at": datetime.now(UTC).isoformat(),
            "client": client,
            "path": path,
            "status": status,
        }
        try:
            self.audit_log_file.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_log_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=True) + "\n")
        except OSError:
            return

    def health(self) -> dict[str, Any]:
        """Return compact platform health for Rick."""

        health = self.app.api_health()
        status = self._status_from_health(health.get("status"))
        return self.envelope(health, status=status, generated_at=health.get("last_update_at"))

    def system_status(self) -> dict[str, Any]:
        """Return read-only system status without secrets or full local paths."""

        snapshot = self.app.snapshot()
        statistics = self.app.api_statistics()
        storage = statistics.get("storage", {})
        services = snapshot.get("services", {})
        latest_events = snapshot.get("latest_events", [])[-50:]
        data = {
            "pandoriki_status": snapshot.get("platform_health", "UNKNOWN"),
            "runtime_seconds": snapshot.get("runtime_seconds")
            or round(time.monotonic() - self.app._started_at, 2),
            "active_modules": sorted(snapshot.get("service_status", {}).keys()),
            "brain_status": snapshot.get("service_status", {}).get("brain"),
            "crypto_status": snapshot.get("service_status", {}).get("crypto"),
            "stock_status": snapshot.get("service_status", {}).get("stock"),
            "data_collectors": {
                "crypto": bool(snapshot.get("last_crypto_analysis") or snapshot.get("last_crypto_price")),
                "stocks": bool(snapshot.get("last_stock_analysis") or snapshot.get("last_stock_price")),
            },
            "database_status": {
                "storage_files": storage.get("total_files"),
                "storage_records": storage.get("total_records"),
                "storage_size_bytes": storage.get("total_size_bytes"),
                "storage_size_human": storage.get("total_size_human"),
                "physical_storage_files": storage.get("physical_total_files"),
                "physical_storage_records": storage.get("physical_total_records"),
                "physical_storage_size_bytes": storage.get("physical_total_size_bytes"),
                "logical_storage_file_references": storage.get("logical_total_files"),
                "overlapping_file_references": storage.get("overlapping_file_references"),
                "totals_status": storage.get("totals_status"),
                "last_scan": storage.get("last_scan"),
            },
            "last_analysis": self._last_analysis(snapshot),
            "last_successful_update": snapshot.get("last_update_at"),
            "warnings": self._warning_events(latest_events),
            "errors": self.app.api_errors(),
            "cpu_percent": statistics.get("developer", {}).get("cpu_percent"),
            "ram_mb": statistics.get("developer", {}).get("ram_mb"),
            "storage": storage,
            "event_bus_queue_size": snapshot.get("event_bus_queue_size"),
        }
        return self.envelope(data, status=self._status_from_health(data["pandoriki_status"]))

    def brain_status(self) -> dict[str, Any]:
        """Return public brain status without exposing internals."""

        snapshot = self.app.snapshot_without_statistics()
        brain = self.app.api_brain()
        decision = brain.get("last_decision") or {}
        learning_update = brain.get("last_learning_update") or {}
        data = {
            "last_decision": self._public_decision(decision),
            "symbol": decision.get("symbol"),
            "market": decision.get("market") or decision.get("market_type"),
            "direction": decision.get("direction") or decision.get("action"),
            "confidence": decision.get("confidence", decision.get("probability")),
            "main_factors": self._public_factors(decision),
            "brain_memory_size": self._brain_memory_size(),
            "last_learning_at": learning_update.get("updated_at") or learning_update.get("created_at"),
            "status": snapshot.get("service_status", {}).get("brain", "UNKNOWN"),
        }
        return self.envelope(data, status="ok" if decision or learning_update else "partial")

    def learning_summary(self) -> dict[str, Any]:
        """Return objective learning counters without claiming success from large counts."""

        statistics = self.app.api_statistics()
        graph = self.app.api_knowledge_graph_overview()
        analyses = statistics.get("analyses", {})
        data = {
            "brain_evaluations": analyses.get("brain_evaluations"),
            "learning_updates": analyses.get("learning_updates"),
            "decisions": analyses.get("decisions"),
            "signals": analyses.get("signals"),
            "crypto_analyses": analyses.get("crypto"),
            "stock_analyses": analyses.get("stocks"),
            "learning_graph_nodes": graph.get("node_count"),
            "learning_graph_edges": graph.get("edge_count"),
            "proven_learning_status": self._learning_status(analyses, graph),
            "data_quality": self._data_quality(statistics),
            "known_limitations": [
                "High counters prove activity, not trading success.",
                "Hit rate stays unavailable until verified trade outcomes exist.",
            ],
        }
        return self.envelope(data)

    def graph_overview(self) -> dict[str, Any]:
        """Return Rick-safe graph overview."""

        graph = self.app.api_knowledge_graph_overview()
        return self.envelope(self._public_graph(graph), generated_at=graph.get("generated_at"))

    def graph_cluster(self, cluster_id: str) -> dict[str, Any]:
        """Return Rick-safe graph cluster."""

        graph = self.app.api_knowledge_graph_cluster(cluster_id)
        return self.envelope(self._public_graph(graph), generated_at=graph.get("generated_at"))

    def graph_node(self, node_id: str) -> dict[str, Any]:
        """Return Rick-safe node neighborhood."""

        graph = self.app.api_knowledge_graph_node(node_id)
        data = self._public_graph(graph)
        if graph.get("node"):
            data["node"] = self._public_node(graph["node"])
        data["neighbors"] = [self._public_node(node) for node in graph.get("neighbors", [])]
        return self.envelope(data, generated_at=graph.get("generated_at"))

    def decisions_recent(self, *, limit: int = 20) -> dict[str, Any]:
        """Return recent final decision events only."""

        decisions: list[dict[str, Any]] = []
        for event in reversed(self.app.orchestrator.event_bus.history()):
            if event.topic != "DECISION_CREATED":
                continue
            payload = event.payload if isinstance(event.payload, dict) else {}
            data = payload.get("payload", payload)
            if not isinstance(data, dict):
                continue
            decisions.append(self._public_decision({**data, "created_at": event.created_at}))
            if len(decisions) >= limit:
                break
        return self.envelope({"decisions": decisions, "limit": limit}, status="ok" if decisions else "partial")

    def statistics(self) -> dict[str, Any]:
        """Return public statistics."""

        return self.envelope(self.app.api_statistics())

    def warnings(self) -> dict[str, Any]:
        """Return data warnings separated from service errors."""

        snapshot = self.app.snapshot()
        latest_events = snapshot.get("latest_events", [])[-100:]
        statistics = self.app.api_statistics()
        data = {
            "warnings": self._warning_events(latest_events),
            "warning_counts": statistics.get("errors_detail", {}).get("warnings", {}),
            "last_error": snapshot.get("last_error"),
        }
        return self.envelope(data, status="ok" if data["warnings"] else "partial")

    def _public_graph(self, graph: dict[str, Any]) -> dict[str, Any]:
        nodes = [self._public_node(node) for node in graph.get("nodes", [])]
        node_ids = {node["id"] for node in nodes}
        edges = [
            self._public_edge(edge)
            for edge in graph.get("edges", [])
            if edge.get("source") in node_ids and edge.get("target") in node_ids
        ]
        return {
            "mode": graph.get("mode"),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "diagnostics": {
                "duplicate_positions": graph.get("diagnostics", {}).get("duplicate_positions"),
                "overlapping_nodes": graph.get("diagnostics", {}).get("overlapping_nodes"),
                "isolated_nodes": graph.get("diagnostics", {}).get("isolated_nodes"),
            },
        }

    def _public_node(self, node: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": node.get("id"),
            "label": node.get("label"),
            "type": node.get("type"),
            "cluster": node.get("group"),
            "community": node.get("community"),
            "status": node.get("status"),
            "health": node.get("health"),
            "confidence": node.get("confidence"),
            "importance": node.get("importance"),
            "degree": node.get("degree"),
            "last_updated": node.get("last_updated"),
        }

    def _public_edge(self, edge: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": edge.get("id"),
            "source": edge.get("source"),
            "target": edge.get("target"),
            "relation": edge.get("relation"),
            "weight": edge.get("weight"),
            "confidence": edge.get("confidence"),
            "last_updated": edge.get("last_updated"),
        }

    def _public_decision(self, decision: dict[str, Any]) -> dict[str, Any]:
        return {
            "decision_id": decision.get("decision_id") or decision.get("id"),
            "created_at": decision.get("created_at") or decision.get("timestamp"),
            "market": decision.get("market") or decision.get("market_type"),
            "symbol": decision.get("symbol"),
            "direction": decision.get("direction") or decision.get("action"),
            "confidence": decision.get("confidence", decision.get("probability")),
            "entry_zone": decision.get("entry_zone"),
            "stop": decision.get("stop") or decision.get("stop_loss"),
            "targets": decision.get("targets") or decision.get("take_profits"),
            "public_reasoning_factors": self._public_factors(decision),
            "risks": decision.get("risks") or decision.get("risk_notes"),
            "data_quality": decision.get("data_quality"),
            "status": decision.get("status"),
            "valid_until": decision.get("valid_until"),
        }

    def _public_factors(self, data: dict[str, Any]) -> list[Any]:
        factors = data.get("main_factors") or data.get("factors") or data.get("reasoning_factors") or data.get("reasons")
        if isinstance(factors, list):
            return factors[:8]
        if isinstance(factors, dict):
            return list(factors.keys())[:8]
        return []

    def _last_analysis(self, snapshot: dict[str, Any]) -> dict[str, Any] | None:
        for market_key, market_name in (("last_crypto_analysis", "crypto"), ("last_stock_analysis", "stock")):
            analyses = snapshot.get(market_key)
            if isinstance(analyses, dict) and analyses:
                symbol, data = next(reversed(list(analyses.items())))
                if isinstance(data, dict):
                    return {
                        "market": market_name,
                        "symbol": data.get("symbol") or symbol,
                        "direction": data.get("direction") or data.get("action"),
                        "updated_at": data.get("updated_at") or data.get("timestamp"),
                    }
        return None

    def _warning_events(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        warnings = []
        for event in events:
            topic = str(event.get("topic", "")).upper()
            if "WARNING" in topic or "NO_DATA" in topic or "RETRY" in topic:
                warnings.append(
                    {
                        "topic": event.get("topic"),
                        "source": event.get("source"),
                        "created_at": event.get("created_at"),
                    }
                )
        return warnings[-20:]

    def _brain_memory_size(self) -> dict[str, Any]:
        path = self.app.orchestrator.config.brain_events_file
        rotated = self.app.orchestrator.config.brain_events_dir
        size = path.stat().st_size if path.exists() else 0
        rotated_files = list(rotated.glob("*.jsonl")) if rotated.exists() else []
        return {
            "active_file_bytes": size,
            "rotated_files": len(rotated_files),
        }

    def _learning_status(self, analyses: dict[str, Any], graph: dict[str, Any]) -> str:
        if int(analyses.get("learning_updates") or 0) > 0 and int(graph.get("node_count") or 0) > 0:
            return "activity_detected"
        return "insufficient_public_evidence"

    def _data_quality(self, statistics: dict[str, Any]) -> dict[str, Any]:
        developer = statistics.get("developer", {})
        return {
            "service_errors": developer.get("service_errors"),
            "data_warnings": developer.get("data_warnings"),
            "duplicate_events_ignored": developer.get("duplicate_events_ignored"),
        }

    def _status_from_health(self, value: Any) -> str:
        normalized = str(value or "").upper()
        if normalized in {"OK", "RUNNING", "STARTED"}:
            return "ok"
        if normalized in {"PENDING", "UNKNOWN", ""}:
            return "partial"
        return "error" if "ERROR" in normalized else "partial"

    def _age_seconds(self, timestamp: str) -> float | None:
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
        return round(max(0.0, (datetime.now(UTC) - parsed).total_seconds()), 2)

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, dict):
            clean: dict[str, Any] = {}
            for key, item in value.items():
                key_text = str(key).lower()
                if any(marker in key_text for marker in SECRET_MARKERS):
                    continue
                clean[key] = self._sanitize(item)
            return clean
        if isinstance(value, list):
            return [self._sanitize(item) for item in value]
        if isinstance(value, str):
            return value.replace(str(Path.home()), "~")
        return value
