"""Observer-only, fail-closed contract for future PandorickKi decisions.

This module does not subscribe to the EventBus and does not release messages,
signals, simulated trades or orders.  It only evaluates one candidate against
an explicit policy and returns a compact, JSON-safe result.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping

from feature_data_quality_contract import (
    FEATURE_DATA_QUALITY_SCHEMA,
    FEATURE_DATA_QUALITY_VERSION,
    project_feature_data_quality,
)


DECISION_GATE_SCHEMA = "pandorickki.decision-gate"
DECISION_GATE_VERSION = 1


@dataclass(frozen=True)
class DecisionGatePolicy:
    """Explicit policy required for an observer evaluation.

    Probability thresholds intentionally have no defaults: a future rollout
    must choose and document them instead of inheriting a hidden product rule.
    """

    minimum_probability: float
    minimum_confidence: float
    confidence_tolerance: float = 0.0
    eligible_directions: frozenset[str] = field(
        default_factory=lambda: frozenset({"LONG", "SHORT"})
    )
    allowed_market_types: frozenset[str] = field(
        default_factory=lambda: frozenset({"crypto", "stock"})
    )
    allowed_quality_statuses: frozenset[str] = field(
        default_factory=lambda: frozenset({"PASS"})
    )
    require_verified_order: bool = True
    require_ready_warmup: bool = True
    require_facts: bool = True
    require_risk_plan: bool = True

    def __post_init__(self) -> None:
        for name, value in (
            ("minimum_probability", self.minimum_probability),
            ("minimum_confidence", self.minimum_confidence),
        ):
            numeric = _finite_number(value)
            if numeric is None or not 0.0 <= numeric <= 100.0:
                raise ValueError(f"{name} must be finite and between 0 and 100")
        tolerance = _finite_number(self.confidence_tolerance)
        if tolerance is None or tolerance < 0.0:
            raise ValueError("confidence_tolerance must be finite and non-negative")
        if not self.eligible_directions:
            raise ValueError("eligible_directions must not be empty")
        if not self.allowed_market_types:
            raise ValueError("allowed_market_types must not be empty")
        if not self.allowed_quality_statuses:
            raise ValueError("allowed_quality_statuses must not be empty")


def project_feature_quality(candidate: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return the bounded quality fields needed by the Decision Gate.

    During migration the report may live in `features.metadata.data_quality`.
    Future compact events can carry the returned projection as
    `feature_quality`, without forwarding the full feature block.
    """

    return project_feature_data_quality(candidate)


def evaluate_decision_gate(
    candidate: Mapping[str, Any],
    *,
    policy: DecisionGatePolicy,
) -> dict[str, Any]:
    """Evaluate a candidate without causing any runtime side effect."""

    reasons: list[str] = []
    market_type = str(candidate.get("market_type") or "").strip().lower()
    symbol = str(candidate.get("symbol") or "").strip().upper()
    direction = str(candidate.get("direction") or "").strip().upper()
    probability = _finite_number(candidate.get("probability"))
    confidence = _finite_number(candidate.get("confidence"))
    price = _finite_number(_first_present(candidate, "current_price", "price"))
    quality = project_feature_quality(candidate)

    if market_type not in policy.allowed_market_types:
        reasons.append("DG_MARKET_NOT_ALLOWED")
    if not symbol:
        reasons.append("DG_SYMBOL_MISSING")
    if direction not in policy.eligible_directions:
        reasons.append("DG_DIRECTION_NOT_ELIGIBLE")
    if price is None or price <= 0.0:
        reasons.append("DG_PRICE_INVALID")

    if probability is None or not 0.0 <= probability <= 100.0:
        reasons.append("DG_PROBABILITY_INVALID")
    elif probability < policy.minimum_probability:
        reasons.append("DG_PROBABILITY_BELOW_THRESHOLD")
    if confidence is None or not 0.0 <= confidence <= 100.0:
        reasons.append("DG_CONFIDENCE_INVALID")
    elif confidence < policy.minimum_confidence:
        reasons.append("DG_CONFIDENCE_BELOW_THRESHOLD")
    if (
        probability is not None
        and confidence is not None
        and abs(probability - confidence) > policy.confidence_tolerance
    ):
        reasons.append("DG_CONFIDENCE_CONFLICT")

    facts = candidate.get("facts")
    if policy.require_facts and not _has_content(facts):
        reasons.append("DG_FACTS_MISSING")
    if candidate.get("feature_error"):
        reasons.append("DG_FEATURE_ERROR")
    _check_quality(quality, policy, reasons)
    if policy.require_risk_plan and direction in policy.eligible_directions:
        _check_risk(candidate.get("risk"), direction, price, reasons)

    qualified = not reasons
    return {
        "schema_name": DECISION_GATE_SCHEMA,
        "schema_version": DECISION_GATE_VERSION,
        "mode": "OBSERVER",
        "gate_status": "QUALIFIED" if qualified else "BLOCKED",
        "release_status": "OBSERVER_ONLY",
        "qualified": qualified,
        # Version 1 can never release Telegram or orders by construction.
        "ready_for_telegram": False,
        "order_execution_allowed": False,
        "reason_codes": ["DG_QUALIFIED"] if qualified else reasons,
        "source_event_id": candidate.get("source_event_id"),
        "market_type": market_type or None,
        "symbol": symbol or None,
        "direction": direction or None,
        "probability": probability,
        "confidence": confidence,
        "price": price,
        "feature_quality": quality,
        "policy": {
            "minimum_probability": float(policy.minimum_probability),
            "minimum_confidence": float(policy.minimum_confidence),
            "confidence_tolerance": float(policy.confidence_tolerance),
            "eligible_directions": sorted(policy.eligible_directions),
            "allowed_market_types": sorted(policy.allowed_market_types),
            "allowed_quality_statuses": sorted(policy.allowed_quality_statuses),
            "require_verified_order": policy.require_verified_order,
            "require_ready_warmup": policy.require_ready_warmup,
            "require_facts": policy.require_facts,
            "require_risk_plan": policy.require_risk_plan,
        },
    }


