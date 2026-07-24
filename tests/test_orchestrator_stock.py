"""Tests for stock adapter integration in the orchestrator."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from adapters.brain_adapter import BrainAdapter
from brain_event_store import BrainEventReader
from event_bus import Event
from orchestrator import NoopAdapter, Orchestrator
from adapters.stock_adapter import STOCK_ANALYSIS_FINISHED, StockAdapter


class FailingAdapter:
    name = "failing"

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def health(self) -> dict:
        return {"name": self.name, "healthy": False}

    async def run_once(self) -> list[Event]:
        raise RuntimeError("planned failure")


class OrchestratorStockIntegrationTest(unittest.TestCase):
    def test_stock_event_reaches_event_bus(self) -> None:
        async def run() -> None:
            bus = None
            orchestrator = Orchestrator(adapters=[])
            bus = orchestrator.event_bus
            orchestrator.adapters = [
                NoopAdapter("crypto", "noop"),
                BrainAdapter(bus, Path("data/test_brain_events.jsonl")),
                StockAdapter(bus, Path(__file__).resolve().parents[2] / "pandorick_stock_bot", test_mode=True),
                NoopAdapter("control_center", "noop"),
            ]
            seen = []
            orchestrator.event_bus.subscribe(STOCK_ANALYSIS_FINISHED, seen.append)
            await orchestrator.start()
            try:
                report = await orchestrator.run_once()
            finally:
                await orchestrator.stop()

            self.assertEqual(report.status, "OK")
            self.assertTrue(seen)
            self.assertEqual(seen[0].payload["event_type"], STOCK_ANALYSIS_FINISHED)
            self.assertEqual(report.services["brain"], "OK")

        asyncio.run(run())

    def test_service_failure_does_not_stop_orchestrator(self) -> None:
        async def run() -> None:
            orchestrator = Orchestrator(
                adapters=[
                    FailingAdapter(),
                    NoopAdapter("brain", "still runs"),
                ]
            )
            await orchestrator.start()
            try:
                report = await orchestrator.run_once()
            finally:
                await orchestrator.stop()

            self.assertEqual(report.status, "DEGRADED")
            self.assertEqual(report.services["failing"], "ERROR")
            self.assertEqual(report.services["brain"], "OK")

        asyncio.run(run())

    def test_main_once_still_works(self) -> None:
        project = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "main.py", "--once"],
            cwd=project,
            text=True,
            capture_output=True,
            timeout=30,
            env={**os.environ, "PANDORICKKI_STOCK_TEST_MODE": "1"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Health:", result.stdout)

    def test_stock_to_brain_jsonl_flow(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                orchestrator = Orchestrator(adapters=[])
                bus = orchestrator.event_bus
                brain_path = Path(temp) / "brain_events.jsonl"
                orchestrator.adapters = [
                    NoopAdapter("crypto", "noop"),
                    BrainAdapter(bus, brain_path),
                    StockAdapter(
                        bus,
                        Path(__file__).resolve().parents[2] / "pandorick_stock_bot",
                        test_mode=True,
                    ),
                    NoopAdapter("control_center", "noop"),
                ]
                await orchestrator.start()
                try:
                    report = await orchestrator.run_once()
                finally:
                    await orchestrator.stop()

                self.assertEqual(report.services["brain"], "OK")
                stored = BrainEventReader(
                    legacy_file=brain_path,
                    rotated_root=brain_path.parent / "brain_events",
                ).recent(limit=20)
                self.assertGreater(len(stored), 0)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
