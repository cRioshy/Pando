# PandorickKi – aktueller Systemzustand

Stand: 1. August 2026
Grundlage: aktueller Arbeitsbaum, statische Codeprüfung, lokale HTTP-API und zuletzt tatsächlich ausgeführte Tests.

Der Outcome-Zeitstempel-Fix wurde am 1. August 2026 kontrolliert live gestartet. Nach vier vollständigen Crypto-Heartbeats meldeten Plattform und alle zehn Services `OK`. Der dauerhafte Fingerprint des früheren Zeitstempelfehlers blieb unverändert bei 158 Vorkommen und seinem letzten Auftreten um 17:13:29 UTC; es entstand kein neues `OUTCOME_TRACKER_ERROR`. Das Journal meldete null Schreibfehler. Telegram blieb deaktiviert, im Dry-Run und bei null versendeten Nachrichten. Storage verarbeitete 114/114 Dateien in 2,275 Sekunden ohne Scannerfehler.

Der neue Journalstand wurde am 1. August 2026 kontrolliert live gestartet. Nach mindestens zwei vollständigen Zyklen meldeten Plattform und alle zehn sichtbaren Services `OK`; `service_error_journal` war gesund, hatte null Schreibfehler und drei Vorkommen eines Fehlerfingerprints erfasst. Crypto zeigte drei und Stock fünf Analysen. Telegram blieb deaktiviert, im Dry-Run und bei null versendeten Nachrichten. Der Storage-Scan schloss 110/110 Dateien in 2,865 Sekunden ab; `DEGRADED` stammt weiterhin aus den bekannten Datenwarnungen, nicht aus einem Scannerfehler.

## Betriebsaktualisierung vom 1. August 2026

PandorickKi wurde nach Veröffentlichung der Scanner-Instrumentierung kontrolliert neu gestartet. Der eingebaute Stop-Befehl wurde um 15:32 Uhr Europe/Berlin akzeptiert; der Prozess beendete sich ohne erzwungenen Prozessabbruch nach dem laufenden 60-Sekunden-Zyklusintervall. Der Runtime-Preflight bestand mit Python 3.12.13. Der neue Webdienst läuft seit 15:34:40 Uhr über die projektlokale `.venv` mit Telegram deaktiviert und im Dry-Run.

Zwei vollständige Produktionszyklen wurden anschließend verifiziert. Gesamt-Health und alle neun Services meldeten `OK`; Crypto lieferte je Zyklus drei Ergebnisse, Stock fünf Ergebnisse und die neue Sitzung erzeugte keine Servicefehler. BTCUSDT, ETHUSDT und XRPUSDT zeigten aktuelle Preise. Telegram blieb `enabled=false`, `dry_run=true` und `messages_sent=0`. Der Storage-Scan bearbeitete 106/106 physische Dateien in 2,416 Sekunden, meldete verifizierte Summen und erhöhte den kumulativen JSONL-Fortschritt auf 9,20 % beziehungsweise 15/59 vollständige Dateien. `DEGRADED` bleibt wegen laufender Nachindexierung und zwei bereits dokumentierter fehlerhafter Stock-JSON-Dateien erwartbar. Das Control Center zeigte die neuen Metriken per WebSocket ohne Browser-Konsolenfehler.

## Betriebsaktualisierung vom 31. Juli 2026

Nach knapp sechs Tagen Dauerbetrieb war die Crypto-Analyse seit dem 27. Juli ausgefallen, während Aktien weiterliefen. Der externe Crypto-Marktdatenpfad verlangte `requests` und behandelte Spot-Kerzen, Open Interest und Funding als untrennbaren Gesamtaufruf. Die aktuell bereitgestellte Python-Runtime enthielt `requests` nach einem Runtime-Austausch nicht mehr. Der konkrete erste Laufzeitfehler vom 27. Juli war wegen der begrenzten In-Memory-Eventhistorie nicht mehr rekonstruierbar.

Der Live-Crypto-Pfad verwendet jetzt `adapters/crypto_market_data_service.py` aus PandorickKi. Er arbeitet nur mit der Python-Standardbibliothek, lädt Kerzen primär von Binance und ersatzweise von Bitget und behandelt Open Interest sowie Funding als optionale Zusatzdaten. Der externe Legacy-Code wird weiterhin nur für die nicht persistierende Analysepipeline verwendet; dessen `market.py` wird nicht mehr importiert.

