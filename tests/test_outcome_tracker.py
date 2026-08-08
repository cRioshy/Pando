"""Tests for persistent simulated outcome tracking."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from adapters.crypto_trade_tracker import CRYPTO_TRADE_UPDATED
from adapters.decision_signal_adapter import DECISION_CREATED, SIGNAL_CREATED
from adapters.outcome_tracker import (
    OUTCOME_TRACKER_ERROR,
    SIMULATED_TRADE_CLOSED,
    SIMULATED_TRADE_OPENED,
    SIMULATED_TRADE_UPDATED,
    OutcomeTracker,
    _duration_seconds,
)
from event_bus import Event, EventBus


def decision(direction: str, *, decision_id: str = "decision-1", symbol: str = "BTCUSDT") -> Event:
    return Event(
        topic=DECISION_CREATED,
        source="decision_core",
        payload={
            "payload": {
                "decision_id": decision_id,
                "market_type": "crypto",
                "symbol": symbol,
                "direction": direction,
                "current_price": 100.0,
                "price": 100.0,
                "created_at": "2026-07-22T10:00:00+00:00",
                "source_event_id": "analysis-1",
            }
        },
    )


def trade_update(
    status: str,
    *,
    decision_id: str = "decision-1",
    symbol: str = "BTCUSDT",
    price: float = 103.0,
    profit: float = 3.0,
) -> Event:
    return Event(
        topic=CRYPTO_TRADE_UPDATED,
        source="crypto_trade_tracker",
        payload={
            "payload": {
                "decision_id": decision_id,
                "symbol": symbol,
                "direction": "LONG",
                "current_price": price,
                "current_stop_loss": 98.0,
                "initial_stop_loss": 98.0,
                "take_profit_1": 103.0,
                "current_profit_percent": profit,
                "max_profit_percent": max(profit, 0.0),
                "max_drawdown_percent": min(profit, 0.0),
                "trade_status": status,
                "updated_at": "2026-07-22T10:05:00+00:00",
            }
        },
    )


def signal(*, decision_id: str = "decision-1", signal_id: str = "signal-1") -> Event:
    return Event(
        topic=SIGNAL_CREATED,
        source="decision_core",
        payload={
            "payload": {
                "decision_id": decision_id,
                "signal_id": signal_id,
                "market_type": "crypto",
                "symbol": "BTCUSDT",
                "direction": "LONG",
            }
        },
    )


def market_update(
    *,
    topic: str = "CRYPTO_ANALYSIS_FINISHED",
    symbol: str = "BTCUSDT",
    market_type: str = "crypto",
    price: float = 104.0,
    source_timestamp: str = "2026-07-22T10:05:00+00:00",
) -> Event:
    return Event(
        topic=topic,
        source=market_type,
        payload={
            "payload": {
                "market_type": market_type,
                "symbol": symbol,
                "current_price": price,
                "price": price,
                "source_timestamp": source_timestamp,
            }
        },
    )


class OutcomeTrackerTest(unittest.TestCase):
    def test_duration_seconds_normalizes_legacy_naive_timestamps_to_utc(self) -> None:
        cases = (
            ("2026-07-22T10:00:00", "2026-07-22T10:05:00", 300.0),
            ("2026-07-22T10:00:00", "2026-07-22T10:05:00+00:00", 300.0),
            ("2026-07-22T10:00:00+00:00", "2026-07-22T10:05:00", 300.0),
            ("2026-07-22T10:00:00Z", "2026-07-22T10:05:00+00:00", 300.0),
            ("2026-07-22T10:00:00+01:00", "2026-07-22T09:05:00+00:00", 300.0),
        )

        for start, end, expected in cases:
            with self.subTest(start=start, end=end):
                self.assertEqual(_duration_seconds(start, end), expected)
        self.assertIsNone(_duration_seconds("not-a-time", "2026-07-22T10:05:00+00:00"))
        self.assertEqual(
            _duration_seconds("2026-07-22T10:05:00+00:00", "2026-07-22T10:00:00+00:00"),
            0.0,
        )

    def test_long_decision_opens_persistent_simulated_trade_once(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                opened = []
                bus.subscribe(SIMULATED_TRADE_OPENED, opened.append)
                tracker = OutcomeTracker(
                    bus,
                    open_trades_file=Path(temp) / "open.json",
                    outcomes_file=Path(temp) / "outcomes.jsonl",
                )

                await tracker.start()
                bus.publish(decision("LONG"))
                bus.publish(decision("LONG"))
                health = await tracker.health()
                await tracker.stop()

                open_data = json.loads((Path(temp) / "open.json").read_text(encoding="utf-8"))
                outcome_lines = (Path(temp) / "outcomes.jsonl").read_text(encoding="utf-8").splitlines()

                self.assertEqual(len(opened), 1)
                self.assertEqual(health["open_trades"], 1)
                self.assertEqual(health["opened_trades"], 1)
                self.assertEqual(health["duplicates_ignored"], 1)
                self.assertIn("decision-1", open_data)
                self.assertEqual(open_data["decision-1"]["trade_status"], "OPEN")
                self.assertEqual(len(outcome_lines), 1)

        asyncio.run(run())

    def test_wait_decision_does_not_open_trade(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                tracker = OutcomeTracker(
                    bus,
                    open_trades_file=Path(temp) / "open.json",
                    outcomes_file=Path(temp) / "outcomes.jsonl",
                )

                await tracker.start()
                bus.publish(decision("WAIT"))
                health = await tracker.health()
                await tracker.stop()

                self.assertEqual(health["open_trades"], 0)
                self.assertEqual(health["ignored_decisions"], 1)
                self.assertFalse((Path(temp) / "outcomes.jsonl").exists())

        asyncio.run(run())

    def test_open_trades_are_loaded_after_restart(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                open_file = Path(temp) / "open.json"
                outcomes_file = Path(temp) / "outcomes.jsonl"
                bus = EventBus()
                tracker = OutcomeTracker(bus, open_trades_file=open_file, outcomes_file=outcomes_file)

                await tracker.start()
                bus.publish(decision("SHORT", decision_id="decision-2", symbol="ETHUSDT"))
                await tracker.stop()

                restarted = OutcomeTracker(EventBus(), open_trades_file=open_file, outcomes_file=outcomes_file)
                await restarted.start()
                health = await restarted.health()
                await restarted.stop()

                self.assertEqual(health["open_trades"], 1)

        asyncio.run(run())

    def test_signal_links_to_open_outcome_by_decision_id(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                tracker = OutcomeTracker(
                    bus,
                    open_trades_file=Path(temp) / "open.json",
                    outcomes_file=Path(temp) / "outcomes.jsonl",
                )

                await tracker.start()
                bus.publish(decision("LONG", decision_id="decision-linked"))
                bus.publish(signal(decision_id="decision-linked", signal_id="signal-linked"))
                health = await tracker.health()
                await tracker.stop()

                open_data = json.loads((Path(temp) / "open.json").read_text(encoding="utf-8"))
                records = [
                    json.loads(line)
                    for line in (Path(temp) / "outcomes.jsonl").read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]

                self.assertEqual(health["linked_signals"], 1)
                self.assertEqual(open_data["decision-linked"]["signal_id"], "signal-linked")
                self.assertEqual(records[-1]["record_type"], "SIMULATED_TRADE_SIGNAL_LINKED")

        asyncio.run(run())

    def test_trade_update_refreshes_open_outcome_without_closing(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                updated = []
                bus.subscribe(SIMULATED_TRADE_UPDATED, updated.append)
                tracker = OutcomeTracker(
                    bus,
                    open_trades_file=Path(temp) / "open.json",
                    outcomes_file=Path(temp) / "outcomes.jsonl",
                )

                await tracker.start()
                bus.publish(decision("LONG"))
                bus.publish(trade_update("BREAK_EVEN", price=101.0, profit=1.0))
                health = await tracker.health()
                await tracker.stop()

                open_data = json.loads((Path(temp) / "open.json").read_text(encoding="utf-8"))
                trade = open_data["decision-1"]
                self.assertEqual(len(updated), 1)
                self.assertEqual(health["open_trades"], 1)
                self.assertEqual(trade["trade_status"], "BREAK_EVEN")
                self.assertEqual(trade["current_profit_percent"], 1.0)

        asyncio.run(run())

    def test_terminal_trade_update_closes_outcome(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                closed = []
                bus.subscribe(SIMULATED_TRADE_CLOSED, closed.append)
                tracker = OutcomeTracker(
                    bus,
                    open_trades_file=Path(temp) / "open.json",
                    outcomes_file=Path(temp) / "outcomes.jsonl",
                )

                await tracker.start()
                bus.publish(decision("LONG"))
                bus.publish(trade_update("TP1_REACHED", price=103.0, profit=3.0))
                health = await tracker.health()
                await tracker.stop()

                open_data = json.loads((Path(temp) / "open.json").read_text(encoding="utf-8"))
                records = [
                    json.loads(line)
                    for line in (Path(temp) / "outcomes.jsonl").read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                closed_payload = closed[0].payload["payload"]

                self.assertEqual(open_data, {})
                self.assertEqual(health["closed_trades"], 1)
                self.assertEqual(closed_payload["outcome_status"], "CLOSED")
                self.assertEqual(closed_payload["result_type"], "WIN")
                self.assertEqual(closed_payload["gross_profit_percent"], 3.0)
                self.assertIsNotNone(closed_payload["holding_seconds"])
                self.assertEqual(records[-1]["record_type"], "SIMULATED_TRADE_CLOSED")

        asyncio.run(run())

    def test_unknown_trade_update_is_ignored(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                tracker = OutcomeTracker(
                    EventBus(),
                    open_trades_file=Path(temp) / "open.json",
                    outcomes_file=Path(temp) / "outcomes.jsonl",
                )

                await tracker.start()
                tracker.event_bus.publish(trade_update("STOPPED", decision_id="missing"))
                health = await tracker.health()
                await tracker.stop()

                self.assertEqual(health["ignored_trade_updates"], 1)
                self.assertEqual(health["closed_trades"], 0)

        asyncio.run(run())

    def test_market_analysis_update_refreshes_profit_without_closing_before_horizon(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                updated = []
                bus.subscribe(SIMULATED_TRADE_UPDATED, updated.append)
                tracker = OutcomeTracker(
                    bus,
                    open_trades_file=Path(temp) / "open.json",
                    outcomes_file=Path(temp) / "outcomes.jsonl",
                    evaluation_horizon_seconds=600,
                )

                await tracker.start()
                bus.publish(decision("LONG"))
                bus.publish(market_update(price=102.5, source_timestamp="2026-07-22T10:05:00+00:00"))
                health = await tracker.health()
                await tracker.stop()

                open_data = json.loads((Path(temp) / "open.json").read_text(encoding="utf-8"))
                trade = open_data["decision-1"]

                self.assertEqual(len(updated), 1)
                self.assertEqual(health["open_trades"], 1)
                self.assertEqual(health["market_price_updates"], 1)
                self.assertEqual(trade["current_price"], 102.5)
                self.assertEqual(trade["current_profit_percent"], 2.5)
                self.assertEqual(trade["max_profit_percent"], 2.5)

        asyncio.run(run())

    def test_market_analysis_update_closes_after_horizon_with_decision_id(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                closed = []
                bus.subscribe(SIMULATED_TRADE_CLOSED, closed.append)
                tracker = OutcomeTracker(
                    bus,
                    open_trades_file=Path(temp) / "open.json",
                    outcomes_file=Path(temp) / "outcomes.jsonl",
                    evaluation_horizon_seconds=60,
                )

                await tracker.start()
                bus.publish(decision("LONG"))
                bus.publish(market_update(price=101.0, source_timestamp="2026-07-22T10:02:00+00:00"))
                health = await tracker.health()
                await tracker.stop()

                open_data = json.loads((Path(temp) / "open.json").read_text(encoding="utf-8"))
                records = [
                    json.loads(line)
                    for line in (Path(temp) / "outcomes.jsonl").read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                closed_payload = closed[0].payload["payload"]

                self.assertEqual(open_data, {})
                self.assertEqual(health["closed_trades"], 1)
                self.assertEqual(closed_payload["decision_id"], "decision-1")
                self.assertEqual(closed_payload["result_type"], "WIN")
                self.assertEqual(closed_payload["gross_profit_percent"], 1.0)
                self.assertEqual(records[-1]["record_type"], "SIMULATED_TRADE_CLOSED")

        asyncio.run(run())

    def test_legacy_naive_entry_time_closes_against_utc_market_update(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                closed = []
                errors = []
                bus.subscribe(SIMULATED_TRADE_CLOSED, closed.append)
                bus.subscribe(OUTCOME_TRACKER_ERROR, errors.append)
                tracker = OutcomeTracker(
                    bus,
                    open_trades_file=Path(temp) / "open.json",
                    outcomes_file=Path(temp) / "outcomes.jsonl",
                    evaluation_horizon_seconds=60,
                )
                legacy_decision = decision("LONG", decision_id="legacy-naive")
                legacy_decision.payload["payload"]["created_at"] = "2026-07-22T10:00:00"

                await tracker.start()
                bus.publish(legacy_decision)
                bus.publish(market_update(price=101.0, source_timestamp="2026-07-22T10:02:00+00:00"))
                health = await tracker.health()
                await tracker.stop()

                self.assertEqual(errors, [])
                self.assertEqual(health["closed_trades"], 1)
                self.assertTrue(health["healthy"])
                self.assertIsNone(health["last_error"])
                self.assertEqual(closed[0].payload["payload"]["decision_id"], "legacy-naive")
                self.assertGreaterEqual(closed[0].payload["payload"]["holding_seconds"], 120.0)

        asyncio.run(run())

    def test_decision_without_entry_price_is_ignored(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                bus = EventBus()
                tracker = OutcomeTracker(
                    bus,
                    open_trades_file=Path(temp) / "open.json",
                    outcomes_file=Path(temp) / "outcomes.jsonl",
                )
                event = decision("LONG", symbol="SPCX")
                event.payload["payload"]["current_price"] = None
                event.payload["payload"]["price"] = None

                await tracker.start()
                bus.publish(event)
                health = await tracker.health()
                await tracker.stop()

                self.assertEqual(health["open_trades"], 0)
                self.assertEqual(health["ignored_decisions"], 1)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
