"""Versioned input-quality contract for feature-engine candle data."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Iterable, Mapping


FEATURE_DATA_QUALITY_SCHEMA = "pandorickki.feature-data-quality"
FEATURE_DATA_QUALITY_VERSION = 1


class FeatureDataQualityError(ValueError):
    """Raised when candle data cannot satisfy the minimum quality contract."""


@dataclass(frozen=True)
class FeatureDataQualityPolicy:
    """Configurable thresholds for the stable version-1 contract."""

    minimum_candles: int = 1
    full_warmup_candles: int = 200
    require_timestamps: bool = False
    duplicate_policy: str = "keep_last"

    def __post_init__(self) -> None:
        if self.minimum_candles < 1:
            raise ValueError("minimum_candles must be at least 1")
        if self.full_warmup_candles < self.minimum_candles:
            raise ValueError("full_warmup_candles must be at least minimum_candles")
        if self.duplicate_policy != "keep_last":
            raise ValueError("version 1 supports only duplicate_policy='keep_last'")


@dataclass(frozen=True)
class FeatureDataQualityResult:
    """Normalized candles plus a JSON-safe quality report."""

    candles: list[dict[str, Any]]
    report: dict[str, Any]


def project_feature_data_quality(value: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return the bounded quality projection used beyond the feature boundary."""

    report: Any = value.get("feature_quality")
    if not isinstance(report, Mapping) and value.get("schema_name") == FEATURE_DATA_QUALITY_SCHEMA:
        report = value
    if not isinstance(report, Mapping):
        features = value.get("features")
        metadata = features.get("metadata") if isinstance(features, Mapping) else None
        report = metadata.get("data_quality") if isinstance(metadata, Mapping) else None
    if not isinstance(report, Mapping):
        return None

    order = report.get("order")
    warmup = report.get("warmup")
    return {
        "schema_name": report.get("schema_name"),
        "schema_version": report.get("schema_version"),
        "status": report.get("status"),
        "input_rows": report.get("input_rows"),
        "accepted_rows": report.get("accepted_rows"),
        "output_rows": report.get("output_rows"),
        "dropped_rows": report.get("dropped_rows"),
        "duplicate_rows": report.get("duplicate_rows"),
        "timestamped_rows": report.get("timestamped_rows"),
        "order": {
            "status": order.get("status") if isinstance(order, Mapping) else None,
            "reason": order.get("reason") if isinstance(order, Mapping) else None,
        },
        "warmup": {
            "status": warmup.get("status") if isinstance(warmup, Mapping) else None,
            "available_candles": warmup.get("available_candles") if isinstance(warmup, Mapping) else None,
        },
    }


_TIMESTAMP_KEYS = ("timestamp", "open_time", "openTime", "time", "datetime", "date")
_VIOLATION_KEYS = (
    "invalid_row_type",
    "missing_ohlc",
    "non_finite_ohlcv",
    "non_positive_price",
    "negative_volume",
    "inconsistent_ohlc",
    "invalid_timestamp",
)


