# PandorickKi – aktueller Systemzustand

Stand: 8. August 2026
Grundlage: aktueller Arbeitsbaum, statische Codeprüfung, lokale HTTP-API und zuletzt tatsächlich ausgeführte Tests.

Der Benutzer hat am 9. August 2026 die diagnostischen Schwellen Probability `60`, Confidence `60` und Toleranz `0` ausdrücklich bestätigt. `start_pandorick_web.bat` aktiviert deshalb den weiterhin rein beobachtenden `decision_gate_observer` mit genau diesen Werten. Nach kontrolliertem Neustart mit öffentlichem Netzwerkzugriff liefen vier vollständige Crypto-/Stock-Zyklen mit Plattform und allen elf Services `OK`. Das getrennte Audit enthielt 32 eindeutige Version-1-Ergebnisse (12 Crypto, 20 Stock), davon 0 `QUALIFIED` und 32 `BLOCKED`; kein Ergebnis setzte `ready_for_telegram` oder `order_execution_allowed`. Seit diesem korrekten Start entstand kein neuer Dienstfehler. Telegram blieb deaktiviert, im Dry-Run und bei null gesendeten Nachrichten.

Die erste Diagnose zeigt keine Gate-Regression, sondern vorgelagerte fachliche Grenzen: 30 Kandidaten waren `WAIT` oder `HOLD`; Stock-Einzelsnapshots bleiben `WARN/UNVERIFIED/WARMING`, und einzelne LONG-Kandidaten besaßen keinen gate-tauglichen Preis beziehungsweise keinen vollständigen Risikoplan. Diese Ergebnisse sind Beobachtungen, keine Freigaben. Der bestehende Decision-/Signalpfad bleibt unverändert parallel aktiv.

Ein eingefrorener erweiterter Snapshot über knapp 39 Minuten und 272 Kandidaten ist in `docs/DECISION_GATE_AUDIT_REPORT.md` dokumentiert. Er enthielt 2 technisch qualifizierte ETHUSDT-LONG-Fälle und 270 Blockierungen, weiterhin null Telegram-/Orderfreigaben, null Schema-/Policyfehler und null neue Dienstfehler seit dem korrekten Netzwerkstart. Alle 102 Crypto-Kandidaten hatten `PASS/VERIFIED/READY`; alle 170 Stock-Kandidaten blieben `WARN/UNVERIFIED/WARMING`. Der Codeabgleich bestätigt zusätzlich, dass Stock derzeit keinen normalisierten Gate-Risikoplan erzeugt und Brain `confidence` noch direkt aus `probability` ableitet.

Am 8. August 2026 wurde die kompakte `feature_quality`-Projektion in den Marktvertrag aufgenommen und bis Brain, Decision und Signal erhalten. Ein neuer `DecisionGateAuditAdapter` kann parallel zu `DecisionSignalAdapter` jedes `BRAIN_DECISION_RECEIVED` fail-closed bewerten und das Ergebnis in `decision_gate_audit.jsonl` mit begrenzter Größenrotation und höchstens vier Archiven speichern. Der Observer ist standardmäßig deaktiviert und lässt sich nur mit ausdrücklich gesetzten Probability- und Confidence-Schwellen erstellen. Er publiziert ausschließlich `DECISION_GATE_EVALUATED`, ersetzt keine Decision oder Signal, setzt niemals Telegram frei und erlaubt keine Orders. Der bestehende aktive Decision-/Signalpfad ist unverändert.

Der Feature-Datenqualitätsvertrag `pandorickki.feature-data-quality` Version 1 wurde am 8. August 2026 über PR #22 nach `main` integriert; `origin/main` steht auf Merge-Commit `14e19bf0a4e79860732ff3b6bba4135a2504b909`. Der gemergte Stand wurde anschließend kontrolliert gestoppt und ohne harten Prozessabbruch aus der projektlokalen `.venv` mit Live-Crypto, Live-Aktien, NeuroBrain aktiv sowie Telegram deaktiviert/Dry-Run neu gestartet. Nach vier vollständigen Produktionszyklen meldeten Plattform und alle zehn Services `OK`, Sitzungsfehler und STALE-Services null, NeuroBrain Queue-Tiefe und Drops null sowie Telegram null gesendete Nachrichten. Das Control Center verband sich nach dem Prozesswechsel wieder per WebSocket und zeigte aktuelle Crypto-/Aktienwerte ohne Browser-Warnungen.

