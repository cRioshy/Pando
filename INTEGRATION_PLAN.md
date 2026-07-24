# PandorickKi Integration Plan

## Phase 2 Status

Status: geplant, noch nicht integriert.

Diese Datei beschreibt die Zielintegration als neues separates Projekt `PandorickKi`.
Die bestehenden Projekte bleiben in Phase 2 unveraendert:

- Crypto: `C:/Users/Admin/Desktop/VIP-Trade-Engine-4.5(Monitor)`
- Stock: `C:/Users/Admin/Documents/Codex/2026-07-09/h/pandorick_stock_bot`
- Assistant/Brain: `C:/Users/Admin/Documents/Codex/2026-07-10/assistant-core-zentrale-koordination-brain-memory/outputs/Pandorick_Jarvis_V1`

Ziel: Die neue Plattform wird spaeter unter `C:/Users/Admin/Desktop/PandorickKi` abgelegt und mit `python main.py` gestartet.

## Grundregel

Bestehender funktionierender Code wird nicht direkt umgeschrieben. Die Integration erfolgt ueber Adapter und gemeinsame Datenmodelle.

## Neue Zielstruktur

```text
PandorickKi/
├── main.py
├── orchestrator.py
├── event_bus.py
├── shared_state.py
├── health_monitor.py
├── config.py
├── README.md
├── INTEGRATION_PLAN.md
│
├── models/
│   ├── __init__.py
│   ├── events.py
│   ├── market.py
│   ├── decisions.py
│   └── health.py
│
├── adapters/
│   ├── __init__.py
│   ├── crypto_service.py
│   ├── stock_service.py
│   ├── brain_adapter.py
│   ├── control_center_adapter.py
│   └── telegram_adapter.py
│
├── services/
│   ├── __init__.py
│   ├── crypto_runner.py
│   ├── stock_runner.py
│   ├── brain_runner.py
│   └── control_runner.py
│
├── tests/
│   ├── __init__.py
│   ├── test_event_bus.py
│   ├── test_adapters.py
│   └── test_integration_full.py
│
└── data/
    ├── shared_state.json
    ├── events.jsonl
    ├── health.json
    └── logs/
```

## Integrationsentscheidungen

Legende:

- `bleibt unveraendert`: Quelle bleibt an Ort und Stelle, keine direkte Aenderung.
- `bekommt Adapter`: Neue Plattform ruft Funktionen ueber Adapter auf.
- `wird neu erstellt`: Neue Datei in `PandorickKi`.
- `wird ersetzt`: Funktion wird in der neuen Plattform nicht direkt verwendet.
- `wird verschoben`: Erst nach Freigabe in neues Projekt kopieren.
- `wird umbenannt`: Nur im neuen Projekt, um Namenskonflikte zu vermeiden.

## Neue PandorickKi-Dateien

