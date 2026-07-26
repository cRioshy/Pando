"""Local web ControlCenter tests."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import time
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


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str) -> dict:
    request = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(request, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def read_ws_frame(sock: socket.socket) -> dict:
    header = sock.recv(2)
    if len(header) < 2:
        raise AssertionError("Missing WebSocket frame header")
    length = header[1] & 0x7F
    if length == 126:
        length = struct.unpack("!H", sock.recv(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", sock.recv(8))[0]
    payload = sock.recv(length)
    while len(payload) < length:
        payload += sock.recv(length - len(payload))
    return json.loads(payload.decode("utf-8"))


class WebControlCenterTest(unittest.TestCase):
    def make_server(self, temp_path: Path) -> tuple[Orchestrator, WebControlServer]:
        config = PlatformConfig(
            project_root=temp_path,
            stock_project_path=temp_path / "stock",
            data_dir=temp_path,
            shared_state_file=temp_path / "shared_state.json",
            brain_events_file=temp_path / "brain.jsonl",
            telegram_bot_token="super-secret-token",
            telegram_chat_id="hidden-chat",
        )
        shared_state = SharedState(temp_path / "shared_state.json")
        orchestrator = Orchestrator(
            config=config,
            shared_state=shared_state,
            adapters=[],
        )
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

    def test_webserver_health_and_status_json(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                orchestrator, server = self.make_server(Path(temp))
                await orchestrator.start()
                server.start()
                try:
                    await orchestrator.run_once(final_control_snapshot=False)
                    health = get_json(f"{server.url}/api/health")
                    status = get_json(f"{server.url}/api/status")
                finally:
                    server.stop()
                    await orchestrator.stop()

                self.assertEqual(health["web_running"], True)
                self.assertIn("platform_health", status)
                self.assertIn("services", status)

        asyncio.run(run())

    def test_public_config_does_not_expose_secrets(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                orchestrator, server = self.make_server(Path(temp))
                await orchestrator.start()
                server.start()
                try:
                    public = get_json(f"{server.url}/api/config/public")
                    full_text = json.dumps(get_json(f"{server.url}/api/status"))
                finally:
                    server.stop()
                    await orchestrator.stop()

                self.assertNotIn("telegram_bot_token", public)
                self.assertNotIn("super-secret-token", json.dumps(public))
                self.assertNotIn("super-secret-token", full_text)

        asyncio.run(run())

    def test_learning_report_endpoint_returns_json(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                orchestrator, server = self.make_server(Path(temp))
                await orchestrator.start()
                server.start()
                try:
                    report = get_json(f"{server.url}/api/learning-report")
                finally:
                    server.stop()
                    await orchestrator.stop()

                self.assertIn("learning_report", report)
                self.assertIn("summary", report["learning_report"])
                self.assertNotIn("super-secret-token", json.dumps(report))

        asyncio.run(run())

    def test_websocket_receives_live_event(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                orchestrator, server = self.make_server(Path(temp))
                await orchestrator.start()
                server.start()
                sock = socket.create_connection(("127.0.0.1", server.port), timeout=3)
                try:
                    key = base64.b64encode(os.urandom(16)).decode("ascii")
                    sock.sendall(
                        (
                            "GET /ws/live HTTP/1.1\r\n"
                            f"Host: 127.0.0.1:{server.port}\r\n"
                            "Upgrade: websocket\r\n"
                            "Connection: Upgrade\r\n"
                            f"Sec-WebSocket-Key: {key}\r\n"
                            "Sec-WebSocket-Version: 13\r\n\r\n"
                        ).encode("ascii")
                    )
                    handshake = sock.recv(4096).decode("ascii", errors="ignore")
                    self.assertIn("101 Switching Protocols", handshake)
                    initial = read_ws_frame(sock)
                    self.assertNotIn("statistics", initial["snapshot"])
                    orchestrator.event_bus.publish(
                        Event(
                            topic="CRYPTO_ANALYSIS_FINISHED",
                            source="crypto",
                            payload={
                                "symbol": "BTCUSDT",
                                "payload": {
                                    "symbol": "BTCUSDT",
                                    "market_type": "crypto",
                                    "direction": "LONG",
                                    "probability": 74,
                                    "price": 58420.10,
                                },
                            },
                        )
                    )
                    frames = [read_ws_frame(sock), read_ws_frame(sock)]
                    frame = next(
                        item
                        for item in frames
                        if item.get("event", {}).get("topic") == "CRYPTO_ANALYSIS_FINISHED"
                    )
                finally:
                    sock.close()
                    server.stop()
                    await orchestrator.stop()

                self.assertEqual(frame["type"], "event")
                self.assertEqual(frame["event"]["topic"], "CRYPTO_ANALYSIS_FINISHED")
                self.assertIn("event_bus", frame["snapshot"]["web"])
                self.assertEqual(
                    frame["snapshot"]["last_crypto_analysis"]["BTCUSDT"]["direction"],
                    "LONG",
                )

        asyncio.run(run())

    def test_frontend_loads_statistics_separately_from_live_snapshot(self) -> None:
        script = (PROJECT_ROOT / "web" / "static" / "control_center.js").read_text(encoding="utf-8")
        routes = (PROJECT_ROOT / "web" / "routes.py").read_text(encoding="utf-8")

        self.assertIn("async function loadStatistics()", script)
        self.assertIn('fetch("/api/statistics"', script)
        self.assertIn("loadStatistics().catch", script)
        self.assertIn("live_event_snapshot()", routes)
        self.assertNotIn('"snapshot": self.server.app.snapshot()', routes)

    def test_bad_event_does_not_stop_webserver(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                orchestrator, server = self.make_server(Path(temp))
                await orchestrator.start()
                server.start()
                try:
                    orchestrator.event_bus.publish(Event(topic="SYSTEM_ERROR", source="test", payload=[]))
                    health = get_json(f"{server.url}/api/health")
                    events = get_json(f"{server.url}/api/events")
                finally:
                    server.stop()
                    await orchestrator.stop()

                self.assertTrue(health["web_running"])
                self.assertIn("event_bus", events)
                self.assertIn("discarded_events", events)

        asyncio.run(run())

    def test_control_commands_are_validated_and_logged(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                orchestrator, server = self.make_server(temp_path)
                await orchestrator.start()
                server.start()
                try:
                    pause = post_json(f"{server.url}/api/control/pause")
                    with self.assertRaises(urllib.error.HTTPError):
                        post_json(f"{server.url}/api/control/not-allowed")
                finally:
                    server.stop()
                    await orchestrator.stop()

                self.assertEqual(pause["command"]["action"], "pause")
                self.assertTrue((temp_path / "commands.jsonl").exists())
                self.assertFalse(server.is_local_address("192.168.0.20"))

        asyncio.run(run())

    def test_shutdown_stops_server_thread(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                orchestrator, server = self.make_server(Path(temp))
                await orchestrator.start()
                server.start()
                thread = server._thread
                server.stop()
                await orchestrator.stop()

                self.assertIsNotNone(thread)
                time.sleep(0.1)
                self.assertFalse(thread.is_alive())

        asyncio.run(run())

    def test_headless_web_cli_starts(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "main.py",
                "--headless",
                "--web",
                "--web-port",
                "0",
                "--cycles",
                "1",
                "--interval",
                "0.1",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            env={
                **os.environ,
                # One symbol is sufficient for this CLI smoke test and keeps it
                # independent of variable legacy-market analysis duration.
                "PANDORICKKI_CRYPTO_SYMBOLS": "BTCUSDT",
                "PANDORICKKI_CRYPTO_LIVE_PRICE_DISPLAY": "0",
                "PANDORICKKI_STOCK_TEST_MODE": "1",
                "PANDORICKKI_STOCK_LIVE_PRICE_DISPLAY": "0",
                "PANDORICKKI_COMMODITIES_ENABLED": "0",
            },
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PandorickKi Web ControlCenter gestartet", result.stdout)
        self.assertIn("Modus: headless", result.stdout)


if __name__ == "__main__":
    unittest.main()