Die Feature-Grenze wurde zusätzlich direkt verifiziert: BTCUSDT akzeptierte 240/240 öffentliche Binance-Kerzen mit `PASS`, Reihenfolge `VERIFIED`, Warmup `READY`, null Duplikaten und null Regelverstößen. Der rückwärtskompatible Stock-Einzelsnapshot lieferte ohne Featurefehler erwartungsgemäß `WARN`, Reihenfolge `UNVERIFIED` und Warmup `WARMING`, weil er nur eine nicht zeitgestempelte Kerze besitzt. Diese sichtbare Unreife ist kein voller Decision-Freigabenachweis und muss vom nächsten fachlichen Decision Gate berücksichtigt werden.

Der vollständig validierte Entwicklungsstand wurde am 8. August 2026 über den konsolidierten Pull Request #18 in `main` integriert. Die zugehörige Abschlussdokumentation aus PR #19 ist ebenfalls gemergt; `origin/main` steht auf `381229a66c5ac8ed121297457fa4315155c55176`. Der geprüfte Integrations-Head `3853d4109ce924737631f575c74faff776f89062` ist enthalten. PR #4 bis #17 wurden anschließend als durch #18 ersetzt geschlossen. PR #3 wurde von GitHub automatisch als gemergt markiert, weil sein Head vollständig durch #18 nach `main` gelangte; es gab keinen zusätzlichen Einzel-Merge. Vor der Veröffentlichung bestanden Runtime-Preflight, 243/243 Tests, JavaScript-Syntax, Diff-, Merge-Simulations-, Runtime- und Secret-Prüfung.

Der gemergte `main`-Stand wurde am 8. August 2026 kontrolliert neu gestartet. Der eingebaute Stop gab Port 8000 nach 15,041 Sekunden frei; ein harter Prozessabbruch war nicht nötig. Der Start erfolgte über die projektlokale `.venv` mit Live-Crypto und Live-Aktien, Telegram deaktiviert und Dry-Run aktiv. Nach sechs vollständigen Crypto- und Stockzyklen meldeten Plattform und alle zehn Services `OK`, die Sitzung null Servicefehler und NeuroBrain null Queue-, Drop- oder Workerfehler. BTCUSDT, ETHUSDT und XRPUSDT lieferten aktuelle Binance-Preise. Der physische Storage-Bestand war mit 145 Dateien, 2.548.436 Datensätzen und 10,52 GB `VERIFIED`; der Scanstatus blieb ausschließlich wegen zweier bereits bekannter beschädigter historischer Stock-Backup-JSONs `DEGRADED`. Die Browser-Automation durfte die lokale URL aufgrund ihrer Sicherheitsrichtlinie nicht öffnen; `web_running`, `websocket_active` und `statistics_active` wurden deshalb über `/api/health`, Status- und Storage-API sowie Serverlogs verifiziert.

Die UI-Härtung wurde am 2. August 2026 implementiert und kontrolliert live verifiziert. Der Browser verwaltet genau einen Polling-Fallback, verhindert parallele Statusabfragen und verbindet den WebSocket nach Abbrüchen mit begrenztem exponentiellem Backoff erneut. Ein laufender Browser wechselte nach einem vollständigen Prozessneustart ohne manuelles Neuladen zurück auf `WebSocket`. Fehlerhafte WebSocket-Nachrichten werden lokal abgefangen.

Heartbeat-Alter und `STALE` werden zentral in REST- und leichten WebSocket-Snapshots berechnet. Die Standardgrenze beträgt 150 Sekunden und ist über `PANDORICKKI_SERVICE_HEARTBEAT_STALE_SECONDS` konfigurierbar. Nur Services mit einem bekannten Heartbeat werden bewertet; `ERROR`, `STOPPED` und `DISABLED` werden nicht durch `STALE` überschrieben.

