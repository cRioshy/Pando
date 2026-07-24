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
                "PANDORICKKI_COMMODITIES_ENABLED": "1",
                "PANDORICKKI_DATA_DIR": "C:/tmp/pandorickki-data",
                "PANDORICKKI_CONTROL_CENTER_ENABLED": "0",
                "PANDORICKKI_EVENT_BUS_MAX_HISTORY": "123",
                "PANDORICKKI_JSONL_LEDGER_ROTATION_BYTES": "2097152",
                "PANDORICKKI_TELEGRAM_ENABLED": "1",
                "PANDORICKKI_TELEGRAM_DRY_RUN": "1",
                "PANDORICKKI_SIMULATED_OPEN_TRADES_FILE": "C:/tmp/pandorickki-data/open_trades.json",
                "PANDORICKKI_TRADE_OUTCOMES_FILE": "C:/tmp/pandorickki-data/outcomes.jsonl",
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
        self.assertTrue(config.commodities_enabled)
        self.assertEqual(config.commodity_symbols, ["GC=F", "CL=F"])
        self.assertEqual(config.data_dir, Path("C:/tmp/pandorickki-data"))
        self.assertEqual(config.shared_state_file, Path("C:/tmp/pandorickki-data/shared_state.json"))
        self.assertFalse(config.control_center_enabled)
        self.assertEqual(config.event_bus_max_history, 123)
        self.assertEqual(config.jsonl_ledger_rotation_bytes, 2097152)
        self.assertTrue(config.telegram_enabled)
        self.assertTrue(config.telegram_dry_run)
        self.assertEqual(config.simulated_open_trades_file, Path("C:/tmp/pandorickki-data/open_trades.json"))
        self.assertEqual(config.trade_outcomes_file, Path("C:/tmp/pandorickki-data/outcomes.jsonl"))

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
        self.assertFalse(config.commodities_enabled)
        self.assertFalse(config.telegram_enabled)
        self.assertTrue(config.telegram_dry_run)

    def test_control_center_toggle_controls_default_adapters(self) -> None:
        enabled = Orchestrator(config=PlatformConfig(control_center_enabled=True))
        commodities_enabled = Orchestrator(config=PlatformConfig(control_center_enabled=True, commodities_enabled=True))
        disabled = Orchestrator(config=PlatformConfig(control_center_enabled=False))

        self.assertIn("control_center", [adapter.name for adapter in enabled.adapters])
        self.assertNotIn("commodity", [adapter.name for adapter in enabled.adapters])
        self.assertIn("commodity", [adapter.name for adapter in commodities_enabled.adapters])
        self.assertIn("outcome_tracker", [adapter.name for adapter in enabled.adapters])
        self.assertNotIn("control_center", [adapter.name for adapter in disabled.adapters])

    def test_html_control_center_contains_switch_commands(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "control_center.html").read_text(encoding="utf-8")

        self.assertIn("controlToggle", html)
        self.assertIn("python main.py --live --control-on", html)
        self.assertIn("python main.py --live --control-off", html)


if __name__ == "__main__":
    unittest.main()