| Datei | Entscheidung | Begruendung |
|---|---|---|
| `main.py` | wird neu erstellt | Neuer gemeinsamer Startpunkt fuer Crypto, Stock, Brain und ControlCenter. |
| `orchestrator.py` | wird neu erstellt | Koordiniert parallele Services und Shutdown. |
| `event_bus.py` | wird neu erstellt | Einheitlicher Event-Transport zwischen BotPy/Krypto, Stock, Brain, ControlCenter und Telegram. |
| `shared_state.py` | wird neu erstellt | Gemeinsamer Statusspeicher fuer laufende Services. |
| `health_monitor.py` | wird neu erstellt | Ueberwacht Laufzeit, Fehler, Service-Status und Speicherdateien. |
| `config.py` | wird neu erstellt | Zentrale Pfade und ENV-basierte Einstellungen ohne hardcoded Tokens. |
| `README.md` | wird neu erstellt | Start, Architektur und Sicherheitsregeln dokumentieren. |
| `INTEGRATION_PLAN.md` | wird neu erstellt | Dieser Plan. |
| `models/__init__.py` | wird neu erstellt | Paketmarker. |
| `models/events.py` | wird neu erstellt | Gemeinsame Eventtypen. |
| `models/market.py` | wird neu erstellt | Normalisierte Crypto- und Stock-Marktdaten. |
| `models/decisions.py` | wird neu erstellt | Einheitliches Decision-Modell fuer beide Marktarten. |
| `models/health.py` | wird neu erstellt | Health-/Statusmodell. |
| `adapters/__init__.py` | wird neu erstellt | Paketmarker. |
| `adapters/crypto_service.py` | wird neu erstellt | Adapter um Crypto-Code ohne direkten Import von `bot.py`. |
| `adapters/stock_service.py` | wird neu erstellt | Adapter fuer `pandorick_stock_bot` mit `run_once`/Service-Funktionen. |
| `adapters/brain_adapter.py` | wird neu erstellt | Normalisiert Crypto-Brain, Stock-Brain und Assistant-Core Brain. |
| `adapters/control_center_adapter.py` | wird neu erstellt | Liefert konsolidierte Statusausgabe. |
| `adapters/telegram_adapter.py` | wird neu erstellt | Sendet nur fertige freigegebene Nachrichten. |
| `services/crypto_runner.py` | wird neu erstellt | Fuehrt Crypto-Zyklen kontrolliert aus. |
| `services/stock_runner.py` | wird neu erstellt | Fuehrt Stock-Zyklen kontrolliert aus. |
| `services/brain_runner.py` | wird neu erstellt | Uebergibt abgeschlossene Entscheidungen an KI/Brain. |
| `services/control_runner.py` | wird neu erstellt | Aktualisiert ControlCenter. |
| `tests/test_event_bus.py` | wird neu erstellt | Testet Event-Publish/Subscribe. |
| `tests/test_adapters.py` | wird neu erstellt | Testet Adapter mit Testdaten. |
| `tests/test_integration_full.py` | wird neu erstellt | Vollstaendiger Test fuer beide Marktarten und Shutdown. |

## Crypto-Projekt: Datei-fuer-Datei-Plan

Quelle: `C:/Users/Admin/Desktop/VIP-Trade-Engine-4.5(Monitor)`

