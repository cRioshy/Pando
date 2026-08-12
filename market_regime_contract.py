"""Observer-only, deterministic three-axis market regime contract."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Mapping, Sequence

from feature_data_quality_contract import (
    FEATURE_DATA_QUALITY_SCHEMA,
    FEATURE_DATA_QUALITY_VERSION,
    FeatureDataQualityError,
    FeatureDataQualityPolicy,
    prepare_feature_candles,
)
from features.feature_engine import FeatureEngine, FeatureEngineError


SCHEMA_NAME = "pandorickki.market-regime-snapshot"
SCHEMA_VERSION = 1
CLASSIFIER_VERSION = "regime-v1"
FEATURE_VERSION = "feature-engine-v1"

TREND_DIRECTIONS = frozenset({"STRONG_UP", "UP", "SIDEWAYS", "DOWN", "STRONG_DOWN", "UNKNOWN"})
VOLATILITY_REGIMES = frozenset({"LOW", "MEDIUM", "HIGH", "EXTREME", "UNKNOWN"})
TREND_PHASES = frozenset({"STABLE", "WEAKENING", "REVERSAL", "BREAKOUT", "UNKNOWN"})
QUALITY_STATUSES = frozenset({"OK", "DEGRADED", "REJECTED"})


@dataclass(frozen=True)
class MarketRegimePolicy:
    """All classifier parameters included in the configuration fingerprint."""

    minimum_candles: int = 200
    full_warmup_candles: int = 200
    slope_lookback: int = 5
    structure_lookback: int = 20
    efficiency_lookback: int = 20
    breakout_lookback: int = 20
    volatility_baseline_candles: int = 60
    trend_score_threshold: float = 0.30
    strong_trend_score_threshold: float = 0.65
    sideways_efficiency_max: float = 0.22
    sideways_slope_max: float = 0.0025
    sideways_crosses_minimum: int = 4
    strong_trend_minimum_groups: int = 5
    trend_minimum_groups: int = 3
    strong_adx_minimum: float = 25.0
    degraded_confidence_cap: float = 0.60
    volatility_low_percentile: float = 0.25
    volatility_high_percentile: float = 0.75
    volatility_extreme_percentile: float = 0.95
    weakening_confirmations: int = 2
    reversal_confirmations: int = 3
    breakout_confirmations: int = 2

    def __post_init__(self) -> None:
        if self.minimum_candles < 30:
            raise ValueError("minimum_candles must be at least 30")
        if self.full_warmup_candles < self.minimum_candles:
            raise ValueError("full_warmup_candles must be at least minimum_candles")
        if min(self.slope_lookback, self.structure_lookback, self.efficiency_lookback, self.breakout_lookback) < 2:
            raise ValueError("lookbacks must be at least 2")
        if self.volatility_baseline_candles < 20:
            raise ValueError("volatility_baseline_candles must be at least 20")
        ordered = (
            self.volatility_low_percentile,
            self.volatility_high_percentile,
            self.volatility_extreme_percentile,
        )
        if not 0.0 < ordered[0] < ordered[1] < ordered[2] < 1.0:
            raise ValueError("volatility percentiles must be strictly ordered inside (0, 1)")
        for value in (
            self.trend_score_threshold,
            self.strong_trend_score_threshold,
            self.sideways_efficiency_max,
            self.sideways_slope_max,
            self.degraded_confidence_cap,
        ):
            if not math.isfinite(value) or value < 0.0 or value > 1.0:
                raise ValueError("normalized policy values must be finite and inside [0, 1]")


@dataclass(frozen=True)
class MarketRegimeSnapshot:
    """Compact public and persisted regime observation."""

    regime_id: str
    symbol: str
    asset_type: str
    source_event_id: str
    feature_snapshot_id: str
    timestamp: str
    trend_direction: str
    trend_confidence: float
    trend_reasons: list[str] = field(default_factory=list)
    volatility_regime: str = "UNKNOWN"
    volatility_score: float = 0.0
    volatility_reasons: list[str] = field(default_factory=list)
    trend_phase: str = "UNKNOWN"
    phase_confidence: float = 0.0
    phase_reasons: list[str] = field(default_factory=list)
    data_quality_status: str = "REJECTED"
    data_quality_score: float = 0.0
    timeframes_used: list[str] = field(default_factory=list)
    missing_timeframes: list[str] = field(default_factory=list)
    classifier_version: str = CLASSIFIER_VERSION
    config_fingerprint: str = ""
    schema_version: int = SCHEMA_VERSION
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.trend_direction not in TREND_DIRECTIONS:
            raise ValueError("unsupported trend_direction")
        if self.volatility_regime not in VOLATILITY_REGIMES:
            raise ValueError("unsupported volatility_regime")
        if self.trend_phase not in TREND_PHASES:
            raise ValueError("unsupported trend_phase")
        if self.data_quality_status not in QUALITY_STATUSES:
            raise ValueError("unsupported data_quality_status")
        for value in (
            self.trend_confidence,
            self.volatility_score,
            self.phase_confidence,
            self.data_quality_score,
        ):
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError("all scores must be finite and inside [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": SCHEMA_NAME,
            **asdict(self),
            "mode": "OBSERVER_ONLY",
            "affects_active_decision": False,
            "ready_for_telegram": False,
            "order_execution_allowed": False,
        }


def configuration_fingerprint(policy: MarketRegimePolicy) -> str:
    """Return a stable SHA-256 for every classification parameter."""

    return _sha256({"classifier_version": CLASSIFIER_VERSION, "policy": asdict(policy)})


def build_market_regime_snapshot(
    *,
    symbol: Any,
    asset_type: Any,
    timeframe: Any,
    candles: Sequence[Mapping[str, Any]] | None,
    source_event_id: Any,
    policy: MarketRegimePolicy | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Classify one timestamped series without mutating any decision path."""

    active = policy or MarketRegimePolicy()
    normalized_symbol = str(symbol or "").strip().upper() or "UNKNOWN"
    normalized_asset = str(asset_type or "").strip().lower() or "unknown"
    normalized_timeframe = str(timeframe or "").strip().lower() or "unknown"
    normalized_source_id = str(source_event_id or "").strip() or "UNKNOWN"
    config_id = configuration_fingerprint(active)
    created = created_at or datetime.now(UTC).isoformat()
    raw_candles = list(candles) if isinstance(candles, Sequence) and not isinstance(candles, (str, bytes)) else []

    try:
        prepared = prepare_feature_candles(
            raw_candles,
            policy=FeatureDataQualityPolicy(
                minimum_candles=active.minimum_candles,
                full_warmup_candles=active.full_warmup_candles,
                require_timestamps=True,
            ),
        )
        feature_result = FeatureEngine(
            quality_policy=FeatureDataQualityPolicy(
                minimum_candles=active.minimum_candles,
                full_warmup_candles=active.full_warmup_candles,
                require_timestamps=True,
            )
        ).compute(
            prepared.candles,
            symbol=normalized_symbol,
            market_type=normalized_asset,
            include_targets=False,
        )
        quality = _quality_projection(prepared.report)
        rows = feature_result.rows
        latest_timestamp = str(prepared.candles[-1].get("timestamp"))
        input_latest = _latest_input_timestamp(raw_candles)
        prepared_latest = _timestamp_number(prepared.candles[-1].get("timestamp"))
        if input_latest is not None and prepared_latest is not None and input_latest > prepared_latest:
            raise FeatureDataQualityError("Latest timestamped provider candle was rejected.")
        feature_id = _feature_snapshot_id(
            asset_type=normalized_asset,
            symbol=normalized_symbol,
            timeframe=normalized_timeframe,
            latest_timestamp=latest_timestamp,
            candles=prepared.candles,
            quality_report=prepared.report,
        )
    except (FeatureDataQualityError, FeatureEngineError, IndexError, TypeError, ValueError) as exc:
        feature_id = _sha256(
            {
                "asset_type": normalized_asset,
                "symbol": normalized_symbol,
                "timeframe": normalized_timeframe,
                "feature_version": FEATURE_VERSION,
                "quality_version": FEATURE_DATA_QUALITY_VERSION,
                "input_fingerprint": _safe_input_fingerprint(raw_candles),
            }
        )
        return _unknown_snapshot(
            symbol=normalized_symbol,
            asset_type=normalized_asset,
            timeframe=normalized_timeframe,
            source_event_id=normalized_source_id,
            feature_snapshot_id=feature_id,
            timestamp="UNKNOWN",
            config_fingerprint=config_id,
            created_at=created,
            reason=f"MR_DATA_REJECTED:{type(exc).__name__}",
        )

    if quality["status"] == "REJECTED":
        return _unknown_snapshot(
            symbol=normalized_symbol,
            asset_type=normalized_asset,
            timeframe=normalized_timeframe,
            source_event_id=normalized_source_id,
            feature_snapshot_id=feature_id,
            timestamp=latest_timestamp,
            config_fingerprint=config_id,
            created_at=created,
            reason="MR_DATA_REJECTED",
        )

    trend = classify_trend(rows, quality_status=quality["status"], policy=active)
    volatility = classify_volatility(rows, quality_status=quality["status"], policy=active)
    phase = classify_phase(
        rows,
        trend_direction=trend["value"],
        quality_status=quality["status"],
        policy=active,
    )
    identity = {
        "asset_type": normalized_asset,
        "symbol": normalized_symbol,
        "timeframe": normalized_timeframe,
        "latest_candle_timestamp": latest_timestamp,
        "feature_snapshot_id": feature_id,
        "classifier_version": CLASSIFIER_VERSION,
        "config_fingerprint": config_id,
    }
    snapshot = MarketRegimeSnapshot(
        regime_id=_sha256(identity),
        symbol=normalized_symbol,
        asset_type=normalized_asset,
        source_event_id=normalized_source_id,
        feature_snapshot_id=feature_id,
        timestamp=latest_timestamp,
        trend_direction=trend["value"],
        trend_confidence=trend["confidence"],
        trend_reasons=trend["reasons"],
        volatility_regime=volatility["value"],
        volatility_score=volatility["score"],
        volatility_reasons=volatility["reasons"],
        trend_phase=phase["value"],
        phase_confidence=phase["confidence"],
        phase_reasons=phase["reasons"],
        data_quality_status=quality["status"],
        data_quality_score=quality["score"],
        timeframes_used=[normalized_timeframe],
        missing_timeframes=_missing_timeframes(normalized_asset, normalized_timeframe),
        config_fingerprint=config_id,
        created_at=created,
    )
    return snapshot.to_dict()


