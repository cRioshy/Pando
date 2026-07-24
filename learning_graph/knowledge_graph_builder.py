"""Build the public interactive Pandorick Knowledge Graph."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from learning_graph.graph_config import PUBLIC_INDICATORS
from learning_graph.knowledge_graph_models import (
    KnowledgeEdge,
    KnowledgeGraph,
    KnowledgeNode,
    stable_knowledge_edge_id,
    stable_knowledge_node_id,
)


NODE_TYPES = {
    "brain",
    "project",
    "market",
    "crypto",
    "stock",
    "indicator",
    "decision",
    "signal",
    "learning",
    "pattern",
    "data_source",
    "bot",
    "service",
    "error",
    "warning",
    "memory",
}

RELATIONS = {
    "uses",
    "generated",
    "influenced",
    "learned_from",
    "belongs_to",
    "depends_on",
    "received_from",
    "confirmed_by",
    "contradicted_by",
    "caused",
    "repaired_by",
}


class KnowledgeGraphBuilder:
    """Create a browser-safe graph without touching trading logic."""

    def build(
        self,
        records: list[dict[str, Any]],
        *,
        node_limit: int = 300,
        edge_limit: int = 800,
    ) -> KnowledgeGraph:
        """Build a public graph from normalized Pandorick records."""

        if not records:
            return KnowledgeGraph.empty()

        nodes: dict[str, KnowledgeNode] = {}
        edges: dict[str, KnowledgeEdge] = {}
        symbol_counts: Counter[str] = Counter()
        latest_timestamp: str | None = None

        project_id = self._add_node(
            nodes,
            "project",
            "PandorickKi",
            "system",
            importance=94,
            metadata={"role": "platform"},
            details_url="/api/status",
        )
        brain_id = self._add_node(
            nodes,
            "brain",
            "Pandorick Brain",
            "brain",
            importance=100,
            metadata={"role": "learning_core"},
            details_url="/api/brain",
        )
        self._add_edge(edges, project_id, "depends_on", brain_id, weight=3.0)

        for record in records:
            symbol = str(record.get("symbol") or "").strip()
            if not symbol:
                continue
            market_type = self._market_type(record)
            group = "crypto" if market_type == "crypto" else "stocks"
            timestamp = str(record.get("received_at") or record.get("source_timestamp") or "")
            latest_timestamp = max(filter(None, [latest_timestamp, timestamp]), default=None)
            symbol_counts[symbol] += 1

            market_label = "Crypto Markets" if market_type == "crypto" else "Stock Markets"
            market_id = self._add_node(
                nodes,
                "market",
                market_label,
                group,
                importance=78,
                count=symbol_counts[symbol],
                last_updated=timestamp,
                metadata={"market_type": market_type},
            )
            symbol_id = self._add_node(
                nodes,
                "crypto" if market_type == "crypto" else "stock",
                symbol,
                group,
                importance=82,
                confidence=self._confidence(record.get("probability")),
                count=symbol_counts[symbol],
                last_updated=timestamp,
                health=self._health(record),
                metadata={
                    "symbol": symbol,
                    "market_type": market_type,
                    "event_type": self._safe_text(record.get("event_type")),
                },
                details_url="/api/crypto" if market_type == "crypto" else "/api/stocks",
            )
            self._add_edge(edges, symbol_id, "belongs_to", market_id, weight=2.2, last_updated=timestamp)

            source_id = self._add_node(
                nodes,
                "data_source",
                "Crypto Market Data" if market_type == "crypto" else "Stock Market Data",
                "infrastructure",
                importance=66,
                last_updated=timestamp,
                metadata={"market_type": market_type},
            )
            bot_id = self._add_node(
                nodes,
                "bot",
                "Crypto Engine" if market_type == "crypto" else "Stock Engine",
                "infrastructure",
                importance=76,
                last_updated=timestamp,
                metadata={"market_type": market_type},
            )
            self._add_edge(edges, project_id, "uses", bot_id, weight=1.6, last_updated=timestamp)
            self._add_edge(edges, bot_id, "received_from", source_id, weight=1.5, last_updated=timestamp)
            self._add_edge(edges, bot_id, "generated", symbol_id, weight=1.8, last_updated=timestamp)

            for indicator in self._public_indicators(record):
                indicator_id = self._add_node(
                    nodes,
                    "indicator",
                    indicator,
                    "indicators",
                    importance=58,
                    last_updated=timestamp,
                    metadata={"category": indicator},
                )
                self._add_edge(edges, symbol_id, "uses", indicator_id, weight=1.1, last_updated=timestamp)

            pattern_id = self._add_node(
                nodes,
                "pattern",
                self._pattern_label(record),
                "patterns",
                importance=62,
                confidence=self._confidence(record.get("probability")),
                last_updated=timestamp,
                metadata={"symbol": symbol, "direction": self._direction(record)},
            )
            self._add_edge(edges, pattern_id, "learned_from", symbol_id, weight=1.7, last_updated=timestamp)
            self._add_edge(edges, brain_id, "learned_from", pattern_id, weight=1.5, last_updated=timestamp)

            decision_id = self._add_node(
                nodes,
                "decision",
                self._direction(record),
                "decisions",
                importance=60,
                confidence=self._confidence(record.get("probability")),
                last_updated=timestamp,
                metadata={"direction": self._direction(record)},
                details_url="/api/signals",
            )
            self._add_edge(edges, brain_id, "generated", decision_id, weight=1.8, last_updated=timestamp)
            self._add_edge(edges, decision_id, "influenced", symbol_id, weight=1.4, last_updated=timestamp)

            if "SIGNAL" in str(record.get("event_type") or "").upper():
                signal_id = self._add_node(
                    nodes,
                    "signal",
                    f"{symbol} {self._direction(record)}",
                    "decisions",
                    importance=70,
                    confidence=self._confidence(record.get("probability")),
                    last_updated=timestamp,
                    metadata={"symbol": symbol, "direction": self._direction(record)},
                    details_url="/api/signals",
                )
                self._add_edge(edges, decision_id, "generated", signal_id, weight=2.1, last_updated=timestamp)

            if self._is_warning(record):
                warning_id = self._add_node(
                    nodes,
                    "warning",
                    "Data Warning",
                    "warnings",
                    importance=48,
                    status="WARNING",
                    health="WARN",
                    last_updated=timestamp,
                    metadata={"symbol": symbol},
                )
                self._add_edge(edges, warning_id, "caused", symbol_id, weight=1.0, last_updated=timestamp)

            if self._is_error(record):
                error_id = self._add_node(
                    nodes,
                    "error",
                    "Service Error",
                    "errors",
                    importance=64,
                    status="ERROR",
                    health="ERROR",
                    last_updated=timestamp,
                    metadata={"source": self._safe_text(record.get("source"))},
                )
                self._add_edge(edges, error_id, "caused", bot_id, weight=1.8, last_updated=timestamp)

        ranked_nodes = self._rank_nodes(nodes, edges)
        node_dicts = [node.to_dict() for node in ranked_nodes[: max(0, node_limit)]]
        allowed = {node["id"] for node in node_dicts}
        ranked_edges = sorted(edges.values(), key=lambda edge: (edge.event_count, edge.weight), reverse=True)
        edge_dicts = [
            edge.to_dict()
            for edge in ranked_edges
            if edge.source in allowed and edge.target in allowed
        ][: max(0, edge_limit)]
        return KnowledgeGraph(
            generated_at=datetime.now(UTC).isoformat(),
            node_count=len(node_dicts),
            edge_count=len(edge_dicts),
            nodes=node_dicts,
            edges=edge_dicts,
        )

    def _add_node(
        self,
        nodes: dict[str, KnowledgeNode],
        node_type: str,
        label: str,
        group: str,
        *,
        importance: float,
        confidence: float | None = None,
        count: int = 1,
        status: str = "ACTIVE",
        last_updated: str | None = None,
        health: str = "OK",
        metadata: dict[str, Any] | None = None,
        details_url: str | None = None,
    ) -> str:
        """Add or merge one node."""

        clean_type = node_type if node_type in NODE_TYPES else "service"
        node_id = stable_knowledge_node_id(clean_type, group, label)
        safe_metadata = self._safe_metadata(metadata or {})
        node = KnowledgeNode(
            id=node_id,
            label=str(label),
            type=clean_type,
            group=str(group),
            importance=round(float(importance), 2),
            confidence=confidence,
            count=max(1, int(count)),
            status=status,
            last_updated=last_updated or None,
            health=health,
            metadata=safe_metadata,
            details_url=details_url,
        )
        existing = nodes.get(node_id)
        if existing is None:
            nodes[node_id] = node
        else:
            nodes[node_id] = replace(
                existing,
                importance=max(existing.importance, node.importance),
                confidence=node.confidence if node.confidence is not None else existing.confidence,
                count=existing.count + node.count,
                status=node.status if node.status != "ACTIVE" else existing.status,
                last_updated=node.last_updated or existing.last_updated,
                health=node.health if node.health != "OK" else existing.health,
                metadata={**existing.metadata, **node.metadata},
                details_url=node.details_url or existing.details_url,
            )
        return node_id

    def _add_edge(
        self,
        edges: dict[str, KnowledgeEdge],
        source: str,
        relation: str,
        target: str,
        *,
        weight: float,
        confidence: float | None = None,
        last_updated: str | None = None,
        direction: str = "directed",
    ) -> None:
        """Add or merge one edge."""

        clean_relation = relation if relation in RELATIONS else "influenced"
        edge_id = stable_knowledge_edge_id(source, clean_relation, target)
        edge = KnowledgeEdge(
            id=edge_id,
            source=source,
            target=target,
            relation=clean_relation,
            weight=round(float(weight), 3),
            confidence=confidence,
            event_count=1,
            last_updated=last_updated,
            direction=direction,
        )
        existing = edges.get(edge_id)
        if existing is None:
            edges[edge_id] = edge
        else:
            edges[edge_id] = replace(
                existing,
                weight=round(min(8.0, existing.weight + edge.weight * 0.08), 3),
                confidence=edge.confidence if edge.confidence is not None else existing.confidence,
                event_count=existing.event_count + 1,
                last_updated=edge.last_updated or existing.last_updated,
            )

    def _rank_nodes(
        self,
        nodes: dict[str, KnowledgeNode],
        edges: dict[str, KnowledgeEdge],
    ) -> list[KnowledgeNode]:
        """Rank important nodes for overview loading."""

        degree: Counter[str] = Counter()
        for edge in edges.values():
            degree[edge.source] += 1
            degree[edge.target] += 1

        ranked: list[KnowledgeNode] = []
        for node in nodes.values():
            score = node.importance + degree[node.id] * 4 + min(35, node.count ** 0.5)
            if node.confidence is not None:
                score += node.confidence * 0.08
            ranked.append(replace(node, importance=round(min(100.0, score), 2)))
        return sorted(ranked, key=lambda node: (node.importance, node.count, node.label), reverse=True)

    def _market_type(self, record: dict[str, Any]) -> str:
        """Return normalized market type."""

        raw = str(record.get("market_type") or "").lower()
        if raw == "crypto":
            return "crypto"
        return "stock"

    def _direction(self, record: dict[str, Any]) -> str:
        """Return normalized public decision direction."""

        direction = str(record.get("direction") or "WAIT").upper()
        if direction in {"LONG", "SHORT", "HOLD", "WAIT", "WATCHLIST"}:
            return direction
        if "UP" in direction:
            return "LONG"
        if "DOWN" in direction:
            return "SHORT"
        return "WAIT"

    def _pattern_label(self, record: dict[str, Any]) -> str:
        """Return a public setup bucket."""

        return f"{record.get('symbol') or 'Market'} {self._direction(record)} Setup"

    def _confidence(self, value: Any) -> float | None:
        """Parse a public confidence value."""

        try:
            return round(max(0.0, min(100.0, float(value))), 2)
        except (TypeError, ValueError):
            return None

    def _public_indicators(self, record: dict[str, Any]) -> list[str]:
        """Return public indicator categories used by one record."""

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

    def _health(self, record: dict[str, Any]) -> str:
        """Return public health class."""

        if self._is_error(record):
            return "ERROR"
        if self._is_warning(record):
            return "WARN"
        return "OK"

    def _is_error(self, record: dict[str, Any]) -> bool:
        """Return whether a record is a service error."""

        text = f"{record.get('event_type') or ''} {record.get('source') or ''}".upper()
        return "ERROR" in text or "EXCEPTION" in text

    def _is_warning(self, record: dict[str, Any]) -> bool:
        """Return whether a record is a data warning."""

        text = f"{record.get('event_type') or ''} {record.get('source') or ''}".upper()
        return "WARNING" in text or "NO_DATA" in text or "RETRY" in text

    def _safe_metadata(self, metadata: dict[str, Any]) -> dict[str, str | int | float | bool | None]:
        """Keep only non-secret primitive metadata."""

        clean: dict[str, str | int | float | bool | None] = {}
        for key, value in metadata.items():
            key_text = str(key).lower()
            if any(marker in key_text for marker in ("token", "secret", "password", "api_key", "path", "raw")):
                continue
            if value is None or isinstance(value, (int, float, bool)):
                clean[str(key)] = value
                continue
            if isinstance(value, str) and not self._looks_secret(value):
                clean[str(key)] = value[:120]
        return clean

    def _safe_text(self, value: Any) -> str:
        """Return a short non-secret text value."""

        text = str(value or "")
        if self._looks_secret(text):
            return ""
        return text[:120]

    def _looks_secret(self, value: str) -> bool:
        """Detect secret-like browser output."""

        lower = value.lower()
        return any(marker in lower for marker in ("c:\\users\\", "/users/", "token=", "api_key", "secret", "password"))