Stop- und Restart-Anforderungen unterbrechen den Warteabschnitt der Orchestratorschleife in Intervallen von höchstens 100 Millisekunden. Restart stoppt und startet die vorhandenen Adapter im selben Prozess, während der Webserver und bestehende Browserverbindungen erhalten bleiben. Die Liveprüfung setzte einen Restart in rund 104 Millisekunden auf `APPLIED`; ein vollständiger kontrollierter Prozess-Stop gab Port 8000 in 2,326 Sekunden frei. Steuerbefehle verwenden `CONTROL_COMMAND_APPLIED` und erzeugen keinen Phantom-Service mehr.

Der Learning Graph koalesziert Interaktionen per `requestAnimationFrame`, lädt nur single-flight und überspringt Hintergrundloads in ausgeblendeten Tabs. Das teure Force-Layout wird nur neu berechnet, wenn sich Knoten- oder Kantenstruktur ändert. Live wurden 76 Knoten und 179 Kanten ohne Browserfehler dargestellt.

Learning-, Outcome- und Graphmetriken verwenden seit dem 2. August 2026 den additiven Vertrag `pandorickki.learning-metrics` Version 1. Hit-Rate bedeutet einheitlich Wins geteilt durch Wins plus Losses; Breakeven und unbekannte Ergebnisse bleiben separate Klassen. Jede Rate liefert Zähler und Nenner. Der Learning Report ordnet geschlossene Outcomes per `decision_id` zu und weist die Outcome-Abdeckung gegenüber outcome-fähigen LONG-/SHORT-Decisions aus. Nicht vergleichbare historische Aggregatzähler liefern für die Abdeckung bewusst `null` statt einer erfundenen Quote.

`AI_LEARNING_UPDATED` ist ausdrücklich ein Projektionsereignis, kein erfolgreicher Lern- oder Modellupdate. Graph-Muster sind sichtbare Muster-Buckets, keine gelernten Modellmuster. Control Center, API und Graph melden `ml_training.active=false` und `model_updates=0`; PandorickKi trainiert weiterhin kein ML-Modell. Alte API-Felder bleiben zunächst als Aliase erhalten, bestehende Statistik-, Learning- und Historydateien wurden nicht umgeschrieben.

Die finale Liveprüfung vom 2. August 2026 zeigte Plattform und alle zehn Services `OK`. Nach zwei Crypto- und Stockzyklen lagen aktuelle BTCUSDT-, ETHUSDT- und XRPUSDT-Preise vor; NeuroBrain hatte Queue-Tiefe, Drops und Fehler jeweils null. Der Learning Report lieferte die Version-1-Metriken mit expliziten Brüchen, während die historischen Trading-Aggregate ihre wegen unterschiedlicher Rekonstruktionsscopes nicht berechenbare Abdeckung korrekt als `null` ausgaben. Telegram blieb deaktiviert, im Dry-Run und bei null versendeten Nachrichten.

NeuroBrain ist seit dem 2. August 2026 vom synchronen Datei-I/O im EventBus-Publisher entkoppelt. Der Publisher erstellt nur noch die kompakte Projektion und reiht sie per `put_nowait` in eine FIFO-Queue mit Standardkapazität 2048 ein. Ein einzelner Worker schreibt bis zu 64 Einträge pro Batch mit einem `fsync` je aktivem Dateichunk und aktualisiert anschließend den atomaren Status. Bei voller Queue wird ausschließlich das neueste Ereignis abgelehnt und dauerhaft sichtbar gezählt; es gibt kein stilles Überschreiben älterer Einträge. `stop()` nimmt zuerst das Abonnement weg und kehrt erst zurück, wenn alle akzeptierten Einträge verarbeitet sind.

