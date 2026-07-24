"""Configuration for the public Pandorick Learning Graph."""

from __future__ import annotations

from dataclasses import dataclass


NODE_TYPES = {
    "MARKET",
    "INDICATOR",
    "PATTERN",
    "LEARNING",
    "DECISION",
    "RESULT",
    "DATA_SOURCE",
    "SYSTEM",
}

EDGE_TYPES = {
    "ANALYZED_BY",
    "USES_PUBLIC_FACTOR",
    "OBSERVED_PATTERN",
    "CREATED_LEARNING",
    "CREATED_DECISION",
    "HAS_RESULT",
    "CONNECTED_TO_SOURCE",
    "RELATED_MARKET",
    "UPDATED_BY",
}

PUBLIC_INDICATORS = {
    "ATR",
    "Gap",
    "EMA",
    "RSI",
    "MACD",
    "Relative Strength",
    "Volume",
    "Volatility",
    "Open Interest",
    "Funding Rate",
    "Trend Consensus",
}

NODE_COLORS = {
    "MARKET": "#39d5ff",
    "INDICATOR": "#4f8cff",
    "PATTERN": "#ffad42",
    "LEARNING": "#3ddc84",
    "DECISION": "#b58cff",
    "RESULT": "#f2f5f7",
    "DATA_SOURCE": "#ffd75e",
    "SYSTEM": "#b8c2cc",
}

ALLOWED_NODE_FIELDS = {
    "id",
    "label",
    "type",
    "status",
    "market",
    "timestamp",
    "data_quality",
    "similar_cases",
    "public_confidence",
    "public_result",
    "analysis_count",
    "last_seen",
    "activity_count",
}

ALLOWED_EDGE_FIELDS = {
    "id",
    "source",
    "target",
    "type",
    "label",
    "count",
    "last_seen",
    "status",
}

SECRET_FIELD_MARKERS = {
    "api_key",
    "calculation",
    "debug",
    "formula",
    "password",
    "path",
    "project_root",
    "raw",
    "raw_result",
    "reasoning",
    "secret",
    "token",
    "weight",
}


@dataclass(frozen=True)
class LearningGraphConfig:
    """Runtime limits for the public graph."""

    default_node_limit: int = 300
    max_node_limit: int = 1000
    default_edge_limit: int = 800
    max_edge_limit: int = 2500
    cache_ttl_seconds: float = 10.0
    recent_limit: int = 50
