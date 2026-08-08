"""Tests for bounded, secret-filtered service error persistence."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from config import PlatformConfig
from event_bus import Event, EventBus
from orchestrator import Orchestrator
from service_error_journal import ServiceErrorJournal
from shared_state import SharedState


class ServiceErrorJournalTest(unittest.TestCase):
    def make_journal(self, root: Path, bus: EventBus | None = None) -> ServiceErrorJournal:
        return ServiceErrorJournal(
            bus or EventBus(),
            journal_file=root / "service_errors.jsonl",
            summary_file=root / "service_error_summary.json",
            rotation_bytes=1024 * 1024,
            max_archives=2,
            max_summary_entries=10,
        )

    def test_persists_compact_projection_and_durable_first_last_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bus = EventBus()
            journal = self.make_journal(root, bus)
            journal.start()
            try:
                for index in (1, 2):
                    bus.publish(
                        Event(
                            topic="CRYPTO_SERVICE_ERROR",
                            source="crypto",
                            payload={
                                "correlation_id": "cycle-1",
                                "payload": {
                                    "symbol": "BTCUSDT",
                                    "stage": "market_data",
                                    "error_type": "ProviderError",
                                    "error": f"attempt {index} token=top-secret Bearer bearer-secret",
                                    "api_key": "top-secret",
                                    "diagnostics": {
                                        "response": {"body": "must-not-persist"},
                                        "attempts": [
                                            {
                                                "source": "binance",
                                                "data_type": "candles",
                                                "status": "error",
                                                "attempt": index,
                                                "error_type": "TimeoutError",
                                                "error": "url?api_key=query-secret",
                                                "authorization": "bearer-secret",
                                            }
                                        ],
                                    },
                                },
                            },
                        )
                    )
            finally:
                journal.stop()

            text = (root / "service_errors.jsonl").read_text(encoding="utf-8")
            records = [json.loads(line) for line in text.splitlines()]
            summary = json.loads((root / "service_error_summary.json").read_text(encoding="utf-8"))

            self.assertEqual(len(records), 2)
            self.assertNotIn("top-secret", text)
            self.assertNotIn("bearer-secret", text)
            self.assertNotIn("query-secret", text)
            self.assertNotIn("must-not-persist", text)
            self.assertEqual(records[0]["providers"], ["binance"])
            self.assertEqual(records[0]["symbol"], "BTCUSDT")
            self.assertEqual(records[0]["stage"], "market_data")
            self.assertEqual(records[0]["error_type"], "ProviderError")
            entry = next(iter(summary["errors"].values()))
            self.assertEqual(entry["count"], 2)
            self.assertIn("attempt 1", entry["first"]["message"])
            self.assertIn("attempt 2", entry["last"]["message"])

            restarted = self.make_journal(root, EventBus())
            self.assertEqual(restarted.snapshot()["total_events"], 2)
            self.assertEqual(next(iter(restarted.snapshot()["errors"].values()))["count"], 2)

    def test_ignores_normal_events_and_accepts_generic_and_tracker_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bus = EventBus()
            journal = self.make_journal(root, bus)
            journal.start()
            bus.publish(Event(topic="SERVICE_HEARTBEAT", source="crypto"))
            bus.publish(Event(topic="service.error", source="worker", payload={"error": "failed"}))
            bus.publish(Event(topic="OUTCOME_TRACKER_ERROR", source="outcome", payload={"error": "failed"}))
            journal.stop()

            records = (root / "service_errors.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(records), 2)
            self.assertEqual(journal.snapshot()["total_events"], 2)

    def test_rotation_keeps_only_configured_archives(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bus = EventBus()
            journal = self.make_journal(root, bus)
            journal._ledger.max_bytes = 1024
            journal.start()
            for index in range(12):
                bus.publish(
                    Event(
                        topic="SYSTEM_ERROR",
                        source="test",
                        payload={"error": f"failure-{index}-" + ("x" * 500)},
                    )
                )
            journal.stop()

            archive_dir = root / "archive" / "service_errors"
            archives = list(archive_dir.glob("service_errors_*.jsonl"))
            self.assertLessEqual(len(archives), 2)
            self.assertTrue((root / "service_errors.jsonl").exists())

    def test_write_failure_never_breaks_publisher_and_is_unhealthy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            bus = EventBus()
            journal = self.make_journal(Path(temp), bus)
            journal.start()
            with patch.object(journal._ledger, "append", side_effect=OSError("disk token=secret")):
                bus.publish(Event(topic="SYSTEM_ERROR", source="test", payload={"error": "boom"}))
            journal.stop()

            health = journal.health()
            self.assertFalse(health["healthy"])
            self.assertEqual(health["failed_writes"], 1)
            self.assertNotIn("secret", health["last_error"])

    def test_orchestrator_records_adapter_failures(self) -> None:
        @dataclass
        class FailingAdapter:
            name: str = "failing"

            async def start(self) -> None:
                return None

            async def stop(self) -> None:
                return None

            async def health(self) -> dict:
                return {"healthy": False}

            async def run_once(self) -> list[Event]:
                raise RuntimeError("planned adapter failure")

        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                bus = EventBus()
                journal = self.make_journal(root, bus)
                config = PlatformConfig(data_dir=root, shared_state_file=root / "state.json")
                orchestrator = Orchestrator(
                    event_bus=bus,
                    shared_state=SharedState(root / "state.json"),
                    adapters=[FailingAdapter()],
                    config=config,
                    error_journal=journal,
                )
                await orchestrator.start()
                try:
                    report = await orchestrator.run_once()
                finally:
                    await orchestrator.stop()

                self.assertEqual(report.services["failing"], "ERROR")
                self.assertEqual(report.services["service_error_journal"], "OK")
                self.assertEqual(journal.snapshot()["total_events"], 1)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