Der Dienst läuft seit dem kontrollierten Neustart am 31. Juli 2026 unter der projektlokalen `.venv`. Zwei verifizierte Produktionszyklen lieferten sechs neue Analysen für BTCUSDT, ETHUSDT und XRPUSDT. Crypto meldete `OK`, `healthy=true`, drei Ergebnisse pro Zyklus und keinen neuen Fehler; der historische Crypto-Fehlerzähler blieb während der Verifikation bei 12.024. Telegram blieb deaktiviert und im Dry-Run, ohne versendete Nachrichten.

## Projektziel

PandorickKi ist eine lokal laufende Integrationsplattform für bestehende Crypto-, Aktien- und optionale Rohstoffanalysen. Sie verbindet externe Analyseprojekte über Adapter mit einem synchronen EventBus, persistiert Analyse-, Entscheidungs- und Simulationsdaten und stellt den Zustand im lokalen Control Center bereit. Der PandorickKi-Kern sendet keine Börsenorders und aktiviert keine reale Orderausführung.

## Aktuelle Architektur

Die Anwendung läuft im Wesentlichen als ein Python-Prozess. Der `Orchestrator` verwaltet Adapter und führt deren `run_once()`-Zyklen parallel als AsyncIO-Tasks aus. Die Adapter kommunizieren überwiegend über einen synchronen In-Process-`EventBus`. Ein `ServiceErrorJournal` hört ausschließlich auf Fehlerereignisse und persistiert daraus kompakte, secret-gefilterte Projektionen. `SharedState` hält den beobachtbaren Laufzeitzustand; `HealthMonitor` erzeugt einen groben Health-Report. Der Webserver basiert auf `ThreadingHTTPServer` und läuft in einem zusätzlichen Thread.

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

Zusätzlich startet der Standard-Orchestrator das interne `ServiceErrorJournal` vor den Adaptern und stoppt es nach ihnen. Es erscheint als Service `service_error_journal`, ist aber kein zyklischer Marktadapter. Konfiguration: standardmäßig aktiv, 5 MiB je aktive Datei, höchstens vier Archive und höchstens 500 zusammengefasste Fehlerfingerprints.

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
4. Fehlerereignisse (`SYSTEM_ERROR`, `service.error` und Themen mit Suffix `_ERROR`) werden als versionierte Projektion journalisiert; vollständige Payloads und externe Antworten werden nicht übernommen.
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

`BrainAdapter` abonniert abgeschlossene Crypto-, Stock- und Commodity-Analysen, projiziert jede neue Analyse einmal auf `pandorickki.compact-market-event` Version 1, schreibt diese Sicht in datums- und größenrotierte JSONL-Dateien und publiziert dieselbe Sicht als `BRAIN_DECISION_RECEIVED`. Quell-Event-ID, Markt-/Preis-/Risiko-/Zeitfelder und kompakte Ersatzfelder bleiben erhalten; Raw Results, Features, Diagnostik und Kerzen werden nicht neu in Brain-History übernommen. Er führt aktuell keine eigene Modellinferenz, Faktenprüfung oder Konfliktauflösung durch.

Der versionierte kompakte Event-Payload-Vertrag liegt in `event_payload_contract.py` und `docs/EVENT_PAYLOAD_CONTRACT.md`. Version 1 erhält die von Brain, Decision Core, Trackern, Learning, Control Center, Telegram und NeuroBrain tatsächlich benötigten Felder, verbietet aber `raw_result`, Feature-/Diagnostikblöcke und Kerzen. Brain ist die erste aktiv migrierte Producer-/Persistenzgrenze. Decision-/Signal- und NeuroBrain-Persistenz reichen noch nicht überall ausschließlich die Projektion weiter.

## Decision Core

`DecisionSignalAdapter` erzeugt aus Brain-Payloads deterministische Decision- und Signal-IDs, normalisiert Markt-, Richtung-, Preis- und Risikofelder und schreibt rotierende JSONL-Ledger. Der Duplikatschutz ist innerhalb der laufenden Instanz in-memory. Eine unabhängige Risiko-Policy, Confidence-Schwelle oder zentrale fachliche Freigabe ist nicht implementiert.

## Outcome Tracker

`OutcomeTracker` und `CryptoTradeTracker` arbeiten ausschließlich simuliert. Valide LONG-/SHORT-Entscheidungen mit Entry-Preis können einen simulierten Trade eröffnen. Preisupdates aktualisieren P/L, Drawdown und Terminalbedingungen wie Stop, TP oder Zeithorizont. Offene Zustände werden als JSON, abgeschlossene Lebenszyklen als rotierende JSONL-Dateien gespeichert. Beim Berechnen von Laufzeiten werden historische ISO-Zeitstempel ohne Offset rückwärtskompatibel als UTC interpretiert; die gespeicherten Originalwerte werden nicht umgeschrieben.

