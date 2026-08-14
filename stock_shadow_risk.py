"""Observer-only stock risk levels derived from a public-data shadow candidate."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping


SCHEMA_NAME = "pandorickki.stock-shadow-risk"
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StockShadowRiskPolicy:
    """Explicit ATR and reward/risk parameters for the observer-only plan."""

    atr_multiplier: float
    minimum_distance_percent: float
    take_profit_multiples: tuple[float, ...]
    price_decimals: int

    def __post_init__(self) -> None:
        if _positive_number(self.atr_multiplier) is None:
            raise ValueError("atr_multiplier must be finite and positive")
        if _positive_number(self.minimum_distance_percent) is None:
            raise ValueError("minimum_distance_percent must be finite and positive")
        if not self.take_profit_multiples:
            raise ValueError("take_profit_multiples must not be empty")
        normalized = [_positive_number(value) for value in self.take_profit_multiples]
        if any(value is None for value in normalized):
            raise ValueError("take_profit_multiples must be finite and positive")
        values = [float(value) for value in normalized if value is not None]
        if values != sorted(set(values)):
            raise ValueError("take_profit_multiples must be unique and strictly increasing")
        if not isinstance(self.price_decimals, int) or not 0 <= self.price_decimals <= 8:
            raise ValueError("price_decimals must be an integer from 0 through 8")


def build_stock_shadow_risk(
    candidate: Mapping[str, Any],
    *,
    policy: StockShadowRiskPolicy,
) -> dict[str, Any]:
    """Return compact levels without publishing, persistence or trade release."""

    base = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "mode": "OBSERVER",
        "release_status": "OBSERVER_ONLY",
        "symbol": candidate.get("symbol"),
        "direction": candidate.get("direction"),
        "source_kind": candidate.get("source_kind"),
        "source_shadow_schema": candidate.get("schema_name"),
        "source_shadow_version": candidate.get("schema_version"),
        "affects_active_decision": False,
        "ready_for_telegram": False,
        "order_execution_allowed": False,
    }
    if candidate.get("status") != "CALCULATED":
        return _blocked(base, "SSR_SHADOW_NOT_CALCULATED")
    direction = str(candidate.get("direction") or "").strip().upper()
    if direction not in {"LONG", "SHORT"}:
        return _blocked(base, "SSR_DIRECTION_NOT_ELIGIBLE")
    entry = _positive_number(candidate.get("current_price"))
    if entry is None:
        return _blocked(base, "SSR_ENTRY_INVALID")
    indicators = candidate.get("indicators")
    atr14 = _positive_number(indicators.get("atr14")) if isinstance(indicators, Mapping) else None
    if atr14 is None:
        return _blocked(base, "SSR_ATR_INVALID")

    atr_distance = atr14 * float(policy.atr_multiplier)
    minimum_distance = entry * float(policy.minimum_distance_percent) / 100.0
    risk_distance = max(atr_distance, minimum_distance)
    sign = 1.0 if direction == "LONG" else -1.0
    rounded_entry = round(entry, policy.price_decimals)
    stop = round(entry - sign * risk_distance, policy.price_decimals)
    targets = [
        round(entry + sign * risk_distance * multiple, policy.price_decimals)
        for multiple in policy.take_profit_multiples
    ]
    if stop <= 0 or stop == rounded_entry:
        return _blocked(base, "SSR_STOP_INVALID")
    if any(target <= 0 or target == rounded_entry for target in targets):
        return _blocked(base, "SSR_TARGET_INVALID")
    if direction == "LONG" and (stop >= rounded_entry or any(target <= rounded_entry for target in targets)):
        return _blocked(base, "SSR_DIRECTIONAL_LEVEL_INVALID")
    if direction == "SHORT" and (stop <= rounded_entry or any(target >= rounded_entry for target in targets)):
        return _blocked(base, "SSR_DIRECTIONAL_LEVEL_INVALID")

    normalized_risk = {
        "action": direction,
        "entry_price": rounded_entry,
        "stop_loss": stop,
        "take_profit": targets,
        "take_profit_1": targets[0],
    }
    return {
        **base,
        "status": "CALCULATED",
        "reason_codes": ["SSR_CALCULATED"],
        "atr14": round(atr14, 8),
        "risk_distance": round(risk_distance, 8),
        "risk_distance_percent": round(risk_distance / entry * 100.0, 6),
        "reward_risk_multiples": list(policy.take_profit_multiples),
        "policy": {
            "atr_multiplier": policy.atr_multiplier,
            "minimum_distance_percent": policy.minimum_distance_percent,
            "price_decimals": policy.price_decimals,
        },
        "risk": normalized_risk,
    }


def _blocked(base: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        **base,
        "status": "BLOCKED",
        "reason_codes": [reason],
        "risk": None,
    }


def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None
