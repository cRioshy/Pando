"""Tests for the isolated strategy arena example."""

from __future__ import annotations

import unittest

from strategy_arena.strategy_arena_example import (
    MarketSnapshot,
    OutcomeRecord,
    RiskGuardStrategy,
    StrategyArena,
    TrendFollowerStrategy,
    demo,
)


class StrategyArenaExampleTest(unittest.TestCase):
    def test_demo_returns_valid_vote(self) -> None:
        result = demo()

        self.assertIn(result["action"], {"LONG", "SHORT", "HOLD", "WAIT"})
        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertGreater(len(result["votes"]), 0)

    def test_risk_guard_waits_after_symbol_losses(self) -> None:
        arena = StrategyArena([TrendFollowerStrategy(), RiskGuardStrategy()])
        outcomes = [
            OutcomeRecord("risk_guard", "AAPL", "LONG", "LOSS", -0.5),
            OutcomeRecord("risk_guard", "AAPL", "LONG", "LOSS", -0.7),
            OutcomeRecord("risk_guard", "AAPL", "LONG", "LOSS", -0.4),
        ]
        snapshot = MarketSnapshot(
            market_type="stock",
            symbol="AAPL",
            trend_score=70,
            momentum_score=60,
            volatility_score=40,
            volume_score=55,
            probability=65,
            current_price=321.74,
        )

        result = arena.vote(snapshot, [], outcomes)
        risk_vote = [vote for vote in result["votes"] if vote["strategy_name"] == "risk_guard"][0]

        self.assertEqual(risk_vote["action"], "WAIT")


if __name__ == "__main__":
    unittest.main()
