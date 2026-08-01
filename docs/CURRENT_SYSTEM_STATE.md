# PandorickKi – aktueller Systemzustand

Stand: 31. Juli 2026
Grundlage: aktueller Arbeitsbaum, statische Codeprüfung, lokale HTTP-API und zuletzt tatsächlich ausgeführte Tests.

## Betriebsaktualisierung vom 31. Juli 2026

Nach knapp sechs Tagen Dauerbetrieb war die Crypto-Analyse seit dem 27. Juli ausgefallen, während Aktien weiterliefen. Der externe Crypto-Marktdatenpfad verlangte `requests` und behandelte Spot-Kerzen, Open Interest und Funding als untrennbaren Gesamtaufruf. Die aktuell bereitgestellte Python-Runtime enthielt `requests` nach einem Runtime-Austausch nicht mehr. Der konkrete erste Laufzeitfehler vom 27. Juli war wegen der begrenzten In-Memory-Eventhistorie nicht mehr rekonstruierbar.

Der Live-Crypto-Pfad verwendet jetzt `adapters/crypto_market_data_service.py` aus PandorickKi. Er arbeitet nur mit der Python-Standardbibliothek, lädt Kerzen primär von Binance und ersatzweise von Bitget und behandelt Open Interest sowie Funding als optionale Zusatzdaten. Der externe Legacy-Code wird weiterhin nur für die nicht persistierende Analysepipeline verwendet; dessen `market.py` wird nicht mehr importiert.

Der Dienst läuft seit dem kontrollierten Neustart am 31. Juli 2026 unter der projektlokalen `.venv`. Zwei verifizierte Produktionszyklen lieferten sechs neue Analysen für BTCUSDT, ETHUSDT und XRPUSDT. Crypto meldete `OK`, `healthy=true`, drei Ergebnisse pro Zyklus und keinen neuen Fehler; der historische Crypto-Fehlerzähler blieb während der Verifikation bei 12.024. Telegram blieb deaktiviert und im Dry-Run, ohne versendete Nachrichten.

## Projektziel

PandorickKi ist eine lokal laufende Integrationsplattform für bestehende Crypto-, Aktien- und optionale Rohstoffanalysen. Sie verbindet externe Analyseprojekte über Adapter mit einem synchronen EventBus, persistiert Analyse-, Entscheidungs- und Simulationsdaten und stellt den Zustand im lokalen Control Center bereit. Der PandorickKi-Kern sendet keine Börsenorders und aktiviert keine reale Orderausführung.

## Aktuelle Architektur

Die Anwendung läuft im Wesentlichen als ein Python-Prozess. Der `Orchestrator` verwaltet Adapter und führt deren `run_once()`-Zyklen parallel als AsyncIO-Tasks aus. Die Adapter kommunizieren überwiegend über einen synchronen In-Process-`EventBus`. `SharedState` hält den beobachtbaren Laufzeitzustand; `HealthMonitor` erzeugt einen groben Health-Report. Der Webserver basiert auf `ThreadingHTTPServer` und läuft in einem zusätzlichen Thread.

Die Architektur ist eine Integrations- und Beobachtungsschicht, kein autonomes Handelssystem. `BrainAdapter` und `DecisionSignalAdapter` übernehmen derzeit hauptsächlich Persistenz, Weiterleitung und deterministische Normalisierung, keine unabhängige KI- oder Risikofreigabe.

## Aktive Services

Der Standard-Orchestrator erstellt, abhängig von der Konfiguration:

1. `CryptoAdapter`
2. `BrainAdapter`
3. `DecisionSignalAdapter` als Service `decision_core`
4. `OutcomeTracker`
5. optional `NeuroBrainReceiverAdapter`
6. `CryptoTradeTracker`
7. `StockAdapter`
8. optional `CommodityAdapter`
9. `TelegramAdapter`
10. optional `ControlCenterAdapter`

Beim letzten lokalen API-Abruf am 26. Juli 2026 meldeten Webserver, WebSocket und Statistikdienst `OK`. Brain, Decision Core, Outcome Tracker, NeuroBrain Receiver, Crypto Trade Tracker, Telegram und Control Center meldeten `OK`; Crypto und Stock befanden sich in einem laufenden Adapterzyklus.

