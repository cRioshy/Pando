"""Versioned compact payload contracts for persisted PandorickKi events."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from feature_data_quality_contract import project_feature_data_quality


CONTRACT_NAME = "pandorickki.compact-market-event"
CONTRACT_VERSION = 1
OBSERVER_CONTRACT_NAME = "pandorickki.compact-observer-event"
OBSERVER_CONTRACT_VERSION = 1

REQUIRED_FIELDS = frozenset({"schema_name", "schema_version", "market_type", "symbol"})
OBSERVER_REQUIRED_FIELDS = frozenset({"schema_name", "schema_version", "event_type"})
FORBIDDEN_FIELDS = frozenset({"raw_result", "features", "market_data_diagnostics", "candles"})

# These are verified legacy reads in the current code. They are migration
# obligations, not permission to keep the bulk fields in the new contract.
LEGACY_FIELD_REPLACEMENTS: dict[str, str] = {
    "crypto_trade_tracker:raw_result.market_data.candles": (
        "market_context.recent_swing_low/recent_swing_high"
    ),
    "learning_graph:raw_result.result": "public_result",
}

# This inventory is intentionally executable: tests fail when a documented
# consumer requires a field that the compact projection cannot provide.
CONSUMER_FIELD_REQUIREMENTS: dict[str, frozenset[str]] = {
    "brain": frozenset(
        {
            "market_type",
            "symbol",
            "direction",
            "probability",
            "price",
            "current_price",
            "indicators",
            "risk",
            "source_timestamp",
        }
    ),
    "decision_core": frozenset(
        {
            "market_type",
            "symbol",
            "direction",
            "probability",
            "confidence",
            "price",
            "current_price",
            "indicators",
            "risk",
            "source_event_id",
            "source_timestamp",
        }
    ),
    "decision_gate_observer": frozenset(
        {
            "market_type",
            "symbol",
            "direction",
            "probability",
            "confidence",
            "price",
            "current_price",
            "facts",
            "risk",
            "feature_quality",
            "source_event_id",
        }
    ),
    "crypto_trade_tracker": frozenset(
        {
            "market_type",
            "symbol",
            "direction",
            "price",
            "current_price",
            "indicators",
            "risk",
            "market_context",
            "signal_id",
            "decision_id",
            "source_event_id",
        }
    ),
    "outcome_tracker": frozenset(
        {
            "market_type",
            "symbol",
            "direction",
            "price",
            "current_price",
            "risk",
            "decision_id",
            "signal_id",
            "source_event_id",
            "created_at",
        }
    ),
    "control_center": frozenset(
        {
            "symbol",
            "direction",
            "probability",
            "price",
            "current_price",
            "price_status",
            "received_at",
        }
    ),
    "telegram_dry_run": frozenset(
        {
            "market_type",
            "symbol",
            "direction",
            "probability",
            "price",
        }
    ),
    "learning_graph": frozenset({"symbol", "direction", "indicators", "public_result"}),
    "neurobrain": frozenset(
        {
            "market_type",
            "symbol",
            "direction",
            "probability",
            "source_event_id",
            "source_timestamp",
        }
    ),
}

_PASSTHROUGH_FIELDS = (
    "event_type",
    "source_event_id",
    "correlation_id",
    "decision_id",
    "decision_event_id",
    "signal_id",
    "market_type",
    "symbol",
    "label",
    "timeframe",
    "direction",
    "strength",
    "probability",
    "confidence",
    "price",
    "current_price",
    "analysis_close",
    "price_source",
    "price_status",
    "price_error",
    "price_attempts",
    "price_timestamp",
    "source_timestamp",
    "received_at",
    "created_at",
    "entry_price",
    "initial_stop_loss",
    "current_stop_loss",
    "take_profit_1",
    "current_profit_percent",
    "max_profit_percent",
    "max_drawdown_percent",
    "trade_status",
    "risk_percent",
    "ready_for_telegram",
    "reason",
)

_OBSERVER_PASSTHROUGH_FIELDS = (
    "event_type",
    "source_event_id",
    "correlation_id",
    "status",
    "count",
    "symbols",
    "updates",
    "memory_size",
    "last_symbol",
    "last_direction",
    "last_confidence",
    "last_update_at",
    "source_timestamp",
    "received_at",
    "created_at",
    "reason",
)


def compact_market_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    """Project a current or legacy event payload onto contract version 1.

    Both the EventBus envelope and its nested ``payload`` are accepted. Large
    diagnostic/training fields are omitted. Legacy candle data is reduced to
    the two swing values needed by the simulated crypto trade tracker.
    """

    outer = dict(value)
    nested = outer.get("payload")
    data = dict(nested) if isinstance(nested, Mapping) else outer

    result: dict[str, Any] = {
        "schema_name": CONTRACT_NAME,
        "schema_version": CONTRACT_VERSION,
    }
    for field in _PASSTHROUGH_FIELDS:
        selected = data.get(field)
        if selected is None and field in {"event_type", "correlation_id"}:
            selected = outer.get(field)
        if selected is None and field == "source_event_id":
            selected = data.get("source_event_id") or outer.get("event_id")
        if selected is not None:
            result[field] = deepcopy(selected)

    # Keep normalized, consumer-visible structures. Their producers are
    # responsible for bounded content; forbidden bulk keys are stripped.
    for field in ("facts", "indicators", "risk"):
        selected = data.get(field)
        result[field] = _without_forbidden(selected) if isinstance(selected, (Mapping, list)) else {}

    public_result = data.get("public_result")
    raw_result = data.get("raw_result")
    if public_result is None and isinstance(raw_result, Mapping):
        public_result = raw_result.get("result")
    result["public_result"] = public_result

    context = data.get("market_context")
    result["market_context"] = (
        _without_forbidden(context) if isinstance(context, Mapping) else _legacy_market_context(raw_result)
    )
    feature_quality = project_feature_data_quality(data)
    if feature_quality is not None:
        result["feature_quality"] = feature_quality
    return result


def contract_errors(payload: Mapping[str, Any]) -> list[str]:
    """Return structural contract violations for one projected payload."""

    errors = [f"missing required field: {field}" for field in sorted(REQUIRED_FIELDS - payload.keys())]
    if payload.get("schema_name") != CONTRACT_NAME:
        errors.append("unexpected schema_name")
    if payload.get("schema_version") != CONTRACT_VERSION:
        errors.append("unsupported schema_version")
    forbidden = _find_forbidden(payload)
    if forbidden:
        errors.append(f"forbidden fields present: {', '.join(sorted(forbidden))}")
    return errors


def compact_observer_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    """Project a lifecycle, learning or aggregate event onto observer version 1."""

    outer = dict(value)
    nested = outer.get("payload")
    data = dict(nested) if isinstance(nested, Mapping) else outer
    result: dict[str, Any] = {
        "schema_name": OBSERVER_CONTRACT_NAME,
        "schema_version": OBSERVER_CONTRACT_VERSION,
    }
    for field in _OBSERVER_PASSTHROUGH_FIELDS:
        selected = data.get(field)
        if selected is None and field in {"event_type", "correlation_id"}:
            selected = outer.get(field)
        if selected is None and field == "source_event_id":
            selected = data.get("source_event_id") or outer.get("event_id")
        if selected is not None:
            result[field] = _without_forbidden(selected)
    return result


def observer_contract_errors(payload: Mapping[str, Any]) -> list[str]:
    """Return structural observer-contract violations for one projection."""

    errors = [
        f"missing required field: {field}"
        for field in sorted(OBSERVER_REQUIRED_FIELDS - payload.keys())
    ]
    if payload.get("schema_name") != OBSERVER_CONTRACT_NAME:
        errors.append("unexpected schema_name")
    if payload.get("schema_version") != OBSERVER_CONTRACT_VERSION:
        errors.append("unsupported schema_version")
    forbidden = _find_forbidden(payload)
    if forbidden:
        errors.append(f"forbidden fields present: {', '.join(sorted(forbidden))}")
    return errors


def _legacy_market_context(raw_result: Any) -> dict[str, Any]:
    if not isinstance(raw_result, Mapping):
        return {}
    market_data = raw_result.get("market_data")
    candles = market_data.get("candles") if isinstance(market_data, Mapping) else None
    if not isinstance(candles, list):
        return {}
    recent = [item for item in candles[-20:] if isinstance(item, Mapping)]
    lows = [_as_float(item.get("low")) for item in recent]
    highs = [_as_float(item.get("high")) for item in recent]
    lows = [item for item in lows if item is not None]
    highs = [item for item in highs if item is not None]
    context: dict[str, Any] = {}
    if lows:
        context["recent_swing_low"] = min(lows)
    if highs:
        context["recent_swing_high"] = max(highs)
    return context


def _without_forbidden(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _without_forbidden(item)
            for key, item in value.items()
            if str(key) not in FORBIDDEN_FIELDS
        }
    if isinstance(value, list):
        return [_without_forbidden(item) for item in value]
    return deepcopy(value)


def _find_forbidden(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in FORBIDDEN_FIELDS:
                found.add(str(key))
            found.update(_find_forbidden(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_find_forbidden(item))
    return found


def _as_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
