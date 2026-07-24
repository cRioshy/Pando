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
    neurobrain_receiver_enabled: bool = False
    neurobrain_inbox_file: Path = PROJECT_ROOT / "data" / "neurobrain" / "inbox.jsonl"
    neurobrain_status_file: Path = PROJECT_ROOT / "data" / "neurobrain" / "status.json"
    live_crypto: bool = False
    crypto_live_price_display: bool = False
    crypto_symbols: list[str] = field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "XRPUSDT"])
    crypto_timeframe: str = "15m"
    crypto_candle_limit: int = 240
    stock_test_mode: bool = True
    stock_live_price_display: bool = False
    commodities_enabled: bool = False
    commodity_symbols: list[str] = field(default_factory=lambda: ["GC=F", "SI=F", "CL=F", "BZ=F"])
    cycle_interval: float = 60.0
    control_center_enabled: bool = True
    control_refresh_seconds: float = 1.0
    event_bus_max_history: int = 2000
    storage_scan_interval_seconds: float = 60.0
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
            neurobrain_receiver_enabled=_env_bool("PANDORICKKI_NEUROBRAIN_RECEIVER_ENABLED", False),
            neurobrain_inbox_file=_env_path(
                "PANDORICKKI_NEUROBRAIN_INBOX_FILE",
                data_dir / "neurobrain" / "inbox.jsonl",
            ),
            neurobrain_status_file=_env_path(
                "PANDORICKKI_NEUROBRAIN_STATUS_FILE",
                data_dir / "neurobrain" / "status.json",
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
            commodities_enabled=_env_bool("PANDORICKKI_COMMODITIES_ENABLED", False),
            commodity_symbols=_env_list(
                "PANDORICKKI_COMMODITY_SYMBOLS",
                ["GC=F", "SI=F", "CL=F", "BZ=F"],
            ),
            cycle_interval=_env_float("PANDORICKKI_CYCLE_INTERVAL", 60.0),
            control_center_enabled=_env_bool("PANDORICKKI_CONTROL_CENTER_ENABLED", True),
            control_refresh_seconds=_env_float("PANDORICKKI_CONTROL_REFRESH", 1.0),
            event_bus_max_history=_env_int("PANDORICKKI_EVENT_BUS_MAX_HISTORY", 2000),
            storage_scan_interval_seconds=_env_float("PANDORICKKI_STORAGE_SCAN_INTERVAL", 60.0),
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
        if self.event_bus_max_history < 100:
            warnings.append("EventBus max history below 100; suitable only for tests.")
        if self.storage_scan_interval_seconds < 5.0:
            warnings.append("Storage scan interval below 5 seconds; minimum runtime value is 5.")
        if self.adapter_cycle_timeout_seconds < 1.0:
            warnings.append("Adapter cycle timeout below 1 second; minimum practical value is 1.")
        if self.brain_event_rotation_bytes < 1024 * 1024:
            warnings.append("Brain event rotation size is below 1 MB; suitable only for tests.")
        if self.jsonl_ledger_rotation_bytes < 1024 * 1024:
            warnings.append("JSONL ledger rotation size is below 1 MB; suitable only for tests.")
        if self.neurobrain_receiver_enabled:
            warnings.append("NeuroBrain receiver is enabled in read-only event mirror mode.")
        if not self.control_center_enabled:
            warnings.append("ControlCenter is disabled.")
        if self.live_crypto:
            warnings.append("Live crypto mode is enabled; Binance/network dependencies are required.")
        if self.crypto_live_price_display:
            warnings.append("Crypto dashboard prices use live spot ticker when reachable.")
        if self.stock_live_price_display:
            warnings.append("Stock dashboard prices use Yahoo Finance when reachable.")
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
            neurobrain_receiver_enabled=self.neurobrain_receiver_enabled,
            neurobrain_inbox_file=self.neurobrain_inbox_file,
            neurobrain_status_file=self.neurobrain_status_file,
            live_crypto=self.live_crypto,
            crypto_live_price_display=self.crypto_live_price_display,
            crypto_symbols=list(self.crypto_symbols),
            crypto_timeframe=self.crypto_timeframe,
            crypto_candle_limit=self.crypto_candle_limit,
            stock_test_mode=self.stock_test_mode,
            stock_live_price_display=self.stock_live_price_display,
            commodities_enabled=self.commodities_enabled,
            commodity_symbols=list(self.commodity_symbols),
            cycle_interval=self.cycle_interval,
            control_center_enabled=enabled,
            control_refresh_seconds=self.control_refresh_seconds,
            event_bus_max_history=self.event_bus_max_history,
            storage_scan_interval_seconds=self.storage_scan_interval_seconds,
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
        )