def classify_trend(
    rows: Sequence[Mapping[str, Any]],
    *,
    quality_status: str,
    policy: MarketRegimePolicy,
) -> dict[str, Any]:
    """Classify trend direction from independent structural evidence groups."""

    if quality_status == "REJECTED" or len(rows) < max(policy.structure_lookback, policy.slope_lookback) + 1:
        return _axis("UNKNOWN", 0.0, ["MR_TREND_INSUFFICIENT"])
    closes = [_number(_path(row, "price", "close")) for row in rows]
    if any(value is None or value <= 0 for value in closes):
        return _axis("UNKNOWN", 0.0, ["MR_TREND_PRICE_INVALID"])
    close_values = [float(value) for value in closes if value is not None]
    latest = rows[-1]
    price = close_values[-1]
    evidence: list[tuple[str, float, float]] = []

    def add(name: str, raw: Any, weight: float) -> None:
        value = _number(raw)
        if value is not None and value != 0:
            evidence.append((name, max(-1.0, min(1.0, value)), weight))

    sma20 = _number(_path(latest, "trend", "sma", "20"))
    sma50 = _number(_path(latest, "trend", "sma", "50"))
    sma200 = _number(_path(latest, "trend", "sma", "200"))
    ema20 = _number(_path(latest, "trend", "ema", "20"))
    ema50 = _number(_path(latest, "trend", "ema", "50"))
    add("MR_TREND_PRICE_SMA20", _signed(price, sma20), 0.10)
    add("MR_TREND_SMA20_SMA50", _signed(sma20, sma50), 0.14)
    add("MR_TREND_SMA50_SMA200", _signed(sma50, sma200), 0.17)
    add("MR_TREND_EMA20_EMA50", _signed(ema20, ema50), 0.14)

    sma20_series = [_number(_path(row, "trend", "sma", "20")) for row in rows]
    slope = _normalized_slope(sma20_series, policy.slope_lookback)
    add("MR_TREND_SMA20_SLOPE", _scaled(slope, 0.01), 0.15)
    structure = _structure_score(close_values, policy.structure_lookback)
    add("MR_TREND_STRUCTURE", structure, 0.13)
    efficiency = _efficiency(close_values, policy.efficiency_lookback)
    add("MR_TREND_EFFICIENCY", _signed_efficiency(close_values, efficiency, policy.efficiency_lookback), 0.09)
    macd = _number(_path(latest, "technical_indicators", "macd_histogram"))
    roc = _number(_path(latest, "technical_indicators", "roc"))
    kama = _number(_path(latest, "technical_indicators", "kama"))
    technical_votes = [_signed(macd, 0.0), _signed(roc, 0.0), _signed(price, kama)]
    technical = sum(value for value in technical_votes if value is not None) / max(
        sum(value is not None for value in technical_votes), 1
    )
    add("MR_TREND_TECHNICAL_CONFIRMATION", technical, 0.08)

    score = sum(value * weight for _, value, weight in evidence)
    positive = sum(value > 0 for _, value, _ in evidence)
    negative = sum(value < 0 for _, value, _ in evidence)
    agreeing = max(positive, negative)
    contradictions = min(positive, negative)
    crossings = _crossings(close_values, [value for value in sma20_series], policy.efficiency_lookback)
    sideways = (
        efficiency is not None
        and efficiency <= policy.sideways_efficiency_max
        and slope is not None
        and abs(slope) <= policy.sideways_slope_max
        and crossings >= policy.sideways_crosses_minimum
        and abs(score) < policy.trend_score_threshold
    )
    adx = _number(_path(latest, "technical_indicators", "adx"))
    reasons = [name for name, value, _ in evidence if (score >= 0 and value > 0) or (score < 0 and value < 0)]
    if sideways:
        value = "SIDEWAYS"
        confidence = min(1.0, 0.45 + (1.0 - efficiency) * 0.3 + min(crossings / 10.0, 0.25))
        reasons = ["MR_TREND_LOW_EFFICIENCY", "MR_TREND_FLAT_SLOPE", "MR_TREND_MEAN_CROSSES"]
    elif contradictions >= agreeing or agreeing < policy.trend_minimum_groups:
        return _axis("UNKNOWN", 0.0, ["MR_TREND_CONFLICTING_EVIDENCE"])
    elif score >= policy.strong_trend_score_threshold and agreeing >= policy.strong_trend_minimum_groups and (adx or 0.0) >= policy.strong_adx_minimum:
        value = "STRONG_UP"
        confidence = _trend_confidence(score, agreeing, len(evidence), contradictions)
    elif score >= policy.trend_score_threshold and agreeing >= policy.trend_minimum_groups:
        value = "UP"
        confidence = _trend_confidence(score, agreeing, len(evidence), contradictions)
    elif score <= -policy.strong_trend_score_threshold and agreeing >= policy.strong_trend_minimum_groups and (adx or 0.0) >= policy.strong_adx_minimum:
        value = "STRONG_DOWN"
        confidence = _trend_confidence(score, agreeing, len(evidence), contradictions)
    elif score <= -policy.trend_score_threshold and agreeing >= policy.trend_minimum_groups:
        value = "DOWN"
        confidence = _trend_confidence(score, agreeing, len(evidence), contradictions)
    else:
        return _axis("UNKNOWN", 0.0, ["MR_TREND_EVIDENCE_WEAK"])
    if quality_status == "DEGRADED":
        if value == "STRONG_UP":
            value = "UP"
            reasons.append("MR_QUALITY_STRONG_CLASS_DOWNGRADED")
        elif value == "STRONG_DOWN":
            value = "DOWN"
            reasons.append("MR_QUALITY_STRONG_CLASS_DOWNGRADED")
        confidence = min(confidence, policy.degraded_confidence_cap)
    return _axis(value, confidence, reasons)


