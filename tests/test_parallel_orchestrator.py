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


class CountingAdapter(TimedAdapter):
    def __init__(self, name: str = "counting", delay: float = 0.0) -> None:
        super().__init__(name, delay)
        self.starts = 0
        self.stops = 0
        self.cycles = 0

    async def start(self) -> None:
        self.starts += 1

    async def stop(self) -> None:
        self.stops += 1

    async def run_once(self) -> list[Event]:
        self.cycles += 1
        return await super().run_once()


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

    def test_stop_interrupts_long_cycle_wait(self) -> None:
        async def run() -> None:
            adapter = CountingAdapter()
            orchestrator = Orchestrator(shared_state=SharedState(), adapters=[adapter])
            stop_requested = False
            await orchestrator.start()
            task = asyncio.create_task(
                orchestrator.run_continuous(
                    cycle_interval=10.0,
                    should_stop=lambda: stop_requested,
                )
            )
            while adapter.cycles < 1:
                await asyncio.sleep(0.01)
            started = time.perf_counter()
            stop_requested = True
            await asyncio.wait_for(task, timeout=0.5)
            elapsed = time.perf_counter() - started
            await orchestrator.stop()

            self.assertLess(elapsed, 0.3)

        asyncio.run(run())

    def test_restart_request_restarts_adapters_in_process(self) -> None:
        async def run() -> None:
            adapter = CountingAdapter()
            orchestrator = Orchestrator(shared_state=SharedState(), adapters=[adapter])
            restart_pending = True

            def take_restart() -> bool:
                nonlocal restart_pending
                if not restart_pending:
                    return False
                restart_pending = False
                return True

            await orchestrator.start()
            try:
                await orchestrator.run_continuous(
                    cycle_interval=10.0,
                    max_cycles=1,
                    take_restart_request=take_restart,
                )
                self.assertEqual(adapter.starts, 2)
                self.assertEqual(adapter.stops, 1)
                self.assertEqual(adapter.cycles, 1)
            finally:
                await orchestrator.stop()

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
