"""Central feature preparation for PandorickKi market data.

The feature engine is intentionally additive: it enriches normalized market
payloads without replacing existing analysis, brain or decision logic.
Training targets are kept in a separate ``training_only`` block so future
information cannot accidentally enter live decisions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable


Number = int | float


class FeatureEngineError(Exception):
    """Raised when feature preparation receives unusable market data."""


@dataclass(frozen=True)
class FeatureResult:
    """Serializable feature payload returned by the engine."""

    live_features: dict[str, Any]
    training_only: dict[str, Any] = field(default_factory=dict)
    rows: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""

        return {
            "live_features": self.live_features,
            "training_only": self.training_only,
            "rows": self.rows,
            "metadata": self.metadata,
        }


class FeatureEngine:
    """Create live-safe market features from candles and optional context."""

    def __init__(
        self,
        *,
        sma_windows: tuple[int, ...] = (5, 10, 20, 50, 200),
        ema_windows: tuple[int, ...] = (5, 10, 20, 50, 200),
        volatility_window: int = 20,
        target_horizon: int = 1,
    ) -> None:
        self.sma_windows = sma_windows
        self.ema_windows = ema_windows
        self.volatility_window = volatility_window
        self.target_horizon = target_horizon

    def compute(
        self,
        candles: Iterable[dict[str, Any]],
        *,
        symbol: str | None = None,
        market_type: str | None = None,
        optional_context: dict[str, Any] | None = None,
        include_targets: bool = False,
    ) -> FeatureResult:
        """Compute a feature bundle for live analysis or offline training."""

        normalized = [_normalize_candle(item) for item in candles]
        normalized = [item for item in normalized if item is not None]
        if not normalized:
            raise FeatureEngineError("No valid candles supplied.")

        rows = self._compute_rows(normalized, include_targets=include_targets)
        latest = rows[-1]
        live_features = {
            "price": latest["price"],
            "trend": latest["trend"],
            "volatility": latest["volatility"],
            "volume": latest["volume"],
            "candles": latest["candles"],
            "technical_indicators": latest["technical_indicators"],
            "optional_context": _clean_optional_context(optional_context or {}),
        }
        training_only = {}
        if include_targets:
            training_only = {
                "target_direction": latest.get("target_direction"),
                "target_future_return": latest.get("target_future_return"),
                "target_horizon": self.target_horizon,
                "warning": "Training-only targets must not be used for live decisions.",
            }

        return FeatureResult(
            live_features=live_features,
            training_only=training_only,
            rows=rows,
            metadata={
                "symbol": symbol,
                "market_type": market_type,
                "input_candles": len(normalized),
                "output_rows": len(rows),
                "ta_package_available": _ta_available(),
                "live_safe": not include_targets,
            },
        )

    def _compute_rows(self, candles: list[dict[str, float]], *, include_targets: bool) -> list[dict[str, Any]]:
        opens = [item["open"] for item in candles]
        highs = [item["high"] for item in candles]
        lows = [item["low"] for item in candles]
        closes = [item["close"] for item in candles]
        adj_closes = [item.get("adj_close") for item in candles]
        volumes = [item["volume"] for item in candles]
        returns = _percent_returns(closes)
        log_returns = _log_returns(closes)
        true_ranges = _true_ranges(highs, lows, closes)
        atr_values = _sma(true_ranges, 14)
        rows: list[dict[str, Any]] = []

        ema_cache = {window: _ema(closes, window) for window in self.ema_windows}
        sma_cache = {window: _sma(closes, window) for window in self.sma_windows}
        volume_sma = _sma(volumes, 20)
        rolling_volatility = _rolling_std(returns, self.volatility_window)
        close_zscore = _zscore(closes, self.volatility_window)
        volume_zscore = _zscore(volumes, 20)
        rsi_values = _rsi(closes, 14)
        macd_line, macd_signal, macd_hist = _macd(closes)
        adx_values = _adx(highs, lows, closes, 14)
        bb_mid, bb_upper, bb_lower = _bollinger(closes, 20, 2.0)
        stoch_k, stoch_d = _stochastic(highs, lows, closes, 14, 3)
        cci_values = _cci(highs, lows, closes, 20)
        williams_values = _williams_r(highs, lows, closes, 14)
        obv_values = _obv(closes, volumes)
        mfi_values = _mfi(highs, lows, closes, volumes, 14)
        roc_values = _roc(closes, 12)
        kama_values = _kama(closes, 10)

        for index, candle in enumerate(candles):
            close = closes[index]
            previous_close = closes[index - 1] if index > 0 else None
            price_change = _safe_sub(close, previous_close)
            body = close - opens[index]
            upper_wick = highs[index] - max(opens[index], close)
            lower_wick = min(opens[index], close) - lows[index]
            full_range = highs[index] - lows[index]
            row = {
                "price": {
                    "open": opens[index],
                    "high": highs[index],
                    "low": lows[index],
                    "close": close,
                    "adj_close": adj_closes[index],
                    "price_change": price_change,
                    "log_return": log_returns[index],
                    "percent_return": returns[index],
                    "momentum": _momentum(closes, index, 10),
                },
                "trend": {
                    "sma": {str(window): sma_cache[window][index] for window in self.sma_windows},
                    "ema": {str(window): ema_cache[window][index] for window in self.ema_windows},
                    "sma_cross": _cross_state(sma_cache.get(20, [None])[index], sma_cache.get(50, [None])[index]),
                    "ema_cross": _cross_state(ema_cache.get(20, [None])[index], ema_cache.get(50, [None])[index]),
                },
                "volatility": {
                    "atr": atr_values[index],
                    "rolling_volatility": rolling_volatility[index],
                    "standard_deviation": _window_std(closes, index, self.volatility_window),
                    "z_score": close_zscore[index],
                },
                "volume": {
                    "volume": volumes[index],
                    "volume_sma": volume_sma[index],
                    "volume_ratio": _safe_div(volumes[index], volume_sma[index]),
                    "volume_zscore": volume_zscore[index],
                    "signed_volume": volumes[index] if body >= 0 else -volumes[index],
                },
                "candles": {
                    "candle_body": body,
                    "upper_wick": upper_wick,
                    "lower_wick": lower_wick,
                    "candle_ratio": _safe_div(abs(body), full_range),
                    "bullish_candle": close > opens[index],
                    "bearish_candle": close < opens[index],
                },
                "technical_indicators": {
                    "rsi": rsi_values[index],
                    "macd": macd_line[index],
                    "macd_signal": macd_signal[index],
                    "macd_histogram": macd_hist[index],
                    "adx": adx_values[index],
                    "bollinger_middle": bb_mid[index],
                    "bollinger_upper": bb_upper[index],
                    "bollinger_lower": bb_lower[index],
                    "stochastic_k": stoch_k[index],
                    "stochastic_d": stoch_d[index],
                    "cci": cci_values[index],
                    "williams_r": williams_values[index],
                    "atr": atr_values[index],
                    "obv": obv_values[index],
                    "mfi": mfi_values[index],
                    "roc": roc_values[index],
                    "kama": kama_values[index],
                },
            }
            if include_targets:
                future_index = index + self.target_horizon
                future_close = closes[future_index] if future_index < len(closes) else None
                future_return = _safe_percent_change(future_close, close)
                row["target_direction"] = _target_direction(future_return)
                row["target_future_return"] = future_return
            rows.append(_clean_dict(row))

        return rows


def _normalize_candle(item: dict[str, Any]) -> dict[str, float] | None:
    try:
        open_price = _as_float(item.get("open") or item.get("open_price"))
        high = _as_float(item.get("high") or item.get("high_price"))
        low = _as_float(item.get("low") or item.get("low_price"))
        close = _as_float(item.get("close") or item.get("close_price") or item.get("price"))
        volume = _as_float(item.get("volume"), default=0.0)
        adj_close = _as_float(item.get("adj_close") or item.get("adjClose"), default=None)
    except (TypeError, ValueError):
        return None
    if open_price is None or high is None or low is None or close is None:
        return None
    return {
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "adj_close": adj_close,
        "volume": volume or 0.0,
    }


def _clean_optional_context(context: dict[str, Any]) -> dict[str, Any]:
    allowed: dict[str, Any] = {}
    for key, value in context.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            allowed[str(key)] = value
        elif isinstance(value, dict):
            allowed[str(key)] = _clean_optional_context(value)
    return allowed


def _as_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    return float(value)


def _safe_sub(value: float | None, previous: float | None) -> float | None:
    if value is None or previous is None:
        return None
    return value - previous


def _safe_div(value: float | None, divisor: float | None) -> float | None:
    if value is None or divisor in (None, 0):
        return None
    return value / divisor


def _safe_percent_change(value: float | None, previous: float | None) -> float | None:
    if value is None or previous in (None, 0):
        return None
    return (value - previous) / previous * 100.0


def _percent_returns(values: list[float]) -> list[float | None]:
    return [None if i == 0 else _safe_percent_change(values[i], values[i - 1]) for i in range(len(values))]


def _log_returns(values: list[float]) -> list[float | None]:
    result: list[float | None] = [None]
    for index in range(1, len(values)):
        previous = values[index - 1]
        current = values[index]
        result.append(math.log(current / previous) if previous > 0 and current > 0 else None)
    return result


def _sma(values: list[float], window: int) -> list[float | None]:
    result: list[float | None] = []
    for index in range(len(values)):
        if index + 1 < window:
            result.append(None)
        else:
            chunk = values[index + 1 - window : index + 1]
            result.append(sum(chunk) / window)
    return result


def _ema(values: list[float], window: int) -> list[float | None]:
    if not values:
        return []
    multiplier = 2.0 / (window + 1)
    result: list[float | None] = []
    current: float | None = None
    for index, value in enumerate(values):
        if index + 1 < window:
            result.append(None)
            continue
        if current is None:
            current = sum(values[index + 1 - window : index + 1]) / window
        else:
            current = (value - current) * multiplier + current
        result.append(current)
    return result


def _rolling_std(values: list[float | None], window: int) -> list[float | None]:
    numeric = [0.0 if value is None else float(value) for value in values]
    return [_window_std(numeric, index, window) for index in range(len(numeric))]


def _window_std(values: list[float], index: int, window: int) -> float | None:
    if index + 1 < window:
        return None
    chunk = values[index + 1 - window : index + 1]
    mean = sum(chunk) / len(chunk)
    variance = sum((value - mean) ** 2 for value in chunk) / len(chunk)
    return math.sqrt(variance)


def _zscore(values: list[float], window: int) -> list[float | None]:
    result: list[float | None] = []
    for index, value in enumerate(values):
        std = _window_std(values, index, window)
        if std in (None, 0):
            result.append(None)
            continue
        chunk = values[index + 1 - window : index + 1]
        mean = sum(chunk) / len(chunk)
        result.append((value - mean) / std)
    return result


def _true_ranges(highs: list[float], lows: list[float], closes: list[float]) -> list[float]:
    ranges: list[float] = []
    for index, high in enumerate(highs):
        low = lows[index]
        previous_close = closes[index - 1] if index > 0 else closes[index]
        ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
    return ranges


def _rsi(values: list[float], window: int) -> list[float | None]:
    gains = [0.0]
    losses = [0.0]
    for index in range(1, len(values)):
        change = values[index] - values[index - 1]
        gains.append(max(change, 0.0))
        losses.append(abs(min(change, 0.0)))
    avg_gain = _sma(gains, window)
    avg_loss = _sma(losses, window)
    result: list[float | None] = []
    for gain, loss in zip(avg_gain, avg_loss):
        if gain is None or loss is None:
            result.append(None)
        elif loss == 0:
            result.append(100.0)
        else:
            rs = gain / loss
            result.append(100.0 - (100.0 / (1.0 + rs)))
    return result


def _macd(values: list[float]) -> tuple[list[float | None], list[float | None], list[float | None]]:
    ema12 = _ema(values, 12)
    ema26 = _ema(values, 26)
    line: list[float | None] = []
    for fast, slow in zip(ema12, ema26):
        line.append(None if fast is None or slow is None else fast - slow)
    signal = _ema([0.0 if value is None else value for value in line], 9)
    hist = [None if value is None or sig is None else value - sig for value, sig in zip(line, signal)]
    return line, signal, hist


def _adx(highs: list[float], lows: list[float], closes: list[float], window: int) -> list[float | None]:
    true_ranges = _true_ranges(highs, lows, closes)
    plus_dm = [0.0]
    minus_dm = [0.0]
    for index in range(1, len(highs)):
        up_move = highs[index] - highs[index - 1]
        down_move = lows[index - 1] - lows[index]
        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0.0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0.0)
    atr = _sma(true_ranges, window)
    plus_di = [None if a in (None, 0) else 100.0 * p / a for p, a in zip(_sma(plus_dm, window), atr)]
    minus_di = [None if a in (None, 0) else 100.0 * m / a for m, a in zip(_sma(minus_dm, window), atr)]
    dx: list[float] = []
    for plus, minus in zip(plus_di, minus_di):
        if plus is None or minus is None or plus + minus == 0:
            dx.append(0.0)
        else:
            dx.append(100.0 * abs(plus - minus) / (plus + minus))
    return _sma(dx, window)


def _bollinger(values: list[float], window: int, deviations: float) -> tuple[list[float | None], list[float | None], list[float | None]]:
    middle = _sma(values, window)
    upper: list[float | None] = []
    lower: list[float | None] = []
    for index, mid in enumerate(middle):
        std = _window_std(values, index, window)
        upper.append(None if mid is None or std is None else mid + deviations * std)
        lower.append(None if mid is None or std is None else mid - deviations * std)
    return middle, upper, lower


def _stochastic(highs: list[float], lows: list[float], closes: list[float], window: int, smooth: int) -> tuple[list[float | None], list[float | None]]:
    k_values: list[float | None] = []
    for index, close in enumerate(closes):
        if index + 1 < window:
            k_values.append(None)
            continue
        high = max(highs[index + 1 - window : index + 1])
        low = min(lows[index + 1 - window : index + 1])
        k_values.append(None if high == low else (close - low) / (high - low) * 100.0)
    d_values = _rolling_mean_nullable(k_values, smooth)
    return k_values, d_values


def _rolling_mean_nullable(values: list[float | None], window: int) -> list[float | None]:
    result: list[float | None] = []
    for index in range(len(values)):
        if index + 1 < window:
            result.append(None)
            continue
        chunk = values[index + 1 - window : index + 1]
        if any(value is None for value in chunk):
            result.append(None)
        else:
            result.append(sum(float(value) for value in chunk) / window)
    return result


def _cci(highs: list[float], lows: list[float], closes: list[float], window: int) -> list[float | None]:
    typical = [(h + l + c) / 3.0 for h, l, c in zip(highs, lows, closes)]
    sma = _sma(typical, window)
    result: list[float | None] = []
    for index, value in enumerate(typical):
        mean = sma[index]
        if mean is None:
            result.append(None)
            continue
        chunk = typical[index + 1 - window : index + 1]
        mean_dev = sum(abs(item - mean) for item in chunk) / window
        result.append(None if mean_dev == 0 else (value - mean) / (0.015 * mean_dev))
    return result


def _williams_r(highs: list[float], lows: list[float], closes: list[float], window: int) -> list[float | None]:
    result: list[float | None] = []
    for index, close in enumerate(closes):
        if index + 1 < window:
            result.append(None)
            continue
        high = max(highs[index + 1 - window : index + 1])
        low = min(lows[index + 1 - window : index + 1])
        result.append(None if high == low else (high - close) / (high - low) * -100.0)
    return result


def _obv(closes: list[float], volumes: list[float]) -> list[float]:
    result = [0.0]
    for index in range(1, len(closes)):
        if closes[index] > closes[index - 1]:
            result.append(result[-1] + volumes[index])
        elif closes[index] < closes[index - 1]:
            result.append(result[-1] - volumes[index])
        else:
            result.append(result[-1])
    return result


def _mfi(highs: list[float], lows: list[float], closes: list[float], volumes: list[float], window: int) -> list[float | None]:
    typical = [(h + l + c) / 3.0 for h, l, c in zip(highs, lows, closes)]
    positive = [0.0]
    negative = [0.0]
    for index in range(1, len(typical)):
        flow = typical[index] * volumes[index]
        if typical[index] > typical[index - 1]:
            positive.append(flow)
            negative.append(0.0)
        else:
            positive.append(0.0)
            negative.append(flow)
    pos_sma = _sma(positive, window)
    neg_sma = _sma(negative, window)
    result: list[float | None] = []
    for pos, neg in zip(pos_sma, neg_sma):
        if pos is None or neg is None:
            result.append(None)
        elif neg == 0:
            result.append(100.0)
        else:
            ratio = pos / neg
            result.append(100.0 - (100.0 / (1.0 + ratio)))
    return result


def _roc(values: list[float], window: int) -> list[float | None]:
    result: list[float | None] = []
    for index, value in enumerate(values):
        if index < window:
            result.append(None)
        else:
            result.append(_safe_percent_change(value, values[index - window]))
    return result


def _kama(values: list[float], window: int) -> list[float | None]:
    if not values:
        return []
    result: list[float | None] = []
    kama: float | None = None
    fast = 2.0 / (2 + 1)
    slow = 2.0 / (30 + 1)
    for index, value in enumerate(values):
        if index < window:
            result.append(None)
            continue
        change = abs(value - values[index - window])
        volatility = sum(abs(values[i] - values[i - 1]) for i in range(index - window + 1, index + 1))
        efficiency = 0.0 if volatility == 0 else change / volatility
        smoothing = (efficiency * (fast - slow) + slow) ** 2
        kama = value if kama is None else kama + smoothing * (value - kama)
        result.append(kama)
    return result


def _momentum(values: list[float], index: int, window: int) -> float | None:
    if index < window:
        return None
    return values[index] - values[index - window]


def _cross_state(short_value: float | None, long_value: float | None) -> str | None:
    if short_value is None or long_value is None:
        return None
    if short_value > long_value:
        return "BULLISH"
    if short_value < long_value:
        return "BEARISH"
    return "NEUTRAL"


def _target_direction(future_return: float | None) -> str | None:
    if future_return is None:
        return None
    if future_return > 0:
        return "UP"
    if future_return < 0:
        return "DOWN"
    return "FLAT"


def _clean_dict(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _clean_dict(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clean_dict(item) for item in value]
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return round(value, 8)
    return value


def _ta_available() -> bool:
    try:
        __import__("ta")
    except Exception:
        return False
    return True