def classify_volatility(
    rows: Sequence[Mapping[str, Any]],
    *,
    quality_status: str,
    policy: MarketRegimePolicy,
) -> dict[str, Any]:
    """Classify normalized ATR against a strictly backward-looking baseline."""

    if quality_status == "REJECTED":
        return {"value": "UNKNOWN", "score": 0.0, "reasons": ["MR_VOL_QUALITY_REJECTED"]}
    normalized: list[float] = []
    for row in rows:
        price = _number(_path(row, "price", "close"))
        atr = _number(_path(row, "volatility", "atr"))
        if price is not None and price > 0 and atr is not None and atr >= 0:
            normalized.append(atr / price)
    if len(normalized) < policy.volatility_baseline_candles + 1:
        return {"value": "UNKNOWN", "score": 0.0, "reasons": ["MR_VOL_BASELINE_INSUFFICIENT"]}
    current = normalized[-1]
    baseline = normalized[-(policy.volatility_baseline_candles + 1) : -1]
    percentile = sum(value <= current for value in baseline) / len(baseline)
    if percentile <= policy.volatility_low_percentile:
        value = "LOW"
    elif percentile <= policy.volatility_high_percentile:
        value = "MEDIUM"
    elif percentile <= policy.volatility_extreme_percentile:
        value = "HIGH"
    else:
        value = "EXTREME"
    reasons = ["MR_VOL_NORMALIZED_ATR", "MR_VOL_BACKWARD_PERCENTILE"]
    if quality_status == "DEGRADED":
        reasons.append("MR_VOL_QUALITY_DEGRADED")
    return {"value": value, "score": _score(percentile), "reasons": reasons}


