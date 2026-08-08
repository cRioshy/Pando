"""Fail fast when a local PandorickKi runtime is incomplete or misconfigured."""

from __future__ import annotations

import sys
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import PlatformConfig


def main() -> int:
    """Validate only files and imports required before service startup."""

    config = PlatformConfig.from_env()
    required_project_files = (
        config.project_root / "main.py",
        config.project_root / "orchestrator.py",
        config.project_root / "adapters" / "crypto_market_data_service.py",
    )
    required_crypto_files = (
        config.crypto_project_path / "pandorick_pipeline.py",
        config.crypto_project_path / "models.py",
        config.crypto_project_path / "brain.py",
    )
    missing = [path for path in (*required_project_files, *required_crypto_files) if not path.is_file()]
    if missing:
        print("PandorickKi preflight failed. Missing required files:", file=sys.stderr)
        for path in missing:
            print(f"- {path}", file=sys.stderr)
        return 1

    try:
        ZoneInfo("America/New_York")
    except ZoneInfoNotFoundError:
        print(
            "PandorickKi preflight failed: IANA timezone data is unavailable.",
            file=sys.stderr,
        )
        return 1

    try:
        from adapters.crypto_adapter import CryptoAdapter  # noqa: F401
        from adapters.crypto_market_data_service import CryptoMarketDataService  # noqa: F401
        from orchestrator import Orchestrator  # noqa: F401
    except Exception as exc:  # noqa: BLE001 - preflight must report all import failures
        print(
            f"PandorickKi preflight failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    print(f"PandorickKi preflight OK: Python {sys.version.split()[0]} at {Path(sys.executable)}")
    print(f"Crypto legacy pipeline: {config.crypto_project_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