Die Liveprüfung verarbeitete 231 neue, eindeutige Inboxzeilen in 48 Batches ohne FIFO-, Schema- oder Bulk-Verstoß. Queue-Tiefe, Drops, Ledger-/Status-/Benachrichtigungsfehler blieben null. Der kontrollierte Stop hinterließ `running=false`, `worker_running=false` und `queue_depth=0`; anschließend wurde PandorickKi wieder mit Queue-Worker, Telegram aus und Dry-Run gestartet. Alle zehn Services waren `OK`, Crypto lieferte sechs und Stock zehn Ergebnisse, das Fehlerjournal blieb bei 180.

Die NeuroBrain-Schemaabgrenzung wurde am 2. August 2026 korrigiert. Neue Learning- und aggregierte Aktien-Update-Zeilen verwenden `pandorickki.compact-observer-event` Version 1; einzelne Crypto-/Commodity-Preisupdates bleiben Markt-Ereignisse und erhalten ihren eindeutigen Markt-Typ aus dem Topic. Nach dem kontrollierten Neustart waren 152 ausschließlich neu angehängte Inboxzeilen ohne Schema-, Pflichtfeld- oder Bulk-Verstoß. Zwei Produktionszyklen lieferten Crypto 6 und Stock 10 Ergebnisse; alle zehn Services waren `OK`, das Fehlerjournal blieb bei 180 und Telegram bei `enabled=false`, `dry_run=true`, `messages_sent=0`.

Die wiederkehrenden Windows-Schreibkonflikte am NeuroBrain-Status und an den aktiven simulierten Crypto-Trades wurden am 2. August 2026 repariert. Beide Pfade verwenden jetzt eindeutige, gleichverzeichnisige Temp-Dateien, eine pro Zielpfad geteilte In-Process-Sperre und einen kurzen begrenzten Retry für transiente `PermissionError`-/Windows-Sharing-Verstöße. Der jeweilige Adapter hält zusätzlich seine Zustandssperre bis zum erfolgreichen atomaren Replace, damit ältere Snapshots keine neueren überschreiben.

Nach dem kontrollierten Neustart liefen zwei vollständige Produktionszyklen mit allen zehn Services `OK`. Crypto lieferte sechs, Stock zehn neue Ergebnisse. Die Fehlerjournal-Summe blieb bei 180; die betroffenen NeuroBrain- und Crypto-Trade-Tracker-Fingerprints blieben bei jeweils drei Vorkommen und ihren bisherigen letzten Zeitpunkten. Es entstanden keine verwaisten Temp-Dateien. Telegram blieb deaktiviert, im Dry-Run und bei null versendeten Nachrichten.

Der vollständige gestapelte Payloadstand wurde am 1. August 2026 kontrolliert live gestartet. Nach dem aussagekräftigen Neustart mit freigegebenem Netzwerkzugriff liefen drei vollständige Produktionszyklen: Plattform, Web und alle zehn Services meldeten `OK`; Crypto lieferte je Zyklus drei und Stock fünf Ergebnisse. BTCUSDT, ETHUSDT und XRPUSDT hatten aktuelle Preise. Seit diesem Neustart entstand kein neuer Journaleintrag; Telegram blieb `enabled=false`, `dry_run=true` und bei null versendeten Nachrichten.

Read-only geprüft wurden ausschließlich neu angehängte Bereiche der Brain-, Decision-, Signal- und NeuroBrain-Ledger. Die Markt-Payloads verwenden `pandorickki.compact-market-event` Version 1, Observer-Ereignisse `pandorickki.compact-observer-event` Version 1. Beide schließen `raw_result`, `features`, `market_data_diagnostics` und `candles` aus; die ID-Kette Brain → Decision → Signal → NeuroBrain blieb vollständig.

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

Die Architektur ist eine Integrations- und Beobachtungsschicht, kein autonomes Handelssystem. `BrainAdapter` und `DecisionSignalAdapter` übernehmen derzeit hauptsächlich Persistenz, Weiterleitung und deterministische Normalisierung, keine unabhängige KI- oder Risikofreigabe. `decision_gate_contract.py` definiert die fail-closed Bewertung; der optionale `DecisionGateAuditAdapter` hängt sie ausschließlich beobachtend parallel an den EventBus. Er beeinflusst den aktiven Decision Core nicht.