## Einstiegspunkte

- `main.py`: CLI und Auswahl zwischen Einmallauf, kontinuierlichem Lauf, Headless- und Webmodus.
- `orchestrator.py`: Lebenszyklus, Adapteraufbau und parallele Zyklen.
- `config.py`: umgebungsbasierte Konfiguration und Pfade.
- `start_once.bat`, `start_live.bat`, `start_headless.bat`, `start_pandorick_web.bat`: Windows-Starthilfen.
- `web/api.py`: Webserver-Lebenszyklus und öffentliche API-Sichten.
- `web/routes.py`: HTTP-Routing und statische Dateien.

## Datenfluss

1. Marktadapter rufen vorhandene externe Analyseprojekte beziehungsweise Preisquellen auf.
2. Crypto und Stock ergänzen OHLCV-Daten optional durch die `FeatureEngine`.
3. Die Adapter publizieren Markt- und Analyseereignisse über den `EventBus`.
4. `BrainAdapter` speichert abgeschlossene Analysen rotierend und publiziert `BRAIN_DECISION_RECEIVED` sowie `AI_LEARNING_UPDATED`.
5. `DecisionSignalAdapter` normalisiert das Brain-Ereignis, erzeugt deterministische IDs und persistiert Decision- und Signal-Ledger.
6. Outcome- und Crypto-Trade-Tracker öffnen und aktualisieren ausschließlich simulierte Trades.
7. Control Center, Statistik, Reports und Graphdienste projizieren den Ereignis- und Persistenzzustand in read-only Sichten.
8. Telegram verarbeitet Analyse- und simulierte Trade-Ereignisse direkt; es liegt derzeit nicht strikt hinter einem finalen Decision-Gate.

## Datenquellen

- Crypto: Binance-Spot-Kerzen mit Bitget-Fallback über den internen `CryptoMarketDataService`; Binance Futures liefert optional Open Interest und Funding. Das externe Legacy-Projekt unter `PANDORICKKI_CRYPTO_PATH` verarbeitet die normalisierten Daten ausschließlich analytisch und nicht persistierend.
- Aktien: externes lokales Stock-Projekt über `PANDORICKKI_STOCK_PATH`.
- Rohstoffe: optionale Preisquelle für konfigurierte Symbole; standardmäßig deaktiviert.
- Interne Historie: JSON-/JSONL-Ledger unter `data/`.
- Learning/Knowledge Graph: Projektionen aus vorhandenen Events, Decisions, Signals und Outcomes.
- NeuroBrain: optionale lokale read-only Datei-Inbox ohne Rückkanal in den Decision Core.

Die Standardpfade für Crypto und Aktien sind rechnergebundene Windows-Pfade und müssen auf anderen Rechnern konfiguriert werden.

## Adapter

- `adapters/crypto_adapter.py`: Crypto-Analyse, Preisstatus, Feature-Anreicherung, genaue Fehlerdiagnose und Events; Feature-Berechnung ist auf die letzten 500 Kerzen begrenzt.
- `adapters/crypto_market_data_service.py`: Abhängigkeitsfreier Candle-Abruf mit Binance/Bitget-Fallback, Retry und optionalem Futures-Kontext.
- `adapters/stock_adapter.py`: Aktienanalyse mit entsprechender Feature-Anreicherung und derselben 500-Kerzen-Grenze.
- `adapters/commodity_adapter.py`: optionale Rohstoffanalyse ohne Feature-Engine-Anbindung.
- `adapters/brain_adapter.py`: Analysepersistenz und Weiterleitung.
- `adapters/decision_signal_adapter.py`: Normalisierung, IDs und Ledger.
- `adapters/outcome_tracker.py`: allgemeine simulierte Outcome-Verfolgung.
- `adapters/crypto_trade_tracker.py`: simulierte Crypto-Trade-Verfolgung.
- `adapters/neurobrain_receiver_adapter.py`: optionale Datei-Inbox mit Topic-Whitelist und Duplikatschutz.
- `adapters/telegram_adapter.py`: Dry-Run oder optionaler Telegram-Versand.
- `adapters/control_center_adapter.py`: kompakte Live-Sicht auf EventBus und SharedState.

## Feature Engine

