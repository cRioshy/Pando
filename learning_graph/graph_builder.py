"""Build public Learning Graph nodes and edges from sanitized source concepts."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from learning_graph.graph_config import PUBLIC_INDICATORS
from learning_graph.graph_models import (
    GraphEdge,
    GraphNode,
    GraphStats,
    LearningGraph,
    stable_edge_id,
    stable_node_id,
)
from learning_graph.graph_sanitizer import GraphSanitizer


class GraphBuilder:
    """Create a public graph without exposing formulas or raw internals."""

    def __init__(self, sanitizer: GraphSanitizer | None = None) -> None:
        self.sanitizer = sanitizer or GraphSanitizer()

    def build(
        self,
        records: list[dict[str, Any]],
        *,
        node_limit: int = 300,
        edge_limit: int = 800,
        system_status: str = "OK",
    ) -> LearningGraph:
        """Build a sanitized graph from brain event records."""

        nodes: dict[str, GraphNode] = {}
        edges: dict[str, GraphEdge] = {}
        market_counts: Counter[str] = Counter()
        latest_timestamp: str | None = None

        for record in records:
            symbol = str(record.get("symbol") or "").strip()
            if not symbol:
                continue
            market_type = str(record.get("market_type") or "market").lower()
            direction = str(record.get("direction") or "WAIT").upper()
            timestamp = str(record.get("received_at") or record.get("source_timestamp") or "")
            latest_timestamp = max(filter(None, [latest_timestamp, timestamp]), default=None)
            market_counts[symbol] += 1

            market_node = GraphNode(
                id=stable_node_id("MARKET", symbol),
                label=symbol,
                type="MARKET",
                status="ACTIVE",
                market=market_type,
                timestamp=timestamp or None,
                data_quality=self._quality(record),
                analysis_count=market_counts[symbol],
                last_seen=timestamp or None,
                activity_count=market_counts[symbol],
            )
            self._merge_node(nodes, market_node)

            source_label = "Crypto Market Data" if market_type == "crypto" else "Stock Market Data"
            self._add_node(nodes, "DATA_SOURCE", source_label, market=market_type, timestamp=timestamp)
            self._add_edge(edges, stable_node_id("DATA_SOURCE", source_label), "CONNECTED_TO_SOURCE", market_node.id, timestamp)

            engine_label = "Crypto Engine" if market_type == "crypto" else "Stock Engine"
            self._add_node(nodes, "SYSTEM", engine_label, market=market_type, timestamp=timestamp)
            self._add_edge(edges, market_node.id, "ANALYZED_BY", stable_node_id("SYSTEM", engine_label), timestamp)

            for indicator in self._public_indicators(record):
                self._add_node(nodes, "INDICATOR", indicator, market=market_type, timestamp=timestamp)
                self._add_edge(edges, market_node.id, "USES_PUBLIC_FACTOR", stable_node_id("INDICATOR", indicator), timestamp)

            pattern_label = self._pattern_label(record)
            self._add_node(nodes, "PATTERN", pattern_label, market=symbol, timestamp=timestamp)
            self._add_edge(edges, market_node.id, "OBSERVED_PATTERN", stable_node_id("PATTERN", pattern_label), timestamp)

            learning_label = "Confidence Update"
            self._add_node(nodes, "LEARNING", learning_label, market=symbol, timestamp=timestamp)
            self._add_edge(edges, stable_node_id("PATTERN", pattern_label), "CREATED_LEARNING", stable_node_id("LEARNING", learning_label), timestamp)

            self._add_node(
                nodes,
                "DECISION",
                direction,
                market=symbol,
                timestamp=timestamp,
                public_confidence=self._public_confidence(record.get("probability")),
            )
            self._add_edge(edges, stable_node_id("LEARNING", learning_label), "CREATED_DECISION", stable_node_id("DECISION", direction), timestamp)

            result_label = self._public_result(record)
            self._add_node(nodes, "RESULT", result_label, market=symbol, timestamp=timestamp, public_result=result_label)
            self._add_edge(edges, stable_node_id("DECISION", direction), "HAS_RESULT", stable_node_id("RESULT", result_label), timestamp)

        node_dicts = [node.to_dict() for node in nodes.values()]
        edge_dicts = [edge.to_dict() for edge in edges.values()]
        node_dicts = node_dicts[-max(0, node_limit):]
        allowed_node_ids = {node["id"] for node in node_dicts}
        edge_dicts = [
            edge for edge in edge_dicts if edge.get("source") in allowed_node_ids and edge.get("target") in allowed_node_ids
        ][-max(0, edge_limit):]

        stats = GraphStats(
            visible_nodes=len(node_dicts),
            visible_edges=len(edge_dicts),
            analyses_processed=len(records),
            patterns_recognized=sum(1 for node in node_dicts if node.get("type") == "PATTERN"),
            new_learnings_today=self._count_today(records),
            active_markets=sum(1 for node in node_dicts if node.get("type") == "MARKET"),
            last_update=latest_timestamp,
            system_status=system_status,
        )
        sanitized = self.sanitizer.sanitize_graph(
            {"nodes": node_dicts, "edges": edge_dicts, "stats": stats.to_dict()}
        )
        return LearningGraph(**sanitized)

    def _merge_node(self, nodes: dict[str, GraphNode], node: GraphNode) -> None:
        """Merge node activity without exposing internal weights."""

        existing = nodes.get(node.id)
        if existing is None:
            nodes[node.id] = node
            return
        nodes[node.id] = replace(
            existing,
            activity_count=max(existing.activity_count, node.activity_count),
            analysis_count=node.analysis_count or existing.analysis_count,
            last_seen=node.last_seen or existing.last_seen,
            timestamp=node.timestamp or existing.timestamp,
        )

    def _add_node(
        self,
        nodes: dict[str, GraphNode],
        node_type: str,
        label: str,
        *,
        market: str | None = None,
        timestamp: str | None = None,
        public_confidence: str | None = None,
        public_result: str | None = None,
    ) -> None:
        """Add or update one node."""

        node = GraphNode(
            id=stable_node_id(node_type, label),
            label=label,
            type=node_type,
            market=market,
            timestamp=timestamp,
            last_seen=timestamp,
            public_confidence=public_confidence,
            public_result=public_result,
        )
        self._merge_node(nodes, node)

    def _add_edge(
        self,
        edges: dict[str, GraphEdge],
        source: str,
        edge_type: str,
        target: str,
        timestamp: str | None,
    ) -> None:
        """Add a deduplicated edge and increment public count."""

        edge_id = stable_edge_id(source, edge_type, target)
        existing = edges.get(edge_id)
        if existing is None:
            edges[edge_id] = GraphEdge(
                id=edge_id,
                source=source,
                target=target,
                type=edge_type,
                label=edge_type.replace("_", " ").title(),
                last_seen=timestamp,
            )
            return
        edges[edge_id] = replace(existing, count=existing.count + 1, last_seen=timestamp or existing.last_seen)

    def _public_indicators(self, record: dict[str, Any]) -> list[str]:
        """Map raw indicator keys into public indicator categories."""

        payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
        indicators = payload.get("indicators") if isinstance(payload.get("indicators"), dict) else {}
        keys = {str(key).lower() for key in indicators.keys()}
        result: list[str] = []
        if {"ema20", "ema50", "ema200", "sma_20", "sma_50"} & keys:
            result.append("EMA")
        if "rsi" in keys:
            result.append("RSI")
        if {"macd", "macd_signal"} & keys:
            result.append("MACD")
        if {"atr", "average_true_range"} & keys:
            result.append("ATR")
        if {"gap_percent", "gap_up", "gap_down"} & keys:
            result.append("Gap")
        if {"relative_strength", "rs_rating"} & keys:
            result.append("Relative Strength")
        if {"volatility", "atr_percent"} & keys:
            result.append("Volatility")
        if {"volume", "average_volume", "volume_average_20"} & keys:
            result.append("Volume")
        if "open_interest" in keys:
            result.append("Open Interest")
        if "funding_rate" in keys:
            result.append("Funding Rate")
        if not result:
            result.append("Trend Consensus")
        return [item for item in result if item in PUBLIC_INDICATORS]

    def _pattern_label(self, record: dict[str, Any]) -> str:
        """Create a public pattern bucket without exposing formula details."""

        symbol = str(record.get("symbol") or "market")
        direction = str(record.get("direction") or "WAIT").upper()
        return f"{symbol} {direction} Setup Cluster"

    def _public_result(self, record: dict[str, Any]) -> str:
        """Return a safe public result label."""

        payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
        raw_result = payload.get("raw_result") if isinstance(payload.get("raw_result"), dict) else {}
        result = payload.get("public_result") or raw_result.get("result")
        allowed = {"TP3_WIN", "TP2_THEN_STOP", "TP1_THEN_STOP", "DIRECT_STOP", "OPEN", "CLOSED"}
        return str(result) if result in allowed else "OPEN"

    def _quality(self, record: dict[str, Any]) -> str:
        """Return public data quality class."""

        payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
        indicators = payload.get("indicators") if isinstance(payload.get("indicators"), dict) else {}
        if len(indicators) >= 5:
            return "HIGH"
        if len(indicators) >= 2:
            return "MEDIUM"
        return "LOW"

    def _public_confidence(self, probability: Any) -> str:
        """Bucket confidence without exposing scores as logic."""

        try:
            value = float(probability)
        except (TypeError, ValueError):
            return "UNKNOWN"
        if value >= 70:
            return "HIGH"
        if value >= 55:
            return "MEDIUM"
        return "LOW"

    def _count_today(self, records: list[dict[str, Any]]) -> int:
        """Count records with today's UTC date for a public activity metric."""

        today = datetime.now(UTC).date()
        count = 0
        for record in records:
            timestamp = str(record.get("received_at") or record.get("source_timestamp") or "")
            try:
                if datetime.fromisoformat(timestamp.replace("Z", "+00:00")).date() == today:
                    count += 1
            except ValueError:
                continue
        return count
