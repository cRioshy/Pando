"""Read-only learning performance report for PandorickKi."""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from threading import Lock, Thread
from typing import Any

from config import PlatformConfig
from jsonl_ledger import related_jsonl_files
from learning_metrics_contract import (
    LEARNING_METRICS_SCHEMA_NAME,
    LEARNING_METRICS_SCHEMA_VERSION,
    build_learning_metrics,
)


INSUFFICIENT_DATA = "Nicht genuegend Daten"
WINDOWS = (100, 500, 1000, 5000)
CONFIDENCE_BINS = (90, 80, 70, 60, 50)
INDICATORS = ("EMA", "RSI", "MACD", "ADX", "ATR", "Volume", "Open Interest", "Funding", "Momentum")
MAX_JSONL_REPORT_RECORDS = 6_000
MAX_BRAIN_REPORT_RECORDS = 20_000
REPORT_CACHE_TTL_SECONDS = 300.0
TAIL_READ_CHUNK_BYTES = 1024 * 1024


@dataclass(frozen=True)
class LearningReportPaths:
    """Concrete read-only data paths used by the learning report."""

    stock_decisions: Path
    stock_logs: Path
    brain_events_file: Path
    brain_events_dir: Path
    platform_decisions: Path | None = None
    trade_outcomes: Path | None = None
    cache_file: Path | None = None

    @classmethod
    def from_config(cls, config: PlatformConfig) -> "LearningReportPaths":
        """Build report paths from platform configuration."""

        stock_data = config.stock_project_path / "data_stock"
        return cls(
            stock_decisions=stock_data / "stock_decisions.json",
            stock_logs=stock_data / "stock_logs.json",
            brain_events_file=config.brain_events_file,
            brain_events_dir=config.brain_events_dir,
            platform_decisions=config.platform_decisions_file,
            trade_outcomes=config.trade_outcomes_file,
            cache_file=config.project_root / "storage" / "statistics" / "learning_report_cache.json",
        )