| Datei | Entscheidung | Begruendung |
|---|---|---|
| `bot.py` | bekommt Adapter / wird nicht direkt importiert | Enthalt Top-Level-Startlogik, Telegram-Startmeldung und `while True`; direkter Import wuerde blockieren. |
| `config.py` | wird ersetzt in neuer Plattform | Enthalt hardcoded Telegram-Credentials; neue Plattform nutzt ENV-Konfiguration. |
| `analysis.py` | bleibt unveraendert / bekommt Adapter | Bestehende Analysefunktion kann ueber CryptoService genutzt werden. |
| `indicators.py` | bleibt unveraendert / bekommt Adapter | Funktionierende technische Indikatoren bleiben erhalten. |
| `strategy.py` | bleibt unveraendert / bekommt Adapter | `analyse_coin` ist Kernfunktion; muss ohne `bot.py` nutzbar gemacht werden. |
| `risk.py` | bleibt unveraendert / bekommt Adapter | Bestehende Trade-Level-Berechnung weiterverwenden. |
| `risk_manager.py` | bleibt unveraendert / bekommt Adapter | Neuere modulare Risk-Schicht kann spaeter eingebunden werden. |
| `market.py` | bleibt unveraendert / bekommt Adapter | Binance-Calls bleiben gekapselt; Adapter faengt Fehler/Timeouts ab. |
| `market_structure.py` | bleibt unveraendert / bekommt Adapter | Liefert OI/Funding/Marktstruktur fuer Crypto. |
| `market_filter.py` | bleibt unveraendert / bekommt Adapter | Bestehende Filterlogik weiterverwenden. |
| `market_memory.py` | bleibt unveraendert / bekommt Adapter | Nutzt globale `history`; Adapter muss Lade-/Speicherreihenfolge kontrollieren. |
| `market_state.py` | bleibt unveraendert / bekommt Adapter | Bestehendes Faktenmodell fuer Pandorick-Pipeline. |
| `market_memory.py` | bleibt unveraendert / bekommt Adapter | Speichert `market_history.json`, nicht verschieben ohne Migration. |
| `market_structure.py` | bleibt unveraendert / bekommt Adapter | Direkte API-Aufrufe bleiben isoliert. |
| `memory.py` | bleibt unveraendert / bekommt Adapter | CSV-History bleibt vorerst Quelle fuer Crypto-Momentum. |
| `brain.py` | bleibt unveraendert / bekommt Adapter | Globaler Brain-State; direkte Integration nur ueber kontrollierten Adapter. |
| `brain_learning.py` | bleibt unveraendert / bekommt Adapter | Lernt aus Trade-Ergebnissen; Adapter liefert abgeschlossene Entscheidungen. |
| `brain_pattern_confidence.py` | bleibt unveraendert / bekommt Adapter | Pattern-Wissen bleibt im Crypto-System. |
| `brain_signal_stability.py` | bleibt unveraendert / bekommt Adapter | Signalstabilitaet kann in normales Decision-Modell uebernommen werden. |
| `decision_core.py` | bleibt unveraendert / bekommt Adapter | Bestehende Decision-Logik nicht ersetzen; spaeter normalisieren. |
| `probability.py` | bleibt unveraendert / bekommt Adapter | Rechenlogik bleibt erhalten. |
| `sensor_engine.py` | bleibt unveraendert / bekommt Adapter | Sensorwerte werden in gemeinsame Modelle uebersetzt. |
| `precedence.py` | bleibt unveraendert / bekommt Adapter | Trade-Lifecycle mit TP/Stop-Regeln bleibt im Crypto-System. |
| `trade_manager.py` | bleibt unveraendert / bekommt Adapter | Neuere Trade-Management-Modelle koennen spaeter verbunden werden. |
| `statistics.py` | bleibt unveraendert / bekommt Adapter | Statistik wird fuer ControlCenter gelesen. |
| `monitor.py` | bleibt unveraendert / bekommt Adapter | Bestehende CPU/RAM/Brain/OpenTrades-Ausgabe wird nicht direkt zur Hauptsteuerung. |
| `telegram.py` | bleibt unveraendert / bekommt Adapter | Formatierung/Audit kann weiterverwendet werden, Versand zentralisieren. |
| `telegram_builder.py` | bleibt unveraendert / bekommt Adapter | Baut fertige Crypto-Nachrichten. |
| `telegram_send.py` | wird ersetzt in neuer Plattform | Direkter Versand mit hardcoded Config wird durch `telegram_adapter.py` ersetzt. |
| `logger.py` | bleibt unveraendert / bekommt Adapter | Schreibt `history.csv`, vorerst nicht migrieren. |
| `crash_logger.py` | bleibt unveraendert / bekommt Adapter | Fehlerlogik kann von CryptoRunner weiter genutzt werden. |
| `audit_log.py` | bleibt unveraendert / bekommt Adapter | Audit-JSONL bleibt bestehen. |
| `pandorick_pipeline.py` | bleibt unveraendert / bekommt Adapter | Wertvoller modularer Pfad fuer spaetere CryptoService-Anbindung. |
| `models.py` | bleibt unveraendert / bekommt Adapter | Crypto-spezifische Modelle werden in gemeinsame Modelle uebersetzt. |
| `state.py` | bleibt unveraendert / bekommt Adapter | `last_state` bleibt kapselungsbeduerftig. |
| `tracker.py` | bleibt unveraendert / bekommt Adapter | Nur nach Bedarf in Trade-Lifecycle einbinden. |
| `PANDORICK_ARCHITECTURE.md` | bleibt unveraendert | Dokumentation, keine Laufzeitintegration. |
| `requirements.txt` | bleibt unveraendert / wird ausgewertet | Abhaengigkeiten in neue Plattform uebernehmen: `requests`, `pandas`, `numpy`, `ta`, `psutil`. |
| `brain.json` | bleibt unveraendert / bekommt Adapter | Aktive Crypto-Brain-Datenquelle; keine direkte Migration ohne Backup. |
| `precedence.json` | bleibt unveraendert / bekommt Adapter | Aktiver Trade-Zustand. |
| `market_history.json` | bleibt unveraendert / bekommt Adapter | Aktive Markthistorie. |
| `history.csv` | bleibt unveraendert / bekommt Adapter | Aktive Analysehistorie. |
| `patterns.json` | bleibt unveraendert / bekommt Adapter | Aktive Pattern-Daten. |
| `pandorick_audit.jsonl` | bleibt unveraendert / bekommt Adapter | Audit-Log bleibt Quelle fuer Auswertung. |
| `crash.log` | bleibt unveraendert | Nur lesen/anzeigen im HealthMonitor. |
| Backup-Ordner `_backup_*` | bleibt unveraendert | Nicht integrieren, nur als Sicherheitskopien erhalten. |
| `__pycache__/` | bleibt unveraendert / wird ignoriert | Keine Integration. |

