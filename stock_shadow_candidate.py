"""Observer-only stock candidate derived exclusively from public market data."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from feature_data_quality_contract import (
    FeatureDataQualityError,
    FeatureDataQualityPolicy,
    prepare_feature_candles,
    project_feature_data_quality,
)


SCHEMA_NAME = "pandorickki.stock-shadow-candidate"
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StockShadowPolicy:
    """Explicit observer thresholds; the score is not a calibrated probability."""

    minimum_candles: int
    full_warmup_candles: int
    long_bullish_score: float = 60.0
    short_bullish_score: float = 40.0

    def __post_init__(self) -> None:
        if self.minimum_candles < 200:
            raise ValueError("minimum_candles must be at least 200 for SMA200")
        if self.full_warmup_candles < self.minimum_candles:
            raise ValueError("full_warmup_candles must be at least minimum_candles")
        if not 50.0 < self.long_bullish_score <= 100.0:
            raise ValueError("long_bullish_score must be greater than 50 and at most 100")
        if not 0.0 <= self.short_bullish_score < 50.0:
            raise ValueError("short_bullish_score must be at least 0 and below 50")


def build_stock_shadow_candidate(
    *,
    symbol: Any,
    candles: Sequence[Mapping[str, Any]] | None,
    current_price: Any,
    price_source: Any,
    price_timestamp: Any,
    candle_source: Any,
    timeframe: Any = "1d",
    policy: StockShadowPolicy,
) -> dict[str, Any]:
    """Build a compact candidate without publishing, persistence, risk or release."""

    base = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "mode": "OBSERVER",
        "release_status": "OBSERVER_ONLY",
        "market_type": "stock",
        "symbol": str(symbol or "").strip().upper() or None,
        "timeframe": str(timeframe or "1d").strip().lower(),
        "source_kind": "PUBLIC_LIVE",
        "candle_source": str(candle_source or "").strip() or None,
        "price_source": str(price_source or "").strip() or None,
        "price_timestamp": str(price_timestamp or "").strip() or None,
        "current_price": _finite_number(current_price),
        "probability_kind": "UNVALIDATED_HEURISTIC_SCORE",
        "risk": None,
        "ready_for_telegram": False,
        "order_execution_allowed": False,
    }
    if not isinstance(candles, Sequence) or isinstance(candles, (str, bytes)):
        return _blocked(base, "SS_CANDLES_MISSING")
    try:
        quality = prepare_feature_candles(
            list(candles),
            policy=FeatureDataQualityPolicy(
                minimum_candles=policy.minimum_candles,
                full_warmup_candles=policy.full_warmup_candles,
                require_timestamps=True,
            ),
        )
    except FeatureDataQualityError as exc:
        return _blocked(base, "SS_CANDLES_INVALID", detail=str(exc))

    projection = project_feature_data_quality({"feature_quality": quality.report})
    if not projection or projection.get("status") != "PASS":
        return _blocked(base, "SS_QUALITY_NOT_PASS", feature_quality=projection)
    price = _finite_number(current_price)
    if price is None or price <= 0:
        return _blocked(base, "SS_PRICE_INVALID", feature_quality=projection)

    rows = quality.candles
    closes = [float(row["close"]) for row in rows]
    highs = [float(row["high"]) for row in rows]
    lows = [float(row["low"]) for row in rows]
    volumes = [float(row["volume"]) for row in rows]
    sma20 = _mean(closes[-20:])
    sma50 = _mean(closes[-50:])
    sma200 = _mean(closes[-200:])
    return20 = ((closes[-1] / closes[-21]) - 1.0) * 100.0
    rsi14 = _rsi(closes, 14)
    atr14 = _atr(highs, lows, closes, 14)
    average_volume20 = _mean(volumes[-20:])
    volume_ratio20 = volumes[-1] / average_volume20 if average_volume20 > 0 else None

    components = {
        "price_vs_sma20": _signed_comparison(price, sma20, 8.0),
        "sma20_vs_sma50": _signed_comparison(sma20, sma50, 8.0),
        "sma50_vs_sma200": _signed_comparison(sma50, sma200, 10.0),
        "return_20d": 8.0 if return20 > 0 else (-8.0 if return20 < 0 else 0.0),
        "rsi14": 6.0 if rsi14 >= 55.0 else (-6.0 if rsi14 <= 45.0 else 0.0),
    }
    bullish_score = max(0.0, min(100.0, 50.0 + sum(components.values())))
    if bullish_score >= policy.long_bullish_score:
        direction = "LONG"
        probability = bullish_score
    elif bullish_score <= policy.short_bullish_score:
        direction = "SHORT"
        probability = 100.0 - bullish_score
    else:
        direction = "HOLD"
        probability = max(bullish_score, 100.0 - bullish_score)

    latest = rows[-1]
    return {
        **base,
        "status": "CALCULATED",
        "reason_codes": ["SS_CALCULATED"],
        "direction": direction,
        "probability": round(probability, 4),
        "bullish_score": round(bullish_score, 4),
        "score_thresholds": {
            "long": policy.long_bullish_score,
            "short": policy.short_bullish_score,
        },
        "score_components": components,
        "facts": {
            "candle_count": len(rows),
            "latest_candle_timestamp": latest.get("timestamp"),
            "latest_close": round(closes[-1], 8),
            "current_price": round(price, 8),
        },
        "indicators": {
            "sma20": round(sma20, 8),
            "sma50": round(sma50, 8),
            "sma200": round(sma200, 8),
            "return_20d_percent": round(return20, 6),
            "rsi14": round(rsi14, 6),
            "atr14": round(atr14, 8),
            "volume_ratio20": round(volume_ratio20, 6) if volume_ratio20 is not None else None,
        },
        "feature_quality": projection,
    }


def _blocked(
    base: Mapping[str, Any],
    reason: str,
    *,
    detail: str | None = None,
    feature_quality: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        **base,
        "status": "BLOCKED",
        "reason_codes": [reason],
        "detail": detail,
        "direction": None,
        "probability": None,
        "bullish_score": None,
        "facts": None,
        "indicators": None,
        "feature_quality": dict(feature_quality) if feature_quality else None,
    }


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _signed_comparison(left: float, right: float, weight: float) -> float:
    if left > right:
        return weight
    if left < right:
        return -weight
    return 0.0


def _rsi(closes: Sequence[float], period: int) -> float:
    changes = [closes[index] - closes[index - 1] for index in range(len(closes) - period, len(closes))]
    gains = sum(max(change, 0.0) for change in changes) / period
    losses = sum(max(-change, 0.0) for change in changes) / period
    if losses == 0:
        return 100.0 if gains > 0 else 50.0
    relative_strength = gains / losses
    return 100.0 - (100.0 / (1.0 + relative_strength))


def _atr(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int) -> float:
    true_ranges = []
    for index in range(len(closes) - period, len(closes)):
        previous_close = closes[index - 1]
        true_ranges.append(max(highs[index] - lows[index], abs(highs[index] - previous_close), abs(lows[index] - previous_close)))
    return _mean(true_ranges)


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None