## Aktive Services

Der Standard-Orchestrator erstellt, abhängig von der Konfiguration:

1. `CryptoAdapter`
2. `BrainAdapter`
3. optional `DecisionGateAuditAdapter` als Service `decision_gate_observer` (standardmäßig aus)
4. `DecisionSignalAdapter` als Service `decision_core`
5. `OutcomeTracker`
6. optional `NeuroBrainReceiverAdapter`
7. `CryptoTradeTracker`
8. `StockAdapter`
9. optional `CommodityAdapter`
10. `TelegramAdapter`
11. optional `ControlCenterAdapter`

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
5. `BrainAdapter` speichert abgeschlossene Analysen einschließlich der kleinen `feature_quality`-Projektion rotierend und publiziert `BRAIN_DECISION_RECEIVED` sowie `AI_LEARNING_UPDATED`.
6. Wenn ausdrücklich aktiviert, bewertet `DecisionGateAuditAdapter` das Brain-Ereignis parallel und schreibt nur ein begrenztes Audit-Ledger. Er blockiert oder verändert kein Ereignis.
7. `DecisionSignalAdapter` normalisiert dasselbe Brain-Ereignis weiterhin ohne Gate, erzeugt deterministische IDs und persistiert Decision- und Signal-Ledger.
8. Outcome- und Crypto-Trade-Tracker öffnen und aktualisieren ausschließlich simulierte Trades.
9. Control Center, Statistik, Reports und Graphdienste projizieren den Ereignis- und Persistenzzustand in read-only Sichten.
10. Telegram verarbeitet Analyse- und simulierte Trade-Ereignisse direkt; es liegt derzeit nicht strikt hinter einem finalen Decision-Gate.

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
- `adapters/decision_gate_audit_adapter.py`: optionaler, rein beobachtender Gate-Auditpfad mit Duplikatschutz und begrenzter Rotation.
- `adapters/outcome_tracker.py`: allgemeine simulierte Outcome-Verfolgung.
- `adapters/crypto_trade_tracker.py`: simulierte Crypto-Trade-Verfolgung.
- `adapters/neurobrain_receiver_adapter.py`: optionale Datei-Inbox mit Topic-Whitelist und Duplikatschutz.
- `adapters/telegram_adapter.py`: Dry-Run oder optionaler Telegram-Versand.
- `adapters/control_center_adapter.py`: kompakte Live-Sicht auf EventBus und SharedState.

## Feature Engine

`features/feature_engine.py` normalisiert OHLCV-Aliase und berechnet Preis-, Return-, Momentum-, Trend-, Volatilitäts-, Volumen-, Kerzenstruktur- und technische Indikatorgruppen. Dazu gehören unter anderem SMA, EMA, ATR, RSI, MACD, ADX, Bollinger, Stochastic, CCI, Williams %R, OBV, MFI, ROC und KAMA.

Vor jeder Berechnung wendet die Feature Engine den Vertrag `pandorickki.feature-data-quality` Version 1 aus `feature_data_quality_contract.py` an. Er prüft endliche und positive OHLC-Werte, OHLC-Konsistenz, nicht negatives Volumen und gültige Zeitstempel. Vollständig zeitgestempelte Reihen werden aufsteigend sortiert; gleiche Zeitstempel behalten deterministisch die letzte Providerzeile. Fehlende oder teilweise Zeitstempel werden nicht geraten, sondern als unverifizierte Providerreihenfolge ausgewiesen. Ungültige Zeilen, Duplikate, Sortierstatus, Mindestanzahl und Warmup erscheinen unter `metadata.data_quality`.

Die Mindestanzahl ist aus Rückwärtskompatibilitätsgründen standardmäßig eine valide Kerze, während vollständiger Indikator-Warmup derzeit 200 Kerzen verlangt. Einzelsnapshots bleiben damit sichtbar, behaupten aber über `warmup.status=WARMING` keine vollständige Indikatorreife. Crypto-Kerzen behalten jetzt ihren Provider-Zeitstempel. Live-Adapter verwenden weiterhin `include_targets=False`; historische Trainingsziele gelangen nicht in den Livepfad. Eine New-Candle-/Cache-Strategie und die aktive Integration eines fachlichen Decision Gates sind weiterhin nicht implementiert.

