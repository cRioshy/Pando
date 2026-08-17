"""Tests for central PandorickKi configuration."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from config import PlatformConfig
from orchestrator import Orchestrator


class PlatformConfigTest(unittest.TestCase):
    def test_config_reads_environment_overrides(self) -> None:
        with patch.dict(
            os.environ,
            {
                "PANDORICKKI_CYCLE_INTERVAL": "12.5",
                "PANDORICKKI_CONTROL_REFRESH": "0.5",
                "PANDORICKKI_LIVE_CRYPTO": "1",
                "PANDORICKKI_CRYPTO_SYMBOLS": "BTCUSDT,SOLUSDT",
                "PANDORICKKI_COMMODITY_SYMBOLS": "GC=F,CL=F",
                "PANDORICKKI_CRYPTO_LIVE_PRICE_DISPLAY": "1",
                "PANDORICKKI_STOCK_TEST_MODE": "0",
                "PANDORICKKI_STOCK_LIVE_PRICE_DISPLAY": "1",
                "PANDORICKKI_STOCK_DATA_OBSERVER_ENABLED": "1",
                "PANDORICKKI_STOCK_DAILY_CANDLE_LIMIT": "300",
                "PANDORICKKI_STOCK_CANDLE_CACHE_TTL_SECONDS": "600",
                "PANDORICKKI_STOCK_DATA_MINIMUM_CANDLES": "210",
                "PANDORICKKI_STOCK_DATA_FULL_WARMUP_CANDLES": "220",
                "PANDORICKKI_STOCK_SHADOW_LONG_BULLISH_SCORE": "64",
                "PANDORICKKI_STOCK_SHADOW_SHORT_BULLISH_SCORE": "36",
                "PANDORICKKI_STOCK_SHADOW_RISK_ATR_MULTIPLIER": "1.25",
                "PANDORICKKI_STOCK_SHADOW_RISK_MINIMUM_DISTANCE_PERCENT": "0.75",
                "PANDORICKKI_STOCK_SHADOW_RISK_TARGET_1_MULTIPLE": "1.5",
                "PANDORICKKI_STOCK_SHADOW_RISK_TARGET_2_MULTIPLE": "2.5",
                "PANDORICKKI_STOCK_SHADOW_RISK_TARGET_3_MULTIPLE": "4",
                "PANDORICKKI_STOCK_SHADOW_RISK_PRICE_DECIMALS": "3",
                "PANDORICKKI_STOCK_SHADOW_VERIFICATION_ENABLED": "1",
                "PANDORICKKI_STOCK_SHADOW_VERIFICATION_FILE": "C:/tmp/pandorickki-data/verification.jsonl",
                "PANDORICKKI_STOCK_SHADOW_VERIFICATION_HORIZON_SECONDS": "7200",
                "PANDORICKKI_STOCK_SHADOW_VERIFICATION_NEUTRAL_BAND_PERCENT": "0.1",
                "PANDORICKKI_MARKET_REGIME_OBSERVER_ENABLED": "1",
                "PANDORICKKI_MARKET_REGIME_FILE": "C:/tmp/pandorickki-data/regimes.jsonl",
                "PANDORICKKI_MARKET_REGIME_QUEUE_CAPACITY": "123",
                "PANDORICKKI_MARKET_REGIME_BATCH_SIZE": "11",
                "PANDORICKKI_MARKET_REGIME_FLUSH_INTERVAL": "0.125",
                "PANDORICKKI_COMMODITIES_ENABLED": "1",
                "PANDORICKKI_DATA_DIR": "C:/tmp/pandorickki-data",
                "PANDORICKKI_CONTROL_CENTER_ENABLED": "0",
                "PANDORICKKI_EVENT_BUS_MAX_HISTORY": "123",
                "PANDORICKKI_JSONL_LEDGER_ROTATION_BYTES": "2097152",
                "PANDORICKKI_SERVICE_ERROR_JOURNAL_ENABLED": "0",
                "PANDORICKKI_SERVICE_ERROR_JOURNAL_FILE": "C:/tmp/pandorickki-data/errors.jsonl",
                "PANDORICKKI_SERVICE_ERROR_SUMMARY_FILE": "C:/tmp/pandorickki-data/errors.json",
                "PANDORICKKI_SERVICE_ERROR_ROTATION_BYTES": "1048576",
                "PANDORICKKI_SERVICE_ERROR_MAX_ARCHIVES": "2",
                "PANDORICKKI_SERVICE_ERROR_MAX_SUMMARY_ENTRIES": "25",
                "PANDORICKKI_NEUROBRAIN_QUEUE_CAPACITY": "321",
                "PANDORICKKI_NEUROBRAIN_BATCH_SIZE": "17",
                "PANDORICKKI_NEUROBRAIN_FLUSH_INTERVAL": "0.125",
                "PANDORICKKI_TELEGRAM_ENABLED": "1",
                "PANDORICKKI_TELEGRAM_DRY_RUN": "1",
                "PANDORICKKI_SIMULATED_OPEN_TRADES_FILE": "C:/tmp/pandorickki-data/open_trades.json",
                "PANDORICKKI_TRADE_OUTCOMES_FILE": "C:/tmp/pandorickki-data/outcomes.jsonl",
                "PANDORICKKI_DECISION_GATE_OBSERVER_ENABLED": "1",
                "PANDORICKKI_DECISION_GATE_MINIMUM_PROBABILITY": "65",
                "PANDORICKKI_DECISION_GATE_MINIMUM_CONFIDENCE": "62.5",
                "PANDORICKKI_DECISION_GATE_CONFIDENCE_TOLERANCE": "3",
                "PANDORICKKI_STOCK_SHADOW_VERIFICATION_MODE": "DRAIN",
            },
            clear=False,
        ):
            config = PlatformConfig.from_env()

        self.assertEqual(config.cycle_interval, 12.5)
        self.assertEqual(config.control_refresh_seconds, 0.5)
        self.assertTrue(config.live_crypto)
        self.assertTrue(config.crypto_live_price_display)
        self.assertEqual(config.crypto_symbols, ["BTCUSDT", "SOLUSDT"])
        self.assertFalse(config.stock_test_mode)
        self.assertTrue(config.stock_live_price_display)
        self.assertTrue(config.stock_data_observer_enabled)
        self.assertEqual(config.stock_daily_candle_limit, 300)
        self.assertEqual(config.stock_candle_cache_ttl_seconds, 600.0)
        self.assertEqual(config.stock_data_minimum_candles, 210)
        self.assertEqual(config.stock_data_full_warmup_candles, 220)
        self.assertEqual(config.stock_shadow_long_bullish_score, 64.0)
        self.assertEqual(config.stock_shadow_short_bullish_score, 36.0)
        self.assertEqual(config.stock_shadow_risk_atr_multiplier, 1.25)
        self.assertEqual(config.stock_shadow_risk_minimum_distance_percent, 0.75)
        self.assertEqual(config.stock_shadow_risk_target_1_multiple, 1.5)
        self.assertEqual(config.stock_shadow_risk_target_2_multiple, 2.5)
        self.assertEqual(config.stock_shadow_risk_target_3_multiple, 4.0)
        self.assertEqual(config.stock_shadow_risk_price_decimals, 3)
        self.assertTrue(config.stock_shadow_verification_enabled)
        self.assertEqual(config.stock_shadow_verification_mode, "DRAIN")
        self.assertEqual(config.stock_shadow_verification_file, Path("C:/tmp/pandorickki-data/verification.jsonl"))
        self.assertEqual(config.stock_shadow_verification_horizon_seconds, 7200.0)
        self.assertEqual(config.stock_shadow_verification_neutral_band_percent, 0.1)
        self.assertTrue(config.market_regime_observer_enabled)
        self.assertEqual(config.market_regime_file, Path("C:/tmp/pandorickki-data/regimes.jsonl"))
        self.assertEqual(config.market_regime_queue_capacity, 123)
        self.assertEqual(config.market_regime_batch_size, 11)
        self.assertEqual(config.market_regime_flush_interval_seconds, 0.125)
        self.assertTrue(config.commodities_enabled)
        self.assertEqual(config.commodity_symbols, ["GC=F", "CL=F"])
        self.assertEqual(config.data_dir, Path("C:/tmp/pandorickki-data"))
        self.assertEqual(config.shared_state_file, Path("C:/tmp/pandorickki-data/shared_state.json"))
        self.assertFalse(config.control_center_enabled)
        self.assertEqual(config.event_bus_max_history, 123)
        self.assertEqual(config.jsonl_ledger_rotation_bytes, 2097152)
        self.assertFalse(config.service_error_journal_enabled)
        self.assertEqual(config.service_error_journal_file, Path("C:/tmp/pandorickki-data/errors.jsonl"))
        self.assertEqual(config.service_error_summary_file, Path("C:/tmp/pandorickki-data/errors.json"))
        self.assertEqual(config.service_error_rotation_bytes, 1048576)
        self.assertEqual(config.service_error_max_archives, 2)
        self.assertEqual(config.service_error_max_summary_entries, 25)
        self.assertEqual(config.neurobrain_queue_capacity, 321)
        self.assertEqual(config.neurobrain_batch_size, 17)
        self.assertEqual(config.neurobrain_flush_interval_seconds, 0.125)
        self.assertTrue(config.telegram_enabled)
        self.assertTrue(config.telegram_dry_run)
        self.assertEqual(config.simulated_open_trades_file, Path("C:/tmp/pandorickki-data/open_trades.json"))
        self.assertEqual(config.trade_outcomes_file, Path("C:/tmp/pandorickki-data/outcomes.jsonl"))
        self.assertTrue(config.decision_gate_observer_enabled)
        self.assertEqual(config.decision_gate_minimum_probability, 65.0)
        self.assertEqual(config.decision_gate_minimum_confidence, 62.5)
        self.assertEqual(config.decision_gate_confidence_tolerance, 3.0)

    def test_orchestrator_uses_configured_paths(self) -> None:
        config = PlatformConfig(
            crypto_project_path=Path("C:/crypto-test"),
            stock_project_path=Path("C:/stock-test"),
            brain_events_file=Path("C:/brain-test/events.jsonl"),
            shared_state_file=Path("C:/state-test/shared_state.json"),
            crypto_symbols=["BTCUSDT"],
        )
        orchestrator = Orchestrator(config=config, adapters=[])

        self.assertEqual(orchestrator.shared_state.path, Path("C:/state-test/shared_state.json"))
        self.assertEqual(orchestrator.config.crypto_symbols, ["BTCUSDT"])

    def test_safe_defaults_keep_live_integrations_disabled(self) -> None:
        config = PlatformConfig()

        self.assertFalse(config.live_crypto)
        self.assertFalse(config.crypto_live_price_display)
        self.assertTrue(config.stock_test_mode)
        self.assertFalse(config.stock_live_price_display)
        self.assertFalse(config.stock_data_observer_enabled)
        self.assertEqual(config.stock_daily_candle_limit, 260)
        self.assertEqual(config.stock_shadow_risk_atr_multiplier, 1.0)
        self.assertEqual(config.stock_shadow_risk_minimum_distance_percent, 0.5)
        self.assertEqual(config.stock_shadow_risk_target_1_multiple, 1.0)
        self.assertEqual(config.stock_shadow_risk_target_2_multiple, 2.0)
        self.assertEqual(config.stock_shadow_risk_target_3_multiple, 3.0)
        self.assertEqual(config.stock_shadow_risk_price_decimals, 4)
        self.assertFalse(config.stock_shadow_verification_enabled)
        self.assertEqual(config.stock_shadow_verification_mode, "NORMAL")
        self.assertEqual(config.stock_shadow_verification_horizon_seconds, 86400.0)
        self.assertEqual(config.stock_shadow_verification_neutral_band_percent, 0.05)
        self.assertFalse(config.market_regime_observer_enabled)
        self.assertEqual(config.market_regime_queue_capacity, 512)
        self.assertEqual(config.market_regime_batch_size, 32)
        self.assertEqual(config.market_regime_flush_interval_seconds, 0.25)
        self.assertFalse(config.commodities_enabled)
        self.assertFalse(config.telegram_enabled)
        self.assertTrue(config.telegram_dry_run)
        self.assertTrue(config.service_error_journal_enabled)
        self.assertEqual(config.neurobrain_queue_capacity, 2048)
        self.assertEqual(config.neurobrain_batch_size, 64)
        self.assertEqual(config.neurobrain_flush_interval_seconds, 0.25)
        self.assertFalse(config.decision_gate_observer_enabled)
        self.assertIsNone(config.decision_gate_minimum_probability)
        self.assertIsNone(config.decision_gate_minimum_confidence)

    def test_custom_data_dir_derives_error_journal_paths(self) -> None:
        config = PlatformConfig(data_dir=Path("C:/tmp/custom-pandorickki-data"))

        self.assertEqual(
            config.service_error_journal_file,
            Path("C:/tmp/custom-pandorickki-data/service_errors.jsonl"),
        )
        self.assertEqual(
            config.service_error_summary_file,
            Path("C:/tmp/custom-pandorickki-data/service_error_summary.json"),
        )

    def test_control_center_toggle_controls_default_adapters(self) -> None:
        enabled = Orchestrator(config=PlatformConfig(control_center_enabled=True))
        commodities_enabled = Orchestrator(config=PlatformConfig(control_center_enabled=True, commodities_enabled=True))
        disabled = Orchestrator(config=PlatformConfig(control_center_enabled=False))

        self.assertIn("control_center", [adapter.name for adapter in enabled.adapters])
        self.assertNotIn("commodity", [adapter.name for adapter in enabled.adapters])
        self.assertIn("commodity", [adapter.name for adapter in commodities_enabled.adapters])
        self.assertIn("outcome_tracker", [adapter.name for adapter in enabled.adapters])
        self.assertNotIn("control_center", [adapter.name for adapter in disabled.adapters])

    def test_decision_gate_observer_requires_explicit_thresholds_and_is_separate(self) -> None:
        config = PlatformConfig(
            decision_gate_observer_enabled=True,
            decision_gate_minimum_probability=65.0,
            decision_gate_minimum_confidence=60.0,
        )
        names = [adapter.name for adapter in Orchestrator(config=config).adapters]

        self.assertIn("decision_gate_observer", names)
        self.assertLess(names.index("brain"), names.index("decision_gate_observer"))
        self.assertLess(names.index("decision_gate_observer"), names.index("decision_core"))
        self.assertIn("decision_core", names)

        with self.assertRaises(ValueError):
            Orchestrator(config=PlatformConfig(decision_gate_observer_enabled=True))

    def test_stock_shadow_verification_is_optional_and_stock_only(self) -> None:
        config = PlatformConfig(
            stock_data_observer_enabled=True,
            stock_shadow_verification_enabled=True,
        )
        names = [adapter.name for adapter in Orchestrator(config=config).adapters]

        self.assertIn("stock_shadow_verification", names)
        self.assertLess(names.index("outcome_tracker"), names.index("stock_shadow_verification"))
        self.assertLess(names.index("stock_shadow_verification"), names.index("stock"))
        self.assertNotIn(
            "stock_shadow_verification",
            [adapter.name for adapter in Orchestrator(config=PlatformConfig()).adapters],
        )

    def test_market_regime_observer_is_optional_and_precedes_market_sources(self) -> None:
        config = PlatformConfig(market_regime_observer_enabled=True)
        orchestrator = Orchestrator(config=config)
        names = [adapter.name for adapter in orchestrator.adapters]

        self.assertIn("market_regime_observer", names)
        self.assertLess(names.index("market_regime_observer"), names.index("crypto"))
        self.assertLess(names.index("market_regime_observer"), names.index("stock"))
        self.assertNotIn(
            "market_regime_observer",
            [adapter.name for adapter in Orchestrator(config=PlatformConfig()).adapters],
        )

    def test_html_control_center_contains_switch_commands(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "control_center.html").read_text(encoding="utf-8")

        self.assertIn("controlToggle", html)
        self.assertIn("python main.py --live --control-on", html)
        self.assertIn("python main.py --live --control-off", html)


if __name__ == "__main__":
    unittest.main()