## Stock-Projekt: Datei-fuer-Datei-Plan

Quelle: `C:/Users/Admin/Documents/Codex/2026-07-09/h/pandorick_stock_bot`

| Datei | Entscheidung | Begruendung |
|---|---|---|
| `bot_stock.py` | bekommt Adapter | Aktueller Stock-Startpunkt; neue Plattform startet nicht direkt per CLI, sondern ueber Adapter. |
| `main.py` | bekommt Adapter | `run_once` ist nutzbar; `run_forever` nicht direkt importieren fuer parallelen Orchestrator. |
| `config.py` | bekommt Adapter / wird ersetzt in neuer Plattform | Stock-Konfiguration bleibt Quelle; gemeinsame Plattform hat eigene Pfade. |
| `stock_data.py` | bleibt unveraendert / bekommt Adapter | Platzhalter-Provider und Snapshot-Modell bleiben nutzbar. |
| `stock_analyse.py` | bleibt unveraendert / bekommt Adapter | Technische Aktienanalyse weiterverwenden. |
| `stock_fundamentals.py` | bleibt unveraendert / bekommt Adapter | Fundamental-Platzhalter weiterverwenden, spaeter echte API. |
| `stock_market_context.py` | bleibt unveraendert / bekommt Adapter | Marktumfeld-Platzhalter weiterverwenden. |
| `stock_strategy.py` | bleibt unveraendert / bekommt Adapter | LONG/HOLD/SHORT-Strategie weiterverwenden. |
| `stock_risk.py` | bleibt unveraendert / bekommt Adapter | Entry/Stop/TP/CRV weiterverwenden. |
| `stock_precedence.py` | bleibt unveraendert / bekommt Adapter | Aktien-Precedence in gemeinsame Trade-Events uebersetzen. |
| `stock_brain.py` | bleibt unveraendert / bekommt Adapter | Stock-Brain mit 500 Memorys pro Aktie bleibt getrennt. |
| `stock_brain_knowledge.py` | bleibt unveraendert / bekommt Adapter | Langzeitwissen in BrainAdapter aufnehmen. |
| `stock_patterns.py` | bleibt unveraendert / bekommt Adapter | Pattern-Daten in gemeinsame Events uebersetzen. |
| `stock_probability.py` | bleibt unveraendert / bekommt Adapter | Signalqualitaet/Hitrate fuer gemeinsame Decisions nutzbar. |
| `stock_monitor.py` | bleibt unveraendert / bekommt Adapter | Statuswerte fuer HealthMonitor nutzbar. |
| `brain.py` | bleibt unveraendert / bekommt Adapter | Lokale Stock-Brain-Basisklasse. |
| `brain_learning.py` | bleibt unveraendert / bekommt Adapter | Paper-Learning bleibt getrennt von Crypto. |
| `decision_core.py` | bleibt unveraendert / bekommt Adapter | Stock-Decision in gemeinsames Decision-Modell uebersetzen. |
| `market_state.py` | bleibt unveraendert / bekommt Adapter | Faktenebene fuer Aktien bleibt erhalten. |
| `probability.py` | bleibt unveraendert / bekommt Adapter | Vollstaendige Rechenschritte bleiben erhalten. |
| `risk_manager.py` | bleibt unveraendert / bekommt Adapter | Stock-Risk-Freigabe weiterverwenden. |
| `sensor_engine.py` | bleibt unveraendert / bekommt Adapter | Snapshot-Sammlung in StockService. |
| `statistics.py` | bleibt unveraendert / bekommt Adapter | Laufstatistiken fuer ControlCenter. |
| `control_unit.py` | bekommt Adapter | Konsolenausgabe wird in ControlCenter ueberfuehrt. |
| `telegram.py` | bleibt unveraendert / bekommt Adapter | Nur Formatierung, Versand zentral ueber `telegram_adapter.py`. |
| `trade_manager.py` | bleibt unveraendert / bekommt Adapter | Stock-Trade-Plans bleiben nicht-exekutierend. |
| `market.py` | bleibt unveraendert / bekommt Adapter | Boersenzeit/Session-Logik weiterverwenden. |
| `README.md` | bleibt unveraendert | Dokumentation des separaten Stock-Bots. |
| `data_stock/stock_brain.json` | bleibt unveraendert / bekommt Adapter | Aktive Stock-Brain-Datenquelle. |
| `data_stock/stock_decisions.json` | bleibt unveraendert / bekommt Adapter | Aktive Stock-Decision-History. |
| `data_stock/stock_history.json` | bleibt unveraendert / bekommt Adapter | Aktive Stock-Markthistorie. |
| `data_stock/stock_precedence.json` | bleibt unveraendert / bekommt Adapter | Aktive Stock-Precedence-History. |
| `data_stock/stock_patterns.json` | bleibt unveraendert / bekommt Adapter | Aktive Pattern-/Strategie-History. |
| `data_stock/stock_knowledge.json` | bleibt unveraendert / bekommt Adapter | Aktives Langzeitwissen. |
| `data_stock/stock_weights.json` | bleibt unveraendert / bekommt Adapter | Gewichtungen fuer Stock-Wahrscheinlichkeit. |
| `data_stock/stock_logs.json` | bleibt unveraendert / bekommt Adapter | Laufprotokolle. |
| `data_stock/backups/` | bleibt unveraendert | Backup-Ziel, nicht automatisch veraendern. |
| `data/` | bleibt unveraendert / wird ignoriert | Alter Stock-Datenordner; nicht fuer neue Integration verwenden, ausser explizit gewuenscht. |
| `__pycache__/` | bleibt unveraendert / wird ignoriert | Keine Integration. |