Der Crypto Trade Tracker bevorzugt für die Stop-Berechnung die kompakten Felder `market_context.recent_swing_low` beziehungsweise `recent_swing_high`. Vorhandene Events und History ohne diese Felder bleiben über den bisherigen Kerzenpfad in `raw_result` lesbar.

## Learning und History

Learning Reports, Statistikdienste und Learning/Knowledge Graph aggregieren vorhandene Historien. `AI_LEARNING_UPDATED` bezeichnet derzeit ein Daten-/Projektionsereignis, kein Training oder Update eines ML-Modells. Die Graphdienste unter `learning_graph/` liefern sanitizierte Nodes, Edges, Cluster und Übersichten für API und Browser.

Der Learning Graph bevorzugt das kompakte Ergebnisfeld `public_result`. Bei älteren Brain-Datensätzen ohne dieses Feld bleibt `raw_result.result` als reiner Legacy-Lesepfad erhalten.

Der Storage-Statistikdienst besitzt inzwischen:

- einen persistenten Ergebnis-Cache `storage/statistics/storage_statistics.json`,
- einen persistenten Dateiindex `storage/statistics/storage_file_index.json`,
- genau einen Hintergrund-Worker mit Sperre,
- kooperative Abbruch- und Timeout-Prüfung,
- inkrementelle JSONL-Offsets,
- atomare Cache-/Index-Schreibvorgänge,
- Metadatenmodus für große SQLite-, JSON-, CSV- und Logdateien,
- ein globales JSONL-Bytebudget pro Scan,
- ein anhand des realen Bestands vermessenes Standardbudget von 64 MiB pro Lauf,
- getrennte Phasenlaufzeiten für Zielermittlung, Pfadauflösung, Metadaten, Fingerprint, Dateiverarbeitung, Index- und Cachepersistenz,
- kumulativen JSONL-Fortschritt mit Gesamt-/indexierten/restlichen Bytes, vollständigen Dateien sowie geschätzten Restläufen und Restzeit,
- einen geschützten Lebenszyklus: Nach `close()` werden keine neuen Scans akzeptiert und laufende Hintergrund- oder synchrone Scans sind vollständig beendet, bevor `close()` zurückkehrt.
- physische Pfad-Deduplizierung innerhalb eines Scans: Überlappende logische Ziele verwenden dasselbe Dateiergebnis und verbrauchen Scanbudget nur einmal,
- getrennte verifizierte Summen für physische Dateien und logische Kategorieverweise einschließlich ausgewiesener Überlappungsanzahl.

Der Cache bleibt bei Timeout oder Teilfehlern sichtbar. Ein alter Cache ohne getrennte Summen wird als `LEGACY_CACHE` markiert; seine bisherigen Gesamtwerte werden nicht als physisch verifiziert ausgegeben. Erst ein neuer vollständiger Scan erzeugt `VERIFIED`-Werte. Eine schreibgeschützte Realmessung am 1. August 2026 fand 105 physische Dateien und 58 JSONL-Dateien mit rund 5,80 GB. Der vorhandene Index deckte 5,69 % ab. Mit dem alten Budget dauerte der Lauf 1,084 Sekunden; 64 MiB wurden in einem zweiten Benchmark in 2,135 Sekunden verarbeitet. Daraus ergaben sich ungefähr 82 weitere Minutenläufe bis zur Nachindexierung. Zwei vorhandene Stock-JSON-Dateien enthalten Syntaxfehler und erklären den Status `DEGRADED`; sie wurden nicht verändert.

## Control Center

Das lokale Control Center wird standardmäßig unter `http://127.0.0.1:8000/` bereitgestellt. Es zeigt Health, Services, Märkte, Brain, Signals, Statistiken, Speicher, Learning Report und Graphen. HTTP-Endpunkte liefern read-only Sichten; `/api/statistics/storage/refresh` startet einen Hintergrundscan und antwortet mit HTTP `202 Accepted`.

Die UI lädt den vollständigen Storage-Snapshot single-flight, zeigt Scanstatus, kumulativen JSONL-Indexfortschritt, geschätzte Restläufe/-zeit, die langsamste Phase sowie getrennte physische und logische Storage-Summen und verwendet Cache-Buster sowie `defer` für lokale Skripte. Überlappende Dateiverweise werden ausdrücklich angezeigt. Live- und Statistik-Broadcasts sind gedrosselt; große interne Felder wie Candles, Features, Steps und Raw Results werden aus Browser-Payloads entfernt, ohne interne Events zu verändern.

