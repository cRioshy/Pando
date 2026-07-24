# PandorickKi Project Overview

PandorickKi is a local trading-analysis platform that coordinates independent
market engines through adapters. The platform keeps the existing crypto bot,
stock bot, Brain, Telegram and Control Center separated and connected through
an async orchestration layer.

## Runtime Architecture

```text
main.py
  -> orchestrator.py
     -> EventBus
     -> SharedState
     -> CryptoAdapter
     -> StockAdapter
     -> CommodityAdapter
     -> BrainAdapter
     -> DecisionSignalAdapter
     -> OutcomeTracker
     -> TelegramAdapter
     -> WebControlServer
```

## Source Layout

```text
PandorickKi/
├── adapters/              # Integration adapters for markets, Brain, Telegram and signals
├── learning_graph/        # Learning Graph and Knowledge Graph services
├── strategy_arena/        # Experimental strategy example module
├── tests/                 # Unit and integration tests
├── web/                   # Local API and browser Control Center
├── docs/                  # Repository and architecture documentation
├── main.py                # CLI entrypoint
├── orchestrator.py        # Async platform coordinator
├── event_bus.py           # Event distribution
├── shared_state.py        # Safe shared snapshots
├── config.py              # Environment based configuration
└── README.md              # Main project documentation
```

## Data Policy

Runtime data is intentionally excluded from GitHub:

- `data/`
- `storage/`
- `runtime_logs/`
- `backups/`
- `*.jsonl`
- `*.db`, `*.sqlite`, `*.sqlite3`

The repository should contain source code, tests, documentation, example
configuration and local startup scripts only. Real Brain memory, trading
history, API responses, logs and backups stay local.

## Public API Areas

- `/api/health`
- `/api/status`
- `/api/services`
- `/api/crypto`
- `/api/stocks`
- `/api/commodities`
- `/api/brain`
- `/api/signals`
- `/api/statistics`
- `/api/learning-report`
- `/api/v1/learning-graph`
- `/api/v1/graph/*`

## Security Notes

- Secrets are configured through environment variables.
- `.env` files are ignored.
- The web server binds locally by default.
- API responses sanitize secret-looking fields.
- The repository must not include local runtime data or private Brain memory.