## Assistant-Core: Datei-fuer-Datei-Plan

Quelle: `C:/Users/Admin/Documents/Codex/2026-07-10/assistant-core-zentrale-koordination-brain-memory/outputs/Pandorick_Jarvis_V1`

| Datei | Entscheidung | Begruendung |
|---|---|---|
| `main.py` | bleibt unveraendert / bekommt Adapter | CLI-Terminal-Assistant nicht direkt starten; BrainAdapter nutzt interne Klassen. |
| `config.py` | bleibt unveraendert / bekommt Adapter | ENV-basierte Settings sind gutes Muster fuer neue Plattform. |
| `README.md` | bleibt unveraendert | Dokumentation. |
| `ROADMAP.md` | bleibt unveraendert | Dokumentation. |
| `core/assistant_core.py` | bekommt Adapter | Zentrale Assistant-Logik kann ueber BrainAdapter angesprochen werden. |
| `core/command_router.py` | bleibt unveraendert / bekommt Adapter | Command-Intent-Logik bleibt getrennt von Event-Logik. |
| `core/module_manager.py` | bleibt unveraendert / bekommt Adapter | Module koennen spaeter ueber AssistantCore genutzt werden. |
| `brain/brain.py` | bekommt Adapter | KI-Entscheidung/Response-Composition fuer abgeschlossene Events. |
| `brain/decision_core.py` | bleibt unveraendert / bekommt Adapter | Assistant-Decision-Modell bleibt getrennt von Trading-Decision. |
| `brain/facts_engine.py` | bleibt unveraendert / bekommt Adapter | Kann Event-Kontext aufnehmen, wenn erweitert. |
| `brain/probability.py` | bleibt unveraendert / bekommt Adapter | Confidence-Modell fuer Assistant-Entscheidungen. |
| `brain/reasoning_engine.py` | bleibt unveraendert / bekommt Adapter | Sprach-/Intent-Reasoning bleibt nutzbar. |
| `memory/memory_manager.py` | bleibt unveraendert / bekommt Adapter | SQLite-Memory bleibt aktiv, neue Plattform uebergibt nur fertige Interaktionen/Entscheidungen. |
| `interfaces/terminal_interface.py` | bleibt unveraendert / wird ersetzt in neuer Plattform | Neue Plattform braucht keine blockierende Terminal-Loop. |
| `modules/pandorick_bot.py` | bleibt unveraendert / bekommt Adapter | Bereits Binance-MarketService-basiert; kann als separate Crypto-Analysequelle dienen. |
| `modules/telegram_module.py` | bleibt unveraendert / wird ersetzt in neuer Plattform | Telegram ist dort noch Stub; zentraler TelegramAdapter uebernimmt Versand. |
| `modules/system_control.py` | bleibt unveraendert / bekommt Adapter | Kann spaeter ControlCenter-Befehle ergaenzen. |
| `modules/weather.py` | bleibt unveraendert / wird ignoriert | Nicht Teil der Trading-Integration. |
| `modules/notes.py` | bleibt unveraendert / wird ignoriert | Nicht Teil der Trading-Integration, ausser fuer Memory-Notizen. |
| `modules/fallback.py` | bleibt unveraendert | Assistant-intern. |
| `modules/base.py` | bleibt unveraendert / bekommt Adapter | ModuleResult kann in Adapter uebersetzt werden. |
| `market/binance_client.py` | bleibt unveraendert / bekommt Adapter | Alternative Crypto-Datenquelle ohne `requests`. |
| `market/market_service.py` | bleibt unveraendert / bekommt Adapter | Modularer Crypto-Service kann fuer Integration sehr nuetzlich sein. |
| `market/indicators.py` | bleibt unveraendert / bekommt Adapter | Assistant-Core-eigene Indikatoren. |
| `market/market_decision.py` | bleibt unveraendert / bekommt Adapter | Assistant-Core-eigene MarketDecision. |
| `market/risk_manager.py` | bleibt unveraendert / bekommt Adapter | Assistant-Core-eigener RiskManager. |
| `security/permissions.py` | bleibt unveraendert / bekommt Adapter | Kann spaeter riskante Aktionen blockieren. |
| `tests/test_market_service.py` | bleibt unveraendert / wird als Referenz genutzt | Teststil fuer neue Tests uebernehmen. |
| `memory/jarvis.db` | bleibt unveraendert / bekommt Adapter | SQLite-DB wird vom Assistant-Core verwaltet. |
| `outputs/` oberhalb von `Pandorick_Jarvis_V1` | bleibt unveraendert | Artefaktbereich, nicht direkt integrieren. |
| `.git`, `.codex`, `.agents` | bleibt unveraendert / wird ignoriert | Projektmetadaten. |

