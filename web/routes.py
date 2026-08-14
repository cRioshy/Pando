"""HTTP route helpers for the local PandorickKi web ControlCenter."""

from __future__ import annotations

import json
import mimetypes
import hmac
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse


STATIC_DIR = Path(__file__).resolve().parent / "static"
RICK_ENDPOINTS = {
    "/api/v1/health",
    "/api/v1/system/status",
    "/api/v1/brain/status",
    "/api/v1/learning/summary",
    "/api/v1/decisions/recent",
    "/api/v1/statistics",
    "/api/v1/warnings",
}


class RouteMixin:
    """Request handler mixin used by WebControlServer."""

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        """Handle static files, JSON API routes and the WebSocket route."""

        if not self.server.app.is_local_address(self.client_address[0]):
            self._send_json({"error": "local access only"}, HTTPStatus.FORBIDDEN)
            return

        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/ws/live":
            self.server.app.websocket_manager.accept(
                self,
                {
                    "type": "snapshot",
                    "snapshot": self.server.app.live_event_snapshot(),
                },
            )
            return
        if path.startswith("/api/"):
            self._handle_api_get(path, parse_qs(parsed.query))
            return
        self._handle_static(path)

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        """Handle safe local control endpoints."""

        if not self.server.app.is_local_address(self.client_address[0]):
            self._send_json({"error": "local control only"}, HTTPStatus.FORBIDDEN)
            return

        path = urlparse(self.path).path
        if path.startswith("/api/v1/"):
            self._send_json({"error": "read-only api"}, HTTPStatus.METHOD_NOT_ALLOWED)
            return
        if path == "/api/statistics/storage/refresh":
            self._send_json(self.server.app.refresh_storage_statistics(), HTTPStatus.ACCEPTED)
            return
        prefix = "/api/control/"
        if not path.startswith(prefix):
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        action = path[len(prefix) :]
        try:
            result = self.server.app.apply_control(action, self.client_address[0])
        except ValueError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json({"ok": True, "command": result})

    def do_PUT(self) -> None:  # noqa: N802 - http.server API
        """Reject writes to the read-only API."""

        self._send_json({"error": "method not allowed"}, HTTPStatus.METHOD_NOT_ALLOWED)

    def do_PATCH(self) -> None:  # noqa: N802 - http.server API
        """Reject writes to the read-only API."""

        self._send_json({"error": "method not allowed"}, HTTPStatus.METHOD_NOT_ALLOWED)

    def do_DELETE(self) -> None:  # noqa: N802 - http.server API
        """Reject writes to the read-only API."""

        self._send_json({"error": "method not allowed"}, HTTPStatus.METHOD_NOT_ALLOWED)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        """Silence default request logs; commands are logged explicitly."""

    def _handle_api_get(self, path: str, query: dict[str, list[str]] | None = None) -> None:
        """Return one JSON API response."""

        app = self.server.app
        query = query or {}
        if self._is_rick_endpoint(path):
            if not self._authorize_rick(path):
                return
            try:
                self._send_json(self._handle_rick_api_get(path, query))
            except KeyError:
                self._send_json(app.rick_api.envelope({"error": "not found"}, status="error"), HTTPStatus.NOT_FOUND)
            return
        routes = {
            "/api/health": app.api_health,
            "/api/status": app.api_status,
            "/api/services": app.api_services,
            "/api/crypto": app.api_crypto,
            "/api/stocks": app.api_stocks,
            "/api/commodities": app.api_commodities,
            "/api/brain": app.api_brain,
            "/api/signals": app.api_signals,
            "/api/errors": app.api_errors,
            "/api/events": app.api_events,
            "/api/config/public": app.api_public_config,
            "/api/statistics": app.api_statistics,
            "/api/statistics/analyses": app.api_statistics_analyses,
            "/api/statistics/storage": app.api_statistics_storage,
            "/api/v1/learning-graph": app.api_learning_graph,
            "/api/v1/learning-graph/nodes": app.api_learning_graph_nodes,
            "/api/v1/learning-graph/edges": app.api_learning_graph_edges,
            "/api/v1/learning-graph/stats": app.api_learning_graph_stats,
            "/api/v1/learning-graph/recent": app.api_learning_graph_recent,
            "/api/v1/graph/overview": app.api_knowledge_graph_overview,
            "/api/learning-report": app.api_learning_report,
        }
        handler = routes.get(path)
        if handler is None and path == "/api/shadow-verification/summary":
            try:
                days = int((query.get("days") or ["7"])[0])
                limit = int((query.get("limit") or ["50"])[0])
            except ValueError:
                self._send_json({"error": "days and limit must be integers"}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json(app.api_shadow_verification_summary(days=days, limit=limit))
            return
        if handler is None and path.startswith("/api/shadow-verification/"):
            verification_id = unquote(path.removeprefix("/api/shadow-verification/"))
            try:
                self._send_json(app.api_shadow_verification_detail(verification_id))
            except KeyError:
                self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        if handler is None and path == "/api/v1/graph/full":
            raw = (query.get("min_edge_weight") or ["0"])[0]
            try:
                min_edge_weight = float(raw)
            except ValueError:
                min_edge_weight = 0.0
            self._send_json(app.api_knowledge_graph_full(min_edge_weight))
            return
        if handler is None and path == "/api/v1/graph/search":
            self._send_json(app.api_knowledge_graph_search((query.get("q") or [""])[0]))
            return
        if handler is None and path == "/api/v1/graph/changes":
            since_raw = (query.get("since_version") or query.get("since") or [None])[0]
            try:
                since_version = int(since_raw) if since_raw not in {None, ""} else None
            except ValueError:
                since_version = None
            self._send_json(app.api_knowledge_graph_changes(since_version))
            return
        if handler is None and path.startswith("/api/v1/graph/cluster/"):
            cluster_id = unquote(path.rsplit("/", 1)[-1])
            try:
                self._send_json(app.api_knowledge_graph_cluster(cluster_id))
            except KeyError:
                self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        if handler is None and path.startswith("/api/v1/graph/node/"):
            node_id = unquote(path.rsplit("/", 1)[-1])
            try:
                self._send_json(app.api_knowledge_graph_node(node_id))
            except KeyError:
                self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        if handler is None and path.startswith("/api/v1/learning-graph/node/"):
            node_id = unquote(path.rsplit("/", 1)[-1])
            try:
                self._send_json(app.api_learning_graph_node(node_id))
            except KeyError:
                self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        if handler is None and path.startswith("/api/statistics/storage/"):
            folder_name = path.rsplit("/", 1)[-1]
            try:
                self._send_json(app.api_statistics_storage_folder(folder_name))
            except KeyError:
                self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        if handler is None:
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        self._send_json(handler())

    def _is_rick_endpoint(self, path: str) -> bool:
        """Return whether the request should use the Rick read-only facade."""

        if path in RICK_ENDPOINTS:
            return True
        if path.startswith("/api/v1/graph/"):
            return self.headers.get("X-Pandorick-Rick-API") == "1" or bool(self.headers.get("Authorization"))
        return False

    def _authorize_rick(self, path: str) -> bool:
        """Validate optional Rick token and audit the request."""

        app = self.server.app
        configured = app.orchestrator.config.rick_api_token
        auth_header = self.headers.get("Authorization", "")
        supplied = ""
        if auth_header.lower().startswith("bearer "):
            supplied = auth_header[7:].strip()
        elif self.headers.get("X-Rick-API-Token"):
            supplied = self.headers.get("X-Rick-API-Token", "").strip()
        if configured and not hmac.compare_digest(configured, supplied):
            app.rick_api.audit(path=path, client=self.client_address[0], status="unauthorized")
            self._send_json(app.rick_api.envelope({"error": "unauthorized"}, status="error"), HTTPStatus.UNAUTHORIZED)
            return False
        app.rick_api.audit(path=path, client=self.client_address[0], status="authorized" if configured else "local_no_token")
        return True

    def _handle_rick_api_get(self, path: str, query: dict[str, list[str]]) -> dict[str, Any]:
        """Dispatch one read-only Rick API route."""

        api = self.server.app.rick_api
        if path == "/api/v1/health":
            return api.health()
        if path == "/api/v1/system/status":
            return api.system_status()
        if path == "/api/v1/brain/status":
            return api.brain_status()
        if path == "/api/v1/learning/summary":
            return api.learning_summary()
        if path == "/api/v1/graph/overview":
            return api.graph_overview()
        if path.startswith("/api/v1/graph/cluster/"):
            return api.graph_cluster(unquote(path.rsplit("/", 1)[-1]))
        if path.startswith("/api/v1/graph/node/"):
            return api.graph_node(unquote(path.rsplit("/", 1)[-1]))
        if path == "/api/v1/decisions/recent":
            raw_limit = (query.get("limit") or ["20"])[0]
            try:
                limit = max(1, min(100, int(raw_limit)))
            except ValueError:
                limit = 20
            return api.decisions_recent(limit=limit)
        if path == "/api/v1/statistics":
            return api.statistics()
        if path == "/api/v1/warnings":
            return api.warnings()
        raise KeyError(path)

    def _handle_static(self, path: str) -> None:
        """Serve static ControlCenter assets."""

        if path in {"", "/"}:
            path = "/control_center.html"
        requested = (STATIC_DIR / path.lstrip("/")).resolve()
        if STATIC_DIR not in requested.parents and requested != STATIC_DIR:
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        if not requested.exists() or not requested.is_file():
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return

        body = requested.read_bytes()
        content_type = mimetypes.guess_type(str(requested))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        try:
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            return

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        """Write one JSON response."""

        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        try:
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            return