def classify_phase(
    rows: Sequence[Mapping[str, Any]],
    *,
    trend_direction: str,
    quality_status: str,
    policy: MarketRegimePolicy,
) -> dict[str, Any]:
    """Classify phase separately from direction using multiple confirmations."""

    if quality_status == "REJECTED" or trend_direction == "UNKNOWN" or len(rows) < policy.breakout_lookback + 3:
        return _axis("UNKNOWN", 0.0, ["MR_PHASE_INSUFFICIENT"])
    closes = [_number(_path(row, "price", "close")) for row in rows]
    highs = [_number(_path(row, "price", "high")) for row in rows]
    lows = [_number(_path(row, "price", "low")) for row in rows]
    if any(value is None for value in closes[-(policy.breakout_lookback + 2) :]):
        return _axis("UNKNOWN", 0.0, ["MR_PHASE_PRICE_INVALID"])
    close_values = [float(value) for value in closes if value is not None]
    current = rows[-1]
    previous = rows[-2]

    prior_closes = close_values[-(policy.breakout_lookback + 1) : -1]
    prior_highs = [float(value) for value in highs[-(policy.breakout_lookback + 1) : -1] if value is not None]
    prior_lows = [float(value) for value in lows[-(policy.breakout_lookback + 1) : -1] if value is not None]
    prior_efficiency = _efficiency(prior_closes, min(policy.breakout_lookback - 1, len(prior_closes) - 1))
    latest_close = close_values[-1]
    atr = _number(_path(current, "volatility", "atr")) or 0.0
    breakout_direction = 1 if prior_highs and latest_close > max(prior_highs) else (-1 if prior_lows and latest_close < min(prior_lows) else 0)
    breakout_checks = [
        breakout_direction != 0,
        prior_efficiency is not None and prior_efficiency <= 0.40,
        atr > 0 and abs(latest_close - close_values[-2]) >= 0.5 * atr,
        (_number(_path(current, "volume", "volume_ratio")) or 0.0) >= 1.10,
        (_number(_path(current, "technical_indicators", "adx")) or 0.0)
        > (_number(_path(previous, "technical_indicators", "adx")) or 0.0),
    ]
    breakout_confirmations = sum(breakout_checks[1:])
    if breakout_direction and breakout_confirmations >= policy.breakout_confirmations:
        confidence = min(1.0, 0.45 + 0.1 * breakout_confirmations)
        return _phase_axis("BREAKOUT", confidence, ["MR_PHASE_RANGE_EXIT", "MR_PHASE_BREAKOUT_CONFIRMED"], quality_status, policy)

    direction_sign = 1 if trend_direction in {"UP", "STRONG_UP"} else (-1 if trend_direction in {"DOWN", "STRONG_DOWN"} else 0)
    momentum_now = _number(_path(current, "price", "momentum"))
    momentum_prev = _number(_path(previous, "price", "momentum"))
    macd_now = _number(_path(current, "technical_indicators", "macd_histogram"))
    macd_prev = _number(_path(previous, "technical_indicators", "macd_histogram"))
    roc_now = _number(_path(current, "technical_indicators", "roc"))
    adx_now = _number(_path(current, "technical_indicators", "adx"))
    adx_prev = _number(_path(previous, "technical_indicators", "adx"))
    slope_now = _normalized_slope([_number(_path(row, "trend", "ema", "20")) for row in rows], policy.slope_lookback)
    slope_prev = _normalized_slope([_number(_path(row, "trend", "ema", "20")) for row in rows[:-1]], policy.slope_lookback)
    recent_returns = [_number(_path(row, "price", "percent_return")) for row in rows[-3:]]

    reversal_checks = [
        direction_sign != 0 and momentum_now is not None and momentum_now * direction_sign < 0,
        direction_sign != 0 and macd_now is not None and macd_prev is not None and macd_now * direction_sign < 0 <= macd_prev * direction_sign,
        direction_sign != 0 and roc_now is not None and roc_now * direction_sign < 0,
        direction_sign != 0 and sum(value is not None and value * direction_sign < 0 for value in recent_returns) >= 2,
        direction_sign != 0 and slope_now is not None and slope_now * direction_sign < 0,
    ]
    reversal_count = sum(reversal_checks)
    if reversal_count >= policy.reversal_confirmations:
        return _phase_axis(
            "REVERSAL",
            min(1.0, 0.45 + 0.1 * reversal_count),
            ["MR_PHASE_MOMENTUM_REVERSAL", "MR_PHASE_MULTI_CONFIRMATION"],
            quality_status,
            policy,
        )

    weakening_checks = [
        direction_sign != 0 and momentum_now is not None and momentum_prev is not None and momentum_now * direction_sign < momentum_prev * direction_sign,
        direction_sign != 0 and macd_now is not None and macd_prev is not None and macd_now * direction_sign < macd_prev * direction_sign,
        adx_now is not None and adx_prev is not None and adx_now < adx_prev,
        slope_now is not None and slope_prev is not None and abs(slope_now) < abs(slope_prev),
    ]
    weakening_count = sum(weakening_checks)
    if direction_sign and weakening_count >= policy.weakening_confirmations:
        return _phase_axis(
            "WEAKENING",
            min(1.0, 0.45 + 0.1 * weakening_count),
            ["MR_PHASE_TREND_EVIDENCE_WEAKENING"],
            quality_status,
            policy,
        )
    if trend_direction in {"UP", "STRONG_UP", "DOWN", "STRONG_DOWN", "SIDEWAYS"}:
        return _phase_axis("STABLE", 0.60, ["MR_PHASE_STRUCTURE_STABLE"], quality_status, policy)
    return _axis("UNKNOWN", 0.0, ["MR_PHASE_CONFLICTING_EVIDENCE"])