## Namenskonflikte

Diese Namen existieren mehrfach und duerfen in `PandorickKi` nicht ungefiltert in denselben Python-Pfad kopiert werden:

- `brain.py`
- `config.py`
- `market.py`
- `market_state.py`
- `decision_core.py`
- `probability.py`
- `risk_manager.py`
- `statistics.py`
- `telegram.py`
- `trade_manager.py`

Loesung:

- Bestehende Projekte bleiben in eigenen Quellordnern.
- Neue Plattform importiert sie nur ueber Adapter mit expliziten Pfaden oder Package-Isolierung.
- Gemeinsame Modelle liegen unter `PandorickKi/models`.

## Bibliotheken

| Quelle | Bibliotheken |
|---|---|
| Crypto | `requests`, `pandas`, `numpy`, `ta`, `psutil` |
| Stock | Standardbibliothek aktuell ausreichend |
| Assistant-Core | Standardbibliothek, `sqlite3`, `urllib` |

Risiko:

- Neue Plattform muss fehlende Crypto-Abhaengigkeiten erkennen und klar melden.
- Tests sollen ohne echte Netzwerkcalls laufen.

## Datenbanken und Dateien

| Bereich | Datei | Umgang |
|---|---|---|
| Crypto | `brain.json` | Lesen/Schreiben nur ueber CryptoAdapter/BrainAdapter. |
| Crypto | `precedence.json` | Lesen/Schreiben nur ueber CryptoAdapter. |
| Crypto | `history.csv` | Lesen fuer Momentum/Statistik, nicht migrieren. |
| Crypto | `market_history.json` | Lesen/Schreiben nur ueber CryptoAdapter. |
| Crypto | `patterns.json` | PatternAdapter/BrainAdapter. |
| Crypto | `pandorick_audit.jsonl` | Nur fuer Audit/Health lesen. |
| Stock | `data_stock/*.json` | StockAdapter nutzt vorhandene Dateien. |
| Assistant | `memory/jarvis.db` | BrainAdapter nutzt Assistant-Core MemoryManager. |
| PandorickKi | `data/events.jsonl` | Neu, fuer gemeinsame Events. |
| PandorickKi | `data/shared_state.json` | Neu, fuer gemeinsamen Status. |

