"""Learning report service tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from web.learning_report_service import INSUFFICIENT_DATA, LearningReportPaths, LearningReportService


class LearningReportServiceTest(unittest.TestCase):
    def test_report_uses_real_outcomes_and_marks_missing_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stock_decisions = root / "stock_decisions.json"
            stock_logs = root / "stock_logs.json"
            brain_events = root / "brain_events.jsonl"
            brain_events_dir = root / "brain_events"
            brain_events_dir.mkdir()

            stock_decisions.write_text(
                json.dumps(
                    [
                        {
                            "timestamp": "2026-07-01T00:00:00+00:00",
                            "symbol": "AAPL",
                            "action": "WAIT",
                            "final_probability": 55,
                            "state": {"labels": ["NORMAL", "RSI"]},
                        },
                        {
                            "timestamp": "2026-07-01T00:01:00+00:00",
                            "symbol": "AAPL",
                            "action": "BUY",
                            "final_probability": 72,
                            "state": {"labels": ["TREND_UP", "VOLUME"]},
                            "brain_adjustment": {"adjustment": 2.0},
                        },
                    ]
                ),
                encoding="utf-8",
            )
            stock_logs.write_text(
                json.dumps(
                    [
                        {
                            "timestamp": "2026-07-01T00:02:00+00:00",
                            "learning_events": [
                                {"symbol": "AAPL", "outcome": "win", "price_change_percent": 0.4, "labels": ["VOLUME"]},
                                {"symbol": "AAPL", "outcome": "loss", "price_change_percent": -0.2, "labels": ["RSI"]},
                            ],
                        }
                    ]
                ),
                encoding="utf-8",
            )
            brain_events.write_text(
                json.dumps(
                    {
                        "market_type": "crypto",
                        "symbol": "BTCUSDT",
                        "direction": "WAIT",
                        "probability": 61,
                        "source_timestamp": "2026-07-01T00:03:00+00:00",
                        "payload": {"timeframe": "15m", "indicators": {"rsi": 58}},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = LearningReportService(
                LearningReportPaths(
                    stock_decisions=stock_decisions,
                    stock_logs=stock_logs,
                    brain_events_file=brain_events,
                    brain_events_dir=brain_events_dir,
                )
            ).report()

            self.assertEqual(report["summary"]["decisions"], 3)
            self.assertEqual(report["summary"]["learning_events_with_outcome"], 2)
            self.assertEqual(report["summary"]["hit_rate"], 50.0)
            self.assertEqual(report["summary"]["drawdown"], INSUFFICIENT_DATA)
            self.assertEqual(report["market_comparison"][0]["market"], "stock")
            self.assertEqual(report["market_comparison"][0]["hit_rate"], 50.0)
            self.assertEqual(report["market_comparison"][1]["market"], "crypto")
            self.assertEqual(report["market_comparison"][1]["hit_rate"], INSUFFICIENT_DATA)
            self.assertGreater(report["learning_score"]["score"], 0)

    def test_corrupt_files_do_not_raise(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stock_decisions = root / "stock_decisions.json"
            stock_logs = root / "stock_logs.json"
            brain_events = root / "brain_events.jsonl"
            brain_events_dir = root / "brain_events"
            brain_events_dir.mkdir()
            stock_decisions.write_text("{broken", encoding="utf-8")
            stock_logs.write_text("{broken", encoding="utf-8")
            brain_events.write_text("{broken\n", encoding="utf-8")

            report = LearningReportService(
                LearningReportPaths(
                    stock_decisions=stock_decisions,
                    stock_logs=stock_logs,
                    brain_events_file=brain_events,
                    brain_events_dir=brain_events_dir,
                )
            ).report()

            self.assertEqual(report["summary"]["decisions"], 0)
            self.assertEqual(report["summary"]["hit_rate"], INSUFFICIENT_DATA)

    def test_cached_report_returns_immediately_and_persists_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stock_decisions = root / "stock_decisions.json"
            stock_logs = root / "stock_logs.json"
            brain_events = root / "brain_events.jsonl"
            brain_events_dir = root / "brain_events"
            cache_file = root / "learning_report_cache.json"
            brain_events_dir.mkdir()
            stock_decisions.write_text("[]", encoding="utf-8")
            stock_logs.write_text("[]", encoding="utf-8")
            brain_events.write_text("", encoding="utf-8")

            service = LearningReportService(
                LearningReportPaths(
                    stock_decisions=stock_decisions,
                    stock_logs=stock_logs,
                    brain_events_file=brain_events,
                    brain_events_dir=brain_events_dir,
                    cache_file=cache_file,
                )
            )

            pending = service.report_cached()
            self.assertEqual(pending["cache"]["status"], "building")

            service.refresh_cache(block=True)
            cached = service.report_cached()

            self.assertIn(cached["cache"]["status"], {"fresh", "stale_refreshing"})
            self.assertTrue(cache_file.exists())
            self.assertEqual(cached["summary"]["decisions"], 0)

    def test_legacy_cache_without_metric_contract_is_rebuilt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            brain_events_dir = root / "brain_events"
            brain_events_dir.mkdir()
            cache_file = root / "learning_report_cache.json"
            cache_file.write_text(
                json.dumps({"summary": {"decisions": 999}, "cache": {"status": "fresh"}}),
                encoding="utf-8",
            )
            service = LearningReportService(
                LearningReportPaths(
                    stock_decisions=root / "stock_decisions.json",
                    stock_logs=root / "stock_logs.json",
                    brain_events_file=root / "brain_events.jsonl",
                    brain_events_dir=brain_events_dir,
                    cache_file=cache_file,
                )
            )

            pending = service.report_cached()

            self.assertEqual(pending["cache"]["status"], "building")
            self.assertNotEqual(pending["summary"]["decisions"], 999)

    def test_report_prefers_decision_id_outcomes_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stock_decisions = root / "stock_decisions.json"
            stock_logs = root / "stock_logs.json"
            brain_events = root / "brain_events.jsonl"
            brain_events_dir = root / "brain_events"
            platform_decisions = root / "platform_decisions.jsonl"
            trade_outcomes = root / "trade_outcomes.jsonl"
            archived_decisions = root / "archive" / "platform_decisions"
            archived_outcomes = root / "archive" / "trade_outcomes"
            brain_events_dir.mkdir()
            archived_decisions.mkdir(parents=True)
            archived_outcomes.mkdir(parents=True)
            stock_decisions.write_text("[]", encoding="utf-8")
            stock_logs.write_text("[]", encoding="utf-8")
            brain_events.write_text("", encoding="utf-8")
            (archived_decisions / "platform_decisions_20260723_095900.jsonl").write_text(
                json.dumps(
                    {
                        "event_type": "DECISION_CREATED",
                        "created_at": "2026-07-23T09:59:00+00:00",
                        "payload": {
                            "decision_id": "decision:archived",
                            "market_type": "stock",
                            "symbol": "MSFT",
                            "direction": "LONG",
                            "confidence": 70,
                            "created_at": "2026-07-23T09:59:00+00:00",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            platform_decisions.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "event_type": "DECISION_CREATED",
                                "created_at": "2026-07-23T10:00:00+00:00",
                                "payload": {
                                    "decision_id": "decision:one",
                                    "market_type": "crypto",
                                    "symbol": "BTCUSDT",
                                    "direction": "LONG",
                                    "confidence": 75,
                                    "created_at": "2026-07-23T10:00:00+00:00",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "event_type": "DECISION_CREATED",
                                "created_at": "2026-07-23T10:01:00+00:00",
                                "payload": {
                                    "decision_id": "decision:two",
                                    "market_type": "stock",
                                    "symbol": "AAPL",
                                    "direction": "LONG",
                                    "confidence": 65,
                                    "created_at": "2026-07-23T10:01:00+00:00",
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )
            trade_outcomes.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "record_type": "SIMULATED_TRADE_CLOSED",
                                "timestamp": "2026-07-23T10:05:00+00:00",
                                "payload": {
                                    "decision_id": "decision:one",
                                    "market_type": "crypto",
                                    "symbol": "BTCUSDT",
                                    "result_type": "WIN",
                                    "gross_profit_percent": 1.2,
                                    "holding_seconds": 300,
                                    "exit_time": "2026-07-23T10:05:00+00:00",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "record_type": "SIMULATED_TRADE_CLOSED",
                                "timestamp": "2026-07-23T10:06:00+00:00",
                                "payload": {
                                    "decision_id": "decision:two",
                                    "market_type": "stock",
                                    "symbol": "AAPL",
                                    "result_type": "LOSS",
                                    "gross_profit_percent": -0.4,
                                    "holding_seconds": 300,
                                    "exit_time": "2026-07-23T10:06:00+00:00",
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )
            (archived_outcomes / "trade_outcomes_20260723_100400.jsonl").write_text(
                json.dumps(
                    {
                        "record_type": "SIMULATED_TRADE_CLOSED",
                        "timestamp": "2026-07-23T10:04:00+00:00",
                        "payload": {
                            "decision_id": "decision:archived",
                            "market_type": "stock",
                            "symbol": "MSFT",
                            "result_type": "WIN",
                            "gross_profit_percent": 0.6,
                            "holding_seconds": 300,
                            "exit_time": "2026-07-23T10:04:00+00:00",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = LearningReportService(
                LearningReportPaths(
                    stock_decisions=stock_decisions,
                    stock_logs=stock_logs,
                    brain_events_file=brain_events,
                    brain_events_dir=brain_events_dir,
                    platform_decisions=platform_decisions,
                    trade_outcomes=trade_outcomes,
                )
            ).report()

            self.assertEqual(report["summary"]["decisions"], 3)
            self.assertEqual(report["summary"]["learning_events_with_outcome"], 3)
            self.assertEqual(report["summary"]["outcome_source"], "decision_id_trade_outcomes")
            self.assertEqual(report["summary"]["hit_rate"], 66.67)
            self.assertEqual(report["summary"]["hit_rate_numerator"], 2)
            self.assertEqual(report["summary"]["hit_rate_denominator"], 3)
            self.assertEqual(report["summary"]["outcome_eligible_decisions"], 3)
            self.assertEqual(report["summary"]["matched_outcomes"], 3)
            self.assertEqual(report["summary"]["outcome_coverage_percent"], 100.0)
            self.assertEqual(report["learning_metrics"]["schema_name"], "pandorickki.learning-metrics")
            self.assertEqual(report["learning_metrics"]["outcomes"]["matched"], 3)
            self.assertFalse(report["learning_metrics"]["ml_training"]["active"])
            self.assertEqual(report["learning_metrics"]["ml_training"]["model_updates"], 0)
            self.assertEqual(report["evaluation_score"], report["learning_score"])
            self.assertTrue(any("ML-Modelltraining" in note for note in report["metric_notes"]))
            self.assertEqual(report["summary"]["average_profit_simulation"], 0.4667)
            self.assertNotIn(
                "Decision-Anzahl und Outcome-Anzahl sind nicht deckungsgleich; Trefferquote wird aus Stock-Learning-Logs berechnet.",
                report["warnings"],
            )
            self.assertEqual(report["market_comparison"][0]["market"], "stock")
            self.assertEqual(report["market_comparison"][0]["hit_rate"], 50.0)
            self.assertEqual(report["market_comparison"][1]["market"], "crypto")
            self.assertEqual(report["market_comparison"][1]["hit_rate"], 100.0)


if __name__ == "__main__":
    unittest.main()
