from __future__ import annotations

import json
import unittest

from event_payload_contract import (
    CONSUMER_FIELD_REQUIREMENTS,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    FORBIDDEN_FIELDS,
    LEGACY_FIELD_REPLACEMENTS,
    OBSERVER_CONTRACT_NAME,
    OBSERVER_CONTRACT_VERSION,
    compact_market_payload,
    compact_observer_payload,
    contract_errors,
    observer_contract_errors,
)


class CompactEventPayloadContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.current_event = {
            "event_type": "CRYPTO_ANALYSIS_FINISHED",
            "event_id": "event-market-1",
            "correlation_id": "cycle-1",
            "payload": {
                "market_type": "crypto",
                "symbol": "BTC/USDT",
                "timeframe": "15m",
                "direction": "LONG",
                "probability": 72.5,
                "price": 100.0,
                "current_price": 100.0,
                "price_status": "OK",
                "indicators": {"atr": 2.0, "rsi": 54.0},
                "facts": {"trend": "up"},
                "risk": {"stop_loss": 97.0, "take_profit_1": 104.5},
                "source_timestamp": "2026-08-01T10:00:00+00:00",
                "received_at": "2026-08-01T10:00:01+00:00",
                "raw_result": {
                    "result": "OPEN",
                    "market_data": {
                        "candles": [
                            {"low": 99.0, "high": 102.0, "secret": "not-needed"},
                            {"low": 98.0, "high": 103.0},
                        ]
                    },
                    "api_token": "must-not-be-copied",
                },
                "features": {
                    "training_only": [1, 2, 3],
                    "metadata": {"data_quality": {
                        "schema_name": "pandorickki.feature-data-quality",
                        "schema_version": 1,
                        "status": "PASS",
                        "order": {"status": "VERIFIED", "reason": "sorted"},
                        "warmup": {"status": "READY", "available_candles": 240},
                    }},
                },
                "market_data_diagnostics": {"attempts": ["large"]},
            },
        }

    def test_projects_current_envelope_to_versioned_compact_payload(self) -> None:
        compact = compact_market_payload(self.current_event)

        self.assertEqual(compact["schema_name"], CONTRACT_NAME)
        self.assertEqual(compact["schema_version"], CONTRACT_VERSION)
        self.assertEqual(compact["source_event_id"], "event-market-1")
        self.assertEqual(compact["public_result"], "OPEN")
        self.assertEqual(compact["market_context"], {"recent_swing_low": 98.0, "recent_swing_high": 103.0})
        self.assertEqual(contract_errors(compact), [])
        encoded = json.dumps(compact)
        for forbidden in FORBIDDEN_FIELDS:
            self.assertNotIn(f'"{forbidden}"', encoded)
        self.assertNotIn("must-not-be-copied", encoded)

    def test_carries_only_compact_feature_quality_projection(self) -> None:
        self.current_event["payload"]["features"] = {
            "training_only": [1, 2, 3],
            "metadata": {
                "data_quality": {
                    "schema_name": "pandorickki.feature-data-quality",
                    "schema_version": 1,
                    "status": "PASS",
                    "input_rows": 240,
                    "accepted_rows": 240,
                    "output_rows": 240,
                    "dropped_rows": 0,
                    "duplicate_rows": 0,
                    "timestamped_rows": 240,
                    "order": {"status": "VERIFIED", "reason": "sorted", "reordered": False},
                    "warmup": {"status": "READY", "available_candles": 240},
                    "violations": {"secret_bulk": 99},
                    "warnings": ["bulk warning"],
                }
            },
        }

        compact = compact_market_payload(self.current_event)

        self.assertEqual(compact["feature_quality"]["status"], "PASS")
        self.assertEqual(compact["feature_quality"]["order"]["status"], "VERIFIED")
        self.assertNotIn("violations", compact["feature_quality"])
        self.assertNotIn("warnings", compact["feature_quality"])
        self.assertNotIn('"features"', json.dumps(compact))

    def test_contract_declares_all_fields_needed_by_current_consumers(self) -> None:
        compact = compact_market_payload(self.current_event)
        available = set(compact)
        # IDs created at later stages are optional at market-analysis time but
        # remain first-class fields in the common contract.
        later_stage_fields = {"decision_id", "signal_id", "created_at", "confidence"}
        available.update(later_stage_fields)

        for consumer, required in CONSUMER_FIELD_REQUIREMENTS.items():
            with self.subTest(consumer=consumer):
                self.assertEqual(required - available, set())

    def test_accepts_flat_stock_payload_without_legacy_raw_result(self) -> None:
        compact = compact_market_payload(
            {
                "market_type": "stock",
                "symbol": "AAPL",
                "direction": "WAIT",
                "probability": 50.0,
                "price": 220.0,
                "indicators": {},
                "risk": {},
            }
        )

        self.assertEqual(compact["market_type"], "stock")
        self.assertEqual(compact["market_context"], {})
        self.assertEqual(contract_errors(compact), [])

    def test_validator_rejects_unversioned_or_bulk_payloads(self) -> None:
        errors = contract_errors({"market_type": "crypto", "symbol": "BTC", "raw_result": {}})

        self.assertTrue(any("schema_name" in error for error in errors))
        self.assertTrue(any("schema_version" in error for error in errors))
        self.assertTrue(any("raw_result" in error for error in errors))

    def test_every_verified_legacy_bulk_read_has_a_compact_replacement(self) -> None:
        self.assertEqual(
            LEGACY_FIELD_REPLACEMENTS,
            {
                "crypto_trade_tracker:raw_result.market_data.candles": (
                    "market_context.recent_swing_low/recent_swing_high"
                ),
                "learning_graph:raw_result.result": "public_result",
            },
        )

    def test_projects_learning_update_to_compact_observer_payload(self) -> None:
        compact = compact_observer_payload(
            {
                "event_type": "AI_LEARNING_UPDATED",
                "payload": {
                    "status": "updated",
                    "updates": 17,
                    "memory_size": 17,
                    "last_symbol": "BTCUSDT",
                    "symbols": ["BTCUSDT", {"raw_result": "drop nested bulk"}],
                    "raw_result": {"drop": True},
                },
            }
        )

        self.assertEqual(compact["schema_name"], OBSERVER_CONTRACT_NAME)
        self.assertEqual(compact["schema_version"], OBSERVER_CONTRACT_VERSION)
        self.assertEqual(compact["event_type"], "AI_LEARNING_UPDATED")
        self.assertEqual(compact["updates"], 17)
        self.assertEqual(observer_contract_errors(compact), [])
        self.assertNotIn("raw_result", json.dumps(compact))

    def test_observer_validator_requires_event_type(self) -> None:
        errors = observer_contract_errors(
            {
                "schema_name": OBSERVER_CONTRACT_NAME,
                "schema_version": OBSERVER_CONTRACT_VERSION,
            }
        )

        self.assertEqual(errors, ["missing required field: event_type"])


if __name__ == "__main__":
    unittest.main()
