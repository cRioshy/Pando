# PandorickKi Foundation Report

Stand: 2026-07-14

Ziel dieser Phase: Pandorick als stabile Version-1.0-Foundation bewerten, ohne Tradinglogik, Brainlogik, Learninglogik, APIs oder Daten zu veraendern.

## 1. Executive Summary

PandorickKi ist inzwischen eine laufende Plattform mit Crypto Engine, Stock Engine, Brain, Learning, Decision Core, Statistics, Learning Graph, Web Control Center und lokaler API.

Der aktuelle Systemzustand ist grundsaetzlich stabil:

- Platform Health: OK
- Crypto-Daten aktiv: BTCUSDT, ETHUSDT, XRPUSDT
- Stock-Daten aktiv: AAPL, MSFT, NVDA, TSLA, SPCX
- Web Control Center aktiv auf `127.0.0.1:8000`
- Learning Graph aktiv und sanitisiert
- Stock-JSON-Speicher wurde repariert und liefert wieder Daten

Die wichtigsten Foundation-Themen vor neuen Erweiterungen:

1. `brain_events.jsonl` ist mit ca. 2.12 GB der groesste Wachstumstreiber.
2. `/api/status` ist zu gross und gibt interne Felder wie `raw_result`, `calculation` und `weight` aus.
3. Der Learning-Graph-Vollabruf ist mit ca. 4.7 Sekunden der langsamste API-Endpunkt.
4. JSON-Speicherdateien sind anfällig fuer Korruption, wenn waehrend eines Schreibvorgangs gestoppt wird.
5. Legacy-Statistik und neue Trading-Statistik muessen klar getrennt bleiben.

## 2. Projektgroesse

Gemessene Projektbereiche:

| Bereich | Dateien | Python | JSON | JSONL | Gesamtgroesse | Datengroesse |
|---|---:|---:|---:|---:|---:|---:|
| PandorickKi | 178 | 53 | 3 | 2 | 2.13 GB | 2.13 GB |
| StockBot | 95 | 27 | 16 | 0 | 203.04 MB | 202.77 MB |
| CryptoBot | 196 | 41 | 4 | 1 | 4.29 MB | n/a |

Groesste bekannte Daten:

| Datei | Groesse | Datensaetze |
|---|---:|---:|
| `PandorickKi/data/brain_events.jsonl` | 2.12 GB | 66,358 Zeilen |
| `PandorickKi/storage/statistics/system_statistics.json` | 1.18 MB | 12 Top-Level-Felder |
| `pandorick_stock_bot/data_stock/stock_decisions.json` | 76.18 MB | 17,685 |
| `pandorick_stock_bot/data_stock/stock_history.json` | 46.89 MB | 25,086 |

## 3. Architekturuebersicht

Startpunkt:

- `main.py`
- `orchestrator.py`
- `event_bus.py`
- `shared_state.py`
- `health_monitor.py`

Adapter-Schicht:

- `adapters/crypto_adapter.py`: bindet den bestehenden Crypto-Bot an.
- `adapters/stock_adapter.py`: bindet den getrennten Stock-Bot an.
- `adapters/brain_adapter.py`: nimmt fertige Analysen auf und persistiert Brain-Events.
- `adapters/decision_signal_adapter.py`: normalisiert Decisions und Signals.
- `adapters/crypto_trade_tracker.py`: simulierte Entry/Stop/TP-Ueberwachung fuer Crypto.
- `adapters/telegram_adapter.py`: Telegram Dry-Run/Message-Ready-Schicht.
- `adapters/control_center_adapter.py`: sammelt Live-Status fuer Terminal/Web.

Web-Schicht:

- `web/api.py`: lokaler Webserver, Snapshots, API-Methoden, WebSocket-Broadcast.
- `web/routes.py`: HTTP-Routen, lokale Zugriffskontrolle, statische Dateien.
- `web/statistics_service.py`: Analyse-, Trading-, Entwickler- und Storage-Statistik.
- `web/websocket_manager.py`: WebSocket-Live-Verbindung.
- `web/static/*`: Browser-ControlCenter.

Learning Graph:

- `learning_graph/graph_service.py`
- `learning_graph/graph_repository.py`
- `learning_graph/graph_builder.py`
- `learning_graph/graph_sanitizer.py`
- `learning_graph/graph_config.py`
- `learning_graph/graph_models.py`

