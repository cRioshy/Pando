"""Small isolated example of a Pandorick-style strategy arena.

The idea mirrors the Iterated Prisoner's Dilemma pattern:
strategies receive history, produce a move, and later get scored from outcomes.

This module is a standalone example only. It does not place orders and it is not
connected to the productive DecisionCore, Brain, Crypto, Stock, or Telegram code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Protocol


Action = str
VALID_ACTIONS = {"LONG", "SHORT", "HOLD", "WAIT"}


@dataclass(frozen=True)
class MarketSnapshot:
    """Minimal market facts a strategy may inspect."""

    market_type: str
    symbol: str
    trend_score: float
    momentum_score: float
    volatility_score: float
    volume_score: float
    probability: float
    current_price: float | None = None


@dataclass(frozen=True)
class DecisionRecord:
    """One previous strategy or platform decision."""

    strategy_name: str
    symbol: str
    action: Action
    confidence: float
    decision_id: str | None = None


@dataclass(frozen=True)
class OutcomeRecord:
    """One completed simulated outcome linked to a decision or strategy."""

    strategy_name: str
    symbol: str
    action: Action
    result: str
    profit_percent: float
    decision_id: str | None = None


@dataclass
class StrategyVote:
    """A strategy's current recommendation."""

    strategy_name: str
    action: Action
    confidence: float
    reason: str


@dataclass
class StrategyScore:
    """Persistent-like score summary for one strategy."""

    strategy_name: str
    decisions: int = 0
    wins: int = 0
    losses: int = 0
    total_profit_percent: float = 0.0

    @property
    def hit_rate(self) -> float | None:
        total = self.wins + self.losses
        if total == 0:
            return None
        return round(self.wins / total * 100, 2)

    @property
    def average_profit_percent(self) -> float | None:
        if self.decisions == 0:
            return None
        return round(self.total_profit_percent / self.decisions, 4)


class Strategy(Protocol):
    """Protocol for arena strategies."""

    name: str

    def decide(
        self,
        snapshot: MarketSnapshot,
        decision_history: list[DecisionRecord],
        outcome_history: list[OutcomeRecord],
    ) -> StrategyVote:
        """Return a recommendation for the current snapshot."""


class TrendFollowerStrategy:
    """Favors LONG when trend and momentum are strong."""

    name = "trend_follower"

    def decide(
        self,
        snapshot: MarketSnapshot,
        decision_history: list[DecisionRecord],
        outcome_history: list[OutcomeRecord],
    ) -> StrategyVote:
        if snapshot.trend_score >= 65 and snapshot.momentum_score >= 55:
            confidence = min(90.0, mean([snapshot.trend_score, snapshot.momentum_score, snapshot.probability]))
            return StrategyVote(self.name, "LONG", round(confidence, 2), "Trend und Momentum bestaetigen LONG.")
        if snapshot.trend_score <= 35 and snapshot.momentum_score <= 45:
            confidence = min(85.0, 100.0 - mean([snapshot.trend_score, snapshot.momentum_score]))
            return StrategyVote(self.name, "SHORT", round(confidence, 2), "Trend und Momentum bestaetigen SHORT.")
        return StrategyVote(self.name, "HOLD", 50.0, "Trend ist nicht klar genug.")


class RiskGuardStrategy:
    """Blocks aggressive moves during high volatility or weak history."""

    name = "risk_guard"

    def decide(
        self,
        snapshot: MarketSnapshot,
        decision_history: list[DecisionRecord],
        outcome_history: list[OutcomeRecord],
    ) -> StrategyVote:
        recent = [item for item in outcome_history[-20:] if item.symbol == snapshot.symbol]
        recent_losses = sum(1 for item in recent if item.result.upper() == "LOSS")
        if snapshot.volatility_score >= 75:
            return StrategyVote(self.name, "WAIT", 70.0, "Volatilitaet ist zu hoch.")
        if recent_losses >= 3:
            return StrategyVote(self.name, "WAIT", 68.0, "Zu viele aktuelle Verluste im Symbol.")
        return StrategyVote(self.name, "HOLD", 55.0, "Risiko ist akzeptabel, aber kein eigener Einstieg.")


