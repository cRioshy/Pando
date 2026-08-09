"""Contract tests for stock-only Live Shadow verification."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from stock_shadow_verification_contract import (
    StockShadowVerificationPolicy,
    build_verification_record,
    complete_forward_outcome,
    configuration_fingerprint,
)


NOW = datetime(2026, 8, 10, 14, 0, tzinfo=UTC)


def observation(*, legacy: str = "LONG", shadow: str = "LONG", audit_status: str = "READY") -> dict:
    return {
        "symbol": "AAPL",
        "cycle_id": "cycle-1",
        "source_event_id": "source-1",
        "analysis_timestamp": NOW.isoformat(),
        "source_timestamp": (NOW - timedelta(seconds=1)).isoformat(),
        "quote_timestamp": (NOW - timedelta(seconds=2)).isoformat(),
        "latest_candle_timestamp": (NOW - timedelta(days=1)).isoformat(),
        "entry_price": 100.0,
        "legacy": {"direction": legacy, "probability": 72.0},
        "shadow": {
            "status": "CALCULATED",
            "direction": shadow,
            "probability": 68.0,
            "probability_kind": "UNVALIDATED_HEURISTIC_SCORE",
            "feature_quality": {"status": "PASS"},
            "reason_codes": ["SS_CALCULATED"],
        },
        "data_audit": {
            "status": audit_status,
            "feature_quality": {"status": "PASS"},
            "reason_codes": ["SD_READY"] if audit_status == "READY" else ["SD_PRICE_STALE"],
        },
        "shadow_risk": {
            "status": "CALCULATED",
            "reason_codes": ["SSR_CALCULATED"],
            "risk": {
                "action": shadow,
                "entry_price": 100.0,
                "stop_loss": 98.0,
                "take_profit": [102.0, 104.0, 106.0],
            },
        },
    }


class StockShadowVerificationContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = StockShadowVerificationPolicy(horizon_seconds=3600, neutral_band_percent=0.05)
        self.fingerprint = configuration_fingerprint({"threshold": 60, "horizon": 3600})

    def test_record_is_deterministic_and_observer_only(self) -> None:
        first = build_verification_record(
            observation(), policy=self.policy, config_fingerprint=self.fingerprint, created_at=NOW
        )
        second = build_verification_record(
            observation(), policy=self.policy, config_fingerprint=self.fingerprint, created_at=NOW
        )

        self.assertEqual(first["verification_id"], second["verification_id"])
        self.assertTrue(first["comparison"]["decisions_match"])
        self.assertEqual(first["shadow"]["gate_status"], "PASS")
        self.assertEqual(first["data_quality"]["status"], "OK")
        self.assertEqual(first["outcome"]["status"], "PENDING")
        self.assertFalse(first["affects_active_decision"])
        self.assertFalse(first["ready_for_telegram"])
        self.assertFalse(first["order_execution_allowed"])
        self.assertNotIn("candles", str(first).lower())

    def test_disagreement_and_degraded_status_remain_explicit(self) -> None:
        record = build_verification_record(
            observation(legacy="LONG", shadow="HOLD", audit_status="BLOCKED"),
            policy=self.policy,
            config_fingerprint=self.fingerprint,
            created_at=NOW,
        )

        self.assertFalse(record["comparison"]["decisions_match"])
        self.assertEqual(record["comparison"]["disagreement_type"], "LEGACY_ACTION_SHADOW_HOLD")
        self.assertEqual(record["shadow"]["gate_status"], "HOLD")
        self.assertEqual(record["data_quality"]["status"], "DEGRADED")
        self.assertEqual(record["outcome"]["shadow"]["status"], "UNKNOWN")

    def test_outcome_requires_due_time_and_strictly_later_quote(self) -> None:
        record = build_verification_record(
            observation(legacy="LONG", shadow="SHORT"),
            policy=self.policy,
            config_fingerprint=self.fingerprint,
            created_at=NOW,
        )
        before_due = complete_forward_outcome(
            record,
            exit_price=101,
            quote_timestamp=(NOW + timedelta(hours=2)).isoformat(),
            evaluated_at=NOW + timedelta(minutes=30),
        )
        stale_quote = complete_forward_outcome(
            record,
            exit_price=101,
            quote_timestamp=record["quote_timestamp"],
            evaluated_at=NOW + timedelta(hours=2),
        )
        completed = complete_forward_outcome(
            record,
            exit_price=101,
            quote_timestamp=(NOW + timedelta(hours=2)).isoformat(),
            evaluated_at=NOW + timedelta(hours=2),
        )

        self.assertIsNone(before_due)
        self.assertIsNone(stale_quote)
        self.assertEqual(completed["status"], "COMPLETED")
        self.assertEqual(completed["legacy"]["status"], "WIN")
        self.assertEqual(completed["shadow"]["status"], "LOSS")
        self.assertEqual(completed["market_move_percent"], 1.0)

    def test_unknown_is_never_counted_as_success(self) -> None:
        data = observation(legacy="HOLD", shadow="HOLD")
        record = build_verification_record(
            data, policy=self.policy, config_fingerprint=self.fingerprint, created_at=NOW
        )
        completed = complete_forward_outcome(
            record,
            exit_price=103,
            quote_timestamp=(NOW + timedelta(hours=2)).isoformat(),
            evaluated_at=NOW + timedelta(hours=2),
        )

        self.assertEqual(completed["legacy"]["status"], "UNKNOWN")
        self.assertEqual(completed["shadow"]["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
