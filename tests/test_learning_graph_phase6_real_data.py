"""Phase 6 tests for real Pandorick data wiring in the Learning Graph."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
import urllib.request
from pathlib import Path

from adapters.control_center_adapter import ControlCenterAdapter
from config import PlatformConfig
from learning_graph.graph_repository import GraphRepository
from learning_graph.graph_service import LearningGraphService
from orchestrator import NoopAdapter, Orchestrator
from shared_state import SharedState
from web.api import WebControlServer


def get_json(url: str) -> dict:
    """Read one JSON response from the local server."""

    with urllib.request.urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def write_json(path: Path, payload: object) -> None:
    """Write JSON test source data."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")


class LearningGraphPhase6RealDataTest(unittest.TestCase):
    """Verify real-source wiring without demo records."""

    def make_config(self, temp_path: Path) -> PlatformConfig:
        """Create a config with isolated real-format data files."""

        stock_path = temp_path / "stock_bot"
        stock_data = stock_path / "data"
        stock_data.mkdir(parents=True)
        return PlatformConfig(
            project_root=temp_path,
            data_dir=temp_path / "data",
            shared_state_file=temp_path / "data" / "shared_state.json",
            brain_events_file=temp_path / "data" / "brain_events.jsonl",
            stock_project_path=stock_path,
            crypto_project_path=temp_path / "crypto_bot",
        )

    def write_sources(self, config: PlatformConfig) -> None:
        """Write realistic Pandorick source files."""

        config.data_dir.mkdir(parents=True)
        config.brain_events_file.write_text(
            json.dumps(
                {
                    "received_at": "2026-07-12T10:00:00+00:00",
                    "source_event_id": "crypto-1",
                    "event_type": "CRYPTO_ANALYSIS_FINISHED",
                    "source": "crypto",
                    "market_type": "crypto",
                    "symbol": "BTCUSDT",
                    "direction": "WAIT",
                    "probability": 62.0,
                    "source_timestamp": "2026-07-12T10:00:00+00:00",
                    "payload": {
                        "indicators": {
                            "ema20": 100,
                            "ema50": 99,
                            "rsi": 52,
                            "volume": 1200,
                            "open_interest": 100000,
                        }
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        write_json(
            config.stock_project_path / "data" / "stock_history.json",
            [
                {
                    "snapshot": {
                        "symbol": "AAPL",
                        "timestamp": "2026-07-12T10:01:00+00:00",
                        "close_price": 222.5,
                        "volume": 1000,
                        "sma_20": 220.0,
                        "rsi": 51,
                        "macd": 0.2,
                        "atr": 4.5,
                        "relative_strength": 64,
                    },
                    "state": {
                        "symbol": "AAPL",
                        "trend": "TREND_UP",
                        "facts": {
                            "close_price": 222.5,
                            "volume": 1000,
                            "sma_20": 220.0,
                            "rsi": 51,
                            "macd": 0.2,
                            "atr": 4.5,
                            "relative_strength": 64,
                        },
                    },
                }
            ],
        )
        write_json(
            config.stock_project_path / "data" / "decisions.json",
            [
                {
                    "symbol": "NVDA",
                    "timestamp": "2026-07-12T10:02:00+00:00",
                    "action": "WATCHLIST",
                    "final_probability": 66.5,
                    "state": {
                        "facts": {
                            "close_price": 176.2,
                            "volume": 1500,
                            "sma_20": 170,
                            "rsi": 58,
                            "macd": 0.5,
                        }
                    },
                }
            ],
        )

    def test_repository_combines_brain_crypto_and_stock_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config = self.make_config(Path(temp))
            self.write_sources(config)
            repository = GraphRepository(
                brain_events_file=config.brain_events_file,
                max_records=50,
                project_root=config.project_root,
                shared_state_file=config.shared_state_file,
                stock_project_path=config.stock_project_path,
                crypto_project_path=config.crypto_project_path,
            )

            records = repository.source_records()
            symbols = {record["symbol"] for record in records}
            markets = {record["market_type"] for record in records}

            self.assertIn("BTCUSDT", symbols)
            self.assertIn("AAPL", symbols)
            self.assertIn("NVDA", symbols)
            self.assertIn("crypto", markets)
            self.assertIn("stock", markets)

    def test_graph_grows_after_new_real_analysis_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config = self.make_config(Path(temp))
            self.write_sources(config)
            service = LearningGraphService(
                brain_events_file=config.brain_events_file,
                project_root=config.project_root,
                shared_state_file=config.shared_state_file,
                stock_project_path=config.stock_project_path,
                crypto_project_path=config.crypto_project_path,
            )
            before = service.graph()["stats"]["analyses_processed"]
            with config.brain_events_file.open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {
                            "received_at": "2026-07-12T10:03:00+00:00",
                            "source_event_id": "stock-2",
                            "event_type": "STOCK_ANALYSIS_FINISHED",
                            "source": "stock",
                            "market_type": "stock",
                            "symbol": "MSFT",
                            "direction": "WAIT",
                            "probability": 57.0,
                            "source_timestamp": "2026-07-12T10:03:00+00:00",
                            "payload": {"indicators": {"sma_20": 400, "rsi": 54, "volume": 2000}},
                        }
                    )
                    + "\n"
                )
            service.invalidate_cache()

            after = service.graph()["stats"]["analyses_processed"]

            self.assertGreater(after, before)

    def test_learning_graph_api_returns_http_200_with_real_sources(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                config = self.make_config(temp_path)
                self.write_sources(config)
                shared_state = SharedState(config.shared_state_file)
                orchestrator = Orchestrator(config=config, shared_state=shared_state, adapters=[])
                bus = orchestrator.event_bus
                orchestrator.adapters = [
                    NoopAdapter("crypto", "test"),
                    NoopAdapter("stock", "test"),
                    NoopAdapter("brain", "test"),
                    ControlCenterAdapter(bus, shared_state, print_output=False),
                ]
                server = WebControlServer(orchestrator, port=0)
                await orchestrator.start()
                server.start()
                try:
                    response = get_json(f"{server.url}/api/v1/learning-graph")
                finally:
                    server.stop()
                    await orchestrator.stop()

                graph = response["learning_graph"]
                self.assertGreaterEqual(graph["stats"]["analyses_processed"], 3)
                self.assertGreater(graph["stats"]["visible_nodes"], 0)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