class MeanReversionStrategy:
    """Looks for exhaustion after strong one-sided movement."""

    name = "mean_reversion"

    def decide(
        self,
        snapshot: MarketSnapshot,
        decision_history: list[DecisionRecord],
        outcome_history: list[OutcomeRecord],
    ) -> StrategyVote:
        if snapshot.trend_score >= 80 and snapshot.momentum_score < 45:
            return StrategyVote(self.name, "SHORT", 62.0, "Starker Trend verliert Momentum.")
        if snapshot.trend_score <= 20 and snapshot.momentum_score > 55:
            return StrategyVote(self.name, "LONG", 62.0, "Abverkauf verliert Druck.")
        return StrategyVote(self.name, "HOLD", 50.0, "Keine klare Ruecklauf-Chance.")


@dataclass
class StrategyArena:
    """Runs multiple strategies and combines their votes safely."""

    strategies: list[Strategy]
    scores: dict[str, StrategyScore] = field(default_factory=dict)

    def vote(
        self,
        snapshot: MarketSnapshot,
        decision_history: list[DecisionRecord],
        outcome_history: list[OutcomeRecord],
    ) -> dict[str, object]:
        """Run all strategies and produce one combined recommendation."""

        votes = [
            strategy.decide(snapshot, decision_history, outcome_history)
            for strategy in self.strategies
        ]
        for vote in votes:
            self.scores.setdefault(vote.strategy_name, StrategyScore(vote.strategy_name))

        weighted: dict[Action, float] = {action: 0.0 for action in VALID_ACTIONS}
        for vote in votes:
            score = self.scores[vote.strategy_name]
            history_weight = 1.0
            if score.hit_rate is not None:
                history_weight += max(-0.25, min(0.35, (score.hit_rate - 50.0) / 100.0))
            weighted[vote.action] += vote.confidence * history_weight

        action = max(weighted.items(), key=lambda item: item[1])[0]
        confidence = round(min(95.0, weighted[action] / max(1, len(votes))), 2)
        return {
            "symbol": snapshot.symbol,
            "action": action,
            "confidence": confidence,
            "votes": [vote.__dict__ for vote in votes],
            "scores": {name: score.__dict__ | {"hit_rate": score.hit_rate} for name, score in self.scores.items()},
        }

    def learn_from_outcome(self, outcome: OutcomeRecord) -> None:
        """Update one strategy score from a completed simulated outcome."""

        score = self.scores.setdefault(outcome.strategy_name, StrategyScore(outcome.strategy_name))
        score.decisions += 1
        if outcome.result.upper() == "WIN":
            score.wins += 1
        elif outcome.result.upper() == "LOSS":
            score.losses += 1
        score.total_profit_percent += outcome.profit_percent


def demo() -> dict[str, object]:
    """Run a tiny standalone demo with fake local input data."""

    arena = StrategyArena(
        strategies=[
            TrendFollowerStrategy(),
            RiskGuardStrategy(),
            MeanReversionStrategy(),
        ]
    )
    outcomes = [
        OutcomeRecord("trend_follower", "BTCUSDT", "LONG", "WIN", 1.2),
        OutcomeRecord("trend_follower", "BTCUSDT", "LONG", "LOSS", -0.8),
        OutcomeRecord("risk_guard", "BTCUSDT", "WAIT", "WIN", 0.0),
    ]
    for outcome in outcomes:
        arena.learn_from_outcome(outcome)

    snapshot = MarketSnapshot(
        market_type="crypto",
        symbol="BTCUSDT",
        trend_score=72.0,
        momentum_score=61.0,
        volatility_score=48.0,
        volume_score=64.0,
        probability=66.0,
        current_price=64488.01,
    )
    return arena.vote(snapshot, [], outcomes)


if __name__ == "__main__":
    import json

    print(json.dumps(demo(), indent=2, ensure_ascii=True))