`features/feature_engine.py` normalisiert OHLCV-Aliase und berechnet Preis-, Return-, Momentum-, Trend-, Volatilitäts-, Volumen-, Kerzenstruktur- und technische Indikatorgruppen. Dazu gehören unter anderem SMA, EMA, ATR, RSI, MACD, ADX, Bollinger, Stochastic, CCI, Williams %R, OBV, MFI, ROC und KAMA.

Live-Adapter verwenden `include_targets=False`; historische Trainingsziele werden damit nicht in den Livepfad gegeben. Es fehlen weiterhin strikte Eingangsvalidierung, Mindestkerzen-/Warmup-Verträge, Feature-Schemaversionierung und eine New-Candle-/Cache-Strategie.

## Brain

`BrainAdapter` abonniert abgeschlossene Crypto-, Stock- und Commodity-Analysen, schreibt sie in datums- und größenrotierte JSONL-Dateien und publiziert Folgeereignisse. Er führt aktuell keine eigene Modellinferenz, Faktenprüfung oder Konfliktauflösung durch.

## Decision Core

`DecisionSignalAdapter` erzeugt aus Brain-Payloads deterministische Decision- und Signal-IDs, normalisiert Markt-, Richtung-, Preis- und Risikofelder und schreibt rotierende JSONL-Ledger. Der Duplikatschutz ist innerhalb der laufenden Instanz in-memory. Eine unabhängige Risiko-Policy, Confidence-Schwelle oder zentrale fachliche Freigabe ist nicht implementiert.

## Outcome Tracker

`OutcomeTracker` und `CryptoTradeTracker` arbeiten ausschließlich simuliert. Valide LONG-/SHORT-Entscheidungen mit Entry-Preis können einen simulierten Trade eröffnen. Preisupdates aktualisieren P/L, Drawdown und Terminalbedingungen wie Stop, TP oder Zeithorizont. Offene Zustände werden als JSON, abgeschlossene Lebenszyklen als rotierende JSONL-Dateien gespeichert.

## Learning und History

Learning Reports, Statistikdienste und Learning/Knowledge Graph aggregieren vorhandene Historien. `AI_LEARNING_UPDATED` bezeichnet derzeit ein Daten-/Projektionsereignis, kein Training oder Update eines ML-Modells. Die Graphdienste unter `learning_graph/` liefern sanitizierte Nodes, Edges, Cluster und Übersichten für API und Browser.

Der Storage-Statistikdienst besitzt inzwischen:

- einen persistenten Ergebnis-Cache `storage/statistics/storage_statistics.json`,
- einen persistenten Dateiindex `storage/statistics/storage_file_index.json`,
- genau einen Hintergrund-Worker mit Sperre,
- kooperative Abbruch- und Timeout-Prüfung,
- inkrementelle JSONL-Offsets,
- atomare Cache-/Index-Schreibvorgänge,
- Metadatenmodus für große SQLite-, JSON-, CSV- und Logdateien,
- ein globales JSONL-Bytebudget pro Scan.

Der Cache bleibt bei Timeout oder Teilfehlern sichtbar. Der laufende Bestand lag beim letzten Abruf bei 7 Ordnern, 93 gecachten Dateien und 4,26 GB. Ein Scan endete dennoch nach 35,236 Sekunden als `TIMEOUT` und bearbeitete 27 von 94 Dateien; das ist ein offener Performancefehler, kein Datenverlustsignal.

## Control Center

Das lokale Control Center wird standardmäßig unter `http://127.0.0.1:8000/` bereitgestellt. Es zeigt Health, Services, Märkte, Brain, Signals, Statistiken, Speicher, Learning Report und Graphen. HTTP-Endpunkte liefern read-only Sichten; `/api/statistics/storage/refresh` startet einen Hintergrundscan und antwortet mit HTTP `202 Accepted`.

Die UI lädt den vollständigen Storage-Snapshot single-flight, zeigt Scanstatus und verwendet Cache-Buster sowie `defer` für lokale Skripte. Live- und Statistik-Broadcasts sind gedrosselt; große interne Felder wie Candles, Features, Steps und Raw Results werden aus Browser-Payloads entfernt, ohne interne Events zu verändern.