def _feature_snapshot_id(
    *,
    asset_type: str,
    symbol: str,
    timeframe: str,
    latest_timestamp: str,
    candles: Sequence[Mapping[str, Any]],
    quality_report: Mapping[str, Any],
) -> str:
    candle_fingerprint = _sha256(
        [
            [row.get("timestamp"), row.get("open"), row.get("high"), row.get("low"), row.get("close"), row.get("volume")]
            for row in candles
        ]
    )
    return _sha256(
        {
            "asset_type": asset_type,
            "symbol": symbol,
            "timeframe": timeframe,
            "latest_candle_timestamp": latest_timestamp,
            "candle_fingerprint": candle_fingerprint,
            "feature_version": FEATURE_VERSION,
            "quality_schema": quality_report.get("schema_name"),
            "quality_version": quality_report.get("schema_version"),
        }
    )


def _quality_projection(report: Mapping[str, Any]) -> dict[str, Any]:
    order = report.get("order") if isinstance(report.get("order"), Mapping) else {}
    warmup = report.get("warmup") if isinstance(report.get("warmup"), Mapping) else {}
    if order.get("status") != "VERIFIED" or warmup.get("status") != "READY":
        return {"status": "REJECTED", "score": 0.0}
    source = str(report.get("status") or "")
    if source == "PASS":
        return {"status": "OK", "score": 1.0}
    if source in {"WARN", "DEGRADED"}:
        input_rows = max(int(report.get("input_rows") or 0), 1)
        affected = int(report.get("dropped_rows") or 0) + int(report.get("duplicate_rows") or 0)
        return {"status": "DEGRADED", "score": _score(1.0 - affected / input_rows)}
    return {"status": "REJECTED", "score": 0.0}