Datenfluss:

```text
CryptoBot / StockBot
  -> Adapter
  -> EventBus
  -> DecisionSignalAdapter
  -> BrainAdapter
  -> StatisticsService
  -> SharedState
  -> Web API / WebSocket / ControlCenter
  -> Learning Graph
```

## 4. API-Uebersicht

Registrierte GET-Endpunkte:

- `/api/health`
- `/api/status`
- `/api/services`
- `/api/crypto`
- `/api/stocks`
- `/api/brain`
- `/api/signals`
- `/api/errors`
- `/api/events`
- `/api/config/public`
- `/api/statistics`
- `/api/statistics/analyses`
- `/api/statistics/storage`
- `/api/statistics/storage/{folder_name}`
- `/api/v1/learning-graph`
- `/api/v1/learning-graph/nodes`
- `/api/v1/learning-graph/edges`
- `/api/v1/learning-graph/stats`
- `/api/v1/learning-graph/recent`
- `/api/v1/learning-graph/node/{node_id}`

Registrierte POST-Endpunkte:

- `/api/statistics/storage/refresh`
- `/api/control/start`
- `/api/control/stop`
- `/api/control/restart`
- `/api/control/pause`
- `/api/control/resume`
- `/api/control/restart/crypto`
- `/api/control/restart/stocks`
- `/api/control/restart/brain`
- `/api/control/restart/telegram`

WebSocket:

- `/ws/live`

Alle Routen sind lokal auf `127.0.0.1` beschraenkt.

## 5. API-Performance

Gemessene Antwortzeiten:

| Endpoint | Status | Zeit | Groesse |
|---|---:|---:|---:|
| `/api/health` | 200 | 240 ms | 144 B |
| `/api/status` | 200 | 246 ms | 48 KB |
| `/api/services` | 200 | 152 ms | 1.6 KB |
| `/api/crypto` | 200 | 554 ms | 1.1 KB |
| `/api/stocks` | 200 | 1076 ms | 1.7 KB |
| `/api/brain` | 200 | 380 ms | 40 KB |
| `/api/signals` | 200 | 170 ms | 441 B |
| `/api/errors` | 200 | 292 ms | 58 B |
| `/api/events` | 200 | 357 ms | 1.8 KB |
| `/api/config/public` | 200 | 176 ms | 351 B |
| `/api/statistics` | 200 | 144 ms | 1.3 KB |
| `/api/statistics/storage` | 200 | 80 ms | 9.5 KB |
| `/api/v1/learning-graph` | 200 | 4733 ms | 66 KB |
| `/api/v1/learning-graph/stats` | 200 | 23 ms | 235 B |
| `/api/v1/learning-graph/recent` | 200 | 24 ms | 2.8 KB |

Bewertung:

- Kritisch fuer UX: `/api/v1/learning-graph` ist deutlich langsamer als alle anderen Endpunkte.
- Beobachten: `/api/stocks` liegt ueber 1 Sekunde.
- Gut: Statistik- und Storage-Endpunkte sind schnell genug.

## 6. Control Center

Aktueller Zustand:

- Dark Theme vorhanden.
- Live-WebSocket aktiv.
- Crypto, Stocks, Brain, Telegram, Statistik und Datenspeicher sichtbar.
- Entwicklerstatistik, Tradingstatistik und Legacy-Statistik getrennt.

Schwaechen:

- `/api/status` liefert sehr grosse verschachtelte Objekte.
- Interne Debugfelder koennen im Status auftauchen.
- Browser kann durch grosse Snapshots unnoetig belastet werden.

Empfehlung:

- Fuer Browser-Live-View einen schlanken `public_status` Snapshot einfuehren.
- `raw_result`, `calculation`, `weight`, volle Indicator-Trace-Daten und Dateipfade aus `/api/status` entfernen oder nur in einem lokalen Developer-Diagnosemodus zeigen.

## 7. Learning Graph

Gemessener Graph:

- Visible Nodes: 72
- Visible Edges: 170
- Analyses processed: 57,048
- Patterns recognized: 39
- New learnings today: 56,371
- Active markets: 8
- System status: OK

Knotentypen:

| Typ | Anzahl |
|---|---:|
| MARKET | 8 |
| DATA_SOURCE | 2 |
| SYSTEM | 2 |
| INDICATOR | 10 |
| PATTERN | 39 |
| LEARNING | 1 |
| DECISION | 9 |
| RESULT | 1 |