def _check_quality(
    quality: Mapping[str, Any] | None,
    policy: DecisionGatePolicy,
    reasons: list[str],
) -> None:
    if quality is None:
        reasons.append("DG_QUALITY_MISSING")
        return
    if (
        quality.get("schema_name") != FEATURE_DATA_QUALITY_SCHEMA
        or quality.get("schema_version") != FEATURE_DATA_QUALITY_VERSION
    ):
        reasons.append("DG_QUALITY_SCHEMA_UNSUPPORTED")
    if quality.get("status") not in policy.allowed_quality_statuses:
        reasons.append("DG_QUALITY_STATUS_NOT_ALLOWED")
    order = quality.get("order")
    if policy.require_verified_order and (
        not isinstance(order, Mapping) or order.get("status") != "VERIFIED"
    ):
        reasons.append("DG_ORDER_NOT_VERIFIED")
    warmup = quality.get("warmup")
    if policy.require_ready_warmup and (
        not isinstance(warmup, Mapping) or warmup.get("status") != "READY"
    ):
        reasons.append("DG_WARMUP_NOT_READY")


def _check_risk(
    risk: Any,
    direction: str,
    price: float | None,
    reasons: list[str],
) -> None:
    if not isinstance(risk, Mapping):
        reasons.append("DG_RISK_MISSING")
        return
    risk_action = str(risk.get("action") or "").strip().upper()
    if risk_action and risk_action != direction:
        reasons.append("DG_RISK_DIRECTION_CONFLICT")

    stop = _finite_number(_first_present(risk, "stop_loss", "stop"))
    take_profit = risk.get("take_profit")
    if isinstance(take_profit, (list, tuple)):
        targets = [_finite_number(value) for value in take_profit]
        targets = [value for value in targets if value is not None]
    else:
        one_target = _finite_number(_first_present(risk, "take_profit_1", "take_profit"))
        targets = [] if one_target is None else [one_target]

    if price is None or stop is None or stop <= 0.0 or (
        direction == "LONG" and stop >= price
    ) or (direction == "SHORT" and stop <= price):
        reasons.append("DG_STOP_LOSS_INVALID")
    if not targets or any(target <= 0.0 for target in targets) or (
        direction == "LONG" and not any(target > price for target in targets if price is not None)
    ) or (
        direction == "SHORT" and not any(target < price for target in targets if price is not None)
    ):
        reasons.append("DG_TAKE_PROFIT_INVALID")


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _first_present(values: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in values and values[key] is not None:
            return values[key]
    return None


def _has_content(value: Any) -> bool:
    return isinstance(value, (Mapping, list, tuple, set)) and bool(value)