def _unknown_snapshot(
    *,
    symbol: str,
    asset_type: str,
    timeframe: str,
    source_event_id: str,
    feature_snapshot_id: str,
    timestamp: str,
    config_fingerprint: str,
    created_at: str,
    reason: str,
) -> dict[str, Any]:
    identity = {
        "asset_type": asset_type,
        "symbol": symbol,
        "timeframe": timeframe,
        "latest_candle_timestamp": timestamp,
        "feature_snapshot_id": feature_snapshot_id,
        "classifier_version": CLASSIFIER_VERSION,
        "config_fingerprint": config_fingerprint,
    }
    return MarketRegimeSnapshot(
        regime_id=_sha256(identity),
        symbol=symbol,
        asset_type=asset_type,
        source_event_id=source_event_id,
        feature_snapshot_id=feature_snapshot_id,
        timestamp=timestamp,
        trend_direction="UNKNOWN",
        trend_confidence=0.0,
        trend_reasons=[reason],
        volatility_regime="UNKNOWN",
        volatility_score=0.0,
        volatility_reasons=[reason],
        trend_phase="UNKNOWN",
        phase_confidence=0.0,
        phase_reasons=[reason],
        data_quality_status="REJECTED",
        data_quality_score=0.0,
        timeframes_used=[timeframe] if timeframe != "unknown" else [],
        missing_timeframes=_missing_timeframes(asset_type, timeframe),
        config_fingerprint=config_fingerprint,
        created_at=created_at,
    ).to_dict()


