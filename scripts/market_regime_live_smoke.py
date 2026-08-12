"""Isolated live-data smoke test for observer-only Market Regime v1."""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from adapters.crypto_market_data_service import CryptoMarketDataService  # noqa: E402
from adapters.market_regime_observer_adapter import MarketRegimeObserverAdapter  # noqa: E402
from adapters.stock_candle_service import StockCandleService  # noqa: E402
from event_bus import EventBus  # noqa: E402


async def main() -> None:
    started = time.perf_counter()
    cpu_started = time.process_time()
    tracemalloc.start()
    topics: list[str] = []
    bus = EventBus()
    bus.subscribe("*", lambda event: topics.append(event.topic))

    crypto = CryptoMarketDataService().fetch("BTCUSDT", "15m", 240)
    stock = StockCandleService(cache_ttl_seconds=0).fetch_daily_candles("AAPL", limit=260)
    if stock is None:
        raise RuntimeError("Public AAPL daily candles unavailable")

    with tempfile.TemporaryDirectory(prefix="pandorickki-regime-smoke-") as temp:
        root = Path(temp)
        observer = MarketRegimeObserverAdapter(
            bus,
            ledger_file=root / "market_regime.jsonl",
            flush_interval_seconds=0.01,
        )
        await observer.start()
        observer.submit(
            symbol=crypto.symbol,
            asset_type="crypto",
            timeframe=crypto.timeframe,
            candles=crypto.candles,
            source_event_id="live-smoke-crypto",
        )
        observer.submit(
            symbol=stock.symbol,
            asset_type="stock",
            timeframe=stock.timeframe,
            candles=stock.candles,
            source_event_id="live-smoke-stock",
        )
        await observer.stop()
        health = await observer.health()
        current = observer.current()
        statistics = observer.statistics()
        ledger_lines = (root / "market_regime.jsonl").read_text(encoding="utf-8").splitlines()

    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    forbidden_prefixes = (
        "DECISION_",
        "SIGNAL_",
        "SIMULATED_TRADE_",
        "TELEGRAM_",
        "ORDER_",
        "STOCK_SHADOW_",
    )
    report = {
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "cpu_seconds": round(time.process_time() - cpu_started, 6),
        "python_peak_allocated_bytes": peak,
        "health": health,
        "snapshots": current["items"],
        "statistics": statistics,
        "ledger_lines": len(ledger_lines),
        "event_topics": topics,
        "forbidden_events": [topic for topic in topics if topic.startswith(forbidden_prefixes)],
        "temporary_storage_removed": not root.exists(),
    }
    print(json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    asyncio.run(main())
