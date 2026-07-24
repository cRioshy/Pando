"""Parallel orchestration tests for Phase 6."""

from __future__ import annotations

import asyncio
import time
import unittest
from dataclasses import dataclass

from event_bus import Event
from orchestrator import Orchestrator
from shared_state import SharedState


@dataclass
class TimedAdapter:
    """Small adapter used to prove concurrent orchestration."""

    name: str
    delay: float

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def health(self) -> dict:
        return {"name": self.name, "healthy": True}

    async def run_once(self) -> list[Event]:
        await asyncio.sleep(self.delay)
        return [Event(topic="TEST_DONE", source=self.name, payload={"delay": self.delay})]


class FailingTimedAdapter(TimedAdapter):
    async def run_once(self) -> list[Event]:
        await asyncio.sleep(self.delay)
        raise RuntimeError("parallel failure")


class ParallelOrchestratorTest(unittest.TestCase):
    def test_adapters_run_concurrently(self) -> None:
        async def run() -> None:
            orchestrator = Orchestrator(
                shared_state=SharedState(),
                adapters=[
                    TimedAdapter("slow_a", 0.25),
                    TimedAdapter("slow_b", 0.25),
                ],
            )
            await orchestrator.start()
            started = time.perf_counter()
            try:
                report = await orchestrator.run_once()
            finally:
                await orchestrator.stop()
            elapsed = time.perf_counter() - started

            self.assertLess(elapsed, 0.45)
            self.assertEqual(report.status, "OK")
            self.assertEqual(report.services["slow_a"], "OK")
            self.assertEqual(report.services["slow_b"], "OK")

        asyncio.run(run())

    def test_one_parallel_failure_does_not_cancel_other_services(self) -> None:
        async def run() -> None:
            orchestrator = Orchestrator(
                shared_state=SharedState(),
                adapters=[
                    FailingTimedAdapter("bad", 0.05),
                    TimedAdapter("good", 0.1),
                ],
            )
            await orchestrator.start()
            try:
                report = await orchestrator.run_once()
            finally:
                await orchestrator.stop()

            self.assertEqual(report.status, "DEGRADED")
            self.assertEqual(report.services["bad"], "ERROR")
            self.assertEqual(report.services["good"], "OK")
            self.assertTrue(
                any(event.source == "good" and event.topic == "TEST_DONE" for event in orchestrator.event_bus.history())
            )

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
