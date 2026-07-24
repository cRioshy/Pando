"""Live ControlCenter tests."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import unittest
from pathlib import Path

from adapters.control_center_adapter import ControlCenterAdapter
from event_bus import Event, EventBus
from shared_state import SharedState


class LiveControlCenterTest(unittest.TestCase):
    def test_control_center_updates_immediately_on_events(self) -> None:
        async def run() -> None:
            bus = EventBus()
            state = SharedState()
            control = ControlCenterAdapter(bus, state, print_output=False)

            await control.start()
            bus.publish(
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
            snapshot = control.get_status()
            await control.stop()

            self.assertEqual(snapshot["events_received"], 2)
            self.assertEqual(snapshot["last_crypto_analysis"]["BTCUSDT"]["direction"], "LONG")
            self.assertEqual(snapshot["last_crypto_analysis"]["BTCUSDT"]["price"], 58420.10)

        asyncio.run(run())

    def test_many_parallel_events_do_not_race(self) -> None:
        async def run() -> None:
            bus = EventBus()
            control = ControlCenterAdapter(bus, SharedState(), print_output=False)
            await control.start()

            async def publish_many(start: int) -> None:
                for index in range(start, start + 50):
                    await asyncio.to_thread(
                        bus.publish,
                        Event(
                            topic="STOCK_ANALYSIS_FINISHED",
                            source="stock",
                            payload={
                                "symbol": f"T{index}",
                                "payload": {
                                    "symbol": f"T{index}",
                                    "market_type": "stock",
                                    "direction": "WAIT",
                                    "probability": 50,
                                    "price": index,
                                },
                            },
                        ),
                    )

            await asyncio.gather(publish_many(0), publish_many(50))
            snapshot = control.get_status()
            await control.stop()

            self.assertEqual(snapshot["event_counts"]["STOCK_ANALYSIS_FINISHED"], 100)
            self.assertEqual(len(snapshot["last_stock_analysis"]), 100)

        asyncio.run(run())

    def test_bad_event_does_not_stop_control_center(self) -> None:
        async def run() -> None:
            bus = EventBus()
            control = ControlCenterAdapter(bus, SharedState(), print_output=False)

            await control.start()
            bus.publish(Event(topic="SYSTEM_ERROR", source="test", payload=[]))
            bus.publish(
                Event(
                    topic="BRAIN_DECISION_RECEIVED",
                    source="brain",
                    payload={"payload": {"symbol": "BTCUSDT", "probability": 70}},
                )
            )
            snapshot = control.get_status()
            await control.stop()

            self.assertTrue(snapshot["running"])
            self.assertGreaterEqual(snapshot["error_count"], 1)
            self.assertEqual(snapshot["last_brain_decision"]["symbol"], "BTCUSDT")

        asyncio.run(run())

    def test_live_task_stops_cleanly(self) -> None:
        async def run() -> None:
            control = ControlCenterAdapter(EventBus(), SharedState(), print_output=False)

            await control.start()
            task = asyncio.create_task(control.run_live_view(refresh_seconds=0.1))
            await asyncio.sleep(0.05)
            await control.stop_live_view()
            await asyncio.wait_for(task, timeout=1.0)
            await control.stop()

            self.assertTrue(task.done())

        asyncio.run(run())

    def test_live_and_headless_cli_modes_start(self) -> None:
        project = Path(__file__).resolve().parents[1]
        env = {**os.environ, "PANDORICKKI_STOCK_TEST_MODE": "1"}
        live = subprocess.run(
            [
                sys.executable,
                "main.py",
                "--live",
                "--cycles",
                "1",
                "--interval",
                "0.1",
                "--refresh",
                "0.1",
            ],
            cwd=project,
            text=True,
            capture_output=True,
            timeout=30,
            env=env,
        )
        headless = subprocess.run(
            [
                sys.executable,
                "main.py",
                "--headless",
                "--cycles",
                "1",
                "--interval",
                "0.1",
            ],
            cwd=project,
            text=True,
            capture_output=True,
            timeout=30,
            env=env,
        )

        self.assertEqual(live.returncode, 0, live.stderr)
        self.assertIn("Modus: live", live.stdout)
        self.assertIn("PANDORICK CONTROL CENTER", live.stdout)
        self.assertEqual(headless.returncode, 0, headless.stderr)
        self.assertIn("Modus: headless", headless.stdout)
        self.assertNotIn("PANDORICK CONTROL CENTER", headless.stdout)

    def test_live_cli_control_off_falls_back_to_headless(self) -> None:
        project = Path(__file__).resolve().parents[1]
        env = {**os.environ, "PANDORICKKI_STOCK_TEST_MODE": "1"}
        result = subprocess.run(
            [
                sys.executable,
                "main.py",
                "--live",
                "--control-off",
                "--cycles",
                "1",
                "--interval",
                "0.1",
            ],
            cwd=project,
            text=True,
            capture_output=True,
            timeout=30,
            env=env,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ControlCenter ist ausgeschaltet", result.stdout)
        self.assertIn("Modus: live-control-off", result.stdout)
        self.assertNotIn("PANDORICK CONTROL CENTER", result.stdout)


if __name__ == "__main__":
    unittest.main()