def _missing_timeframes(asset_type: str, timeframe: str) -> list[str]:
    expected = ["1m", "5m", "15m", "1h", "4h"] if asset_type == "crypto" else ["1m", "5m", "15m", "1h", "4h", "1d"]
    return [item for item in expected if item != timeframe]


def _phase_axis(value: str, confidence: float, reasons: list[str], quality: str, policy: MarketRegimePolicy) -> dict[str, Any]:
    if quality == "DEGRADED":
        confidence = min(confidence, policy.degraded_confidence_cap)
        reasons = [*reasons, "MR_PHASE_QUALITY_DEGRADED"]
    return _axis(value, confidence, reasons)


def _axis(value: str, confidence: float, reasons: list[str]) -> dict[str, Any]:
    return {"value": value, "confidence": _score(confidence), "reasons": list(dict.fromkeys(reasons))}


def _trend_confidence(score: float, agreeing: int, total: int, contradictions: int) -> float:
    agreement = agreeing / max(total, 1)
    penalty = contradictions / max(total, 1)
    return _score(abs(score) * 0.7 + agreement * 0.3 - penalty * 0.25)


def _structure_score(closes: Sequence[float], lookback: int) -> float | None:
    values = closes[-lookback:]
    if len(values) < 4:
        return None
    half = len(values) // 2
    earlier, later = values[:half], values[half:]
    votes = [
        1 if max(later) > max(earlier) else (-1 if max(later) < max(earlier) else 0),
        1 if min(later) > min(earlier) else (-1 if min(later) < min(earlier) else 0),
    ]
    return sum(votes) / len(votes)