Der WebSocket-Client fällt bei `close` auf Polling zurück. Reconnect, mehrfacher Close, `error`-Fallback sowie JSON-/Renderfehler sind noch nicht vollständig robust. Servicezustände berücksichtigen inzwischen zusätzlich das Ergebnis von `adapter.health()`: null Crypto-Ergebnisse bei Fehlern werden als `ERROR` statt fälschlich als `OK` projiziert.

## Telegram

Telegram ist über Umgebungsvariablen steuerbar. Sichere Vorgaben sind `PANDORICKKI_TELEGRAM_ENABLED=0` und `PANDORICKKI_TELEGRAM_DRY_RUN=1`. Tokens und Chat-IDs dürfen nicht versioniert oder dokumentiert werden. Telegram abonniert derzeit Crypto-/Stock-Analysen und simulierte Crypto-Trade-Updates direkt und ist nicht ausschließlich an finale Decision-/Signal-Ereignisse gekoppelt.

## Speicherformate

- JSON: Shared State, offene simulierte Trades, Status-, Cache- und begrenzte Servicefehler-Zusammenfassung (`service_error_summary.json`).
- JSONL: Brain-Ereignisse, Decisions, Signals, Outcomes, Trade-Historie, NeuroBrain-Inbox, Telegram-Dry-Run, Audits und kompakte Servicefehler (`service_errors.jsonl`).
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
python -m unittest tests.test_service_error_journal tests.test_config tests.test_parallel_orchestrator
python -m compileall .
```

Der vollständige Lauf am 1. August 2026 bestand nach der kompakten Brain-Migration mit 222/222 Tests in 52,209 Sekunden. Der neue Brain-Test prüft Persistenz und Folgeevent, Schema/IDs, den Ausschluss aller Bulk-Felder und eine Größenreduktion auf weniger als ein Viertel des umfangreichen Testinputs. 28 gezielte Brain-/Decision-/Tracker-/Graph-/Integrations-/Vertragstests bestanden ebenfalls.

## Bekannte Risiken

1. Storage-Laufzeiten müssen nach dem Neustart weiter beobachtet werden; der 64-MiB-Realbenchmark blieb mit 2,135 Sekunden deutlich unter dem 30-Sekunden-Limit.
2. Der synchrone EventBus kann Produzenten durch langsame Handler blockieren.
3. WebSocket-Reconnect und Polling-Fallback sind nicht vollständig robust.
4. Brain und Decision Core bieten weniger fachliche Prüfung, als ihre Namen vermuten lassen.
5. Telegram umgeht derzeit eine strikt zentrale finale Freigabekette.
6. Runtime-Ledger wachsen insgesamt ohne zentrale Retention-Policy.
7. Absolute Windows-Pfade begrenzen die Portabilität.
8. Feature-Eingangsdaten werden nicht streng genug validiert.
9. Heartbeats werden nicht automatisch als `STALE` klassifiziert.
10. Der Crypto-Reparaturstand ist auf `origin/agent/add-market-feature-engine` veröffentlicht und liegt in Draft-PR #3 gegen `main`; er ist noch nicht gemergt.
11. Brain persistiert und publiziert neue Analysen kompakt. Decision Core erzeugt derzeit weiterhin eigene Payloads mit dem Legacy-Feld `raw_result` (bei kompaktem Brain-Input `None`), und NeuroBrain persistiert weiterhin komplette empfangene Event-Payloads neben seiner Kopfsicht.
12. Das Fehlerjournal läuft als synchroner EventBus-Handler. Es schreibt nur bei Fehlern und fängt eigene Schreibfehler ab, kann bei langsamen Datenträgern aber den Fehler-Publisher kurzzeitig verzögern.
13. Der Storage-Shutdown-Fix liegt gestapelt in Draft-PR #4 gegen `agent/add-market-feature-engine`; auch dieser PR ist noch nicht gemergt.
14. Die Storage-Deduplizierung liegt gestapelt in Draft-PR #5 gegen `agent/fix-storage-worker-shutdown`; auch dieser PR ist noch nicht gemergt.
15. Zwei vorhandene Stock-JSON-Dateien enthalten Syntaxfehler und halten Storage auf `DEGRADED`; sie wurden bewusst nicht repariert oder gelöscht.
16. Die Scanner-Instrumentierung liegt gestapelt in Draft-PR #6 gegen `agent/fix-storage-physical-totals`; auch dieser PR ist noch nicht gemergt.
