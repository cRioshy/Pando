"""Full Phase 5 integration test for PandorickKi."""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from adapters.brain_adapter import BRAIN_DECISION_RECEIVED, BrainAdapter
from adapters.control_center_adapter import CONTROL_STATUS_UPDATED, ControlCenterAdapter
from adapters.crypto_adapter import CRYPTO_ANALYSIS_FINISHED, CryptoAdapter
from adapters.decision_signal_adapter import DECISION_CREATED, SIGNAL_CREATED, DecisionSignalAdapter
from adapters.stock_adapter import STOCK_ANALYSIS_FINISHED, StockAdapter
from adapters.telegram_adapter import TelegramAdapter
from brain_event_store import BrainEventReader
from event_bus import Event
from orchestrator import Orchestrator
from shared_state import SharedState


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STOCK_PROJECT = PROJECT_ROOT.parent / "pandorick_stock_bot"
CRYPTO_PROJECT = Path("C:/Users/Admin/Desktop/VIP-Trade-Engine-4.5(Monitor)")


class FullIntegrationTest(unittest.TestCase):
    def test_phase5_full_platform_flow_with_test_data(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                event_bus_events: list[Event] = []
                brain_path = temp_path / "brain_events.jsonl"
                shared_state = SharedState(temp_path / "shared_state.json")

                orchestrator = Orchestrator(adapters=[], shared_state=shared_state)
                bus = orchestrator.event_bus
                control = ControlCenterAdapter(bus, shared_state, print_output=False)
                orchestrator.adapters = [
                    CryptoAdapter(
                        bus,
                        CRYPTO_PROJECT,
                        symbols=["BTCUSDT", "ETHUSDT"],
                        test_mode=True,
                        persist_existing=False,
                    ),
                    BrainAdapter(bus, brain_path),
                    DecisionSignalAdapter(bus),
                    StockAdapter(bus, STOCK_PROJECT, test_mode=True),
                    TelegramAdapter(bus, enabled=False, dry_run=True, log_file=temp_path / "telegram.jsonl"),
                    control,
                ]
                bus.subscribe("*", event_bus_events.append)

                await orchestrator.start()
                try:
                    report = await orchestrator.run_once()
                    control_status = control.get_status()
                finally:
                    await orchestrator.stop()

                topics = [event.topic for event in event_bus_events]
                crypto_events = [event for event in event_bus_events if event.topic == CRYPTO_ANALYSIS_FINISHED]
                stock_events = [event for event in event_bus_events if event.topic == STOCK_ANALYSIS_FINISHED]
                brain_events = [event for event in event_bus_events if event.topic == BRAIN_DECISION_RECEIVED]
                decision_events = [event for event in event_bus_events if event.topic == DECISION_CREATED]
                signal_events = [event for event in event_bus_events if event.topic == SIGNAL_CREATED]

                self.assertEqual(report.status, "OK")
                self.assertTrue(crypto_events, "Krypto-Daten muessen ankommen.")
                self.assertTrue(stock_events, "Aktien-Daten muessen ankommen.")
                self.assertIn(CONTROL_STATUS_UPDATED, topics)

                market_types = {
                    event.payload["payload"]["market_type"]
                    for event in [*crypto_events, *stock_events]
                }
                self.assertEqual(market_types, {"crypto", "stock"})

                self.assertEqual(len(brain_events), len(crypto_events) + len(stock_events))
                self.assertEqual(len(decision_events), len(brain_events))
                self.assertEqual(len(signal_events), len(brain_events))
                stored = BrainEventReader(
                    legacy_file=brain_path,
                    rotated_root=brain_path.parent / "brain_events",
                ).recent(limit=20)
                self.assertEqual(
                    {record["market_type"] for record in stored},
                    {"crypto", "stock"},
                )

                self.assertEqual(control_status["platform_health"], "OK")
                self.assertGreaterEqual(
                    control_status["event_counts"].get(CRYPTO_ANALYSIS_FINISHED, 0),
                    1,
                )
                self.assertGreaterEqual(
                    control_status["event_counts"].get(STOCK_ANALYSIS_FINISHED, 0),
                    1,
                )
                self.assertEqual(
                    control_status["event_counts"].get(BRAIN_DECISION_RECEIVED, 0),
                    len(crypto_events) + len(stock_events),
                )
                self.assertEqual(
                    control_status["event_counts"].get(DECISION_CREATED, 0),
                    len(brain_events),
                )
                self.assertEqual(
                    control_status["event_counts"].get(SIGNAL_CREATED, 0),
                    len(brain_events),
                )

                self.assertNotIn("TELEGRAM_MESSAGE_SENT", topics)
                self.assertIn("TELEGRAM_MESSAGE_READY", topics)

                stopped_services = shared_state.to_dict()["services"]
                self.assertEqual(stopped_services["crypto"]["status"], "STOPPED")
                self.assertEqual(stopped_services["brain"]["status"], "STOPPED")
                self.assertEqual(stopped_services["decision_core"]["status"], "STOPPED")
                self.assertEqual(stopped_services["stock"]["status"], "STOPPED")
                self.assertEqual(stopped_services["control_center"]["status"], "STOPPED")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