Der WebSocket-Client fällt bei `close` auf Polling zurück. Reconnect, mehrfacher Close, `error`-Fallback sowie JSON-/Renderfehler sind noch nicht vollständig robust. Servicezustände berücksichtigen inzwischen zusätzlich das Ergebnis von `adapter.health()`: null Crypto-Ergebnisse bei Fehlern werden als `ERROR` statt fälschlich als `OK` projiziert.

## Telegram

Telegram ist über Umgebungsvariablen steuerbar. Sichere Vorgaben sind `PANDORICKKI_TELEGRAM_ENABLED=0` und `PANDORICKKI_TELEGRAM_DRY_RUN=1`. Tokens und Chat-IDs dürfen nicht versioniert oder dokumentiert werden. Telegram abonniert derzeit Crypto-/Stock-Analysen und simulierte Crypto-Trade-Updates direkt und ist nicht ausschließlich an finale Decision-/Signal-Ereignisse gekoppelt.

## Speicherformate

- JSON: Shared State, offene simulierte Trades, Status- und Cachedateien.
- JSONL: Brain-Ereignisse, Decisions, Signals, Outcomes, Trade-Historie, NeuroBrain-Inbox, Telegram-Dry-Run und Audits.
- Rotierte JSONL: Größen- beziehungsweise datumsbezogene Ledgersegmente.
- SQLite: vorhandene externe beziehungsweise historische Datenbestände; große Dateien werden vom Statistikscanner nur per Metadaten erfasst.
- Statische HTML-/CSS-/JavaScript-Dateien: lokales Control Center und Graphvisualisierung.

Runtime-Verzeichnisse wie `data/`, `storage/`, `runtime_logs/` und `backups/` können private Historien, lokale Pfade oder sensible Betriebsdaten enthalten und dürfen nicht ungefragt gelöscht oder veröffentlicht werden.

## Startbefehle

```powershell
setup_local_env.bat
.\.venv\Scripts\python.exe scripts\runtime_preflight.py
.\.venv\Scripts\python.exe main.py --once
.\.venv\Scripts\python.exe main.py --live
.\.venv\Scripts\python.exe main.py --headless --web
```

Lokales Control Center: `http://127.0.0.1:8000/`

Die Batch-Starter erzeugen die ignorierte projektlokale `.venv` bei Bedarf, installieren `tzdata`, führen den Preflight aus und verwenden danach ausschließlich diese Umgebung. `start_pandorick_web.bat` setzt Telegram ausdrücklich auf deaktiviert und Dry-Run.

## Testbefehle

```powershell
python -m unittest discover -s tests
python -m unittest tests.test_statistics_and_storage tests.test_web_control_center
python -m compileall .
```

Der vollständige Lauf am 31. Juli 2026 bestand mit 200/200 Tests in 61,863 Sekunden. Zusätzlich bestand ein nicht persistierender Live-Crypto-Diagnoselauf mit drei von drei Symbolen sowie die anschließende Verifikation von zwei Produktionszyklen. Die bekannte nicht-deterministische Storage-Shutdown-Race bleibt unabhängig davon offen.

## Bekannte Risiken

1. Der Storage-Worker kann den einsekündigen Shutdown-Join überleben und danach noch in temporäre Verzeichnisse schreiben.
2. Storage-Scans überschreiten im realen Datenbestand weiterhin teilweise das konfigurierte Timeout.
3. Der synchrone EventBus kann Produzenten durch langsame Handler blockieren.
4. WebSocket-Reconnect und Polling-Fallback sind nicht vollständig robust.
5. Brain und Decision Core bieten weniger fachliche Prüfung, als ihre Namen vermuten lassen.
6. Telegram umgeht derzeit eine strikt zentrale finale Freigabekette.
7. Runtime-Ledger wachsen insgesamt ohne zentrale Retention-Policy.
8. Absolute Windows-Pfade begrenzen die Portabilität.
9. Feature-Eingangsdaten werden nicht streng genug validiert.
10. Heartbeats werden nicht automatisch als `STALE` klassifiziert.
11. Der aktuelle Stand ist auf `origin/agent/add-market-feature-engine` veröffentlicht, aber Draft-PR #2 ist noch nicht nach `main` gemergt.
