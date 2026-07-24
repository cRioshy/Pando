# Phase 10.1 - Learning Graph Performance und Brain-Dateirotation Analyse

Stand: 2026-07-14

Status: Nur Analyse. Keine Codeaenderung. Keine Dateirotation. Keine Cache-Umstellung. Keine Datenmigration.

## 1. Kurzantworten

### 1. Ist die aktuelle 2,12-GB-Datei echtes JSONL oder ein JSON-Array?

Die Datei ist echtes JSONL.

Nachweis:

- Datei: `C:/Users/Admin/Desktop/PandorickKi/data/brain_events.jsonl`
- Groesse: ca. 2.13 GB
- Erste Zeile beginnt mit `{`
- Datei beginnt nicht mit `[`
- Jede Zeile ist ein einzelnes JSON-Objekt
- Letzte Zeile war vollstaendig und endete mit `}`

Beispiel-Felder einer Zeile:

- `received_at`
- `source_event_id`
- `event_type`
- `source`
- `market_type`
- `symbol`
- `direction`
- `probability`
- `source_timestamp`
- `payload`

### 2. Welche Funktionen lesen sie vollstaendig ein?

Vollstaendig oder potenziell vollstaendig:

1. `web/statistics_service.py`
   - `count_jsonl(path)`
   - wird vom Storage-Scanner fuer `.jsonl` verwendet
   - liest die komplette Datei zeilenweise und parsed jede Zeile mit `json.loads`

2. `web/statistics_service.py`
   - `AnalysisStatisticsService._reconstruct_jsonl(path)`
   - liest die komplette Datei nur, wenn Statistik-Reconstruction noetig ist
   - aktuell nicht bei jedem Request, aber bei fehlender/kaputter Statistik teuer

Nicht vollstaendig:

1. `learning_graph/graph_repository.py`
   - `recent_brain_events()`
   - liest nicht die ganze 2.13-GB-Datei
   - liest nur den Tail der Datei ueber `_recent_jsonl_lines()`
   - aktuelles Tail-Limit: 12 MB

Wichtig: Der Storage-Scanner zaehlt `brain_events.jsonl` aktuell doppelt, weil die Datei sowohl unter `platform_data` als auch als eigener Target `brain_events` erscheint. Damit wird die grosse JSONL-Datei periodisch zweimal gelesen/geparsed.

### 3. Was verursacht die 4,7 Sekunden beim Learning Graph?

Der Learning Graph liest nicht die komplette 2.13-GB-Brain-Datei. Die Verzögerung entsteht vor allem aus:

- Cold-Cache-Aufbau nach Cache-Invalidierung
- Lesen und Parsen des 12-MB-Brain-Tails
- Lesen zusaetzlicher Quellen aus Stock/Crypto-Dateien
- GraphBuilder-Aggregation von Nodes/Edges
- Sanitizer
- gleichzeitiger Systemlast durch Storage-Scanner/JSONL-Zaehler

Gemessene Einzelwerte:

| Schritt | Zeit |
|---|---:|
| `recent_brain_events(limit=1000)` | ca. 758 ms |
| `stock_history_records(limit=1000)` | ca. 54 ms |
| `stock_decision_records(limit=1000)` | ca. 16 ms |
| `crypto_trade_records(limit=1000)` | ca. 17 ms |
| `source_records(limit=1000)` | ca. 516 ms |
| `GraphBuilder.build(...)` | ca. 567 ms |
| `LearningGraphService.graph()` cold | ca. 1766 ms |
| `LearningGraphService.graph()` hot cache | ca. 0-4 ms |

Live-API-Messungen:

| Endpoint | Zeit |
|---|---:|
| `/api/v1/learning-graph` erster/cold Request | ca. 1337 ms bis 4733 ms |
| `/api/v1/learning-graph` direkter Cache-Hit | ca. 3-4 ms |
| `/api/v1/learning-graph/stats` | ca. 23 ms |
| `/api/v1/learning-graph/recent` | ca. 24 ms |

Der 4.7-Sekunden-Wert ist also wahrscheinlich Cold-Cache plus Lastspitze, nicht jeder Request.

### 4. Welche kleinste sichere Aenderung bringt den groessten Geschwindigkeitsgewinn?

Die kleinste sichere Aenderung mit groesstem Effekt ist nicht zuerst Graph-Layout, sondern Storage-/Reader-Entkopplung:

1. `brain_events.jsonl` im Storage-Scanner nicht doppelt scannen.
2. `count_jsonl()` fuer die 2.13-GB-Datei nicht alle 60 Sekunden voll parsen.
3. Stattdessen persistierte Metadaten/Index fuer Zeilenanzahl und Groesse verwenden.
4. Danach Learning Graph persistent aus einem kleinen Snapshot bedienen.

