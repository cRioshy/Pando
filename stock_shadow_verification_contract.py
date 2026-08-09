"""Versioned, observer-only contract for stock shadow verification."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping
from uuid import NAMESPACE_URL, uuid5


SCHEMA_NAME = "pandorickki.stock-shadow-verification"
SCHEMA_VERSION = 1
OBSERVER_VERSION = "stock-shadow-verification-v1"
DECISIONS = frozenset({"LONG", "SHORT", "HOLD"})


@dataclass(frozen=True)
class StockShadowVerificationPolicy:
    """Stable forward-mark-to-market policy for one verification run."""

    horizon_seconds: float = 86400.0
    neutral_band_percent: float = 0.05
    observer_version: str = OBSERVER_VERSION

    def __post_init__(self) -> None:
        if not math.isfinite(float(self.horizon_seconds)) or self.horizon_seconds <= 0:
            raise ValueError("horizon_seconds must be finite and positive")
        if not math.isfinite(float(self.neutral_band_percent)) or self.neutral_band_percent < 0:
            raise ValueError("neutral_band_percent must be finite and non-negative")
        if not str(self.observer_version).strip():
            raise ValueError("observer_version must not be empty")


def configuration_fingerprint(values: Mapping[str, Any]) -> str:
    """Return a stable, secret-free fingerprint for explicit observer settings."""

    canonical = json.dumps(dict(values), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_verification_record(
    observation: Mapping[str, Any],
    *,
    policy: StockShadowVerificationPolicy,
    config_fingerprint: str,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    """Build one immutable observation record without changing active decisions."""

    now = _utc(created_at or datetime.now(UTC))
    symbol = str(observation.get("symbol") or "").strip().upper()
    source_timestamp = _timestamp_text(observation.get("source_timestamp"))
    quote_timestamp = _timestamp_text(observation.get("quote_timestamp"))
    candle_timestamp = _timestamp_text(observation.get("latest_candle_timestamp"))
    legacy = _mapping(observation.get("legacy"))
    shadow = _mapping(observation.get("shadow"))
    audit = _mapping(observation.get("data_audit"))
    risk = _mapping(observation.get("shadow_risk"))
    legacy_direction = _decision(legacy.get("direction"))
    shadow_direction = _decision(shadow.get("direction"))
    identity = "|".join(
        (
            SCHEMA_NAME,
            symbol,
            source_timestamp or "",
            quote_timestamp or "",
            candle_timestamp or "",
            str(policy.observer_version),
            str(config_fingerprint),
        )
    )
    verification_id = f"stock-shadow-verification:{uuid5(NAMESPACE_URL, identity)}"
    analysis_timestamp = _timestamp_text(observation.get("analysis_timestamp")) or now.isoformat()
    analysis_time = _parse_timestamp(analysis_timestamp) or now
    entry_price = _positive_number(observation.get("entry_price"))
    quality = project_data_quality(audit, shadow)
    gate_status = project_shadow_gate_status(audit, shadow, risk)
    decisions_match, disagreement_type = compare_decisions(legacy_direction, shadow_direction)
    record = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "observer_version": policy.observer_version,
        "mode": "OBSERVER_ONLY",
        "verification_id": verification_id,
        "asset_type": "stock",
        "symbol": symbol or None,
        "cycle_id": observation.get("cycle_id"),
        "source_event_ids": [str(observation.get("source_event_id"))]
        if observation.get("source_event_id")
        else [],
        "analysis_timestamp": analysis_timestamp,
        "source_timestamp": source_timestamp,
        "quote_timestamp": quote_timestamp,
        "latest_candle_timestamp": candle_timestamp,
        "entry_price": entry_price,
        "evaluation_due_at": (analysis_time + timedelta(seconds=policy.horizon_seconds)).isoformat(),
        "outcome_policy": {
            "kind": "FORWARD_MARK_TO_MARKET",
            "horizon_seconds": float(policy.horizon_seconds),
            "neutral_band_percent": float(policy.neutral_band_percent),
            "requires_later_quote_timestamp": True,
            "uses_stop_or_target_hits": False,
        },
        "data_quality": quality,
        "legacy": {
            "decision": legacy_direction,
            "confidence": _finite_number(legacy.get("confidence", legacy.get("probability"))),
            "decision_id": None,
        },
        "shadow": {
            "decision": shadow_direction,
            "confidence": _finite_number(shadow.get("confidence")),
            "score": _finite_number(shadow.get("probability")),
            "score_kind": shadow.get("probability_kind"),
            "status": shadow.get("status"),
            "risk": _safe_risk(risk),
            "gate_status": gate_status,
            "reason_codes": _reason_codes(shadow, risk, audit),
        },
        "comparison": {
            "decisions_match": decisions_match,
            "disagreement_type": disagreement_type,
        },
        "outcome": {
            "status": "PENDING" if entry_price is not None else "UNKNOWN",
            "evaluated_at": None,
            "quote_timestamp": None,
            "exit_price": None,
            "market_move_percent": None,
            "legacy": _pending_outcome(legacy_direction, entry_price),
            "shadow": _pending_outcome(shadow_direction, entry_price),
            "tracker": None,
        },
        "config_fingerprint": str(config_fingerprint),
        "created_at": now.isoformat(),
        "ready_for_telegram": False,
        "order_execution_allowed": False,
        "affects_active_decision": False,
    }
    return record


def complete_forward_outcome(
    record: Mapping[str, Any],
    *,
    exit_price: Any,
    quote_timestamp: Any,
    evaluated_at: datetime | None = None,
) -> dict[str, Any] | None:
    """Return an append-only outcome projection when the fixed horizon is due."""

    if _mapping(record.get("outcome")).get("status") != "PENDING":
        return None
    now = _utc(evaluated_at or datetime.now(UTC))
    due = _parse_timestamp(record.get("evaluation_due_at"))
    if due is None or now < due:
        return None
    original_quote = _parse_timestamp(record.get("quote_timestamp"))
    later_quote = _parse_timestamp(quote_timestamp)
    if later_quote is None or (original_quote is not None and later_quote <= original_quote):
        return None
    entry = _positive_number(record.get("entry_price"))
    exit_value = _positive_number(exit_price)
    if entry is None or exit_value is None:
        return None
    market_move = (exit_value / entry - 1.0) * 100.0
    policy = _mapping(record.get("outcome_policy"))
    neutral_band = _finite_number(policy.get("neutral_band_percent")) or 0.0
    legacy_direction = _decision(_mapping(record.get("legacy")).get("decision"))
    shadow_direction = _decision(_mapping(record.get("shadow")).get("decision"))
    return {
        "status": "COMPLETED",
        "evaluated_at": now.isoformat(),
        "quote_timestamp": later_quote.isoformat(),
        "exit_price": exit_value,
        "market_move_percent": round(market_move, 8),
        "legacy": classify_directional_outcome(legacy_direction, market_move, neutral_band),
        "shadow": classify_directional_outcome(shadow_direction, market_move, neutral_band),
        "tracker": _mapping(record.get("outcome")).get("tracker"),
    }


def classify_directional_outcome(
    direction: str | None,
    market_move_percent: float,
    neutral_band_percent: float,
) -> dict[str, Any]:
    """Classify one direction without treating missing/HOLD as success."""

    if direction not in {"LONG", "SHORT"}:
        return {"status": "UNKNOWN", "value_percent": None}
    directional = market_move_percent if direction == "LONG" else -market_move_percent
    if directional > neutral_band_percent:
        status = "WIN"
    elif directional < -neutral_band_percent:
        status = "LOSS"
    else:
        status = "NEUTRAL"
    return {"status": status, "value_percent": round(directional, 8)}


def compare_decisions(legacy: str | None, shadow: str | None) -> tuple[bool | None, str]:
    """Describe agreement without converting missing values into HOLD."""

    if legacy not in DECISIONS or shadow not in DECISIONS:
        return None, "UNCOMPARABLE"
    if legacy == shadow:
        return True, "MATCH"
    if legacy == "HOLD" and shadow in {"LONG", "SHORT"}:
        return False, "LEGACY_HOLD_SHADOW_ACTION"
    if shadow == "HOLD" and legacy in {"LONG", "SHORT"}:
        return False, "LEGACY_ACTION_SHADOW_HOLD"
    return False, "DIRECTION_CONFLICT"


def project_data_quality(audit: Mapping[str, Any], shadow: Mapping[str, Any]) -> dict[str, Any]:
    """Preserve raw contract states and add a display-only three-state projection."""

    feature_quality = _mapping(audit.get("feature_quality")) or _mapping(shadow.get("feature_quality"))
    feature_status = str(feature_quality.get("status") or "UNKNOWN").upper()
    contract_status = str(audit.get("status") or "UNKNOWN").upper()
    reasons = [str(item) for item in audit.get("reason_codes", []) if item]
    if contract_status == "READY":
        display = "OK"
    elif feature_status in {"PASS", "WARN"} and reasons and all(_degraded_reason(item) for item in reasons):
        display = "DEGRADED"
    elif feature_status == "WARN":
        display = "DEGRADED"
    else:
        display = "REJECTED"
    return {
        "status": display,
        "contract_status": contract_status,
        "feature_status": feature_status,
        "score": None,
        "reason_codes": reasons,
    }


def project_shadow_gate_status(
    audit: Mapping[str, Any],
    shadow: Mapping[str, Any],
    risk: Mapping[str, Any],
) -> str:
    """Project stock-data eligibility; this never activates the Decision Gate."""

    if str(shadow.get("status") or "").upper() != "CALCULATED":
        return "UNKNOWN"
    direction = _decision(shadow.get("direction"))
    if direction == "HOLD":
        return "HOLD"
    if (
        direction in {"LONG", "SHORT"}
        and str(audit.get("status") or "").upper() == "READY"
        and str(risk.get("status") or "").upper() == "CALCULATED"
    ):
        return "PASS"
    return "BLOCK"


def _pending_outcome(direction: str | None, entry_price: float | None) -> dict[str, Any]:
    status = "PENDING" if direction in {"LONG", "SHORT"} and entry_price is not None else "UNKNOWN"
    return {"status": status, "value_percent": None}


def _reason_codes(*sources: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for source in sources:
        values.extend(str(item) for item in source.get("reason_codes", []) if item)
    return list(dict.fromkeys(values))


def _safe_risk(risk: Mapping[str, Any]) -> dict[str, Any] | None:
    normalized = _mapping(risk.get("risk"))
    if not normalized:
        return None
    targets = normalized.get("take_profit")
    return {
        "action": _decision(normalized.get("action")),
        "entry_price": _positive_number(normalized.get("entry_price")),
        "stop_loss": _positive_number(normalized.get("stop_loss")),
        "take_profit": [
            value
            for item in (targets if isinstance(targets, (list, tuple)) else [])
            if (value := _positive_number(item)) is not None
        ],
    }


def _degraded_reason(reason: str) -> bool:
    return reason in {
        "SD_CANDLES_STALE",
        "SD_PRICE_STALE",
        "SD_DIRECTION_NOT_ELIGIBLE",
    }


def _decision(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    if text in {"WAIT", "HOLD"}:
        return "HOLD"
    return text if text in {"LONG", "SHORT"} else None


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _positive_number(value: Any) -> float | None:
    number = _finite_number(value)
    return number if number is not None and number > 0 else None


def _timestamp_text(value: Any) -> str | None:
    parsed = _parse_timestamp(value)
    return parsed.isoformat() if parsed is not None else None


def _parse_timestamp(value: Any) -> datetime | None:
    if value in {None, ""} or isinstance(value, bool):
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), UTC)
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        return _utc(parsed)
    except (OSError, OverflowError, TypeError, ValueError):
        return None


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