class LearningReportService:
    """Build objective learning-quality metrics from stored production data."""

    def __init__(self, paths: LearningReportPaths) -> None:
        self.paths = paths
        self._cache_lock = Lock()
        self._cached_report = self._load_cache()
        self._refresh_thread: Thread | None = None
        self._last_refresh_started = 0.0

    def report_cached(self) -> dict[str, Any]:
        """Return a cached report immediately and refresh stale data in the background."""

        with self._cache_lock:
            cached = dict(self._cached_report) if isinstance(self._cached_report, dict) else None
        if cached is None:
            self.refresh_cache(block=False)
            return self._pending_report("Learning-Report wird im Hintergrund aufgebaut.")
        age_seconds = self._cache_age_seconds(cached)
        stale = age_seconds is None or age_seconds > REPORT_CACHE_TTL_SECONDS
        if stale:
            self.refresh_cache(block=False)
        cached.setdefault("cache", {})
        cached["cache"].update(
            {
                "status": "stale_refreshing" if stale else "fresh",
                "ttl_seconds": REPORT_CACHE_TTL_SECONDS,
                "age_seconds": round(age_seconds, 2) if age_seconds is not None else None,
                "refresh_running": self._refresh_running(),
            }
        )
        return cached

    def refresh_cache(self, *, block: bool = False) -> None:
        """Refresh the report cache once, optionally blocking the caller."""

        if self._refresh_running():
            if block and self._refresh_thread is not None:
                self._refresh_thread.join(timeout=60.0)
            return
        now = time.monotonic()
        if not block and now - self._last_refresh_started < 5.0:
            return
        self._last_refresh_started = now
        if block:
            self._build_and_store_cache()
            return
        self._refresh_thread = Thread(
            target=self._build_and_store_cache,
            name="pandorickki-learning-report-cache",
            daemon=True,
        )
        self._refresh_thread.start()

    def _refresh_running(self) -> bool:
        return self._refresh_thread is not None and self._refresh_thread.is_alive()

    def _build_and_store_cache(self) -> None:
        try:
            report = self.report()
            report["cache"] = {
                "status": "fresh",
                "generated_at": datetime.now(UTC).isoformat(),
                "ttl_seconds": REPORT_CACHE_TTL_SECONDS,
                "max_jsonl_records": MAX_JSONL_REPORT_RECORDS,
                "max_brain_records": MAX_BRAIN_REPORT_RECORDS,
            }
            with self._cache_lock:
                self._cached_report = report
            self._write_cache(report)
        except Exception as exc:
            with self._cache_lock:
                cached = self._cached_report
                if isinstance(cached, dict):
                    cached.setdefault("cache", {})
                    cached["cache"].update(
                        {
                            "status": "refresh_failed",
                            "last_error": str(exc),
                            "failed_at": datetime.now(UTC).isoformat(),
                        }
                    )

    def _pending_report(self, message: str) -> dict[str, Any]:
        metrics = build_learning_metrics(
            decisions_total=0,
            outcome_eligible_decisions=0,
            matched_outcomes=0,
            wins=0,
            losses=0,
            matching_method="cache_pending",
            coverage_reliable=False,
        )
        evaluation_score = {"score": 0, "components": {}, "verdict": message}
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "data_sources": self._data_sources(),
            "summary": {
                "decisions": 0,
                "learning_events_with_outcome": 0,
                "outcome_source": "cache_pending",
                "crypto_decision_records": 0,
                "hit_rate": INSUFFICIENT_DATA,
                "average_confidence": INSUFFICIENT_DATA,
                "average_profit_simulation": INSUFFICIENT_DATA,
                "average_loss_simulation": INSUFFICIENT_DATA,
                "drawdown": INSUFFICIENT_DATA,
                "holding_duration": INSUFFICIENT_DATA,
                "learning_updates_per_decision": INSUFFICIENT_DATA,
                "outcome_eligible_decisions": 0,
                "matched_outcomes": 0,
                "outcome_coverage_percent": None,
                "hit_rate_numerator": 0,
                "hit_rate_denominator": 0,
            },
            "learning_metrics": metrics,
            "windows": [],
            "progress": {"verdict": message},
            "confidence_quality": [],
            "market_comparison": [],
            "symbol_comparison": [],
            "timeframes": [],
            "indicators": [],
            "learning_curve": [],
            "evaluation_score": evaluation_score,
            "learning_score": evaluation_score,
            "warnings": [message],
            "recommendations": ["Bitte kurz warten; die Live-Ansicht bleibt waehrenddessen bedienbar."],
            "cache": {
                "status": "building",
                "refresh_running": self._refresh_running(),
                "ttl_seconds": REPORT_CACHE_TTL_SECONDS,
            },
        }

    def _load_cache(self) -> dict[str, Any] | None:
        cache_file = self.paths.cache_file
        if cache_file is None or not cache_file.exists() or cache_file.stat().st_size == 0:
            return None
        try:
            with cache_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict):
            return None
        metrics = data.get("learning_metrics")
        if not isinstance(metrics, dict):
            return None
        if metrics.get("schema_name") != LEARNING_METRICS_SCHEMA_NAME:
            return None
        if metrics.get("schema_version") != LEARNING_METRICS_SCHEMA_VERSION:
            return None
        return data

    def _cache_age_seconds(self, report: dict[str, Any]) -> float | None:
        generated_at = report.get("cache", {}).get("generated_at") or report.get("generated_at")
        if not generated_at:
            return None
        try:
            created = datetime.fromisoformat(str(generated_at).replace("Z", "+00:00"))
        except ValueError:
            return None
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        return max(0.0, (datetime.now(UTC) - created.astimezone(UTC)).total_seconds())

    def _write_cache(self, report: dict[str, Any]) -> None:
        cache_file = self.paths.cache_file
        if cache_file is None:
            return
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        temp = cache_file.with_suffix(cache_file.suffix + ".tmp")
        with temp.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=True)
            handle.flush()
        temp.replace(cache_file)

    def report(self) -> dict[str, Any]:
        """Return a browser-safe report without mutating productive data."""

        platform_decisions = self._platform_decisions()
        simulated_outcomes = self._simulated_outcomes()
        if platform_decisions:
            stock_decisions: list[dict[str, Any]] = []
            stock_learning_events: list[dict[str, Any]] = []
            crypto_records: list[dict[str, Any]] = []
            all_decisions = platform_decisions
            outcome_events = simulated_outcomes
            outcome_source = "decision_id_trade_outcomes" if simulated_outcomes else "no_outcomes_found"
        else:
            stock_decisions = self._load_json_list(self.paths.stock_decisions)
            stock_learning_events = self._stock_learning_events()
            crypto_records = list(self._iter_brain_events())
            all_decisions = self._combined_decisions(stock_decisions, crypto_records)
            outcome_events = stock_learning_events
            outcome_source = "stock_learning_logs"

        learning_metrics, matched_outcomes = self._learning_metrics(
            all_decisions,
            outcome_events,
            outcome_source,
        )
        scoped_outcomes = matched_outcomes
        evaluation_score = self._learning_score(all_decisions, scoped_outcomes)
        metric_notes = [
            "AI_LEARNING_UPDATED bezeichnet eine Beobachtungsprojektion; ein ML-Modelltraining ist nicht implementiert.",
            "Hit-Rate verwendet ausschließlich Wins und Losses; Breakeven und unbekannte Outcomes stehen separat.",
        ]
        coverage = learning_metrics["rates"]["outcome_coverage_percent"]
        if coverage is not None:
            metric_notes.append(
                "Outcome-Abdeckung: "
                f"{learning_metrics['rates']['outcome_coverage_numerator']}/"
                f"{learning_metrics['rates']['outcome_coverage_denominator']} "
                f"outcome-faehige Decisions ({coverage:.2f} %)."
            )
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "data_sources": self._data_sources(),
            "summary": self._summary(
                all_decisions,
                matched_outcomes,
                crypto_records,
                outcome_source,
                learning_metrics,
            ),
            "learning_metrics": learning_metrics,
            "metric_notes": metric_notes,
            "windows": self._windows(all_decisions, scoped_outcomes),
            "progress": self._progress(all_decisions, scoped_outcomes),
            "confidence_quality": self._confidence_quality(all_decisions, scoped_outcomes),
            "market_comparison": self._market_comparison(all_decisions, scoped_outcomes, crypto_records, outcome_source),
            "symbol_comparison": self._symbol_comparison(all_decisions, scoped_outcomes),
            "timeframes": self._timeframes(all_decisions),
            "indicators": self._indicator_report(stock_decisions, crypto_records, scoped_outcomes),
            "learning_curve": self._learning_curve(all_decisions, scoped_outcomes),
            "evaluation_score": evaluation_score,
            "learning_score": evaluation_score,
            "warnings": self._warnings(all_decisions, scoped_outcomes, crypto_records, outcome_source),
            "recommendations": self._recommendations(all_decisions, scoped_outcomes, crypto_records, outcome_source),
        }

    def _data_sources(self) -> dict[str, str]:
        """Return relative-ish path names only, never full user paths."""

        return {
            "stock_decisions": self.paths.stock_decisions.name,
            "stock_logs": self.paths.stock_logs.name,
            "brain_events_file": self.paths.brain_events_file.name,
            "brain_events_dir": self.paths.brain_events_dir.name,
            "platform_decisions": self.paths.platform_decisions.name if self.paths.platform_decisions else "-",
            "trade_outcomes": self.paths.trade_outcomes.name if self.paths.trade_outcomes else "-",
        }

    def _load_json_list(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists() or path.stat().st_size == 0:
            return []
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]

    def _load_jsonl_records(self, path: Path | None, *, max_records: int = MAX_JSONL_REPORT_RECORDS) -> list[dict[str, Any]]:
        """Load JSONL records safely without mutating production data."""

        if path is None:
            return []
        parts: list[list[dict[str, Any]]] = []
        remaining = max_records
        for ledger in reversed(related_jsonl_files(path)):
            if remaining <= 0:
                break
            if not ledger.exists() or ledger.stat().st_size == 0:
                continue
            records = self._tail_jsonl_records(ledger, remaining)
            if records:
                parts.append(records)
                remaining -= len(records)
        return [record for part in reversed(parts) for record in part]

    def _tail_jsonl_records(self, path: Path, max_records: int) -> list[dict[str, Any]]:
        """Read recent JSONL records from the end of a file without scanning the whole file."""

        if max_records <= 0:
            return []
        try:
            with path.open("rb") as handle:
                handle.seek(0, 2)
                position = handle.tell()
                buffer = b""
                while position > 0 and buffer.count(b"\n") <= max_records:
                    read_size = min(TAIL_READ_CHUNK_BYTES, position)
                    position -= read_size
                    handle.seek(position)
                    buffer = handle.read(read_size) + buffer
        except OSError:
            return []
        lines = buffer.splitlines()[-max_records:]
        records: list[dict[str, Any]] = []
        for raw in lines:
            if not raw.strip():
                continue
            try:
                record = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(record, dict):
                records.append(record)
        return records

    def _platform_decisions(self) -> list[dict[str, Any]]:
        """Return normalized final platform decisions with stable decision_id."""

        decisions: list[dict[str, Any]] = []
        for record in self._load_jsonl_records(self.paths.platform_decisions):
            payload = record.get("payload", {})
            if not isinstance(payload, dict):
                continue
            decisions.append(
                {
                    "decision_id": payload.get("decision_id"),
                    "market_type": str(payload.get("market_type") or "-").lower(),
                    "symbol": str(payload.get("symbol") or "-").upper(),
                    "direction": str(payload.get("direction") or "").upper(),
                    "confidence": self._num(payload.get("confidence", payload.get("probability"))),
                    "timestamp": payload.get("created_at") or record.get("created_at"),
                    "timeframe": payload.get("timeframe") or "final",
                    "labels": self._labels(payload) + self._crypto_labels(payload),
                    "raw": payload,
                }
            )
        decisions.sort(key=lambda row: str(row.get("timestamp") or ""))
        return decisions

    def _simulated_outcomes(self) -> list[dict[str, Any]]:
        """Return only closed simulated outcomes linked to final decisions."""

        outcomes: list[dict[str, Any]] = []
        seen: set[str] = set()
        for record in self._load_jsonl_records(self.paths.trade_outcomes):
            if str(record.get("record_type") or "").upper() != "SIMULATED_TRADE_CLOSED":
                continue
            payload = record.get("payload", {})
            if not isinstance(payload, dict):
                continue
            decision_id = str(payload.get("decision_id") or "")
            if not decision_id or decision_id in seen:
                continue
            seen.add(decision_id)
            result_type = str(payload.get("result_type") or "").lower()
            outcomes.append(
                {
                    "decision_id": decision_id,
                    "symbol": str(payload.get("symbol") or "-").upper(),
                    "market_type": str(payload.get("market_type") or "-").lower(),
                    "outcome": result_type,
                    "price_change_percent": self._num(
                        payload.get("gross_profit_percent", payload.get("current_profit_percent"))
                    ),
                    "holding_seconds": self._num(payload.get("holding_seconds")),
                    "max_drawdown_percent": self._num(payload.get("max_drawdown_percent")),
                    "timestamp": payload.get("exit_time") or record.get("timestamp"),
                    "raw": payload,
                }
            )
        outcomes.sort(key=lambda row: str(row.get("timestamp") or ""))
        return outcomes

    def _stock_learning_events(self) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for log in self._load_json_list(self.paths.stock_logs):
            timestamp = log.get("timestamp")
            for event in log.get("learning_events", []) or []:
                if isinstance(event, dict):
                    row = dict(event)
                    row.setdefault("timestamp", timestamp)
                    row.setdefault("market_type", "stock")
                    events.append(row)
        return events

    def _iter_brain_events(self) -> list[dict[str, Any]]:
        files: list[Path] = []
        if self.paths.brain_events_file.exists():
            files.append(self.paths.brain_events_file)
        if self.paths.brain_events_dir.exists():
            files.extend(sorted(self.paths.brain_events_dir.glob("**/*.jsonl")))
        records: deque[dict[str, Any]] = deque(maxlen=MAX_BRAIN_REPORT_RECORDS)
        for path in files:
            try:
                with path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(record, dict):
                            records.append(record)
            except OSError:
                continue
        return records

    def _combined_decisions(
        self,
        stock_decisions: list[dict[str, Any]],
        crypto_records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        combined: list[dict[str, Any]] = []
        for item in stock_decisions:
            combined.append(
                {
                    "market_type": "stock",
                    "symbol": str(item.get("symbol") or "-").upper(),
                    "direction": str(item.get("action") or item.get("direction") or "").upper(),
                    "confidence": self._num(item.get("final_probability")),
                    "timestamp": item.get("timestamp"),
                    "timeframe": item.get("timeframe") or "1D",
                    "labels": self._labels(item),
                    "raw": item,
                }
            )
        for record in crypto_records:
            payload = record.get("payload", {})
            if not isinstance(payload, dict):
                payload = {}
            combined.append(
                {
                    "market_type": str(record.get("market_type") or payload.get("market_type") or "crypto").lower(),
                    "symbol": str(record.get("symbol") or payload.get("symbol") or "-").upper(),
                    "direction": str(record.get("direction") or payload.get("direction") or "").upper(),
                    "confidence": self._num(record.get("probability", payload.get("probability"))),
                    "timestamp": record.get("source_timestamp") or record.get("received_at"),
                    "timeframe": payload.get("timeframe") or "15m",
                    "labels": self._crypto_labels(payload),
                    "raw": record,
                }
            )
        combined.sort(key=lambda row: str(row.get("timestamp") or ""))
        return combined

    def _summary(
        self,
        decisions: list[dict[str, Any]],
        matched_outcomes: list[dict[str, Any]],
        crypto_records: list[dict[str, Any]],
        outcome_source: str,
        learning_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        rates = learning_metrics["rates"]
        metric_decisions = learning_metrics["decisions"]
        outcomes = learning_metrics["outcomes"]
        return {
            "decisions": len(decisions),
            "learning_events_with_outcome": len(matched_outcomes),
            "matched_outcomes": outcomes["matched"],
            "outcome_eligible_decisions": metric_decisions["outcome_eligible"],
            "outcome_coverage_percent": rates["outcome_coverage_percent"],
            "outcome_source": outcome_source,
            "crypto_decision_records": len(crypto_records),
            "hit_rate": rates["hit_rate_percent"] if rates["hit_rate_percent"] is not None else INSUFFICIENT_DATA,
            "hit_rate_numerator": rates["hit_rate_numerator"],
            "hit_rate_denominator": rates["hit_rate_denominator"],
            "average_confidence": self._avg([d.get("confidence") for d in decisions]),
            "average_profit_simulation": self._avg([e.get("price_change_percent") for e in matched_outcomes]),
            "average_loss_simulation": self._avg(
                [e.get("price_change_percent") for e in matched_outcomes if str(e.get("outcome")).lower() == "loss"]
            ),
            "drawdown": INSUFFICIENT_DATA,
            "holding_duration": INSUFFICIENT_DATA,
            "learning_updates_per_decision": INSUFFICIENT_DATA,
        }

    def _learning_metrics(
        self,
        decisions: list[dict[str, Any]],
        outcome_events: list[dict[str, Any]],
        outcome_source: str,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Build metrics from outcomes actually matched to this decision scope."""

        pairs = self._paired_decision_outcomes(decisions, outcome_events)
        matched_outcomes = [event for _, event in pairs]
        stats = self._outcome_stats(matched_outcomes)
        eligible = sum(
            1
            for decision in decisions
            if str(decision.get("direction") or "").upper() in {"LONG", "BUY", "SHORT", "SELL"}
        )
        exact = outcome_source == "decision_id_trade_outcomes"
        metrics = build_learning_metrics(
            decisions_total=len(decisions),
            outcome_eligible_decisions=eligible,
            matched_outcomes=len(matched_outcomes),
            wins=stats["wins"],
            losses=stats["losses"],
            breakeven=stats["breakeven"],
            unknown=stats["unknown"],
            matching_method="decision_id" if exact else "legacy_order_fallback",
            coverage_reliable=exact,
        )
        return metrics, matched_outcomes

    def _windows(self, decisions: list[dict[str, Any]], learning_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        for size in WINDOWS:
            rows.append(self._window_row(f"Letzte {size}", decisions[-size:], learning_events[-size:]))
        rows.append(self._window_row("Gesamte Historie", decisions, learning_events))
        return rows

    def _window_row(
        self,
        label: str,
        decisions: list[dict[str, Any]],
        learning_events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        directions = Counter(str(d.get("direction") or "").upper() for d in decisions)
        outcomes = self._outcome_stats(learning_events)
        losses = [self._num(e.get("price_change_percent")) for e in learning_events if str(e.get("outcome")).lower() == "loss"]
        losses = [value for value in losses if value is not None]
        return {
            "label": label,
            "decisions": len(decisions),
            "long": directions["LONG"] + directions["BUY"],
            "short": directions["SHORT"] + directions["SELL"],
            "hold": directions["HOLD"] + directions["WAIT"],
            "watchlist": directions["WATCHLIST"],
            "hit_rate": outcomes["hit_rate"],
            "average_confidence": self._avg([d.get("confidence") for d in decisions]),
            "average_profit_simulation": self._avg([e.get("price_change_percent") for e in learning_events]),
            "average_loss": self._avg(losses),
            "average_drawdown": INSUFFICIENT_DATA,
            "average_holding_duration": INSUFFICIENT_DATA,
            "learning_updates_per_decision": round(len(learning_events) / len(decisions), 4) if decisions else INSUFFICIENT_DATA,
        }

    def _progress(self, decisions: list[dict[str, Any]], learning_events: list[dict[str, Any]]) -> dict[str, Any]:
        first_decisions = decisions[:1000]
        last_decisions = decisions[-1000:]
        first_events = learning_events[:1000]
        last_events = learning_events[-1000:]
        first = self._window_row("Erste 1000", first_decisions, first_events)
        last = self._window_row("Letzte 1000", last_decisions, last_events)
        return {
            "first_1000": first,
            "last_1000": last,
            "hit_rate_delta": self._delta(last["hit_rate"], first["hit_rate"]),
            "confidence_delta": self._delta(last["average_confidence"], first["average_confidence"]),
            "profit_delta": self._delta(last["average_profit_simulation"], first["average_profit_simulation"]),
            "verdict": self._progress_verdict(first, last),
        }

    def _confidence_quality(
        self,
        decisions: list[dict[str, Any]],
        learning_events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        rows = []
        paired = self._paired_decision_outcomes(decisions, learning_events)
        for threshold in CONFIDENCE_BINS:
            events = [event for decision, event in paired if self._num(decision.get("confidence")) is not None and float(decision["confidence"]) >= threshold]
            stats = self._outcome_stats(events)
            rows.append(
                {
                    "confidence": f">= {threshold} %",
                    "sample_size": len(events),
                    "actual_hit_rate": stats["hit_rate"],
                }
            )
        return rows

    def _market_comparison(
        self,
        decisions: list[dict[str, Any]],
        learning_events: list[dict[str, Any]],
        crypto_records: list[dict[str, Any]],
        outcome_source: str,
    ) -> list[dict[str, Any]]:
        rows = []
        found_markets = {str(row.get("market_type") or "-") for row in decisions if row.get("market_type")}
        preferred_order = ["stock", "crypto", "commodity"]
        markets = [market for market in preferred_order if market in found_markets]
        markets.extend(sorted(found_markets - set(markets)))
        if not markets:
            markets = ["stock", "crypto"]
        for market in markets:
            market_decisions = [d for d in decisions if d.get("market_type") == market]
            market_events = [event for event in learning_events if str(event.get("market_type") or "").lower() == market]
            rows.append(
                {
                    "market": market,
                    "decisions": len(market_decisions),
                    "hit_rate": self._outcome_stats(market_events)["hit_rate"] if market_events else INSUFFICIENT_DATA,
                    "learning_rate": round(len(market_events) / len(market_decisions), 4) if market_decisions and market_events else INSUFFICIENT_DATA,
                    "average_confidence": self._avg([d.get("confidence") for d in market_decisions]),
                    "average_profit": self._avg([e.get("price_change_percent") for e in market_events]) if market_events else INSUFFICIENT_DATA,
                    "outcome_source": outcome_source if market_events else "Nicht genuegend Ergebnisdaten",
                }
            )
        return rows

    def _symbol_comparison(
        self,
        decisions: list[dict[str, Any]],
        learning_events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
        by_symbol_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for decision in decisions:
            by_symbol[str(decision.get("symbol") or "-")].append(decision)
        for event in learning_events:
            by_symbol_events[str(event.get("symbol") or "-").upper()].append(event)
        rows = []
        for symbol, symbol_decisions in by_symbol.items():
            events = by_symbol_events.get(symbol, [])
            rows.append(
                {
                    "symbol": symbol,
                    "hit_rate": self._outcome_stats(events)["hit_rate"] if events else INSUFFICIENT_DATA,
                    "confidence": self._avg([d.get("confidence") for d in symbol_decisions]),
                    "decisions": len(symbol_decisions),
                    "profit": self._avg([e.get("price_change_percent") for e in events]) if events else INSUFFICIENT_DATA,
                }
            )
        return sorted(rows, key=lambda row: (self._sortable(row["hit_rate"]), row["decisions"]), reverse=True)[:20]

    def _timeframes(self, decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        for timeframe in ("5m", "15m", "1h", "4h", "1D"):
            scoped = [d for d in decisions if str(d.get("timeframe")).lower() == timeframe.lower()]
            rows.append(
                {
                    "timeframe": timeframe,
                    "decisions": len(scoped),
                    "hit_rate": INSUFFICIENT_DATA,
                    "average_confidence": self._avg([d.get("confidence") for d in scoped]),
                }
            )
        return rows

    def _indicator_report(
        self,
        stock_decisions: list[dict[str, Any]],
        crypto_records: list[dict[str, Any]],
        learning_events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        text_by_success: dict[str, list[str]] = {"win": [], "loss": []}
        for event in learning_events:
            outcome = str(event.get("outcome") or "").lower()
            text_by_success.setdefault(outcome, []).extend(str(label).upper() for label in event.get("labels", []) or [])
        all_labels = Counter()
        for decision in stock_decisions:
            all_labels.update(label.upper() for label in self._labels(decision))
        for record in crypto_records:
            payload = record.get("payload", {})
            if isinstance(payload, dict):
                all_labels.update(label.upper() for label in self._crypto_labels(payload))
        rows = []
        for indicator in INDICATORS:
            key = indicator.upper().replace(" ", "_")
            used = sum(count for label, count in all_labels.items() if key in label or indicator.upper() in label)
            success = sum(1 for label in text_by_success.get("win", []) if key in label or indicator.upper() in label)
            failure = sum(1 for label in text_by_success.get("loss", []) if key in label or indicator.upper() in label)
            total_outcomes = success + failure
            rows.append(
                {
                    "indicator": indicator,
                    "used": used,
                    "successful": success,
                    "hit_rate": round(success / total_outcomes * 100, 2) if total_outcomes else INSUFFICIENT_DATA,
                    "average_influence": INSUFFICIENT_DATA,
                    "current_weight": INSUFFICIENT_DATA,
                }
            )
        return rows

    def _learning_curve(
        self,
        decisions: list[dict[str, Any]],
        learning_events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        points = []
        step = 1000
        max_len = min(len(decisions), len(learning_events))
        for end in range(step, max_len + 1, step):
            scoped_decisions = decisions[:end]
            scoped_events = learning_events[:end]
            points.append(
                {
                    "decisions": end,
                    "hit_rate": self._outcome_stats(scoped_events)["hit_rate"],
                    "confidence": self._avg([d.get("confidence") for d in scoped_decisions]),
                    "profit": self._avg([e.get("price_change_percent") for e in scoped_events]),
                    "error_rate": INSUFFICIENT_DATA,
                }
            )
        return points[-30:]

    def _learning_score(
        self,
        decisions: list[dict[str, Any]],
        learning_events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        progress = self._progress(decisions, learning_events)
        hit_delta = self._num(progress.get("hit_rate_delta")) or 0.0
        confidence_delta = self._num(progress.get("confidence_delta")) or 0.0
        data_score = min(25.0, len(learning_events) / 1000 * 5)
        stability = 20.0 if len(learning_events) >= 1000 else max(0.0, len(learning_events) / 1000 * 20)
        hit_score = max(0.0, min(25.0, 12.5 + hit_delta))
        confidence_score = max(0.0, min(15.0, 7.5 + confidence_delta / 2))
        parameter_score = 15.0 if any(self._num(d.get("raw", {}).get("brain_adjustment", {}).get("adjustment")) for d in decisions if isinstance(d.get("raw"), dict)) else 0.0
        score = round(data_score + stability + hit_score + confidence_score + parameter_score, 2)
        return {
            "score": min(100.0, score),
            "components": {
                "data_volume": round(data_score, 2),
                "stability": round(stability, 2),
                "hit_rate_progress": round(hit_score, 2),
                "confidence_progress": round(confidence_score, 2),
                "parameter_adjustment_proven": parameter_score,
            },
            "verdict": progress["verdict"],
        }

    def _warnings(
        self,
        decisions: list[dict[str, Any]],
        learning_events: list[dict[str, Any]],
        crypto_records: list[dict[str, Any]],
        outcome_source: str,
    ) -> list[str]:
        warnings = []
        if not learning_events:
            warnings.append("Keine eindeutigen Ergebnisdaten fuer Trefferquote gefunden.")
        if outcome_source != "decision_id_trade_outcomes" and crypto_records and not any(record.get("payload", {}).get("result") for record in crypto_records if isinstance(record.get("payload"), dict)):
            warnings.append("Crypto-Events enthalten keine belastbaren abgeschlossenen Ergebnisdaten.")
        if outcome_source != "decision_id_trade_outcomes":
            warnings.append("Drawdown, Haltedauer, Slippage und Gebuehren sind in den vorhandenen Daten nicht belastbar rekonstruierbar.")
        else:
            warnings.append("Gebuehren und Slippage sind weiterhin nur Platzhalter, bis ein Broker-/Order-Modell angeschlossen ist.")
        if len(decisions) != len(learning_events) and outcome_source != "decision_id_trade_outcomes":
            warnings.append("Decision-Anzahl und Outcome-Anzahl sind nicht deckungsgleich; Trefferquote wird aus Stock-Learning-Logs berechnet.")
        return warnings

    def _recommendations(
        self,
        decisions: list[dict[str, Any]],
        learning_events: list[dict[str, Any]],
        crypto_records: list[dict[str, Any]],
        outcome_source: str,
    ) -> list[str]:
        if outcome_source == "decision_id_trade_outcomes":
            recommendations = [
                "Mehr abgeschlossene simulierte Trades sammeln, damit Trefferquoten statistisch belastbarer werden.",
                "Gebuehren und Slippage spaeter mit realistischem Kostenmodell fuellen.",
                "Outcome-Auswertung je Markt und Symbol weiter beobachten.",
            ]
        else:
            recommendations = [
                "Outcome-Daten mit eindeutiger decision_id speichern, damit Trefferquote pro Entscheidung exakt messbar wird.",
                "Crypto-Ergebnisbewertung an abgeschlossene simulierte Trades koppeln, bevor Crypto-Lernen als nachgewiesen gilt.",
                "Profit, Drawdown, Haltedauer, Gebuehren und Slippage als eigene Felder persistieren.",
            ]
        if self._progress(decisions, learning_events)["verdict"].startswith("Verbesserung"):
            recommendations.insert(0, "Aktuelle Stock-Lernlogik weiter beobachten und gegen Ueberanpassung testen.")
        return recommendations

    def _paired_decision_outcomes(
        self,
        decisions: list[dict[str, Any]],
        learning_events: list[dict[str, Any]],
    ) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        """Pair outcomes to decisions by decision_id, with legacy zip fallback."""

        by_id = {str(decision.get("decision_id")): decision for decision in decisions if decision.get("decision_id")}
        pairs = [
            (by_id[str(event.get("decision_id"))], event)
            for event in learning_events
            if event.get("decision_id") and str(event.get("decision_id")) in by_id
        ]
        if pairs:
            return pairs
        if by_id or any(event.get("decision_id") for event in learning_events):
            return []
        return list(zip(decisions[-len(learning_events) :], learning_events)) if learning_events else []

    def _outcome_stats(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        wins = sum(1 for event in events if str(event.get("outcome") or "").lower() == "win")
        losses = sum(1 for event in events if str(event.get("outcome") or "").lower() == "loss")
        breakeven = sum(1 for event in events if str(event.get("outcome") or "").lower() == "breakeven")
        unknown = max(0, len(events) - wins - losses - breakeven)
        total = wins + losses
        return {
            "wins": wins,
            "losses": losses,
            "breakeven": breakeven,
            "unknown": unknown,
            "closed": len(events),
            "classified_for_hit_rate": total,
            "hit_rate": round(wins / total * 100, 2) if total else INSUFFICIENT_DATA,
        }

    def _progress_verdict(self, first: dict[str, Any], last: dict[str, Any]) -> str:
        delta = self._delta(last.get("hit_rate"), first.get("hit_rate"))
        if not isinstance(delta, (int, float)):
            return "Nicht genuegend Daten"
        if delta > 2:
            return f"Verbesserung nachweisbar: Trefferquote +{delta:.2f} Prozentpunkte"
        if delta < -2:
            return f"Verschlechterung sichtbar: Trefferquote {delta:.2f} Prozentpunkte"
        return f"Stagnation: Trefferquote veraendert sich nur um {delta:.2f} Prozentpunkte"

    def _labels(self, decision: dict[str, Any]) -> list[str]:
        state = decision.get("state", {})
        if isinstance(state, dict) and isinstance(state.get("labels"), list):
            return [str(label) for label in state["labels"]]
        return []

    def _crypto_labels(self, payload: dict[str, Any]) -> list[str]:
        labels: list[str] = []
        indicators = payload.get("indicators")
        if isinstance(indicators, dict):
            labels.extend(str(name) for name in indicators.keys())
        facts = payload.get("facts")
        if isinstance(facts, dict):
            labels.extend(str(value) for value in facts.values())
        return labels

    def _avg(self, values: list[Any]) -> float | str:
        numeric = [self._num(value) for value in values]
        clean = [value for value in numeric if value is not None]
        return round(mean(clean), 4) if clean else INSUFFICIENT_DATA

    def _delta(self, later: Any, earlier: Any) -> float | str:
        left = self._num(later)
        right = self._num(earlier)
        if left is None or right is None:
            return INSUFFICIENT_DATA
        return round(left - right, 4)

    def _sortable(self, value: Any) -> float:
        numeric = self._num(value)
        return numeric if numeric is not None else -1.0

    def _num(self, value: Any) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value))
        except (TypeError, ValueError):
            return None