Warum:

- Vollstaendiges `count_jsonl()` auf `brain_events.jsonl` dauerte ca. 102.8 Sekunden.
- Das ist wesentlich teurer als der Graph-Cold-Build.
- Diese Last kann CPU und API-Antwortzeiten indirekt verschlechtern.

### 5. Welche Risiken bestehen bei der Umstellung waehrend Pandorick laeuft?

Risiken:

- Writer kann waehrend Rotation gerade eine Zeile schreiben.
- Reader kann eine halb geschriebene letzte Zeile sehen.
- Manifest/Index koennen inkonsistent werden, wenn Prozess stoppt.
- Doppelte Events koennen entstehen, wenn alte und neue Quelle gemeinsam gelesen werden.
- Eventverlust moeglich, wenn alte Datei abgeschaltet wird, bevor neuer Writer bestaetigt schreibt.
- Laufender Graph-Cache kann waehrend Umstellung alte und neue Quellen vermischen.
- Tests koennen Daten verfälschen, wenn sie gegen echte Produktionspfade laufen.

Sichere Vorgehensweise:

1. Pandorick stoppen.
2. Code-Backup anlegen.
3. Neue Repository-Schicht im Testpfad validieren.
4. Writer zunaechst dual-faehig bauen, aber Legacy-Datei nicht veraendern.
5. Neue Events erst nach bestandenem Test nur in Rotation schreiben.
6. Reader dedupliziert alte und neue Quellen.
7. Manifest/Index atomisch schreiben.
8. Nach Neustart Health/API/Graph pruefen.

## 2. Aktueller Schreibpfad

Schreiber:

- Datei: `adapters/brain_adapter.py`
- Methode: `BrainAdapter._append_jsonl(record)`
- Speicherpfad: `config.brain_events_file`
- Standard: `C:/Users/Admin/Desktop/PandorickKi/data/brain_events.jsonl`

Aktuelles Verhalten:

```text
BrainAdapter empfängt:
  STOCK_ANALYSIS_FINISHED
  CRYPTO_ANALYSIS_FINISHED

BrainAdapter erstellt Record:
  received_at
  source_event_id
  event_type
  source
  market_type
  symbol
  direction
  probability
  source_timestamp
  payload

BrainAdapter schreibt:
  open(path, "a")
  json.dumps(record) + "\n"
```

Bewertung:

- Append-only JSONL ist grundsaetzlich passend.
- Aktuell keine sichtbare Thread-Lock-Sicherung im Writer.
- Kein explizites `flush`.
- Kein `fsync`.
- Keine Rotation.
- Keine Manifest-/Indexdatei.
- Keine explizite Recovery bei unvollstaendiger letzter Zeile.

## 3. Aktuelle Leser

### Learning Graph

Dateien:

- `learning_graph/graph_service.py`
- `learning_graph/graph_repository.py`
- `learning_graph/graph_builder.py`
- `learning_graph/graph_sanitizer.py`

Lesepfad:

```text
Web API
  -> LearningGraphService.graph()
  -> GraphRepository.source_records()
  -> GraphRepository.recent_brain_events()
  -> GraphBuilder.build()
  -> GraphSanitizer.sanitize_graph()
```

Wichtig:

- `recent_brain_events()` liest nur den Tail der Brain-Datei.
- Tail-Limit: 12 MB.
- GraphService hat In-Memory-Cache mit TTL.
- Cache wird bei Learning-Graph-Source-Events invalidiert.

Zusaetzliche Quellen:

- `stock_project_path / data / stock_history.json`
- `stock_project_path / data / decisions.json`
- `project_root / data / crypto_active_trades.json`

Auffaellig:

- GraphRepository nutzt fuer Stock-Zusatzquellen aktuell `pandorick_stock_bot/data/...`, also Legacy-Stock-Daten.
- Die aktiven grossen Stock-Dateien liegen unter `pandorick_stock_bot/data_stock/...`.
- Aktuelle Stock-Events kommen aber trotzdem ueber `brain_events.jsonl` im Graph an.

### Statistics

Dateien:

- `web/statistics_service.py`

Lesepfade:

- `AnalysisStatisticsService.reconstruct()`
- `StorageStatisticsService.refresh()`
- `count_jsonl()`

Bewertung:

- Statistik-Reconstruction scannt Brain-Events nur bei Bedarf.
- Storage-Scanner scannt JSONL-Dateien periodisch.
- `brain_events.jsonl` wird aktuell doppelt im Storage-Snapshot erfasst:
  - innerhalb `platform_data`
  - separat als Target `brain_events`
