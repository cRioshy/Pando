"""Central configuration for PandorickKi."""

from __future__ import annotations

import os
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CRYPTO_PROJECT_PATH = Path("C:/Users/Admin/Desktop/VIP-Trade-Engine-4.5(Monitor)")
DEFAULT_STOCK_PROJECT_PATH = Path("C:/Users/Admin/Documents/Codex/2026-07-09/h/pandorick_stock_bot")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_optional_float(name: str) -> float | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_path(name: str, default: Path) -> Path:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return Path(value)


def _env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None or not value.strip():
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class PlatformConfig:
    """Runtime settings for the PandorickKi platform."""

    project_root: Path = PROJECT_ROOT
    crypto_project_path: Path = DEFAULT_CRYPTO_PROJECT_PATH
    stock_project_path: Path = DEFAULT_STOCK_PROJECT_PATH
    data_dir: Path = PROJECT_ROOT / "data"
    shared_state_file: Path = PROJECT_ROOT / "data" / "shared_state.json"
    brain_events_file: Path = PROJECT_ROOT / "data" / "brain_events.jsonl"
    brain_events_dir: Path = PROJECT_ROOT / "data" / "brain_events"
    brain_event_rotation_bytes: int = 200 * 1024 * 1024
    brain_event_day_warning_bytes: int = int(1.5 * 1024 * 1024 * 1024)
    jsonl_ledger_rotation_bytes: int = 128 * 1024 * 1024
    service_error_journal_enabled: bool = True
    service_error_journal_file: Path = PROJECT_ROOT / "data" / "service_errors.jsonl"
    service_error_summary_file: Path = PROJECT_ROOT / "data" / "service_error_summary.json"
    service_error_rotation_bytes: int = 5 * 1024 * 1024
    service_error_max_archives: int = 4
    service_error_max_summary_entries: int = 500
    neurobrain_receiver_enabled: bool = False
    neurobrain_inbox_file: Path = PROJECT_ROOT / "data" / "neurobrain" / "inbox.jsonl"
    neurobrain_status_file: Path = PROJECT_ROOT / "data" / "neurobrain" / "status.json"
    neurobrain_queue_capacity: int = 2048
    neurobrain_batch_size: int = 64
    neurobrain_flush_interval_seconds: float = 0.25
    live_crypto: bool = False
    crypto_live_price_display: bool = False
    crypto_symbols: list[str] = field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "XRPUSDT"])
    crypto_timeframe: str = "15m"
    crypto_candle_limit: int = 240
    stock_test_mode: bool = True
    stock_live_price_display: bool = False
    stock_data_observer_enabled: bool = False
    stock_daily_candle_limit: int = 260
    stock_candle_cache_ttl_seconds: float = 900.0
    stock_data_minimum_candles: int = 200
    stock_data_full_warmup_candles: int = 200
    stock_data_maximum_candle_age_seconds: float = 345600.0
    stock_data_maximum_quote_age_seconds: float = 900.0
    stock_data_maximum_future_skew_seconds: float = 30.0
    stock_data_maximum_entry_deviation_percent: float = 0.5
    stock_shadow_long_bullish_score: float = 60.0
    stock_shadow_short_bullish_score: float = 40.0
    stock_shadow_risk_atr_multiplier: float = 1.0
    stock_shadow_risk_minimum_distance_percent: float = 0.5
    stock_shadow_risk_target_1_multiple: float = 1.0
    stock_shadow_risk_target_2_multiple: float = 2.0
    stock_shadow_risk_target_3_multiple: float = 3.0
    stock_shadow_risk_price_decimals: int = 4
    commodities_enabled: bool = False
    commodity_symbols: list[str] = field(default_factory=lambda: ["GC=F", "SI=F", "CL=F", "BZ=F"])
    cycle_interval: float = 60.0
    control_center_enabled: bool = True
    control_refresh_seconds: float = 1.0
    service_heartbeat_stale_seconds: float = 150.0
    event_bus_max_history: int = 2000
    storage_scan_interval_seconds: float = 60.0
    storage_scan_timeout_seconds: float = 30.0
    storage_large_file_threshold_bytes: int = 50 * 1024 * 1024
    storage_scan_byte_budget: int = 64 * 1024 * 1024
    adapter_error_backoff_seconds: float = 5.0
    adapter_cycle_timeout_seconds: float = 45.0
    stop_timeout_seconds: float = 2.0
    telegram_enabled: bool = False
    telegram_dry_run: bool = True
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_log_file: Path = PROJECT_ROOT / "data" / "telegram_dry_run.jsonl"
    rick_api_token: str | None = None
    rick_api_audit_log_file: Path = PROJECT_ROOT / "data" / "rick_api_audit.jsonl"
    simulated_open_trades_file: Path = PROJECT_ROOT / "data" / "simulated_open_trades.json"
    trade_outcomes_file: Path = PROJECT_ROOT / "data" / "trade_outcomes.jsonl"
    simulated_outcome_horizon_seconds: float = 3600.0
    platform_decisions_file: Path = PROJECT_ROOT / "data" / "platform_decisions.jsonl"
    platform_signals_file: Path = PROJECT_ROOT / "data" / "platform_signals.jsonl"
    decision_gate_observer_enabled: bool = False
    decision_gate_audit_file: Path = PROJECT_ROOT / "data" / "decision_gate_audit.jsonl"
    decision_gate_audit_rotation_bytes: int = 5 * 1024 * 1024
    decision_gate_audit_max_archives: int = 4
    decision_gate_minimum_probability: float | None = None
    decision_gate_minimum_confidence: float | None = None
    decision_gate_confidence_tolerance: float = 0.0

    def __post_init__(self) -> None:
        """Align derived brain event defaults with a custom data directory."""

        default_brain_dir = PROJECT_ROOT / "data" / "brain_events"
        if self.brain_events_dir == default_brain_dir and self.data_dir != PROJECT_ROOT / "data":
            object.__setattr__(self, "brain_events_dir", self.data_dir / "brain_events")
        default_open_trades = PROJECT_ROOT / "data" / "simulated_open_trades.json"
        if self.simulated_open_trades_file == default_open_trades and self.data_dir != PROJECT_ROOT / "data":
            object.__setattr__(self, "simulated_open_trades_file", self.data_dir / "simulated_open_trades.json")
        default_outcomes = PROJECT_ROOT / "data" / "trade_outcomes.jsonl"
        if self.trade_outcomes_file == default_outcomes and self.data_dir != PROJECT_ROOT / "data":
            object.__setattr__(self, "trade_outcomes_file", self.data_dir / "trade_outcomes.jsonl")
        default_decisions = PROJECT_ROOT / "data" / "platform_decisions.jsonl"
        if self.platform_decisions_file == default_decisions and self.data_dir != PROJECT_ROOT / "data":
            object.__setattr__(self, "platform_decisions_file", self.data_dir / "platform_decisions.jsonl")
        default_signals = PROJECT_ROOT / "data" / "platform_signals.jsonl"
        if self.platform_signals_file == default_signals and self.data_dir != PROJECT_ROOT / "data":
            object.__setattr__(self, "platform_signals_file", self.data_dir / "platform_signals.jsonl")
        default_neurobrain_inbox = PROJECT_ROOT / "data" / "neurobrain" / "inbox.jsonl"
        if self.neurobrain_inbox_file == default_neurobrain_inbox and self.data_dir != PROJECT_ROOT / "data":
            object.__setattr__(self, "neurobrain_inbox_file", self.data_dir / "neurobrain" / "inbox.jsonl")
        default_neurobrain_status = PROJECT_ROOT / "data" / "neurobrain" / "status.json"
        if self.neurobrain_status_file == default_neurobrain_status and self.data_dir != PROJECT_ROOT / "data":
            object.__setattr__(self, "neurobrain_status_file", self.data_dir / "neurobrain" / "status.json")
        default_error_journal = PROJECT_ROOT / "data" / "service_errors.jsonl"
        if self.service_error_journal_file == default_error_journal and self.data_dir != PROJECT_ROOT / "data":
            object.__setattr__(self, "service_error_journal_file", self.data_dir / "service_errors.jsonl")
        default_error_summary = PROJECT_ROOT / "data" / "service_error_summary.json"
        if self.service_error_summary_file == default_error_summary and self.data_dir != PROJECT_ROOT / "data":
            object.__setattr__(self, "service_error_summary_file", self.data_dir / "service_error_summary.json")
        default_gate_audit = PROJECT_ROOT / "data" / "decision_gate_audit.jsonl"
        if self.decision_gate_audit_file == default_gate_audit and self.data_dir != PROJECT_ROOT / "data":
            object.__setattr__(self, "decision_gate_audit_file", self.data_dir / "decision_gate_audit.jsonl")

    @classmethod
    def from_env(cls) -> "PlatformConfig":
        """Build configuration from environment variables."""

        project_root = _env_path("PANDORICKKI_PROJECT_ROOT", PROJECT_ROOT)
        data_dir = _env_path("PANDORICKKI_DATA_DIR", project_root / "data")
        return cls(
            project_root=project_root,
            crypto_project_path=_env_path(
                "PANDORICKKI_CRYPTO_PATH",
                DEFAULT_CRYPTO_PROJECT_PATH,
            ),
            stock_project_path=_env_path(
                "PANDORICKKI_STOCK_PATH",
                DEFAULT_STOCK_PROJECT_PATH,
            ),
            data_dir=data_dir,
            shared_state_file=_env_path(
                "PANDORICKKI_SHARED_STATE_FILE",
                data_dir / "shared_state.json",
            ),
            brain_events_file=_env_path(
                "PANDORICKKI_BRAIN_EVENTS_FILE",
                data_dir / "brain_events.jsonl",
            ),
            brain_events_dir=_env_path(
                "PANDORICKKI_BRAIN_EVENTS_DIR",
                data_dir / "brain_events",
            ),
            brain_event_rotation_bytes=_env_int(
                "PANDORICKKI_BRAIN_EVENT_ROTATION_BYTES",
                200 * 1024 * 1024,
            ),
            brain_event_day_warning_bytes=_env_int(
                "PANDORICKKI_BRAIN_EVENT_DAY_WARNING_BYTES",
                int(1.5 * 1024 * 1024 * 1024),
            ),
            jsonl_ledger_rotation_bytes=_env_int(
                "PANDORICKKI_JSONL_LEDGER_ROTATION_BYTES",
                128 * 1024 * 1024,
            ),
            service_error_journal_enabled=_env_bool("PANDORICKKI_SERVICE_ERROR_JOURNAL_ENABLED", True),
            service_error_journal_file=_env_path(
                "PANDORICKKI_SERVICE_ERROR_JOURNAL_FILE",
                data_dir / "service_errors.jsonl",
            ),
            service_error_summary_file=_env_path(
                "PANDORICKKI_SERVICE_ERROR_SUMMARY_FILE",
                data_dir / "service_error_summary.json",
            ),
            service_error_rotation_bytes=_env_int(
                "PANDORICKKI_SERVICE_ERROR_ROTATION_BYTES",
                5 * 1024 * 1024,
            ),
            service_error_max_archives=_env_int("PANDORICKKI_SERVICE_ERROR_MAX_ARCHIVES", 4),
            service_error_max_summary_entries=_env_int(
                "PANDORICKKI_SERVICE_ERROR_MAX_SUMMARY_ENTRIES",
                500,
            ),
            neurobrain_receiver_enabled=_env_bool("PANDORICKKI_NEUROBRAIN_RECEIVER_ENABLED", False),
            neurobrain_inbox_file=_env_path(
                "PANDORICKKI_NEUROBRAIN_INBOX_FILE",
                data_dir / "neurobrain" / "inbox.jsonl",
            ),
            neurobrain_status_file=_env_path(
                "PANDORICKKI_NEUROBRAIN_STATUS_FILE",
                data_dir / "neurobrain" / "status.json",
            ),
            neurobrain_queue_capacity=_env_int("PANDORICKKI_NEUROBRAIN_QUEUE_CAPACITY", 2048),
            neurobrain_batch_size=_env_int("PANDORICKKI_NEUROBRAIN_BATCH_SIZE", 64),
            neurobrain_flush_interval_seconds=_env_float(
                "PANDORICKKI_NEUROBRAIN_FLUSH_INTERVAL",
                0.25,
            ),
            live_crypto=_env_bool("PANDORICKKI_LIVE_CRYPTO", False),
            crypto_live_price_display=_env_bool("PANDORICKKI_CRYPTO_LIVE_PRICE_DISPLAY", False),
            crypto_symbols=_env_list(
                "PANDORICKKI_CRYPTO_SYMBOLS",
                ["BTCUSDT", "ETHUSDT", "XRPUSDT"],
            ),
            crypto_timeframe=os.getenv("PANDORICKKI_CRYPTO_TIMEFRAME", "15m"),
            crypto_candle_limit=_env_int("PANDORICKKI_CRYPTO_CANDLE_LIMIT", 240),
            stock_test_mode=_env_bool("PANDORICKKI_STOCK_TEST_MODE", True),
            stock_live_price_display=_env_bool("PANDORICKKI_STOCK_LIVE_PRICE_DISPLAY", False),
            stock_data_observer_enabled=_env_bool("PANDORICKKI_STOCK_DATA_OBSERVER_ENABLED", False),
            stock_daily_candle_limit=_env_int("PANDORICKKI_STOCK_DAILY_CANDLE_LIMIT", 260),
            stock_candle_cache_ttl_seconds=_env_float("PANDORICKKI_STOCK_CANDLE_CACHE_TTL_SECONDS", 900.0),
            stock_data_minimum_candles=_env_int("PANDORICKKI_STOCK_DATA_MINIMUM_CANDLES", 200),
            stock_data_full_warmup_candles=_env_int("PANDORICKKI_STOCK_DATA_FULL_WARMUP_CANDLES", 200),
            stock_data_maximum_candle_age_seconds=_env_float(
                "PANDORICKKI_STOCK_DATA_MAXIMUM_CANDLE_AGE_SECONDS", 345600.0
            ),
            stock_data_maximum_quote_age_seconds=_env_float(
                "PANDORICKKI_STOCK_DATA_MAXIMUM_QUOTE_AGE_SECONDS", 900.0
            ),
            stock_data_maximum_future_skew_seconds=_env_float(
                "PANDORICKKI_STOCK_DATA_MAXIMUM_FUTURE_SKEW_SECONDS", 30.0
            ),
            stock_shadow_long_bullish_score=_env_float(
                "PANDORICKKI_STOCK_SHADOW_LONG_BULLISH_SCORE", 60.0
            ),
            stock_shadow_short_bullish_score=_env_float(
                "PANDORICKKI_STOCK_SHADOW_SHORT_BULLISH_SCORE", 40.0
            ),
            stock_shadow_risk_atr_multiplier=_env_float(
                "PANDORICKKI_STOCK_SHADOW_RISK_ATR_MULTIPLIER", 1.0
            ),
            stock_shadow_risk_minimum_distance_percent=_env_float(
                "PANDORICKKI_STOCK_SHADOW_RISK_MINIMUM_DISTANCE_PERCENT", 0.5
            ),
            stock_shadow_risk_target_1_multiple=_env_float(
                "PANDORICKKI_STOCK_SHADOW_RISK_TARGET_1_MULTIPLE", 1.0
            ),
            stock_shadow_risk_target_2_multiple=_env_float(
                "PANDORICKKI_STOCK_SHADOW_RISK_TARGET_2_MULTIPLE", 2.0
            ),
            stock_shadow_risk_target_3_multiple=_env_float(
                "PANDORICKKI_STOCK_SHADOW_RISK_TARGET_3_MULTIPLE", 3.0
            ),
            stock_shadow_risk_price_decimals=_env_int(
                "PANDORICKKI_STOCK_SHADOW_RISK_PRICE_DECIMALS", 4
            ),
            stock_data_maximum_entry_deviation_percent=_env_float(
                "PANDORICKKI_STOCK_DATA_MAXIMUM_ENTRY_DEVIATION_PERCENT", 0.5
            ),
            commodities_enabled=_env_bool("PANDORICKKI_COMMODITIES_ENABLED", False),
            commodity_symbols=_env_list(
                "PANDORICKKI_COMMODITY_SYMBOLS",
                ["GC=F", "SI=F", "CL=F", "BZ=F"],
            ),
            cycle_interval=_env_float("PANDORICKKI_CYCLE_INTERVAL", 60.0),
            control_center_enabled=_env_bool("PANDORICKKI_CONTROL_CENTER_ENABLED", True),
            control_refresh_seconds=_env_float("PANDORICKKI_CONTROL_REFRESH", 1.0),
            service_heartbeat_stale_seconds=_env_float(
                "PANDORICKKI_SERVICE_HEARTBEAT_STALE_SECONDS",
                150.0,
            ),
            event_bus_max_history=_env_int("PANDORICKKI_EVENT_BUS_MAX_HISTORY", 2000),
            storage_scan_interval_seconds=_env_float("PANDORICKKI_STORAGE_SCAN_INTERVAL", 60.0),
            storage_scan_timeout_seconds=_env_float("PANDORICKKI_STORAGE_SCAN_TIMEOUT", 30.0),
            storage_large_file_threshold_bytes=_env_int(
                "PANDORICKKI_STORAGE_LARGE_FILE_THRESHOLD_BYTES",
                50 * 1024 * 1024,
            ),
            storage_scan_byte_budget=_env_int(
                "PANDORICKKI_STORAGE_SCAN_BYTE_BUDGET",
                64 * 1024 * 1024,
            ),
            adapter_error_backoff_seconds=_env_float("PANDORICKKI_ERROR_BACKOFF", 5.0),
            adapter_cycle_timeout_seconds=_env_float("PANDORICKKI_ADAPTER_CYCLE_TIMEOUT", 45.0),
            stop_timeout_seconds=_env_float("PANDORICKKI_STOP_TIMEOUT", 2.0),
            telegram_enabled=_env_bool("PANDORICKKI_TELEGRAM_ENABLED", False),
            telegram_dry_run=_env_bool("PANDORICKKI_TELEGRAM_DRY_RUN", True),
            telegram_bot_token=os.getenv("PANDORICKKI_TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("PANDORICKKI_TELEGRAM_CHAT_ID"),
            telegram_log_file=_env_path(
                "PANDORICKKI_TELEGRAM_LOG_FILE",
                data_dir / "telegram_dry_run.jsonl",
            ),
            rick_api_token=os.getenv("PANDORICKKI_RICK_API_TOKEN"),
            rick_api_audit_log_file=_env_path(
                "PANDORICKKI_RICK_API_AUDIT_LOG_FILE",
                data_dir / "rick_api_audit.jsonl",
            ),
            simulated_open_trades_file=_env_path(
                "PANDORICKKI_SIMULATED_OPEN_TRADES_FILE",
                data_dir / "simulated_open_trades.json",
            ),
            trade_outcomes_file=_env_path(
                "PANDORICKKI_TRADE_OUTCOMES_FILE",
                data_dir / "trade_outcomes.jsonl",
            ),
            simulated_outcome_horizon_seconds=_env_float(
                "PANDORICKKI_SIMULATED_OUTCOME_HORIZON_SECONDS",
                3600.0,
            ),
            platform_decisions_file=_env_path(
                "PANDORICKKI_PLATFORM_DECISIONS_FILE",
                data_dir / "platform_decisions.jsonl",
            ),
            platform_signals_file=_env_path(
                "PANDORICKKI_PLATFORM_SIGNALS_FILE",
                data_dir / "platform_signals.jsonl",
            ),
            decision_gate_observer_enabled=_env_bool(
                "PANDORICKKI_DECISION_GATE_OBSERVER_ENABLED", False
            ),
            decision_gate_audit_file=_env_path(
                "PANDORICKKI_DECISION_GATE_AUDIT_FILE",
                data_dir / "decision_gate_audit.jsonl",
            ),
            decision_gate_audit_rotation_bytes=_env_int(
                "PANDORICKKI_DECISION_GATE_AUDIT_ROTATION_BYTES",
                5 * 1024 * 1024,
            ),
            decision_gate_audit_max_archives=_env_int(
                "PANDORICKKI_DECISION_GATE_AUDIT_MAX_ARCHIVES", 4
            ),
            decision_gate_minimum_probability=_env_optional_float(
                "PANDORICKKI_DECISION_GATE_MINIMUM_PROBABILITY"
            ),
            decision_gate_minimum_confidence=_env_optional_float(
                "PANDORICKKI_DECISION_GATE_MINIMUM_CONFIDENCE"
            ),
            decision_gate_confidence_tolerance=_env_float(
                "PANDORICKKI_DECISION_GATE_CONFIDENCE_TOLERANCE", 0.0
            ),
        )

    def validate(self) -> list[str]:
        """Return warnings for missing optional paths or unsafe settings."""

        warnings: list[str] = []
        if not self.crypto_project_path.exists():
            warnings.append(f"Crypto project path not found: {self.crypto_project_path}")
        if not self.stock_project_path.exists():
            warnings.append(f"Stock project path not found: {self.stock_project_path}")
        if self.cycle_interval < 0.1:
            warnings.append("Cycle interval below 0.1 seconds; minimum runtime value is 0.1.")
        if self.control_refresh_seconds < 0.1:
            warnings.append("Control refresh below 0.1 seconds; minimum runtime value is 0.1.")
        if self.service_heartbeat_stale_seconds < 1.0:
            warnings.append("Service heartbeat stale threshold below 1 second; suitable only for tests.")
        if self.event_bus_max_history < 100:
            warnings.append("EventBus max history below 100; suitable only for tests.")
        if self.storage_scan_interval_seconds < 5.0:
            warnings.append("Storage scan interval below 5 seconds; minimum runtime value is 5.")
        if self.storage_scan_timeout_seconds < 1.0:
            warnings.append("Storage scan timeout below 1 second; minimum practical value is 1.")
        if self.storage_large_file_threshold_bytes < 1024 * 1024:
            warnings.append("Storage large-file threshold below 1 MB; suitable only for tests.")
        if self.storage_scan_byte_budget < 64 * 1024:
            warnings.append("Storage scan byte budget below 64 KB; suitable only for tests.")
        if self.adapter_cycle_timeout_seconds < 1.0:
            warnings.append("Adapter cycle timeout below 1 second; minimum practical value is 1.")
        if self.brain_event_rotation_bytes < 1024 * 1024:
            warnings.append("Brain event rotation size is below 1 MB; suitable only for tests.")
        if self.jsonl_ledger_rotation_bytes < 1024 * 1024:
            warnings.append("JSONL ledger rotation size is below 1 MB; suitable only for tests.")
        if self.service_error_rotation_bytes < 64 * 1024:
            warnings.append("Service error journal rotation size is below 64 KB; suitable only for tests.")
        if self.service_error_max_archives < 1:
            warnings.append("Service error journal keeps no archives; only the active file remains.")
        if self.service_error_max_summary_entries < 10:
            warnings.append("Service error summary entry limit below 10; suitable only for tests.")
        if self.neurobrain_receiver_enabled:
            warnings.append("NeuroBrain receiver is enabled in read-only event mirror mode.")
        if self.neurobrain_queue_capacity < 1:
            warnings.append("NeuroBrain queue capacity below 1; runtime clamps it to 1.")
        if self.neurobrain_batch_size < 1:
            warnings.append("NeuroBrain batch size below 1; runtime clamps it to 1.")
        if self.neurobrain_flush_interval_seconds <= 0:
            warnings.append("NeuroBrain flush interval is not positive; runtime uses 0.01 seconds.")
        if self.decision_gate_observer_enabled:
            warnings.append("Decision Gate is enabled in observer-only audit mode.")
            if self.decision_gate_minimum_probability is None:
                warnings.append("Decision Gate observer enabled but minimum probability is missing.")
            if self.decision_gate_minimum_confidence is None:
                warnings.append("Decision Gate observer enabled but minimum confidence is missing.")
        if self.decision_gate_audit_rotation_bytes < 1024 * 1024:
            warnings.append("Decision Gate audit rotation size is below 1 MB; runtime clamps it to 1 MB.")
        if self.decision_gate_audit_max_archives < 0:
            warnings.append("Decision Gate audit archive limit is negative; runtime clamps it to 0.")
        if not self.control_center_enabled:
            warnings.append("ControlCenter is disabled.")
        if self.live_crypto:
            warnings.append("Live crypto mode is enabled; Binance/network dependencies are required.")
        if self.crypto_live_price_display:
            warnings.append("Crypto dashboard prices use live spot ticker when reachable.")
        if self.stock_live_price_display:
            warnings.append("Stock dashboard prices use Yahoo Finance when reachable.")
        if self.stock_data_observer_enabled:
            warnings.append("Stock daily candles are enabled in read-only contract observer mode.")
        if self.stock_daily_candle_limit < self.stock_data_minimum_candles:
            warnings.append("Stock daily candle limit is below the stock-data minimum candle count.")
        if self.stock_data_full_warmup_candles < self.stock_data_minimum_candles:
            warnings.append("Stock data full warmup is below the minimum candle count.")
        if self.stock_shadow_long_bullish_score <= 50:
            warnings.append("Stock shadow LONG score must be greater than 50.")
        if self.stock_shadow_short_bullish_score >= 50:
            warnings.append("Stock shadow SHORT score must be below 50.")
        if self.stock_shadow_risk_atr_multiplier <= 0:
            warnings.append("Stock shadow risk ATR multiplier must be positive.")
        if self.stock_shadow_risk_minimum_distance_percent <= 0:
            warnings.append("Stock shadow minimum risk distance must be positive.")
        if not (
            0 < self.stock_shadow_risk_target_1_multiple
            < self.stock_shadow_risk_target_2_multiple
            < self.stock_shadow_risk_target_3_multiple
        ):
            warnings.append("Stock shadow risk targets must be positive and strictly increasing.")
        if not 0 <= self.stock_shadow_risk_price_decimals <= 8:
            warnings.append("Stock shadow risk price decimals must be from 0 through 8.")
        if self.commodities_enabled:
            warnings.append("Commodities use free Yahoo Finance futures prices when reachable.")
        if self.telegram_enabled and not self.telegram_dry_run:
            if not self.telegram_bot_token:
                warnings.append("Telegram live mode enabled but bot token is missing.")
            if not self.telegram_chat_id:
                warnings.append("Telegram live mode enabled but chat id is missing.")
        return warnings

    def telegram_settings(self) -> dict[str, Any]:
        """Return settings for TelegramAdapter without exposing unrelated config."""

        return {
            "enabled": self.telegram_enabled,
            "dry_run": self.telegram_dry_run,
            "bot_token": self.telegram_bot_token,
            "chat_id": self.telegram_chat_id,
            "log_file": self.telegram_log_file,
        }

    def with_control_center(self, enabled: bool) -> "PlatformConfig":
        """Return a copy with ControlCenter explicitly toggled."""

        return PlatformConfig(
            project_root=self.project_root,
            crypto_project_path=self.crypto_project_path,
            stock_project_path=self.stock_project_path,
            data_dir=self.data_dir,
            shared_state_file=self.shared_state_file,
            brain_events_file=self.brain_events_file,
            brain_events_dir=self.brain_events_dir,
            brain_event_rotation_bytes=self.brain_event_rotation_bytes,
            brain_event_day_warning_bytes=self.brain_event_day_warning_bytes,
            jsonl_ledger_rotation_bytes=self.jsonl_ledger_rotation_bytes,
            service_error_journal_enabled=self.service_error_journal_enabled,
            service_error_journal_file=self.service_error_journal_file,
            service_error_summary_file=self.service_error_summary_file,
            service_error_rotation_bytes=self.service_error_rotation_bytes,
            service_error_max_archives=self.service_error_max_archives,
            service_error_max_summary_entries=self.service_error_max_summary_entries,
            neurobrain_receiver_enabled=self.neurobrain_receiver_enabled,
            neurobrain_inbox_file=self.neurobrain_inbox_file,
            neurobrain_status_file=self.neurobrain_status_file,
            neurobrain_queue_capacity=self.neurobrain_queue_capacity,
            neurobrain_batch_size=self.neurobrain_batch_size,
            neurobrain_flush_interval_seconds=self.neurobrain_flush_interval_seconds,
            live_crypto=self.live_crypto,
            crypto_live_price_display=self.crypto_live_price_display,
            crypto_symbols=list(self.crypto_symbols),
            crypto_timeframe=self.crypto_timeframe,
            crypto_candle_limit=self.crypto_candle_limit,
            stock_test_mode=self.stock_test_mode,
            stock_live_price_display=self.stock_live_price_display,
            stock_data_observer_enabled=self.stock_data_observer_enabled,
            stock_daily_candle_limit=self.stock_daily_candle_limit,
            stock_candle_cache_ttl_seconds=self.stock_candle_cache_ttl_seconds,
            stock_data_minimum_candles=self.stock_data_minimum_candles,
            stock_data_full_warmup_candles=self.stock_data_full_warmup_candles,
            stock_data_maximum_candle_age_seconds=self.stock_data_maximum_candle_age_seconds,
            stock_data_maximum_quote_age_seconds=self.stock_data_maximum_quote_age_seconds,
            stock_data_maximum_future_skew_seconds=self.stock_data_maximum_future_skew_seconds,
            stock_data_maximum_entry_deviation_percent=self.stock_data_maximum_entry_deviation_percent,
            stock_shadow_long_bullish_score=self.stock_shadow_long_bullish_score,
            stock_shadow_short_bullish_score=self.stock_shadow_short_bullish_score,
            stock_shadow_risk_atr_multiplier=self.stock_shadow_risk_atr_multiplier,
            stock_shadow_risk_minimum_distance_percent=self.stock_shadow_risk_minimum_distance_percent,
            stock_shadow_risk_target_1_multiple=self.stock_shadow_risk_target_1_multiple,
            stock_shadow_risk_target_2_multiple=self.stock_shadow_risk_target_2_multiple,
            stock_shadow_risk_target_3_multiple=self.stock_shadow_risk_target_3_multiple,
            stock_shadow_risk_price_decimals=self.stock_shadow_risk_price_decimals,
            commodities_enabled=self.commodities_enabled,
            commodity_symbols=list(self.commodity_symbols),
            cycle_interval=self.cycle_interval,
            control_center_enabled=enabled,
            control_refresh_seconds=self.control_refresh_seconds,
            service_heartbeat_stale_seconds=self.service_heartbeat_stale_seconds,
            event_bus_max_history=self.event_bus_max_history,
            storage_scan_interval_seconds=self.storage_scan_interval_seconds,
            storage_scan_timeout_seconds=self.storage_scan_timeout_seconds,
            storage_large_file_threshold_bytes=self.storage_large_file_threshold_bytes,
            storage_scan_byte_budget=self.storage_scan_byte_budget,
            adapter_error_backoff_seconds=self.adapter_error_backoff_seconds,
            adapter_cycle_timeout_seconds=self.adapter_cycle_timeout_seconds,
            stop_timeout_seconds=self.stop_timeout_seconds,
            telegram_enabled=self.telegram_enabled,
            telegram_dry_run=self.telegram_dry_run,
            telegram_bot_token=self.telegram_bot_token,
            telegram_chat_id=self.telegram_chat_id,
            telegram_log_file=self.telegram_log_file,
            rick_api_token=self.rick_api_token,
            rick_api_audit_log_file=self.rick_api_audit_log_file,
            simulated_open_trades_file=self.simulated_open_trades_file,
            trade_outcomes_file=self.trade_outcomes_file,
            simulated_outcome_horizon_seconds=self.simulated_outcome_horizon_seconds,
            platform_decisions_file=self.platform_decisions_file,
            platform_signals_file=self.platform_signals_file,
            decision_gate_observer_enabled=self.decision_gate_observer_enabled,
            decision_gate_audit_file=self.decision_gate_audit_file,
            decision_gate_audit_rotation_bytes=self.decision_gate_audit_rotation_bytes,
            decision_gate_audit_max_archives=self.decision_gate_audit_max_archives,
            decision_gate_minimum_probability=self.decision_gate_minimum_probability,
            decision_gate_minimum_confidence=self.decision_gate_minimum_confidence,
            decision_gate_confidence_tolerance=self.decision_gate_confidence_tolerance,
        )