## Brain

`BrainAdapter` abonniert abgeschlossene Crypto-, Stock- und Commodity-Analysen, projiziert jede neue Analyse einmal auf `pandorickki.compact-market-event` Version 1, schreibt diese Sicht in datums- und größenrotierte JSONL-Dateien und publiziert dieselbe Sicht als `BRAIN_DECISION_RECEIVED`. Quell-Event-ID, Markt-/Preis-/Risiko-/Zeitfelder, kompakte Ersatzfelder und die begrenzte `feature_quality`-Sicht bleiben erhalten; Raw Results, vollständige Features, Diagnostik und Kerzen werden nicht neu in Brain-History übernommen. Er führt aktuell keine eigene Modellinferenz, Faktenprüfung oder Konfliktauflösung durch.

Der versionierte kompakte Event-Payload-Vertrag liegt in `event_payload_contract.py` und `docs/EVENT_PAYLOAD_CONTRACT.md`. Version 1 erhält die von Brain, Decision Core, Trackern, Learning, Control Center, Telegram und NeuroBrain tatsächlich benötigten Felder, verbietet aber `raw_result`, Feature-/Diagnostikblöcke und Kerzen. Brain, Decision-/Signal-Persistenz und NeuroBrain verwenden für neue Einträge die verifizierten kompakten Projektionen; alte History bleibt unverändert lesbar.

## Decision Core

`DecisionSignalAdapter` erzeugt aus Brain-Payloads deterministische Decision- und Signal-IDs, projiziert beide Stufen auf `pandorickki.compact-market-event` Version 1 und verwendet die jeweilige Projektion unverändert für Event und rotierendes JSONL-Ledger. Quell-, Decision-, Signal- und Decision-Event-IDs bleiben erhalten; `raw_result`, Features und Kerzen werden nicht neu in Decision-/Signal-Payloads übernommen. Der Duplikatschutz ist innerhalb der laufenden Instanz in-memory. Der aktive Adapter erzeugt weiterhin für jedes Brain-Ereignis Decision und Signal und setzt `ready_for_telegram=true`, ohne eine unabhängige Freigabe.

Der ausführbare Vertrag `pandorickki.decision-gate` Version 1 liegt in `decision_gate_contract.py` und `docs/DECISION_GATE_CONTRACT.md`. Er bewertet Kandidaten rein beobachtend und fail-closed anhand explizit zu konfigurierender Probability-/Confidence-Schwellen, Richtung, Preis, Fakten, kompakter Feature-Qualität, Warmup, Reihenfolge und Risikokonsistenz. Der optionale `DecisionGateAuditAdapter` persistiert diese Resultate getrennt und begrenzt. Unabhängig vom Ergebnis bleiben `ready_for_telegram=false` und `order_execution_allowed=false`; der heutige Eventfluss wird nicht verändert.

## Outcome Tracker

`OutcomeTracker` und `CryptoTradeTracker` arbeiten ausschließlich simuliert. Valide LONG-/SHORT-Entscheidungen mit Entry-Preis können einen simulierten Trade eröffnen. Preisupdates aktualisieren P/L, Drawdown und Terminalbedingungen wie Stop, TP oder Zeithorizont. Offene Zustände werden als JSON, abgeschlossene Lebenszyklen als rotierende JSONL-Dateien gespeichert. Beim Berechnen von Laufzeiten werden historische ISO-Zeitstempel ohne Offset rückwärtskompatibel als UTC interpretiert; die gespeicherten Originalwerte werden nicht umgeschrieben.

Der Crypto Trade Tracker serialisiert Zustandsänderung und aktiven JSON-Snapshot unter derselben Adapter-Sperre. Sein atomarer Schreibpfad verwendet konfliktfreie Temp-Dateien und einen begrenzten Windows-Retry; die append-only Trade-History bleibt unverändert.

