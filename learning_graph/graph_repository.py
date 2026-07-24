"""Read-only repository for Learning Graph source data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from brain_event_store import BrainEventReader


class GraphRepository:
    """Read existing Pandorick data without exposing raw files to the browser."""

    def __init__(
        self,
        *,
        brain_events_file: Path,
        max_records: int = 500,
        max_jsonl_tail_bytes: int = 12_000_000,
        brain_events_dir: Path | None = None,
        project_root: Path | None = None,
        shared_state_file: Path | None = None,
        stock_project_path: Path | None = None,
        crypto_project_path: Path | None = None,
    ) -> None:
        self.brain_events_file = brain_events_file
        self.brain_events_dir = brain_events_dir or brain_events_file.parent / "brain_events"
        self.max_records = max(0, max_records)
        self.max_jsonl_tail_bytes = max(1024, int(max_jsonl_tail_bytes))
        self.project_root = project_root or brain_events_file.parent.parent
        self.shared_state_file = shared_state_file or brain_events_file.parent / "shared_state.json"
        self.stock_project_path = stock_project_path
        self.crypto_project_path = crypto_project_path

    def source_records(self, *, limit: int | None = None) -> list[dict[str, Any]]:
        """Return normalized real Pandorick records from all safe local sources."""

        effective_limit = self.max_records if limit is None else max(0, min(limit, self.max_records))
        if effective_limit == 0:
            return []
        records: list[dict[str, Any]] = []
        records.extend(self.recent_brain_events(limit=effective_limit))
        records.extend(self._stock_history_records(limit=effective_limit))
        records.extend(self._stock_decision_records(limit=effective_limit))
        records.extend(self._crypto_trade_records(limit=effective_limit))
        return self._dedupe(records)[-effective_limit:]

    def recent_brain_events(self, *, limit: int | None = None) -> list[dict[str, Any]]:
        """Read recent parseable brain events through the compatibility reader."""

        effective_limit = self.max_records if limit is None else max(0, min(limit, self.max_records))
        if effective_limit == 0:
            return []
        reader = BrainEventReader(
            legacy_file=self.brain_events_file,
            rotated_root=self.brain_events_dir,
            max_tail_bytes=self.max_jsonl_tail_bytes,
        )
        return reader.recent(limit=effective_limit)

    def _recent_jsonl_lines(self, path: Path, limit: int) -> list[str]:
        """Read recent JSONL lines without scanning very large history files."""

        try:
            size = path.stat().st_size
            start = max(0, size - self.max_jsonl_tail_bytes)
            with path.open("rb") as handle:
                handle.seek(start)
                data = handle.read(self.max_jsonl_tail_bytes)
        except OSError:
            return []
        lines = data.decode("utf-8", errors="replace").splitlines()
        if start > 0 and lines:
            lines = lines[1:]
        return lines[-limit:]

    def _stock_history_records(self, *, limit: int) -> list[dict[str, Any]]:
        """Read normalized stock history records from the separated stock bot."""

        path = self._stock_data_file("stock_history.json")
        data = self._read_json(path)
        if not isinstance(data, list):
            return []
        records: list[dict[str, Any]] = []
        for item in data[-limit:]:
            if not isinstance(item, dict):
                continue
            snapshot = item.get("snapshot") if isinstance(item.get("snapshot"), dict) else {}
            state = item.get("state") if isinstance(item.get("state"), dict) else {}
            symbol = snapshot.get("symbol") or state.get("symbol")
            if not symbol:
                continue
            timestamp = snapshot.get("timestamp") or item.get("timestamp")
            facts = state.get("facts") if isinstance(state.get("facts"), dict) else {}
            indicators = {**snapshot, **facts}
            records.append(
                {
                    "received_at": timestamp,
                    "source_event_id": f"stock-history:{symbol}:{timestamp}",
                    "event_type": "STOCK_HISTORY_UPDATED",
                    "source": "stock_history",
                    "market_type": "stock",
                    "symbol": symbol,
                    "direction": state.get("trend") or "WAIT",
                    "probability": None,
                    "source_timestamp": timestamp,
                    "payload": {
                        "indicators": self._public_indicator_values(indicators),
                        "public_result": state.get("trend") or "OPEN",
                    },
                }
            )
        return records

    def _stock_decision_records(self, *, limit: int) -> list[dict[str, Any]]:
        """Read normalized stock decisions from the separated stock bot."""

        path = self._stock_data_file("decisions.json")
        data = self._read_json(path)
        if not isinstance(data, list):
            return []
        records: list[dict[str, Any]] = []
        for item in data[-limit:]:
            if not isinstance(item, dict):
                continue
            symbol = item.get("symbol")
            if not symbol:
                continue
            timestamp = item.get("timestamp")
            state = item.get("state") if isinstance(item.get("state"), dict) else {}
            facts = state.get("facts") if isinstance(state.get("facts"), dict) else {}
            records.append(
                {
                    "received_at": timestamp,
                    "source_event_id": f"stock-decision:{symbol}:{timestamp}",
                    "event_type": "STOCK_DECISION_RECORDED",
                    "source": "stock_decisions",
                    "market_type": "stock",
                    "symbol": symbol,
                    "direction": item.get("action") or "WAIT",
                    "probability": item.get("final_probability"),
                    "source_timestamp": timestamp,
                    "payload": {
                        "indicators": self._public_indicator_values(facts),
                        "public_result": item.get("action") or "OPEN",
                    },
                }
            )
        return records

    def _crypto_trade_records(self, *, limit: int) -> list[dict[str, Any]]:
        """Read simulated crypto trade memory when it exists."""

        path = self.project_root / "data" / "crypto_active_trades.json"
        data = self._read_json(path)
        if isinstance(data, dict):
            items = list(data.values())
        elif isinstance(data, list):
            items = data
        else:
            return []
        records: list[dict[str, Any]] = []
        for item in items[-limit:]:
            if not isinstance(item, dict):
                continue
            symbol = item.get("symbol")
            if not symbol:
                continue
            timestamp = item.get("updated_at") or item.get("entry_time")
            records.append(
                {
                    "received_at": timestamp,
                    "source_event_id": item.get("signal_id") or f"crypto-trade:{symbol}:{timestamp}",
                    "event_type": "CRYPTO_TRADE_MEMORY_UPDATED",
                    "source": "crypto_trade_tracker",
                    "market_type": "crypto",
                    "symbol": symbol,
                    "direction": item.get("direction") or "WAIT",
                    "probability": None,
                    "source_timestamp": timestamp,
                    "payload": {
                        "indicators": self._public_indicator_values(
                            {
                                "current_price": item.get("current_price"),
                                "current_profit_percent": item.get("current_profit_percent"),
                                "max_profit_percent": item.get("max_profit_percent"),
                            }
                        ),
                        "public_result": item.get("trade_status") or "OPEN",
                    },
                }
            )
        return records

    def _stock_data_file(self, filename: str) -> Path:
        """Return one optional stock bot data file path."""

        if self.stock_project_path is None:
            return Path()
        return self.stock_project_path / "data" / filename

    def _read_json(self, path: Path) -> Any:
        """Read a JSON file safely."""

        if not path or not path.exists() or not path.is_file():
            return None
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError):
            return None

    def _public_indicator_values(self, values: dict[str, Any]) -> dict[str, Any]:
        """Keep only public market indicators needed for graph categories."""

        allowed = {
            "atr",
            "atr_percent",
            "average_volume",
            "close",
            "close_price",
            "current_price",
            "ema20",
            "ema50",
            "ema200",
            "funding_rate",
            "gap_percent",
            "macd",
            "macd_signal",
            "open_interest",
            "relative_strength",
            "rsi",
            "sma_20",
            "sma_50",
            "volume",
            "volume_average_20",
            "volatility",
        }
        return {key: value for key, value in values.items() if key in allowed}

    def _dedupe(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate source records without guessing hidden meaning."""

        seen: set[tuple[str, str, str, str]] = set()
        unique: list[dict[str, Any]] = []
        for record in records:
            key = (
                str(record.get("source_event_id") or record.get("source") or ""),
                str(record.get("event_type") or ""),
                str(record.get("symbol") or ""),
                str(record.get("source_timestamp") or record.get("received_at") or ""),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(record)
        return unique