Edge-Typen:

| Typ | Anzahl |
|---|---:|
| CONNECTED_TO_SOURCE | 8 |
| ANALYZED_BY | 8 |
| USES_PUBLIC_FACTOR | 58 |
| OBSERVED_PATTERN | 39 |
| CREATED_LEARNING | 39 |
| CREATED_DECISION | 9 |
| HAS_RESULT | 9 |

Top Super-Knoten:

| Degree | Typ | Label |
|---:|---|---|
| 48 | LEARNING | Confidence Update |
| 19 | MARKET | AAPL |
| 19 | MARKET | TSLA |
| 18 | MARKET | MSFT |
| 18 | MARKET | NVDA |
| 12 | MARKET | SPCX |
| 9 | MARKET | XRPUSDT |
| 9 | RESULT | OPEN |
| 9 | MARKET | BTCUSDT |
| 9 | MARKET | ETHUSDT |
| 8 | INDICATOR | EMA |
| 8 | INDICATOR | RSI |

Bewertung:

- Der Super-Knoten `Confidence Update` verbindet sehr viele Pattern- und Learning-Knoten.
- Die Struktur ist fuer 72/170 noch handhabbar, kann aber bei mehr Patterns schnell wieder unuebersichtlich werden.
- Der Vollabruf ist mit 4.7 Sekunden teuer.
- `graph_sanitizer` funktioniert im Graph-Endpunkt: keine Treffer fuer `token`, `api_key`, `raw_result`, `calculation`, `weight` oder absolute Windows-Pfade.

Empfehlungen:

- Graph initial nur mit Stats/Recent laden, Vollgraph nur bei Bedarf.
- Super-Knoten visuell aggregieren oder einklappen.
- Cache fuer Vollgraph verstaerken.
- Edge-Limit und Node-Limit beibehalten, aber UI mit Cluster-Level-of-Detail ausbauen.

## 8. Statistikstatus

Aktuelle professionelle Statistik:

Entwicklerstatistik:

- Analyse-Events: 57,056
- Brain-Updates: 56,379
- API-Aufrufe: 0
- Datenbank-Schreibvorgaenge: 0
- Retry-Vorgaenge: 0
- Service-Fehler: 15
- Datenwarnungen: 0
- Einzigartige Fehlertypen: 1
- Wiederholte Fehler: 14
- Duplicate Events ignored: 0

Tradingstatistik:

- Analysen gesamt: 57,056
- Finale LONG: 470
- Finale SHORT: 0
- Finale HOLD: 2,386
- WATCHLIST: 0
- Aktive Maerkte: 2
- Gelernte Muster: 0
- Erfolgreiche Learnings: 2,856
- Confidence-Durchschnitt: 57.97
- Hit Rate: nicht vorhanden
- Durchschnittliche Analysezeit: nicht vorhanden

Legacy-Statistik:

- Legacy Analysen: 57,056
- Legacy LONG: 6,627
- Legacy SHORT: 0
- Legacy HOLD: 148,558
- Legacy Fehler: 12,387

Bewertung:

- Die neue Tradingstatistik ist plausibler als Legacy, weil sie nur finale `DECISION_CREATED` zaehlt.
- `final_short = 0` ist plausibel, wenn die Decision-Regeln bisher keine Short-Freigabe erzeugen.
- `watchlist = 0` kann fachlich korrekt sein, falls Watchlist in der Plattform normalisiert oder nicht mehr final erzeugt wird.
- Legacy-HOLD ist weiter extrem hoch, weil alte Analyse-, Signal- und Decision-Events vermischt wurden.
- Service-Fehler 15 sind persistierte Stock-Fehler aus der Zeit vor der JSON-Reparatur; aktueller Live-Status hatte danach 0 neue Stock-Service-Fehler.

Empfehlungen:

- Legacy-Anzeige weiter als Vergleich markieren oder in Developer-Ansicht einklappen.
- Persistierte Fehler mit Zeitfenstern trennen: seit Start, heute, gesamt.
- Datenwarnungen fuer kaputte JSON-Dateien aufnehmen, statt als Service-Fehler zu zaehlen.

## 9. Brainstatus

Brain-Speicher:

- `brain_events.jsonl`: ca. 2.12 GB
- Zeilen: 66,358
- `BrainAdapter` schreibt Analyse-/Decision-Daten in JSONL.
- Learning Graph verarbeitet diese Datei fuer Graph und Learning-Metriken.

Bewertung:

- JSONL ist robust fuer Append-only, aber die Datei ist inzwischen sehr gross.
- API `/api/brain` ist mit ca. 40 KB nicht riesig, aber enthaelt umfangreiche letzte Entscheidung.
- Wachstum wird langfristig RAM, Startzeit, Graph-Aufbau und Storage-Scans belasten.

Risiken:

- Keine Rotation/Archivierung fuer Brain-Events sichtbar.
- `raw_result` kann in Brain-/Status-Snapshots landen.
- Dedupe ist vorhanden, aber historisches Wachstum bleibt.

Empfehlungen:

- Brain-Events periodisch partitionieren, z. B. pro Tag oder Monat.
- Kompakte Brain-Summary getrennt von voller Rohhistorie speichern.
- Retention-Regeln definieren: Rohdaten behalten, aber UI/API nur Zusammenfassung.
- Pruefen, ob `raw_result` im Brain-Event dauerhaft wirklich gebraucht wird.

## 10. Datenbank- und Speicherstatus

Pandorick nutzt aktuell primar JSON/JSONL statt einer echten relationalen Plattform-Datenbank.

Aktueller Storage laut API:

- Total files: 24
- Total records: 168,775
- Total size: 4.16 GB
- Scan interval: 60 Sekunden

Bewertung:

- JSON-Dateien sind gut fuer Transparenz, aber schlecht fuer grosse, haeufig geschriebene Listen.
- Stock-Dateien wurden bereits einmal korrupt und mussten repariert werden.
- `stock_decisions.json` und `stock_history.json` sind grosse JSON-Arrays; bei jedem Append wird typischerweise die ganze Datei gelesen/geschrieben.

Empfehlungen:

- Append-only JSONL fuer neue Records statt grosser JSON-Arrays.
- Atomic write: erst `.tmp`, dann replace.
- Automatische Backup-/Repair-Strategie fuer JSONDecodeError.
- Mittelfristig SQLite fuer Decisions, Signals, Statistics und Brain-Index.

## 11. Architekturpruefung

Gefundene doppelte/alte Bereiche:

- `PandorickKi/backups/phase_learning_graph_before_phase5_desktop`
- `PandorickKi/backups/phase_learning_graph_before_phase6_desktop`
- viele `PHASE*.md` Zwischenberichte im Root
- alte statische `control_center.html` im Root neben `web/static/control_center.html`
- `stock_legacy_data` wird im Storage-Scanner weiterhin beobachtet
- `NoopAdapter` existiert noch fuer Tests und Platzhalter
- Stock-Provider ist weiterhin `PlaceholderStockDataProvider`

Nicht loeschen, aber dokumentieren:

- Backups gehoeren in ein separates Archiv oder `backups/`.
- Root sollte spaeter auf Betriebsdateien, Reports und Startskripte reduziert werden.
- Alte Phase-Reports sollten in `docs/phases/` verschoben werden.

Moeglicher toter/uebergangsweiser Code:

- Test-/Noop-Pfade im Orchestrator.
- alte Backup-Kopien von API und Learning Graph.
- Root-HTML neben Web-HTML.

## 12. Sicherheitspruefung

Positiv:

- Webserver bindet lokal auf `127.0.0.1`.
- Control-Endpunkte pruefen lokale Adresse.
- `/api/config/public` gibt keine Telegram-Tokens aus.
- Learning Graph ist sanitisiert.
- Graph-API enthaelt keine Treffer fuer Tokens, API Keys, `raw_result`, `calculation`, `weight` oder absolute Benutzerpfade.

Kritisch:

- `/api/config/public` enthaelt `project_root`. Das ist kein Secret, aber ein lokaler Pfad und sollte fuer Browser-UI nicht notwendig sein.
- `/api/status` enthaelt interne Felder wie `raw_result`, `calculation`, `weight`.
- `/api/status` enthaelt sehr grosse verschachtelte Analyseobjekte.
- Interne Score-Berechnungen koennen ueber Status sichtbar werden.

Empfehlungen:

- Public API und Developer API trennen.
- `/api/status` fuer Browser stark kuerzen.
- Vollstaendige Debugdaten nur lokal im Developer-Diagnosemodus und optional hinter Flag anzeigen.
- `graph_sanitizer`-Prinzip auch fuer Status, Brain und Signals anwenden.