Der Crypto Trade Tracker bevorzugt für die Stop-Berechnung die kompakten Felder `market_context.recent_swing_low` beziehungsweise `recent_swing_high`. Vorhandene Events und History ohne diese Felder bleiben über den bisherigen Kerzenpfad in `raw_result` lesbar.

## Learning und History

Learning Reports, Statistikdienste und Learning/Knowledge Graph aggregieren vorhandene Historien. `AI_LEARNING_UPDATED` bezeichnet derzeit ein Daten-/Projektionsereignis, kein Training oder Update eines ML-Modells. Die Graphdienste unter `learning_graph/` liefern sanitizierte Nodes, Edges, Cluster und Übersichten für API und Browser.

Der ausführbare Learning-Metrikvertrag liegt in `learning_metrics_contract.py`, die Feld- und Nennerdefinition in `docs/LEARNING_METRICS_CONTRACT.md`. Der Report lädt begrenzte aktuelle Decision-/Outcome-Fenster, ordnet exakte Outcomes per `decision_id` zu und zeigt Zähler/Nenner sowie Outcome-Abdeckung. Persistente Trading-Aggregate verwenden denselben Hit-Rate-Nenner; ihre Abdeckung bleibt `null`, wenn historisch rekonstruierte Decision- und Outcome-Zähler nicht denselben Scope belegen. `successful_learnings` und `learned_patterns` werden nicht mehr aus Projektionszählern erfunden.

Der Learning Graph unterscheidet `pattern_buckets`, `learning_projection_records_today` und kumulative `learning_update_events_total`. Die ersten beiden beziehen sich auf das geladene Graph-Fenster; keiner dieser Werte ist ein Modelltrainingsergebnis.

Der Learning Graph bevorzugt das kompakte Ergebnisfeld `public_result`. Bei älteren Brain-Datensätzen ohne dieses Feld bleibt `raw_result.result` als reiner Legacy-Lesepfad erhalten.

Der optionale `NeuroBrainReceiverAdapter` behält für jede Inboxzeile seine eigenständige Kopfsicht mit tatsächlich gespiegelter Event-ID, Topic, Quelle, Markt-, Symbol-, Decision-/Signal- und Zeitfeldern. Das zusätzliche Feld `payload` enthält für neue Zeilen ausschließlich Version 1 des passenden Vertrags. Eine darin vorhandene vorgelagerte `source_event_id` bleibt erhalten; bestehende alte Inboxzeilen werden nicht umgeschrieben. Analysis-, Brain-, Decision-, Signal-, Trade- und einzelwertige Marktupdates verwenden den Marktvertrag. `AI_LEARNING_UPDATED` und das aggregierte Aktien-Update verwenden den Observer-Vertrag ohne künstlichen singulären Marktbezug. Persistiert wird über einen einzelnen begrenzten FIFO-Worker; Queue-, Batch-, Drop- und Fehlerzähler sind in Health, Heartbeat und Statusdatei sichtbar.

Seine kleine Statusdatei wird unter der Adapter-Sperre über denselben konfliktresistenten atomaren JSON-Schreibpfad ersetzt. Die Inbox selbst bleibt append-only und wurde durch diese Reparatur nicht migriert oder umgeschrieben.

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

Die Learning-Oberfläche heißt fachlich Outcome-Auswertung, zeigt Hit-Rate und Outcome-Abdeckung einschließlich Zähler/Nenner und kennzeichnet sichtbar, dass kein ML-Training aktiv ist. Trading-Statistik, Outcome-Auswertung und Graph verwenden getrennte Scope-Bezeichnungen; nicht vergleichbare Aggregate erscheinen als `nicht vergleichbar`.

Die UI lädt den vollständigen Storage-Snapshot single-flight, zeigt Scanstatus, kumulativen JSONL-Indexfortschritt, geschätzte Restläufe/-zeit, die langsamste Phase sowie getrennte physische und logische Storage-Summen und verwendet Cache-Buster sowie `defer` für lokale Skripte. Überlappende Dateiverweise werden ausdrücklich angezeigt. Live- und Statistik-Broadcasts sind gedrosselt; große interne Felder wie Candles, Features, Steps und Raw Results werden aus Browser-Payloads entfernt, ohne interne Events zu verändern.