## Telegram-Integration

Aktueller Zustand:

- Crypto sendet direkt ueber `telegram_send.py`.
- Crypto Token/Chat-ID sind hardcoded in `config.py`.
- Stock hat nur Placeholder-Formatierung.
- Assistant-Core hat ENV-basierte Telegram-Settings, aber Versand ist Stub.

Ziel:

- `telegram_adapter.py` ist die einzige sendende Stelle.
- Token und Chat-ID kommen aus ENV.
- Telegram erhaelt nur fertige Nachrichten-Events.
- Keine halbfertigen Analyse-Events versenden.

Sicherheitsmassnahme:

- Der bestehende Crypto-Telegram-Token sollte rotiert werden, da er im Quellcode steht.

## API-Anbieter

| Bereich | Anbieter |
|---|---|
| Crypto Altbestand | Binance Spot/Futures via `requests` |
| Assistant-Core Crypto | Binance Spot/Futures via `urllib` |
| Stock | Placeholder-Provider, spaeter echter Stock-API-Anbieter |
| Telegram | Telegram Bot API |

Ziel:

- API-Zugriffe werden ueber Adapter gekapselt.
- Testmodus nutzt Testdaten und keine Live-Requests.

## Risiken vor Phase 3

1. `bot.py` darf nicht direkt importiert werden.
2. Gleiche Modulnamen koennen falsche Imports ausloesen.
3. Crypto nutzt globale Zustandslisten und globale Brain-Dicts.
4. Telegram-Credentials sind im Crypto-Code hardcoded.
5. Aktive JSON/CSV-Dateien koennen gross werden und sollten nicht blind kopiert werden.
6. Assistant-Core ist command-orientiert, die neue Plattform braucht Event-Orientierung.
7. Stock-Daten sind derzeit Placeholder, nicht echter Marktfeed.

## Phase 3 Vorschlag

Betroffene neue Dateien:

- `main.py`
- `orchestrator.py`
- `event_bus.py`
- `shared_state.py`
- `health_monitor.py`
- `models/events.py`
- `models/market.py`
- `models/decisions.py`
- `models/health.py`
- `adapters/crypto_service.py`
- `adapters/stock_service.py`
- `adapters/brain_adapter.py`
- `adapters/control_center_adapter.py`

Warum notwendig:

- Gemeinsames Grundsystem schaffen, ohne bestehende Bots zu veraendern.

Risiken:

- Adapter duerfen keine Endlosschleifen aus Altprojekten ausloesen.
- Tests muessen mit Testdaten laufen.

Test:

- `python -m unittest discover tests`
- Import-Test aller neuen Module.
- EventBus-Test mit Fake-Crypto- und Fake-Stock-Events.