## 13. Performancebewertung

Prozess:

- Python-Prozess: ca. 709 MB Working Set, ca. 718 MB Private Memory.
- CPU-Messung schwankt je nach Probe; hohe Werte entstehen vor allem bei Datei-/Graph-Verarbeitung.

Haupttreiber:

- `brain_events.jsonl` 2.12 GB
- Storage-Scan ueber grosse Dateien
- Learning-Graph Vollaufbau
- Stock JSON-Arrays
- grosse `/api/status` Snapshots

Optimierungsvorschlaege:

- Graph lazy-loaden.
- Brain-Daten partitionieren.
- Status-Snapshot schlanker machen.
- grosse JSON-Arrays durch JSONL/SQLite ersetzen.
- Storage-Scanner inkrementell statt vollstaendig periodisch scannen.

## 14. Tests und Stabilitaet

Vorherige Tests nach Phase 7.4:

- `tests.test_statistics_and_storage`: 12 Tests OK
- `unittest discover`: 91 Tests OK

Aktuelle Phase 9 war reine Analysephase; es wurden keine Tests erneut gestartet, weil kein Code veraendert wurde.

## 15. Bekannte Schwaechen

HIGH:

- `/api/status` exponiert interne Debug-/Berechnungsdaten.
- `brain_events.jsonl` ist sehr gross und waechst weiter.
- Stock-Daten verwenden grosse JSON-Arrays und koennen bei Schreibabbruch korrupt werden.
- Learning-Graph Vollabruf ist langsam.

MEDIUM:

- Legacy-Statistik kann Benutzer verwirren.
- Persistierte Fehlerzaehler unterscheiden noch nicht sauber zwischen seit Start, heute und gesamt.
- Stock Engine nutzt noch Placeholder-Datenanbieter.
- Root-Verzeichnis enthaelt viele historische Phase-Reports und Backups.
- Prozess-RAM liegt bereits bei ca. 700 MB.

LOW:

- NoopAdapter und Testpfade sind noch im produktiven Code sichtbar.
- `project_root` in public config ist unnoetig.
- `ram_mb` in Developer-Statistik liefert aktuell null, obwohl Prozesswerte per PowerShell messbar sind.

## 16. Roadmap

### HIGH

1. Public Snapshot Sanitizer fuer `/api/status`, `/api/brain`, `/api/signals`.
2. Brain-Event-Wachstum begrenzen: Partitionierung oder SQLite-Index.
3. Atomic JSON writes fuer Stock-Dateien.
4. Automatischer JSON-Recovery-Modus mit Backup statt Service-Loop-Fehler.
5. Learning-Graph Vollabruf optimieren und standardmaessig nur Summary/Recent laden.

### MEDIUM

1. Legacy-Statistik einklappen oder als Developer-Legacy kennzeichnen.
2. Fehlerzaehler trennen in `since_start`, `today`, `total`.
3. Storage-Scanner inkrementell machen.
4. API-Antwortzeiten in Developer-Statistik persistieren.
5. Root-Dokumente strukturieren: `docs/phases`, `docs/reports`, `backups`.
6. Stock-Provider-Schicht fuer echten Anbieter vorbereiten, aber noch nicht anbinden.

### LOW

1. Noop/Testpfade optisch von Production-Code trennen.
2. Public Config um `project_root` reduzieren.
3. UI-Texte fuer Legacy/Developer/Trading weiter schaerfen.
4. Alte statische Root-HTML pruefen und spaeter archivieren.

## 17. Schlussbewertung

Pandorick ist funktional als lokale Plattform lauffaehig und nach der Stock-JSON-Reparatur wieder stabil. Fuer eine Foundation 1.0 sollte der Fokus nicht auf neuen Datenquellen liegen, sondern auf:

- stabiler Persistenz,
- schlanken oeffentlichen Snapshots,
- kontrolliertem Brain-Wachstum,
- sicherer API-Sanitization,
- Performance des Learning Graph,
- sauberer Dokumentstruktur.

Keine Dateien wurden geloescht. Keine Tradinglogik wurde veraendert. Keine Optimierungen wurden umgesetzt. Dieser Bericht ist die Grundlage fuer die naechste gemeinsame Priorisierung.