- Dadurch entstehen doppelte Record-Counts und doppelte Full-Scans.

## 4. Eventrate und Wachstum

Gemessener Tail der Brain-Datei:

- Tail-Records: 105
- Zeitspanne: ca. 1073 Sekunden
- Events pro Minute: ca. 5.87
- Hochrechnung pro Tag: ca. 8454 Events/Tag

Historisch grob:

- Gesamtzeilen: ca. 66,563
- Zeitraum seit erstem Event: 2026-07-10 bis 2026-07-14
- Grobe Tagesrate: ca. 8k bis 14k Events/Tag, je nach Laufmodus und Stock/Crypto-Zyklen.

Wachstumsrisiko:

- Bei mehreren tausend Events pro Tag bleibt eine einzige JSONL-Datei schnell ein Performance- und Recovery-Problem.
- Die einzelnen Records sind gross, weil `payload` umfangreiche Analyse- und Rohdaten enthaelt.

## 5. Welche Felder braucht der Learning Graph wirklich?

Der GraphBuilder benoetigt fuer die oeffentliche Graphansicht im Kern:

Top-Level:

- `symbol`
- `market_type`
- `direction`
- `received_at`
- `source_timestamp`
- `probability`
- `event_type`
- `source_event_id`

Payload:

- `payload.indicators`
- optional `payload.public_result`
- optional `payload.raw_result.result`, aber nur fuer erlaubte Result Labels

Aus `payload.indicators` werden nur oeffentliche Kategorien gebraucht:

- EMA
- RSI
- MACD
- ATR
- Gap
- Relative Strength
- Volatility
- Volume
- Open Interest
- Funding Rate
- Trend Consensus

Nicht notwendig fuer den oeffentlichen Graph:

- vollstaendige Candle-Listen
- komplette `raw_result`
- Rechenschritte
- `calculation`
- `weight`
- interne Reasoning-/Debugdaten
- komplette Risk-Objekte
- volle Brain-Memory-Details
- absolute Pfade
- Secrets/Tokens

## 6. Was kann historisch archiviert werden?

Kann archiviert/aus dem Live-Graph-Pfad herausgehalten werden:

- alte `payload.raw_result`
- alte detaillierte Calculation-Steps
- alte komplette Candle-Snapshots
- alte Risk-/Reason-Details
- alte Debug-Objekte
- historische abgeschlossene Tage

Soll fuer Live-Graph schnell verfuegbar bleiben:

- aktuelle/letzte Events je Markt
- kompakte Node/Edge-Snapshots
- Zaehler je Symbol/Pattern/Decision
- Manifest/Index je Tagesdatei
- letzte verarbeitete Datei/Zeile fuer inkrementellen Cache

## 7. Aktuelle Atomik und Recovery

Gefundene Schreibstellen:

- `BrainAdapter._append_jsonl()` schreibt direkt append-only.
- `StatisticsService.save()` schreibt `system_statistics.json` direkt mit `write_text`.
- `SharedState.save()` schreibt direkt per `json.dump`.
- `CryptoTradeTracker` schreibt Active-JSON direkt und History JSONL append-only.
- `TelegramAdapter` schreibt JSONL append-only.
- `StockBot.save_json()` schreibt grosse JSON-Dateien direkt per `open("w")` und `json.dump`.

Nicht sichtbar:

- kein allgemeines `os.replace` fuer atomische JSON-Schreibvorgaenge
- kein zentrales Repository fuer Brain-Events
- kein Manifest/Index
- kein Rotation-Lock
- kein fsync-Konzept

Recovery-Verhalten:

- GraphRepository ueberspringt kaputte JSONL-Zeilen beim Parsen.
- Statistics-Reconstruction ueberspringt kaputte JSONL-Zeilen.
- Storage `count_jsonl()` wuerde bei kaputter Zeile eine Exception werfen und Datei/Folder als WARN markieren.
- StockBot brach zuletzt bei kaputten JSON-Dateien ab; manuelle Reparatur war notwendig.

## 8. Vorher-Benchmarks

### Datei

| Messwert | Wert |
|---|---:|
| `brain_events.jsonl` Groesse | ca. 2.13 GB |
| Zeilen | ca. 66,563 |
| Letzte Zeile vollstaendig | ja |

### JSONL-Vollscan

| Operation | Zeit |
|---|---:|
| `count_jsonl(brain_events.jsonl)` | ca. 102,848 ms |

### Learning Graph intern

| Operation | Zeit |
|---|---:|
| Brain Tail lesen/parsen | ca. 758 ms |
| Stock History Zusatzquelle | ca. 54 ms |
| Stock Decision Zusatzquelle | ca. 16 ms |
| Crypto Trade Zusatzquelle | ca. 17 ms |
| Source Records gesamt | ca. 516 ms |
| GraphBuilder | ca. 567 ms |
| Service cold | ca. 1766 ms |
| Service hot cache | ca. 0-4 ms |