Der WebSocket-Client fällt bei `close` oder `error` auf genau einen idempotenten Polling-Timer zurück und verbindet sich mit begrenztem exponentiellem Backoff erneut. Veraltete Socket-Callbacks werden über eine Verbindungsgeneration ignoriert; erfolgreiche Verbindung beendet den Fallback-Timer. Polling ist single-flight, JSON-/Renderfehler bleiben auf die Verbindungssicht begrenzt. Servicezustände berücksichtigen zusätzlich das Ergebnis von `adapter.health()`: null Crypto-Ergebnisse bei Fehlern werden als `ERROR` statt fälschlich als `OK` projiziert. Bekannte Heartbeats erhalten Alter und zentrale `STALE`-Klassifikation.

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

Der vollständige Lauf am 2. August 2026 bestand nach der UI-Härtung mit 243/243 Tests in 43,586 Sekunden. 15 gezielte Web-/Orchestrator-Tests bestanden. Die neuen Regressionen decken einmaliges Konsumieren von Restart, echten In-Process-Adapterrestart, unterbrechbaren Stop, zentrale STALE-Klassifikation, leichte WebSocket-Snapshots und die Frontend-Verträge für Reconnect, Timer und Frame-Koaleszierung ab. JavaScript-Syntaxprüfung und `git diff --check` bestanden ebenfalls.

## Bekannte Risiken

1. Storage-Laufzeiten müssen nach dem Neustart weiter beobachtet werden; der 64-MiB-Realbenchmark blieb mit 2,135 Sekunden deutlich unter dem 30-Sekunden-Limit.
2. Der synchrone EventBus kann Produzenten durch langsame Handler blockieren.
3. WebSocket-Reconnect und Polling-Fallback sind gehärtet; reale Netzwerksonderfälle und sehr lange aktive Adapterzyklen bleiben weiter zu beobachten.
4. Brain und aktiver Decision Core bieten weniger fachliche Prüfung, als ihre Namen vermuten lassen; der neue Observer-Vertrag ist noch nicht integriert.
5. Telegram umgeht derzeit eine strikt zentrale finale Freigabekette.
6. Runtime-Ledger wachsen insgesamt ohne zentrale Retention-Policy.
7. Absolute Windows-Pfade begrenzen die Portabilität.
8. Feature-Eingangsdaten sind technisch validiert; ihre kompakte Qualitätsprojektion erreicht den Brain-/Decision-Pfad noch nicht.
9. Nur Services mit vorhandenem Heartbeat können als `STALE` klassifiziert werden; heartbeatlose Services bleiben bei ihrem sonstigen Status.
10. Brain, Decision Core und NeuroBrain persistieren neue Marktstufen kompakt; der vollständige Stand ist live verifiziert. NeuroBrain trennt neue Markt- und Observer-Zeilen topicbasiert. Vorhandene alte Ledger und Inboxzeilen enthalten erwartungsgemäß weiterhin ihre bisherigen Payloadformen und werden nicht umgeschrieben.
11. Das Fehlerjournal läuft als synchroner EventBus-Handler. Es schreibt nur bei Fehlern und fängt eigene Schreibfehler ab, kann bei langsamen Datenträgern aber den Fehler-Publisher kurzzeitig verzögern.
12. Zwei vorhandene Stock-JSON-Dateien enthalten Syntaxfehler und halten Storage auf `DEGRADED`; sie wurden bewusst nicht repariert oder gelöscht.
13. Der konfliktresistente Atomic-JSON-Helfer ist bewusst auf NeuroBrain-Status und aktive Crypto-Trades begrenzt. Andere bestehende atomare JSON-Schreiber verwenden weiterhin ihre bisherigen Implementierungen und müssen nur bei tatsächlicher Konkurrenz oder eigenem Fehlerbefund migriert werden.
