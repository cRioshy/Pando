"""Fail-closed stock market input contract for future adapter integration."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from feature_data_quality_contract import (
    FeatureDataQualityError,
    FeatureDataQualityPolicy,
    prepare_feature_candles,
    project_feature_data_quality,
)


SCHEMA_NAME = "pandorickki.stock-data"
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StockDataPolicy:
    """Explicit policy for a gate-capable stock input."""

    minimum_candles: int
    full_warmup_candles: int
    maximum_candle_age_seconds: float
    maximum_quote_age_seconds: float
    maximum_future_skew_seconds: float = 30.0
    maximum_entry_deviation_percent: float = 0.5
    allowed_timeframes: tuple[str, ...] = ("1d",)
    allowed_price_sources: tuple[str, ...] = ("yahoo_finance_chart",)

    def __post_init__(self) -> None:
        if self.minimum_candles < 1:
            raise ValueError("minimum_candles must be at least 1")
        if self.full_warmup_candles < self.minimum_candles:
            raise ValueError("full_warmup_candles must be at least minimum_candles")
        for name, value in (
            ("maximum_candle_age_seconds", self.maximum_candle_age_seconds),
            ("maximum_quote_age_seconds", self.maximum_quote_age_seconds),
            ("maximum_future_skew_seconds", self.maximum_future_skew_seconds),
            ("maximum_entry_deviation_percent", self.maximum_entry_deviation_percent),
        ):
            number = _finite_number(value)
            if number is None or number < 0:
                raise ValueError(f"{name} must be finite and non-negative")
        if not self.allowed_timeframes:
            raise ValueError("allowed_timeframes must not be empty")
        if not self.allowed_price_sources:
            raise ValueError("allowed_price_sources must not be empty")


def evaluate_stock_data(
    candidate: Mapping[str, Any],
    *,
    policy: StockDataPolicy,
    evaluated_at: datetime | None = None,
) -> dict[str, Any]:
    """Evaluate stock data without publishing, persisting or releasing it."""

    reasons: list[str] = []
    market_type = str(candidate.get("market_type") or "").strip().lower()
    symbol = str(candidate.get("symbol") or "").strip().upper()
    timeframe = str(candidate.get("timeframe") or "").strip().lower()
    direction = str(candidate.get("direction") or "").strip().upper()
    source_kind = str(candidate.get("source_kind") or "").strip().upper()

    if market_type != "stock":
        reasons.append("SD_MARKET_NOT_STOCK")
    if not symbol:
        reasons.append("SD_SYMBOL_MISSING")
    if timeframe not in {item.lower() for item in policy.allowed_timeframes}:
        reasons.append("SD_TIMEFRAME_NOT_ALLOWED")
    if source_kind != "PUBLIC_LIVE":
        reasons.append("SD_SOURCE_NOT_LIVE")
    if direction not in {"LONG", "SHORT"}:
        reasons.append("SD_DIRECTION_NOT_ELIGIBLE")

    now = evaluated_at or datetime.now(UTC)
    now = now.replace(tzinfo=UTC) if now.tzinfo is None else now.astimezone(UTC)
    quality_projection = _evaluate_candles(candidate.get("candles"), policy, now, reasons)
    price = _finite_number(candidate.get("current_price"))
    if price is None or price <= 0:
        reasons.append("SD_PRICE_INVALID")

    price_source = str(candidate.get("price_source") or "").strip()
    if price_source not in policy.allowed_price_sources:
        reasons.append("SD_PRICE_SOURCE_NOT_ALLOWED")

    quote_time = _parse_timestamp(candidate.get("price_timestamp"))
    quote_age_seconds: float | None = None
    if quote_time is None:
        reasons.append("SD_PRICE_TIMESTAMP_INVALID")
    else:
        quote_age_seconds = (now - quote_time).total_seconds()
        if quote_age_seconds < -policy.maximum_future_skew_seconds:
            reasons.append("SD_PRICE_TIMESTAMP_IN_FUTURE")
        elif quote_age_seconds > policy.maximum_quote_age_seconds:
            reasons.append("SD_PRICE_STALE")

    _evaluate_risk(candidate.get("risk"), direction, price, policy, reasons)
    reason_codes = list(dict.fromkeys(reasons))
    ready = not reason_codes
    return {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "mode": "REFERENCE_ONLY",
        "status": "READY" if ready else "BLOCKED",
        "reason_codes": reason_codes if reason_codes else ["SD_READY"],
        "symbol": symbol or None,
        "timeframe": timeframe or None,
        "direction": direction or None,
        "current_price": price,
        "price_source": price_source or None,
        "quote_age_seconds": round(quote_age_seconds, 3) if quote_age_seconds is not None else None,
        "feature_quality": quality_projection,
        "usable_for_feature_engine": ready,
        "usable_for_decision_gate": ready,
        "ready_for_telegram": False,
        "order_execution_allowed": False,
    }


def _evaluate_candles(
    candles: Any,
    policy: StockDataPolicy,
    evaluated_at: datetime,
    reasons: list[str],
) -> dict[str, Any] | None:
    if not isinstance(candles, list):
        reasons.append("SD_CANDLES_MISSING")
        return None
    try:
        result = prepare_feature_candles(
            candles,
            policy=FeatureDataQualityPolicy(
                minimum_candles=policy.minimum_candles,
                full_warmup_candles=policy.full_warmup_candles,
                require_timestamps=True,
            ),
        )
    except FeatureDataQualityError:
        reasons.append("SD_CANDLES_INVALID")
        return None

    projection = project_feature_data_quality({"features": {"metadata": {"data_quality": result.report}}})
    if not isinstance(projection, dict):
        reasons.append("SD_QUALITY_MISSING")
        return None
    if projection.get("status") != "PASS":
        reasons.append("SD_QUALITY_NOT_PASS")
    if (projection.get("order") or {}).get("status") != "VERIFIED":
        reasons.append("SD_ORDER_NOT_VERIFIED")
    if (projection.get("warmup") or {}).get("status") != "READY":
        reasons.append("SD_WARMUP_NOT_READY")
    latest_time = _parse_timestamp(result.candles[-1].get("timestamp")) if result.candles else None
    if latest_time is None:
        reasons.append("SD_LATEST_CANDLE_TIMESTAMP_INVALID")
    else:
        candle_age = (evaluated_at - latest_time).total_seconds()
        if candle_age < -policy.maximum_future_skew_seconds:
            reasons.append("SD_LATEST_CANDLE_IN_FUTURE")
        elif candle_age > policy.maximum_candle_age_seconds:
            reasons.append("SD_CANDLES_STALE")
    return projection


def _evaluate_risk(risk: Any, direction: str, price: float | None, policy: StockDataPolicy, reasons: list[str]) -> None:
    if not isinstance(risk, Mapping):
        reasons.append("SD_RISK_MISSING")
        return
    action = str(risk.get("action") or "").strip().upper()
    if action != direction:
        reasons.append("SD_RISK_DIRECTION_CONFLICT")
    entry = _finite_number(risk.get("entry_price"))
    stop = _finite_number(risk.get("stop_loss"))
    targets_value = risk.get("take_profit")
    targets = targets_value if isinstance(targets_value, (list, tuple)) else [risk.get("take_profit_1")]
    take_profits = [number for value in targets if (number := _finite_number(value)) is not None]

    if entry is None or entry <= 0:
        reasons.append("SD_RISK_ENTRY_INVALID")
    elif price is not None and price > 0:
        deviation = abs(entry - price) / price * 100.0
        if deviation > policy.maximum_entry_deviation_percent:
            reasons.append("SD_RISK_ENTRY_PRICE_MISMATCH")
    if stop is None or stop <= 0 or price is None:
        reasons.append("SD_STOP_LOSS_INVALID")
    elif direction == "LONG" and stop >= price:
        reasons.append("SD_STOP_LOSS_INVALID")
    elif direction == "SHORT" and stop <= price:
        reasons.append("SD_STOP_LOSS_INVALID")
    if not take_profits or price is None:
        reasons.append("SD_TAKE_PROFIT_INVALID")
    elif direction == "LONG" and not any(target > price for target in take_profits):
        reasons.append("SD_TAKE_PROFIT_INVALID")
    elif direction == "SHORT" and not any(target < price for target in take_profits):
        reasons.append("SD_TAKE_PROFIT_INVALID")


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            number = float(value)
            if not math.isfinite(number):
                return None
            if abs(number) >= 1_000_000_000_000:
                number /= 1000.0
            return datetime.fromtimestamp(number, UTC)
        text = str(value).strip()
        if not text:
            return None
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    except (OverflowError, OSError, TypeError, ValueError):
        return None
