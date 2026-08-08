"""Versioned, denominator-explicit learning and outcome metrics."""

from __future__ import annotations

from typing import Any


LEARNING_METRICS_SCHEMA_NAME = "pandorickki.learning-metrics"
LEARNING_METRICS_SCHEMA_VERSION = 1


def build_learning_metrics(
    *,
    decisions_total: int,
    outcome_eligible_decisions: int,
    matched_outcomes: int,
    wins: int,
    losses: int,
    breakeven: int = 0,
    unknown: int = 0,
    learning_update_events: int | None = None,
    matching_method: str = "aggregate_counters",
    coverage_reliable: bool = True,
) -> dict[str, Any]:
    """Return one explicit metric snapshot without implying ML training."""

    decisions_total = max(0, int(decisions_total))
    eligible = max(0, int(outcome_eligible_decisions))
    matched = max(0, int(matched_outcomes))
    wins = max(0, int(wins))
    losses = max(0, int(losses))
    breakeven = max(0, int(breakeven))
    unknown = max(0, int(unknown))
    classified = wins + losses
    closed = wins + losses + breakeven + unknown
    scope_consistent = bool(coverage_reliable and matched <= eligible)
    hit_rate = round(wins / classified * 100, 2) if classified else None
    coverage = round(matched / eligible * 100, 2) if eligible and scope_consistent else None

    return {
        "schema_name": LEARNING_METRICS_SCHEMA_NAME,
        "schema_version": LEARNING_METRICS_SCHEMA_VERSION,
        "decisions": {"total": decisions_total, "outcome_eligible": eligible},
        "outcomes": {
            "matched": matched,
            "closed": closed,
            "wins": wins,
            "losses": losses,
            "breakeven": breakeven,
            "unknown": unknown,
            "classified_for_hit_rate": classified,
            "matching_method": str(matching_method),
        },
        "rates": {
            "hit_rate_percent": hit_rate,
            "hit_rate_numerator": wins,
            "hit_rate_denominator": classified,
            "outcome_coverage_percent": coverage,
            "outcome_coverage_numerator": matched,
            "outcome_coverage_denominator": eligible,
            "outcome_coverage_scope_consistent": scope_consistent,
        },
        "learning": {
            "update_events": None if learning_update_events is None else max(0, int(learning_update_events)),
            "successful_model_updates": None,
            "patterns_learned": None,
        },
        "ml_training": {"active": False, "model_updates": 0, "status": "not_implemented"},
        "definitions": {
            "hit_rate": "wins / (wins + losses); breakeven and unknown are excluded",
            "outcome_coverage": "matched closed outcomes / outcome-eligible LONG or SHORT decisions",
            "learning_update": "AI_LEARNING_UPDATED projection event; not a model-training success",
        },
    }