def prepare_feature_candles(
    candles: Iterable[dict[str, Any]],
    *,
    policy: FeatureDataQualityPolicy | None = None,
) -> FeatureDataQualityResult:
    """Validate, normalize, order and deduplicate candle input.

    Invalid OHLCV rows are removed and counted. Timestamped series are sorted
    ascending and duplicate timestamps retain the last provider row. A series
    without complete timestamp coverage keeps provider order and is explicitly
    marked as unverified rather than being silently rearranged.
    """

    active_policy = policy or FeatureDataQualityPolicy()
    source_rows = list(candles)
    violations = {key: 0 for key in _VIOLATION_KEYS}
    accepted: list[tuple[int, dict[str, Any], float | None]] = []

    for index, item in enumerate(source_rows):
        normalized, timestamp_key, violation = _normalize_and_validate_candle(item)
        if violation is not None:
            violations[violation] += 1
            continue
        accepted.append((index, normalized, timestamp_key))

    timestamped_rows = sum(1 for _, _, timestamp in accepted if timestamp is not None)
    duplicate_rows = 0
    order_status = "UNVERIFIED"
    order_reason = "timestamps_missing"
    reordered = False

    if accepted and timestamped_rows == len(accepted):
        latest_by_timestamp: dict[float, tuple[int, dict[str, Any], float]] = {}
        for index, normalized, timestamp in accepted:
            assert timestamp is not None
            latest_by_timestamp[timestamp] = (index, normalized, timestamp)
        duplicate_rows = len(accepted) - len(latest_by_timestamp)
        ordered = sorted(latest_by_timestamp.values(), key=lambda entry: entry[2])
        kept_input_indexes = [entry[0] for entry in ordered]
        reordered = kept_input_indexes != sorted(kept_input_indexes)
        output = [entry[1] for entry in ordered]
        order_status = "VERIFIED"
        order_reason = "timestamps_sorted_ascending"
    else:
        output = [entry[1] for entry in accepted]
        if timestamped_rows:
            order_reason = "timestamps_partial"

    if active_policy.require_timestamps and order_status != "VERIFIED":
        raise FeatureDataQualityError(
            f"Feature data quality requires timestamps for every valid candle; {order_reason}."
        )

    if len(output) < active_policy.minimum_candles:
        dropped = len(source_rows) - len(accepted)
        raise FeatureDataQualityError(
            "Feature data quality accepted "
            f"{len(output)} candle(s), minimum {active_policy.minimum_candles}; "
            f"dropped {dropped} invalid row(s) and {duplicate_rows} duplicate row(s)."
        )

    dropped_rows = len(source_rows) - len(accepted)
    warmup_status = (
        "READY" if len(output) >= active_policy.full_warmup_candles else "WARMING"
    )
    status = (
        "DEGRADED"
        if dropped_rows or duplicate_rows
        else ("WARN" if order_status != "VERIFIED" else "PASS")
    )
    warnings: list[str] = []
    if duplicate_rows:
        warnings.append(
            f"Removed {duplicate_rows} duplicate timestamp row(s) using keep_last."
        )
    if order_status != "VERIFIED":
        warnings.append(
            "Candle order could not be verified because timestamp coverage is incomplete."
        )
    if warmup_status != "READY":
        warnings.append("Some indicators are still in warmup and may return null.")

    report = {
        "schema_name": FEATURE_DATA_QUALITY_SCHEMA,
        "schema_version": FEATURE_DATA_QUALITY_VERSION,
        "status": status,
        "input_rows": len(source_rows),
        "accepted_rows": len(accepted),
        "output_rows": len(output),
        "dropped_rows": dropped_rows,
        "duplicate_rows": duplicate_rows,
        "timestamped_rows": timestamped_rows,
        "violations": violations,
        "order": {
            "status": order_status,
            "reason": order_reason,
            "direction": "ascending" if order_status == "VERIFIED" else None,
            "reordered": reordered,
            "duplicate_policy": active_policy.duplicate_policy,
        },
        "warmup": {
            "status": warmup_status,
            "available_candles": len(output),
            "minimum_candles": active_policy.minimum_candles,
            "full_warmup_candles": active_policy.full_warmup_candles,
            "minimum_met": len(output) >= active_policy.minimum_candles,
        },
        "warnings": warnings,
    }
    return FeatureDataQualityResult(candles=output, report=report)


def _normalize_and_validate_candle(
    item: Any,
) -> tuple[dict[str, Any], float | None, str | None]:
    if not isinstance(item, dict):
        return {}, None, "invalid_row_type"

    raw_open = _first_defined(item, "open", "open_price")
    raw_high = _first_defined(item, "high", "high_price")
    raw_low = _first_defined(item, "low", "low_price")
    raw_close = _first_defined(item, "close", "close_price", "price")
    if any(value is None for value in (raw_open, raw_high, raw_low, raw_close)):
        return {}, None, "missing_ohlc"

    raw_volume = _first_defined(item, "volume")
    raw_adj_close = _first_defined(item, "adj_close", "adjClose")
    try:
        open_price = float(raw_open)
        high = float(raw_high)
        low = float(raw_low)
        close = float(raw_close)
        volume = 0.0 if raw_volume is None else float(raw_volume)
        adj_close = None if raw_adj_close is None else float(raw_adj_close)
    except (TypeError, ValueError):
        return {}, None, "non_finite_ohlcv"

    numeric = [open_price, high, low, close, volume]
    if adj_close is not None:
        numeric.append(adj_close)
    if not all(math.isfinite(value) for value in numeric):
        return {}, None, "non_finite_ohlcv"
    if min(open_price, high, low, close) <= 0 or (
        adj_close is not None and adj_close <= 0
    ):
        return {}, None, "non_positive_price"
    if volume < 0:
        return {}, None, "negative_volume"
    if high < max(open_price, close, low) or low > min(open_price, close, high):
        return {}, None, "inconsistent_ohlc"

    raw_timestamp = _first_defined(item, *_TIMESTAMP_KEYS)
    timestamp_key: float | None = None
    timestamp_value: float | str | None = None
    if raw_timestamp is not None:
        try:
            timestamp_key, timestamp_value = _normalize_timestamp(raw_timestamp)
        except (TypeError, ValueError, OverflowError):
            return {}, None, "invalid_timestamp"

    normalized: dict[str, Any] = {
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "adj_close": adj_close,
        "volume": volume,
    }
    if timestamp_value is not None:
        normalized["timestamp"] = timestamp_value
    return normalized, timestamp_key, None


def _first_defined(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in item and item[key] is not None:
            return item[key]
    return None


def _normalize_timestamp(value: Any) -> tuple[float, float | str]:
    if isinstance(value, bool):
        raise ValueError("boolean is not a timestamp")
    if isinstance(value, (int, float)):
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError("timestamp is not finite")
        return numeric, numeric

    text = str(value).strip()
    if not text:
        raise ValueError("timestamp is empty")
    try:
        numeric = float(text)
    except ValueError:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        normalized = parsed.astimezone(UTC)
        return normalized.timestamp(), normalized.isoformat()
    if not math.isfinite(numeric):
        raise ValueError("timestamp is not finite")
    return numeric, numeric
