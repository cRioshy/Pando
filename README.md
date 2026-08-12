# PandorickKi

PandorickKi is a local AI-assisted trading-analysis platform. It connects
independent market engines for crypto, stocks and commodities with a Brain,
learning layer, Knowledge Graph, statistics service, Telegram dry-run output
and a live browser Control Center.

Market Regime v1 ergänzt eine ausschließlich beobachtende Drei-Achsen-Sicht auf Trendrichtung, Volatilität und Trendphase. Crypto nutzt echte `15m`-Serien, Stocks öffentliche `1d`-Serien. Regime-Snapshots beeinflussen keine Decisions, Signale, Outcomes, Telegram-Nachrichten oder Orders. Vertrag und API sind in `docs/MARKET_REGIME_CONTRACT.md` und `docs/API.md` beschrieben.

The platform is designed as an integration layer. Existing bots and working
analysis modules stay separated and are connected through adapters instead of
being overwritten or refactored into one monolith.

## Highlights

- Async orchestration for parallel services
- EventBus based communication
- Safe SharedState snapshots
- Crypto, stock and commodity adapters
- Brain and learning integration
- Persistent decision/outcome linking
- Knowledge Graph with 2D and optional 3D view
- Live Web Control Center on localhost
- Telegram dry-run support
- Unit and integration test suite

## Architecture

```text
main.py
  -> Orchestrator
     -> EventBus
     -> SharedState
     -> HealthMonitor
     -> CryptoAdapter
     -> StockAdapter
     -> CommodityAdapter
     -> BrainAdapter
     -> DecisionSignalAdapter
     -> OutcomeTracker
     -> TelegramAdapter
     -> WebControlServer
```

## Repository Structure

```text
PandorickKi/
|-- adapters/              # Market, Brain, signal, outcome and Telegram adapters
|-- learning_graph/        # Learning Graph and public Knowledge Graph services
|-- strategy_arena/        # Example strategy module
|-- tests/                 # Unit and integration tests
|-- web/                   # Local API, WebSocket manager and Control Center assets
|-- docs/                  # Architecture and repository documentation
|-- main.py                # CLI entrypoint
|-- orchestrator.py        # Async service coordinator
|-- event_bus.py           # Event publishing and subscriptions
|-- shared_state.py        # Thread/async safe platform snapshots
|-- config.py              # Environment based configuration
|-- .env.example           # Safe example configuration
|-- .gitignore             # Keeps runtime data and secrets out of GitHub
|-- requirements.txt       # Python dependency notes
`-- LICENSE
```

Runtime folders such as `data/`, `storage/`, `runtime_logs/` and `backups/`
are intentionally excluded from GitHub because they can contain private Brain
memory, trading history, logs and local machine paths.

## Installation

1. Install Python 3.12 or newer.
2. Clone the repository.
3. Create a local environment file from `.env.example`.
4. Point `PANDORICKKI_CRYPTO_PATH` and `PANDORICKKI_STOCK_PATH` to your local
   external bot folders.
5. Start the platform.

```powershell
python main.py --headless --web
```

Open the Control Center:

```text
http://127.0.0.1:8000
```

## Start Modes

```powershell
python main.py --once
python main.py --live
python main.py --headless
python main.py --live --web
python main.py --headless --web
```

Batch helpers are also included:

```text
start_once.bat
start_live.bat
start_headless.bat
start_pandorick_web.bat
```

## Brain System

The Brain adapter receives normalized decisions and learning events. It keeps
learning separate from the market engines so existing Brain behavior can be
used without changing trading logic.

## Learning System

The learning layer reads real Pandorick event history, decision records and
outcome data. It produces aggregated learning reports and public graph data for
the Control Center without exposing raw internal formulas or secrets.

## Knowledge Graph

PandorickKi includes a public Knowledge Graph API and browser visualization.
The Control Center supports:

- 2D Sigma/WebGL graph
- optional 3D graph view
- cluster grouping
- search and node focus
- hover neighbor highlighting
- public sanitized node and edge payloads

## Trading Engine

The platform coordinates analysis outputs from crypto, stock and commodity
services. Decisions and signals are simulated and tracked for learning. Real
order execution is not enabled by default.

## Control Center

The Web Control Center shows:

- system health
- service status
- crypto, stock and commodity tables
- Brain status
- statistics
- learning report
- Knowledge Graph
- Telegram dry-run status

The web server is local by default and should not be exposed to the public
internet without a separate security review.

## Telegram

Telegram support is controlled by environment variables. Dry-run mode is the
safe default. Tokens and chat IDs must never be committed to GitHub.

## Tests

```powershell
python -m unittest discover tests
python -m compileall .
```

## Roadmap

- Stabilize repository packaging and CI
- Add automated import and secret scanning
- Improve data retention and JSONL rotation policies
- Add stronger provider-health dashboards
- Expand outcome quality tracking
- Add documentation for deployment and recovery

## Safety

PandorickKi is analysis software. It does not provide financial advice and does
not execute real trades by default. Use live trading only after explicit review,
testing and risk controls.
