"""Statistics and storage metadata tests."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import socket
import sqlite3
import struct
import tempfile
import unittest
import urllib.request
from pathlib import Path

from adapters.control_center_adapter import ControlCenterAdapter
from config import PlatformConfig
from event_bus import Event
from orchestrator import NoopAdapter, Orchestrator
from shared_state import SharedState
from web.api import WebControlServer
from web.statistics_service import (
    AnalysisStatisticsService,
    StorageStatisticsService,
    count_csv_rows,
    count_json_records,
    count_jsonl,
)


def read_ws_frame(sock: socket.socket) -> dict:
    header = sock.recv(2)
    if len(header) < 2:
        raise AssertionError("Missing WebSocket frame header")
    length = header[1] & 0x7F
    if length == 126:
        length = struct.unpack("!H", sock.recv(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", sock.recv(8))[0]
    payload = b""
    while len(payload) < length:
        payload += sock.recv(length - len(payload))
    return json.loads(payload.decode("utf-8"))


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str) -> dict:
    request = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(request, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


class StatisticsAndStorageTest(unittest.TestCase):
    def make_config(self, root: Path) -> PlatformConfig:
        data = root / "data"
        return PlatformConfig(
            project_root=root,
            data_dir=data,
            shared_state_file=data / "shared_state.json",
            brain_events_file=data / "brain_events.jsonl",
            telegram_log_file=data / "telegram.jsonl",
            crypto_project_path=root / "crypto",
            stock_project_path=root / "stock",
            storage_scan_interval_seconds=5.0,
            telegram_bot_token="secret-token",
        )

    def make_server(self, root: Path) -> tuple[Orchestrator, WebControlServer]:
        config = self.make_config(root)
        shared_state = SharedState(config.shared_state_file)
        orchestrator = Orchestrator(config=config, shared_state=shared_state, adapters=[])
        bus = orchestrator.event_bus
        orchestrator.adapters = [
            NoopAdapter("crypto", "test"),
            NoopAdapter("stock", "test"),
            NoopAdapter("brain", "test"),
            ControlCenterAdapter(bus, shared_state, print_output=False),
        ]
        return orchestrator, WebControlServer(orchestrator, port=0)

    def test_crypto_stock_and_duplicate_count_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            service = AnalysisStatisticsService(Path(temp) / "system_statistics.json")
            event = Event(
                topic="CRYPTO_ANALYSIS_FINISHED",
                source="crypto",
                payload={
                    "symbol": "BTCUSDT",
                    "timeframe": "15m",
                    "timestamp": "t1",
                    "payload": {
                        "symbol": "BTCUSDT",
                        "timeframe": "15m",
                        "direction": "LONG",
                        "source_timestamp": "source-1",
                    },
                },
                event_id="same-id",
            )
            self.assertTrue(service.apply_event(event))
            self.assertTrue(service.apply_event(event))
            stock = Event(
                topic="STOCK_ANALYSIS_FINISHED",
                source="stock",
                payload={
                    "symbol": "AAPL",
                    "timestamp": "t2",
                    "payload": {"symbol": "AAPL", "direction": "HOLD", "source_timestamp": "source-2"},
                },
            )
            service.apply_event(stock)
            snapshot = service.snapshot()

            self.assertEqual(snapshot["crypto_analyses"], 1)
            self.assertEqual(snapshot["stock_analyses"], 1)
            self.assertEqual(snapshot["total_analyses"], 2)
            self.assertEqual(snapshot["long_count"], 1)
            self.assertEqual(snapshot["hold_count"], 1)
            self.assertEqual(snapshot["duplicate_events_ignored"], 1)

    def test_short_decision_signal_learning_error_and_telegram_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            service = AnalysisStatisticsService(Path(temp) / "system_statistics.json")
            service.apply_event(Event(topic="DECISION_CREATED", source="core", payload={"payload": {"direction": "SHORT"}}))
            service.apply_event(Event(topic="SIGNAL_CREATED", source="core", payload={"payload": {"direction": "WAIT"}}))
            service.apply_event(Event(topic="AI_LEARNING_UPDATED", source="brain", payload={}))
            service.apply_event(Event(topic="SYSTEM_ERROR", source="system", payload={}))
            service.apply_event(Event(topic="TELEGRAM_MESSAGE_SENT", source="telegram", payload={}))
            snapshot = service.snapshot()

            self.assertEqual(snapshot["decisions_created"], 1)
            self.assertEqual(snapshot["signals_created"], 1)
            self.assertEqual(snapshot["short_count"], 1)
            self.assertEqual(snapshot["hold_count"], 1)
            self.assertEqual(snapshot["learning_updates"], 1)
            self.assertEqual(snapshot["error_count"], 1)
            self.assertEqual(snapshot["telegram_messages_sent"], 1)

    def test_professional_trading_counts_only_final_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            service = AnalysisStatisticsService(Path(temp) / "system_statistics.json")
            service.apply_event(Event(topic="CRYPTO_ANALYSIS_FINISHED", source="crypto", payload={"payload": {"direction": "WAIT"}}))
            service.apply_event(Event(topic="SIGNAL_CREATED", source="core", payload={"payload": {"direction": "WAIT"}}))
            service.apply_event(
                Event(
                    topic="DECISION_CREATED",
                    source="core",
                    payload={"payload": {"direction": "HOLD", "confidence": 72.5}},
                )
            )
            snapshot = service.snapshot()

            self.assertEqual(snapshot["hold_count"], 3)
            self.assertEqual(snapshot["trading"]["final_hold"], 1)
            self.assertEqual(snapshot["trading"]["final_long"], 0)
            self.assertEqual(snapshot["trading"]["final_short"], 0)
            self.assertEqual(snapshot["trading"]["average_confidence"], 72.5)

    def test_simulated_outcome_events_drive_hit_rate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            service = AnalysisStatisticsService(Path(temp) / "system_statistics.json")
            service.apply_event(
                Event(
                    topic="SIMULATED_TRADE_OPENED",
                    source="outcome_tracker",
                    payload={"payload": {"decision_id": "d1", "symbol": "BTCUSDT"}},
                    event_id="open-1",
                )
            )
            service.apply_event(
                Event(
                    topic="SIMULATED_TRADE_CLOSED",
                    source="outcome_tracker",
                    payload={
                        "payload": {
                            "decision_id": "d1",
                            "symbol": "BTCUSDT",
                            "result_type": "WIN",
                            "gross_profit_percent": 2.5,
                            "holding_seconds": 300,
                        }
                    },
                    event_id="close-1",
                )
            )
            snapshot = service.snapshot()

            self.assertEqual(snapshot["trading"]["simulated_open_trades"], 0)
            self.assertEqual(snapshot["trading"]["simulated_closed_trades"], 1)
            self.assertEqual(snapshot["trading"]["simulated_wins"], 1)
            self.assertEqual(snapshot["trading"]["simulated_losses"], 0)
            self.assertEqual(snapshot["trading"]["hit_rate"], 100.0)
            self.assertEqual(snapshot["trading"]["average_outcome_profit_percent"], 2.5)
            self.assertEqual(snapshot["trading"]["average_holding_seconds"], 300.0)

    def test_outcome_reconstruction_uses_trade_outcomes_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self.make_config(root)
            config.data_dir.mkdir(parents=True)
            config.trade_outcomes_file.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "record_type": "SIMULATED_TRADE_OPENED",
                                "timestamp": "2026-07-22T10:00:00+00:00",
                                "payload": {"decision_id": "d1", "symbol": "ETHUSDT"},
                            }
                        ),
                        json.dumps(
                            {
                                "record_type": "SIMULATED_TRADE_CLOSED",
                                "timestamp": "2026-07-22T10:05:00+00:00",
                                "payload": {
                                    "decision_id": "d1",
                                    "symbol": "ETHUSDT",
                                    "result_type": "LOSS",
                                    "gross_profit_percent": -1.25,
                                    "holding_seconds": 300,
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )
            service = AnalysisStatisticsService(root / "storage" / "statistics" / "system_statistics.json")

            service.start(config)
            snapshot = service.snapshot()

            self.assertTrue(snapshot["outcome_reconstructed"])
            self.assertEqual(snapshot["trading"]["simulated_closed_trades"], 1)
            self.assertEqual(snapshot["trading"]["simulated_losses"], 1)
            self.assertEqual(snapshot["trading"]["hit_rate"], 0.0)
            self.assertEqual(snapshot["trading"]["average_outcome_profit_percent"], -1.25)

    def test_retry_warning_and_service_error_are_separated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            service = AnalysisStatisticsService(Path(temp) / "system_statistics.json")
            service.apply_event(Event(topic="API_RETRY", source="crypto", payload={}))
            service.apply_event(Event(topic="CANDLE_MISSING_WARNING", source="stock", payload={}))
            service.apply_event(Event(topic="COMMODITY_DATA_WARNING", source="commodity", payload={"payload": {"symbol": "GC=F"}}))
            service.apply_event(Event(topic="STOCK_SERVICE_ERROR", source="stock", payload={"payload": {"symbol": "AAPL"}}))
            snapshot = service.snapshot()

            self.assertEqual(snapshot["error_count"], 1)
            self.assertEqual(snapshot["developer"]["retry_events"], 1)
            self.assertEqual(snapshot["developer"]["data_warnings"], 2)
            self.assertEqual(snapshot["developer"]["service_errors"], 1)
            self.assertEqual(snapshot["errors_detail"]["by_type"]["STOCK_SERVICE_ERROR"], 1)
            self.assertEqual(snapshot["errors_detail"]["warnings"]["COMMODITY_DATA_WARNING"], 1)

    def test_counters_persist_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "system_statistics.json"
            first = AnalysisStatisticsService(path)
            first.apply_event(
                Event(topic="CRYPTO_ANALYSIS_FINISHED", source="crypto", payload={"payload": {"direction": "LONG"}})
            )
            second = AnalysisStatisticsService(path)
            second.load()

            self.assertEqual(second.snapshot()["crypto_analyses"], 1)

    def test_file_record_counters(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            jsonl = root / "records.jsonl"
            jsonl.write_text('{"a":1}\n\n{"a":2}\n', encoding="utf-8")
            csv_file = root / "records.csv"
            csv_file.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
            json_file = root / "records.json"
            json_file.write_text('[{"a":1},{"a":2},{"a":3}]', encoding="utf-8")

            self.assertEqual(count_jsonl(jsonl), 2)
            self.assertEqual(count_csv_rows(csv_file), 2)
            self.assertEqual(count_json_records(json_file, json_file.stat().st_size), 3)

    def test_storage_scan_handles_broken_and_sqlite_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self.make_config(root)
            config.data_dir.mkdir(parents=True)
            (config.data_dir / "broken.jsonl").write_text('{"ok": true}\n{bad json}\n', encoding="utf-8")
            db = config.data_dir / "store.sqlite"
            connection = sqlite3.connect(db)
            try:
                connection.execute("CREATE TABLE records (id INTEGER)")
                connection.executemany("INSERT INTO records (id) VALUES (?)", [(1,), (2,), (3,)])
                connection.commit()
            finally:
                connection.close()

            service = StorageStatisticsService(config)
            snapshot = service.refresh()

            self.assertEqual(snapshot["total_files"], 2)
            self.assertGreaterEqual(snapshot["total_records"], 3)
            folder = snapshot["folders"][0]
            self.assertEqual(folder["status"], "WARN")
            self.assertTrue(folder["errors"])

    def test_backup_file_warning_does_not_mark_folder_warn(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self.make_config(root)
            config.data_dir.mkdir(parents=True)
            backup_dir = config.data_dir / "backups"
            backup_dir.mkdir()
            (config.data_dir / "records.jsonl").write_text('{"ok": true}\n', encoding="utf-8")
            (backup_dir / "broken_backup.json").write_text('{"broken": true', encoding="utf-8")

            service = StorageStatisticsService(config)
            snapshot = service.refresh()
            folder = snapshot["folders"][0]

            self.assertEqual(folder["status"], "OK")
            self.assertFalse(folder["errors"])
            self.assertTrue(folder["backup_warnings"])

    def test_large_jsonl_is_counted_line_by_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "large.jsonl"
            with path.open("w", encoding="utf-8") as handle:
                for index in range(1000):
                    handle.write(json.dumps({"index": index}) + "\n")

            self.assertEqual(count_jsonl(path), 1000)

    def test_storage_scan_async_does_not_block_event_loop(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                config = self.make_config(root)
                config.data_dir.mkdir(parents=True)
                (config.data_dir / "records.jsonl").write_text('{"a":1}\n', encoding="utf-8")
                service = StorageStatisticsService(config)
                scan_task = asyncio.create_task(service.refresh_async())
                tick_task = asyncio.create_task(asyncio.sleep(0))
                await asyncio.gather(scan_task, tick_task)

                self.assertTrue(tick_task.done())
                self.assertEqual(scan_task.result()["total_records"], 1)

        asyncio.run(run())

    def test_api_statistics_and_manual_refresh_are_safe(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                config = self.make_config(root)
                config.data_dir.mkdir(parents=True)
                (config.data_dir / "records.csv").write_text("a\n1\n2\n", encoding="utf-8")
                orchestrator, server = self.make_server(root)
                await orchestrator.start()
                server.start()
                try:
                    orchestrator.event_bus.publish(
                        Event(
                            topic="SIMULATED_TRADE_CLOSED",
                            source="outcome_tracker",
                            payload={
                                "payload": {
                                    "decision_id": "d1",
                                    "symbol": "BTCUSDT",
                                    "result_type": "WIN",
                                    "gross_profit_percent": 1.75,
                                    "holding_seconds": 120,
                                }
                            },
                        )
                    )
                    stats = get_json(f"{server.url}/api/statistics")
                    storage = post_json(f"{server.url}/api/statistics/storage/refresh")
                    status_text = json.dumps(get_json(f"{server.url}/api/status"))
                finally:
                    server.stop()
                    await orchestrator.stop()

                self.assertIn("analyses", stats)
                self.assertIn("developer", stats)
                self.assertIn("trading", stats)
                self.assertEqual(stats["trading"]["simulated_closed_trades"], 1)
                self.assertEqual(stats["trading"]["simulated_wins"], 1)
                self.assertEqual(stats["trading"]["hit_rate"], 100.0)
                self.assertGreaterEqual(storage["storage"]["total_records"], 2)
                self.assertNotIn(str(root), status_text)
                self.assertNotIn("secret-token", status_text)

        asyncio.run(run())

    def test_websocket_sends_statistics_updated(self) -> None:
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
                    self.assertIn("101 Switching Protocols", sock.recv(4096).decode("ascii", errors="ignore"))
                    _initial = read_ws_frame(sock)
                    orchestrator.event_bus.publish(
                        Event(
                            topic="SIMULATED_TRADE_CLOSED",
                            source="outcome_tracker",
                            payload={
                                "payload": {
                                    "decision_id": "d1",
                                    "symbol": "BTCUSDT",
                                    "result_type": "WIN",
                                    "gross_profit_percent": 2.0,
                                    "holding_seconds": 60,
                                }
                            },
                        )
                    )
                    frame = read_ws_frame(sock)
                finally:
                    sock.close()
                    server.stop()
                    await orchestrator.stop()

                self.assertEqual(frame["event"]["topic"], "STATISTICS_UPDATED")
                self.assertEqual(frame["payload"]["trading"]["simulated_closed_trades"], 1)
                self.assertEqual(frame["payload"]["trading"]["hit_rate"], 100.0)

        asyncio.run(run())


class StatisticsUiStateTest(unittest.TestCase):
    """Guard the browser statistics view against lightweight live snapshots."""

    def test_live_snapshots_do_not_reset_statistics_to_zero(self) -> None:
        script = (Path(__file__).resolve().parents[1] / "web" / "static" / "control_center.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("statistics: null", script)
        self.assertIn("const statistics = snapshot.statistics || state.statistics", script)
        self.assertIn("state.statistics = snapshot.statistics", script)
        self.assertIn('data.event.topic === "STATISTICS_UPDATED"', script)
        self.assertIn("state.statistics = data.payload", script)


if __name__ == "__main__":
    unittest.main()