### API

| Endpoint | Vorher |
|---|---:|
| `/api/v1/learning-graph` cold/live | ca. 1337 ms bis 4733 ms |
| `/api/v1/learning-graph` hot | ca. 3-4 ms |
| `/api/v1/learning-graph/stats` | ca. 23 ms |
| `/api/v1/learning-graph/recent` | ca. 24 ms |

### Prozess

| Messwert | Wert |
|---|---:|
| Python Working Set | ca. 623-709 MB |
| Python Private Memory | ca. 640-718 MB |

## 9. Risiken im Ist-Zustand

High:

- Storage-Scanner liest/parst 2.13-GB-Brain-Datei periodisch vollstaendig.
- Brain-Datei wird doppelt im Storage-Scanner erfasst.
- Eine einzige riesige Brain-Datei bleibt ein Wachstums- und Recovery-Risiko.
- Brain-Writer hat keine Rotation und kein Manifest.
- Public Graph ist performant bei Hot Cache, aber Cold Cache bleibt teuer.

Medium:

- GraphRepository mischt aktuelle Brain-Events mit Legacy-Stock-Daten aus `data/`.
- Stats-Reconstruction waere bei Verlust der Statistikdatei teuer.
- JSON-Schreiber sind nicht atomisch.
- Unvollstaendige letzte JSONL-Zeile ist fuer Graph/Stats teilweise toleriert, fuer Storage aber WARN/Fehler.

Low:

- API-Benchmarks schwanken stark je nach Storage-Scan.
- `ram_mb` in Web-Developer-Statistik liefert aktuell null, obwohl Prozess-RAM extern messbar ist.

## 10. Umsetzungsplan fuer Phase 10.2 bis 10.4

### Phase 10.2 - Reader-/Writer-Schicht und Rotation

Vorschlag:

1. Neue zentrale Datei-Schicht erstellen, z. B. `brain_event_store.py`.
2. `BrainEventWriter`:
   - schreibt neue Events in `brain_events/YYYY-MM-DD/events_0001.jsonl`
   - Rotation bei konfigurierbarer Groesse, Standard 200 MB
   - Thread-Lock
   - append-only
   - periodischer flush
   - Index/Manifest atomisch via `.tmp` plus `os.replace`
3. `BrainEventReader`:
   - liest Legacy-Datei
   - liest neue Rotation
   - dedupliziert ueber `source_event_id`
   - erzeugt deterministische technische ID, falls Event-ID fehlt
   - ueberspringt unvollstaendige letzte Zeile
4. `BrainAdapter` nur auf Writer-Schicht umstellen.
5. Tests fuer Rotation, Tageswechsel, Manifest, Index, Dedupe, Parallelzugriff.
6. Danach anhalten.

### Phase 10.3 - Inkrementeller Learning-Graph-Cache

Vorschlag:

1. `learning_graph/cache/` einführen.
2. Cache-Dateien:
   - `graph_snapshot.json`
   - `graph_stats.json`
   - `node_index.json`
   - `edge_index.json`
   - `cache_state.json`
3. Cache verarbeitet nur neue Events seit letzter Quelldatei/Offset.
4. API liest zuerst Snapshot.
5. GraphBuilder/Sanitizer bleiben aktiv.
6. Benchmarks vorher/nachher.
7. Danach anhalten.

### Phase 10.4 - Recovery und Archivvorbereitung

Vorschlag:

1. Recovery fuer kaputte Manifest-/Index-/Cache-Dateien.
2. Optional `.jsonl.gz`-Reader vorbereiten.
3. Komprimierung noch deaktiviert lassen.
4. Gesamttests.
5. Abschlussbericht.

## 11. Empfehlung vor Freigabe

Ich empfehle als ersten Umsetzungsschritt:

1. Keine Migration der alten 2.13-GB-Datei.
2. Legacy-Datei unveraendert lassen.
3. Neue Events ab Umstellung in rotierte Tagesdateien schreiben.
4. Reader kann Legacy + Rotation gemeinsam lesen.
5. Storage-Scanner so umbauen, dass die Legacy-Brain-Datei nicht mehr doppelt und nicht mehr alle 60 Sekunden voll geparsed wird.

Das bringt die groesste Stabilitaets- und Performance-Verbesserung mit minimalem Risiko.

## 12. Stopp-Punkt

Phase 10.1 ist hiermit abgeschlossen.

Es wurde noch kein Code veraendert.

Naechster Schritt nur nach Freigabe: Phase 10.2.
