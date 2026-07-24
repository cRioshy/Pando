"""Tests for the read-only Rick API facade."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from adapters.control_center_adapter import ControlCenterAdapter
from config import PlatformConfig
from event_bus import Event
from orchestrator import NoopAdapter, Orchestrator
from shared_state import SharedState
from web.api import WebControlServer


def get_json(url: str, *, token: str | None = None, rick: bool = True) -> dict:
    request = urllib.request.Request(url, method="GET")
    if rick:
        request.add_header("X-Pandorick-Rick-API", "1")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, *, token: str | None = None) -> dict:
    request = urllib.request.Request(url, method="POST")
    request.add_header("X-Pandorick-Rick-API", "1")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


class RickReadOnlyApiTest(unittest.TestCase):
    """Verify Rick endpoints are read-only, wrapped and safe."""

    def make_server(self, temp_path: Path, *, token: str | None = "rick-test-token") -> tuple[Orchestrator, WebControlServer]:
        config = PlatformConfig(
            project_root=temp_path,
            stock_project_path=temp_path / "stock",
            data_dir=temp_path,
            shared_state_file=temp_path / "shared_state.json",
            brain_events_file=temp_path / "brain_events.jsonl",
            brain_events_dir=temp_path / "brain_events",
            telegram_bot_token="super-secret-token",
            telegram_chat_id="hidden-chat",
            rick_api_token=token,
            rick_api_audit_log_file=temp_path / "rick_api_audit.jsonl",
        )
        shared_state = SharedState(temp_path / "shared_state.json")
        orchestrator = Orchestrator(config=config, shared_state=shared_state, adapters=[])
        bus = orchestrator.event_bus
        orchestrator.adapters = [
            NoopAdapter("crypto", "test"),
            NoopAdapter("stock", "test"),
            NoopAdapter("brain", "test"),
            NoopAdapter("telegram", "test"),
            ControlCenterAdapter(bus, shared_state, print_output=False),
        ]
        server = WebControlServer(orchestrator, port=0, command_log_file=temp_path / "commands.jsonl")
        return orchestrator, server

    def test_rick_endpoints_return_uniform_envelope(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                orchestrator, server = self.make_server(temp_path)
                await orchestrator.start()
                server.start()
                try:
                    await orchestrator.run_once(final_control_snapshot=False)
                    paths = (
                        "/api/v1/health",
                        "/api/v1/system/status",
                        "/api/v1/brain/status",
                        "/api/v1/learning/summary",
                        "/api/v1/graph/overview",
                        "/api/v1/decisions/recent",
                        "/api/v1/statistics",
                        "/api/v1/warnings",
                    )
                    responses = [get_json(f"{server.url}{path}", token="rick-test-token") for path in paths]
                finally:
                    server.stop()
                    await orchestrator.stop()

                for response in responses:
                    self.assertIn(response["status"], {"ok", "partial", "stale", "unavailable", "error"})
                    self.assertEqual(response["source"], "pandoriki")
                    self.assertEqual(response["version"], "v1")
                    self.assertIn("generated_at", response)
                    self.assertIn("data_age_seconds", response)
                    self.assertIn("data", response)

        asyncio.run(run())

    def test_invalid_token_is_rejected_and_audited(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                orchestrator, server = self.make_server(temp_path)
                await orchestrator.start()
                server.start()
                try:
                    with self.assertRaises(urllib.error.HTTPError) as ctx:
                        get_json(f"{server.url}/api/v1/health", token="wrong")
                finally:
                    server.stop()
                    await orchestrator.stop()

                self.assertEqual(ctx.exception.code, 401)
                audit_text = (temp_path / "rick_api_audit.jsonl").read_text(encoding="utf-8")
                self.assertIn("unauthorized", audit_text)
                self.assertNotIn("rick-test-token", audit_text)

        asyncio.run(run())

    def test_rick_api_does_not_expose_secrets_or_absolute_user_path(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                orchestrator, server = self.make_server(Path(temp))
                await orchestrator.start()
                server.start()
                try:
                    payload = get_json(f"{server.url}/api/v1/system/status", token="rick-test-token")
                finally:
                    server.stop()
                    await orchestrator.stop()

                text = json.dumps(payload)
                self.assertNotIn("super-secret-token", text)
                self.assertNotIn("telegram_bot_token", text)
                self.assertNotIn(str(Path.home()), text)

        asyncio.run(run())

    def test_graph_payload_has_unique_ids_and_valid_edges(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                orchestrator, server = self.make_server(Path(temp))
                await orchestrator.start()
                server.start()
                try:
                    graph = get_json(f"{server.url}/api/v1/graph/overview", token="rick-test-token")["data"]
                finally:
                    server.stop()
                    await orchestrator.stop()

                node_ids = [node["id"] for node in graph["nodes"]]
                self.assertEqual(len(node_ids), len(set(node_ids)))
                node_id_set = set(node_ids)
                for edge in graph["edges"]:
                    self.assertIn(edge["source"], node_id_set)
                    self.assertIn(edge["target"], node_id_set)

        asyncio.run(run())

    def test_recent_decisions_are_final_decision_events_only(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                orchestrator, server = self.make_server(Path(temp))
                await orchestrator.start()
                server.start()
                try:
                    orchestrator.event_bus.publish(
                        Event(
                            topic="DECISION_CREATED",
                            source="decision_core",
                            payload={
                                "symbol": "BTCUSDT",
                                "market_type": "crypto",
                                "direction": "LONG",
                                "confidence": 74,
                            },
                        )
                    )
                    decisions = get_json(f"{server.url}/api/v1/decisions/recent", token="rick-test-token")["data"]
                finally:
                    server.stop()
                    await orchestrator.stop()

                self.assertEqual(decisions["decisions"][0]["symbol"], "BTCUSDT")
                self.assertEqual(decisions["decisions"][0]["direction"], "LONG")

        asyncio.run(run())

    def test_rick_api_rejects_writes(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                orchestrator, server = self.make_server(Path(temp))
                await orchestrator.start()
                server.start()
                try:
                    with self.assertRaises(urllib.error.HTTPError) as ctx:
                        post_json(f"{server.url}/api/v1/statistics", token="rick-test-token")
                finally:
                    server.stop()
                    await orchestrator.stop()

                self.assertEqual(ctx.exception.code, 405)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