def _efficiency(values: Sequence[float], lookback: int) -> float | None:
    window = list(values[-(lookback + 1) :])
    if len(window) < 2:
        return None
    path = sum(abs(window[index] - window[index - 1]) for index in range(1, len(window)))
    return abs(window[-1] - window[0]) / path if path > 0 else 0.0


def _signed_efficiency(values: Sequence[float], efficiency: float | None, lookback: int) -> float | None:
    if efficiency is None or len(values) < lookback + 1:
        return None
    return efficiency if values[-1] > values[-(lookback + 1)] else (-efficiency if values[-1] < values[-(lookback + 1)] else 0.0)


def _crossings(prices: Sequence[float], averages: Sequence[float | None], lookback: int) -> int:
    pairs = [(price, average) for price, average in zip(prices[-lookback:], averages[-lookback:]) if average is not None]
    states = [1 if price > float(average) else (-1 if price < float(average) else 0) for price, average in pairs]
    return sum(states[index] and states[index - 1] and states[index] != states[index - 1] for index in range(1, len(states)))


def _normalized_slope(values: Sequence[float | None], lookback: int) -> float | None:
    usable = list(values[-(lookback + 1) :])
    if len(usable) < lookback + 1 or any(value is None for value in usable):
        return None
    first, last = float(usable[0]), float(usable[-1])
    return (last - first) / abs(first) / lookback if first else None


def _scaled(value: float | None, scale: float) -> float | None:
    return None if value is None else max(-1.0, min(1.0, value / scale))


def _signed(left: Any, right: Any) -> float | None:
    a, b = _number(left), _number(right)
    if a is None or b is None:
        return None
    return 1.0 if a > b else (-1.0 if a < b else 0.0)


def _path(value: Mapping[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _score(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 6)


def _safe_input_fingerprint(candles: Sequence[Mapping[str, Any]]) -> str:
    safe: list[Any] = []
    for row in candles[:500]:
        if isinstance(row, Mapping):
            safe.append([_json_scalar(row.get(key)) for key in ("timestamp", "open", "high", "low", "close", "volume")])
        else:
            safe.append(type(row).__name__)
    return _sha256(safe)


def _latest_input_timestamp(candles: Sequence[Mapping[str, Any]]) -> float | None:
    timestamps = [_timestamp_number(row.get("timestamp")) for row in candles if isinstance(row, Mapping)]
    values = [value for value in timestamps if value is not None]
    return max(values) if values else None


def _timestamp_number(value: Any) -> float | None:
    number = _number(value)
    if number is not None:
        return number
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).timestamp()


def _json_scalar(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    number = _number(value)
    return number if number is not None else type(value).__name__


def _sha256(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
