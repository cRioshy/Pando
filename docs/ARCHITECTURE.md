# PandorickKi – Ist-Architektur

Stand: 8. August 2026

Dieses Dokument beschreibt ausschließlich die im aktuellen Code nachweisbare Architektur. Es ist keine Zielarchitektur.

## Systemkontext

```mermaid
flowchart LR
    BN["Binance Spot/Futures"] --> CM["CryptoMarketDataService"]
    BG["Bitget Candle-Fallback"] --> CM
    CM --> CA["CryptoAdapter"]
    CE["Externes Crypto-Projekt: Analysepipeline"] --> CA
    SE["Externes Stock-Projekt"] --> SA["StockAdapter"]
    CP["Optionale Commodity-Quelle"] --> CO["CommodityAdapter"]
    CA --> DQ["Feature-Datenqualität v1: OHLCV, Zeit, Duplikate, Warmup"]
    SA --> DQ
    DQ --> FE["FeatureEngine"]
    FE -. additive Features .-> CA
    FE -. additive Features .-> SA
    DG["DecisionGateAuditAdapter: optional, fail-closed Observer"]
    DQ -. kompakte feature_quality .-> BA
    BA -. BRAIN_DECISION_RECEIVED .-> DG
    DG --> GA["Begrenztes Decision-Gate-Audit"]
    DG -. keine aktive Freigabe .-> DC
    CA --> EB["Synchroner In-Process EventBus"]
    SA --> EB
    CO --> EB
    EB --> BA["BrainAdapter: persistieren und weiterleiten"]
    BA --> EB
    EB --> DC["DecisionSignalAdapter: normalisieren und persistieren"]
    DC --> EB
    EB --> OT["OutcomeTracker: Simulation"]
    EB --> CT["CryptoTradeTracker: Simulation"]
    EB --> TG["Telegram: Dry-Run oder optionaler Versand"]
    EB --> NQ["NeuroBrain FIFO-Queue: 2048, drop newest"]
    NQ --> NW["Ein Writer: Batch bis 64"]
    NW --> NB["NeuroBrainReceiver: lokale read-only Inbox"]
    EB --> CC["ControlCenterAdapter"]
    EB --> EJ["ServiceErrorJournal: kompakt und secret-gefiltert"]
    EJ --> EF["Begrenzte JSONL-Archive + atomare Zusammenfassung"]
    OR["Orchestrator"] --> SS["SharedState"]
    OR --> HM["HealthMonitor"]
    SS --> CC
    HM --> CC
    CC --> WEB["ThreadingHTTPServer + WebSocket + Browser UI"]
    LEDGER["JSON/JSONL/SQLite-Historie"] --> ST["Statistik, Reports und Graphprojektion"]
    ST --> LM["Learning-Metrikvertrag v1: explizite Nenner, kein ML-Training"]
    ST --> CACHE["Persistenter Storage-/Report-Cache"]
    LM --> WEB
    CACHE --> WEB
```

## Prozess- und Lebenszyklusmodell

`main.py` erzeugt den `Orchestrator` und startet abhängig von den CLI-Argumenten einen einzelnen oder kontinuierlichen Lauf. `Orchestrator.start()` startet Adapter sequentiell. Pro Zyklus werden deren `run_once()`-Methoden als AsyncIO-Tasks erstellt und mit `asyncio.gather()` gemeinsam abgewartet. Ein allgemeiner Timeout um alle Adaptertasks existiert nicht. Der Warteabschnitt zwischen Zyklen prüft Stop und Restart höchstens alle 100 Millisekunden. Restart stoppt und startet dieselben Adapterinstanzen im Prozess; bei aktivem Terminal-Control-Center wird dessen Live-Task ebenfalls wieder gestartet. Ein bereits laufender Adapterzyklus wird bewusst nicht hart abgebrochen.

Im Webmodus erzeugt `main.py` zusätzlich `WebControlServer`. Der HTTP-Server läuft als `ThreadingHTTPServer` in einem Hintergrundthread. Periodische Webaufgaben laufen im vorhandenen AsyncIO-Loop; der Storage-Scanner verwendet zusätzlich genau einen eigenen Workerthread.

## Adapter- und Ereignisfluss

```mermaid
sequenceDiagram
    participant Source as Externe Marktquelle
    participant Market as Marktadapter
    participant Quality as Datenqualität v1
    participant Feature as FeatureEngine
    participant Bus as EventBus
    participant Brain as BrainAdapter
    participant Gate as DecisionGateAuditAdapter
    participant Decision as DecisionSignalAdapter
    participant Tracker as Outcome/Trade Tracker
    participant View as Control Center/Statistik
    participant Telegram as TelegramAdapter

    Source->>Market: Analyse und OHLCV
    Market->>Quality: maximal 500 OHLCV-Kerzen
    Quality->>Quality: validieren, sortieren, keep_last, Warmup
    Quality->>Feature: normalisierte Kerzen + Qualitätsbericht
    Feature-->>Market: live_features ohne Targets
    Market->>Bus: MARKET_DATA_UPDATED
    Market->>Bus: ANALYSIS_FINISHED
    Bus->>Brain: abgeschlossene Analyse
    Brain->>Brain: rotierende JSONL-Persistenz
    Brain->>Bus: BRAIN_DECISION_RECEIVED
    Bus-->>Gate: optional parallel beobachten
    Gate->>Gate: fail-closed bewerten + begrenzt auditieren
    Gate-->>Bus: DECISION_GATE_EVALUATED (keine Freigabe)
    Brain->>Bus: AI_LEARNING_UPDATED
    Bus->>Decision: Brain-Payload
    Decision->>Decision: normalisieren, IDs und Ledger
    Decision->>Bus: DECISION_CREATED
    Decision->>Bus: SIGNAL_CREATED
    Bus->>Tracker: simulierten Trade öffnen/aktualisieren
    Bus->>View: Status, Märkte, Statistik und Graph
    Bus->>Telegram: Analyse/Trade direkt
```

Der `EventBus` kopiert Handler unter einem Lock und führt sie danach synchron im veröffentlichenden Thread aus. Seine `queue_size()` ist die Größe der begrenzten History-Deque und keine Arbeitsqueue.

## Komponentenverantwortung

| Komponente | Tatsächliche Verantwortung | Nicht implementiert |
|---|---|---|
| `CryptoMarketDataService` | Binance-Kerzen, Bitget-Fallback, Retry, optionales Open Interest/Funding | Orders, private APIs |
| `CryptoAdapter` | Normalisierte Marktdaten an externe Crypto-Analyse übergeben, Preise, maximal 500 Kerzen für Features, Fehlerdiagnose, Ereignisse | Börsenorder |
| `StockAdapter` | Externe Aktienanalyse, Preise, maximal 500 Kerzen für Features, Ereignisse | Börsenorder |
| `CommodityAdapter` | Optionale Rohstoffdaten und Ereignisse | Feature-Engine-Anbindung |
| `feature_data_quality_contract.py` | Versionierte OHLCV-Prüfung, Zeitordnung, `keep_last`-Duplikate, Mindestkerzen, Warmup und Qualitätsbericht | Fachliche Decision-Freigabe |
| `FeatureEngine` | Technische Features, Qualitätsmetadaten und optionale historische Targets | ML-Training, Decision-Gate, New-Candle-Cache |
| `decision_gate_contract.py` | Explizite fail-closed Observer-Bewertung, kompakte Qualitätsprojektion und Reason Codes | Aktive Signal-/Telegram-Freigabe, Orders |
| `DecisionGateAuditAdapter` | Optionaler EventBus-Observer, Duplikatschutz, begrenztes Audit-Ledger | Decision-/Signal-Erzeugung, Telegram-Freigabe, Orders |
| `BrainAdapter` | Rotierende Analysepersistenz und Folgeereignisse | Eigene KI-Inferenz oder Faktenprüfung |
| `DecisionSignalAdapter` | Normalisierung, deterministische IDs, Decision-/Signal-Ledger | Risiko-Policy, Confidence-Gate, Konfliktlösung |
| `OutcomeTracker` | Simulierte allgemeine Trade-Outcomes | Reale Orders |
| `CryptoTradeTracker` | Simulierte Crypto-Trades | Reale Orders |
| `NeuroBrainReceiverAdapter` | Read-only Datei-Inbox, Duplikatschutz, begrenzte FIFO-Queue, Batch-Writer und Flush-Shutdown | Rückkanal in Decision Core |
| `TelegramAdapter` | Dry-Run oder optionaler Nachrichtenversand | Zwingende finale Decision-Freigabe |
| `ControlCenterAdapter` | Kompakte Event-/Statussicht | Stale-Heartbeat-Klassifikation |
| `ServiceErrorJournal` | Versionierte Projektion von Fehlerereignissen, Secret-Filter, begrenzte Rotation, persistente Erst-/Letztbeobachtung | Vollständige Payload-Ablage, zentrale Retention aller anderen Ledger |
| `learning_metrics_contract.py` | Einheitliche Outcome-/Hit-Rate-/Abdeckungsprojektion mit expliziten Zählern und Nennern | ML-Training, Modellbewertung oder Musterlernen |

## Persistenzarchitektur

```mermaid
flowchart TD
    EVENTS["Plattformereignisse"] --> BRAIN["Brain JSONL, datums-/größenrotiert"]
    EVENTS --> DEC["Decision JSONL, größenrotiert"]
    EVENTS --> SIG["Signal JSONL, größenrotiert"]
    EVENTS --> OUT["Outcome JSONL, größenrotiert"]
    EVENTS --> GATE["Decision-Gate-Audit JSONL, 5 MiB + max. 4 Archive"]
    EVENTS --> MP["Kompakte Marktprojektion v1"]
    EVENTS --> OP["Kompakte Observer-Projektion v1"]
    MP --> NEURO["NeuroBrain Inbox JSONL"]
    OP --> NEURO
    ERRORS["Nur Fehlerereignisse"] --> ERRLOG["service_errors.jsonl, 5 MiB + max. 4 Archive"]
    ERRORS --> ERRSUM["service_error_summary.json, atomar + max. 500 Fingerprints"]
    OPEN["Offene simulierte Trades"] --> JSON["Konfliktresistent atomar ersetztes JSON"]
    BRAIN & DEC & SIG & OUT & NEURO --> SCAN["StorageStatisticsService"]
    SQLITE["Vorhandene SQLite-Dateien"] --> SCAN
    SCAN --> UNIQUE["Einmaliger Scan je aufgelöstem physischen Pfad"]
    UNIQUE --> LOGICAL["Logische Kategorien und Dateiverweise"]
    UNIQUE --> PHYSICAL["Physisch eindeutige Gesamtwerte"]
    UNIQUE --> INDEX["storage_file_index.json"]
    UNIQUE --> METRICS["Phasenlaufzeiten und kumulativer JSONL-Fortschritt"]
    LOGICAL & PHYSICAL --> SNAP["storage_statistics.json"]
    METRICS --> SNAP
    INDEX -->|"Offsets und Dateiidentität"| SCAN
    SNAP --> API["Storage API und Control Center"]
```

Der Scanner lädt beim Start den letzten Cache. `start_scan()` akzeptiert nur einen laufenden Scan, arbeitet im Hintergrund und liefert unmittelbar Scan-ID und Status zurück. Alle Zielpfade werden logisch beibehalten, aber pro Scan über ihren aufgelösten physischen Pfad dedupliziert. Ein gemeinsamer Dateiergebnis-Cache verhindert wiederholtes Lesen und mehrfachen Budgetverbrauch; die Kategorieansicht erhält weiterhin den jeweils passenden relativen Pfad. `total_*` bezeichnet verifizierte physische Werte, zusätzlich werden `physical_total_*`, `logical_total_*` und `overlapping_file_references` explizit geliefert. Alte Caches ohne diese Felder werden als `LEGACY_CACHE` statt als physisch verifiziert markiert.

JSONL-Dateien werden binär ab dem persistierten Offset gelesen; unvollständige letzte Zeilen werden erst nach einem Zeilenabschluss übernommen. Schrumpfung oder Austausch einer Datei setzt den Index zurück. Ein globales Standardbudget von 64 MiB begrenzt jeden Lauf. Der Scanstatus projiziert kumulativ Gesamt-, indexierte und restliche Bytes, vollständige JSONL-Dateien sowie aus Budget und Intervall abgeleitete Restläufe/-zeit. Große SQLite-, JSON-, CSV- und Logdateien werden nur per Metadaten erfasst. Cache und Index werden über temporäre Dateien und `os.replace()` atomar ersetzt.

Timeout, Abbruch und einzelne verschwundene Dateien beenden nicht die Verfügbarkeit des letzten Caches. Laufzeiten werden für Zielermittlung, Pfadauflösung, Metadaten, Fingerprint, Dateiverarbeitung, Index- und Cachepersistenz getrennt erfasst. Der Realbenchmark mit 64 MiB blieb bei 2,135 Sekunden und damit deutlich unter dem 30-Sekunden-Limit; der Dauerbetrieb muss nach Neustart weiter beobachtet werden.

Das Fehlerjournal wird vor den Adaptern an den Wildcard-Kanal des EventBus gehängt und nach deren Shutdown entfernt. Es speichert Ereignis-/Korrelations-ID, Zeit, Topic, Service, Stufe, Symbol, Provider, Fehlerart und bis zu zehn kompakte Provider-Versuche. Secrets werden anhand sensibler Schlüsselnamen und Textmustern ersetzt; rohe Payloads und Response-Bodies werden nicht persistiert. Eigene Schreibfehler werden im Journal-Health gezählt und nicht an den Publisher weitergeworfen.

Der Scanner besitzt einen eigenen Lebenszyklus-Lock und einen dauerhaften `closed`-Zustand. `start_scan()` lehnt nach `close()` neue Hintergrundscans mit `CLOSED` ab; synchrone `refresh()`-Aufrufe liefern danach nur noch den letzten Snapshot. `close()` setzt das Abbruchsignal und wartet ohne willkürlichen Ein-Sekunden-Abbruch auf den aktiven Worker. Eine Sperrbarriere stellt zusätzlich sicher, dass auch ein synchron laufender Refresh beendet ist. Deshalb kann nach Rückkehr von `close()` kein Cache- oder Index-Schreibvorgang mehr stattfinden. Wiederholtes `close()` ist idempotent.

`atomic_json.py` stellt für kleine, häufig ersetzte Runtime-Zustände einen konfliktresistenten Pfad bereit. Er serialisiert Schreiber auf denselben aufgelösten Zielpfad, schreibt jede Version in eine eigene Temp-Datei im Zielverzeichnis, validiert und `fsync`-t den JSON-Inhalt und ersetzt danach atomar. Transiente Windows-`PermissionError`- beziehungsweise Sharing-Verstöße werden mit kurzen begrenzten Delays erneut versucht; bei endgültigem Fehler wird nur die eigene Temp-Datei aufgeräumt und der Fehler weitergereicht. Aktuell verwenden NeuroBrain-Status und aktive Crypto-Trades diesen Helfer. Beide Adapter halten ihre Zustandssperre bis zum erfolgreichen Replace, damit Snapshot- und Dateireihenfolge übereinstimmen.

Der NeuroBrain-Wildcard-Handler führt keine Dateioperation mehr im Publisher-Thread aus. Er prüft Topic und Duplikat, erstellt die kompakte Projektion und verwendet `put_nowait`. Die Queue ist standardmäßig auf 2048 Einträge begrenzt; bei Überlauf bleibt die bereits akzeptierte FIFO-Reihenfolge erhalten und nur das neueste Ereignis wird mit `dropped_events` abgelehnt. Ein nicht-daemonisierter Worker sammelt bis zu 64 Einträge beziehungsweise 250 Millisekunden und schreibt sie geordnet über `RotatingJsonlLedger.append_many()`. Status- und Receipt-Fehler beenden den Worker nicht. Beim Shutdown wird zuerst abonniertes Neugeschäft gestoppt, danach die Queue vollständig geleert und der Thread gejoint; nach Rückkehr kann kein Queue-Schreibvorgang mehr laufen.

## Webarchitektur

```mermaid
flowchart LR
    API["HTTP JSON API"] --> UI["Control Center"]
    WS["/ws/live"] --> UI
    WS -->|"close/error"| POLL["ein Polling-Fallback"]
    POLL -->|"Backoff-Reconnect"| WS
    STATIC["Lokale HTML/CSS/JS/Vendor-Dateien"] --> UI
    STATE["SharedState + ControlCenterAdapter"] --> API
    STATE --> STALE["Heartbeat-Alter + STALE-Projektion"]
    STALE --> API
    STALE --> WS
    STATS["Analyse-/Storage-Statistik"] --> API
    GRAPH["Learning/Knowledge Graph"] --> API
    RICK["Read-only Rick API + Audit"] --> API
```

Die Web-API sanitiziert öffentliche Payloads und entfernt Secrets sowie große interne Felder. Markt-/Heartbeat-Broadcasts und Statistikupdates werden gedrosselt. Der Storage-Refresh antwortet asynchron mit HTTP `202`.

Die Browseroberfläche verwendet WebSocket-Liveupdates und genau einen idempotenten HTTP-Polling-Fallback. Polling-Aufrufe sind single-flight. Nach `close` oder `error` startet ein begrenzter exponentieller Reconnect; Verbindungsgenerationen verhindern, dass alte Socket-Callbacks den neuen Zustand überschreiben. Storage- und Learning-Graph-Ladevorgänge sind single-flight. Graphinteraktionen werden mit `requestAnimationFrame` koalesziert; Force-Layoutpositionen werden für unveränderte Knoten-/Kantenstruktur wiederverwendet. Lokale Skripte verwenden `defer` und Cache-Buster.

## Learning- und Outcome-Metrikgrenze

```mermaid
flowchart LR
    DEC["Finale Decisions im betrachteten Scope"] --> ELIGIBLE["Outcome-faehig: LONG/SHORT"]
    OUT["Geschlossene simulierte Outcomes"] --> MATCH["decision_id-Zuordnung"]
    MATCH --> CLASS["Win / Loss / Breakeven / Unknown"]
    CLASS --> HIT["Hit-Rate = Wins / (Wins + Losses)"]
    ELIGIBLE --> COVERAGE["Outcome-Abdeckung = zugeordnet / outcome-faehig"]
    MATCH --> COVERAGE
    UPDATE["AI_LEARNING_UPDATED"] --> PROJECTION["Learning-Update-Event"]
    PROJECTION -. "kein Trainingsnachweis" .-> NOML["ml_training.active = false"]
    GRAPH["Graph Pattern Nodes"] --> BUCKETS["Muster-Buckets"]
    BUCKETS -. "kein gelerntes Modellmuster" .-> NOML
```

`learning_metrics_contract.py` ist die ausführbare Version-1-Referenz. Report und Trading-Statistik verwenden denselben Hit-Rate-Nenner; Breakeven und unbekannte Outcomes werden separat ausgewiesen. Der Report darf Outcome-Abdeckung nur aus per `decision_id` zugeordneten Outcomes und Decisions desselben geladenen Fensters berechnen. Historische Aggregatzähler liefern keine Abdeckung, wenn ihr Rekonstruktionsscope nicht übereinstimmt. Alle öffentlichen Raten enthalten Zähler und Nenner.

Der Graph benennt beobachtete Kategorien als `pattern_buckets` und Datensätze im geladenen Tagesfenster als `learning_projection_records_today`. Der kumulative Wert `learning_update_events_total` bleibt davon getrennt. Keine dieser Projektionen belegt Modelltraining; Version 1 veröffentlicht deshalb `ml_training_active=false` und `model_updates=0`.

## Sicherheitsgrenzen

- Keine reale Orderausführung im Kern.
- Webserver standardmäßig nur lokal binden.
- Telegram standardmäßig deaktiviert und im Dry-Run.
- Rick- und Steuerendpunkte bei externer Freigabe zusätzlich absichern.
- Secrets ausschließlich über lokale Umgebungskonfiguration bereitstellen.
- Runtime-Historien, Lerndaten und Tokens nicht löschen oder veröffentlichen.
- Externe Legacy-Projekte bleiben außerhalb dieses Repositories und werden nur adaptiert.
- Crypto-Marktdaten verwenden ausschließlich öffentliche read-only HTTP-Endpunkte; Futures-Kontext ist optional und löst keine Orders aus.

## Kompakter Event-Payload-Vertrag

Die produktiv aktiven Verträge `pandorickki.compact-market-event` und `pandorickki.compact-observer-event`, jeweils Version 1, beschreiben die kontrollierte Migration weg von vollständigen Raw Results. Ihre ausführbare Referenz ist `event_payload_contract.py`; Feldmatrix, Topiczuordnung und Migrationsregeln stehen in `docs/EVENT_PAYLOAD_CONTRACT.md`.

```mermaid
flowchart LR
    LEGACY["Heutige normalisierte Markt-Events samt raw_result"] --> PROJECT["Versionierte kompakte Projektion v1"]
    PROJECT --> BRAIN["Brain"]
    PROJECT --> DECISION["Decision Core"]
    PROJECT --> TRACKERS["Trade- und Outcome-Tracker"]
    PROJECT --> UI["Control Center / Telegram Dry-Run"]
    PROJECT --> LEARNING["Learning Graph"]
    PROJECT --> NEURO["Marktbezogene NeuroBrain-Zeilen"]
    OBSERVER["Learning-/Aggregat-Events"] --> OPROJECT["Kompakte Observer-Projektion v1"]
    OPROJECT --> NEUROOBS["Observer-NeuroBrain-Zeilen"]
    LEGACY -. "nur während Migration" .-> SWING["Kerzen zu recent_swing_low/high verdichten"]
    LEGACY -. "nur während Migration" .-> RESULT["raw result label zu public_result"]
    SWING --> PROJECT
    RESULT --> PROJECT
```

Brain verwendet die Marktprojektion als aktive Eingangsgrenze für neue History und `BRAIN_DECISION_RECEIVED`; Decision Core verwendet sie für neue Decision-/Signal-Events und beide Ledger. NeuroBrain behält eine kompakte Kopfsicht und wählt sein Detailpayload topicbasiert: Learning und aggregierte Aktienupdates verwenden den Observer-Vertrag, einzelwertige Crypto-/Commodity-Updates sowie Analysis-, Brain-, Decision-, Signal- und Trade-Topics den Marktvertrag. Der Crypto Trade Tracker liest `market_context.recent_swing_low/high` und der Learning Graph `public_result` jeweils bevorzugt. Bestehende Payloads und History bleiben über die bisherigen Raw-Lesepfade verfügbar und werden nicht umgeschrieben. Beide NeuroBrain-Schemata sind kontrolliert live verifiziert.

## Crypto-Ausfall- und Fallback-Semantik

```mermaid
flowchart LR
    CA["CryptoAdapter pro Symbol"] --> BS["Binance Spot-Kerzen mit Retry"]
    BS -->|Erfolg| FC["Optionale Binance-Futures-Daten"]
    BS -->|Fehler| BG["Bitget Spot-Kerzen mit Retry"]
    BG -->|Erfolg| FC
    BG -->|Fehler| ER["CRYPTO_SERVICE_ERROR mit Diagnostik"]
    FC -->|OI/Funding verfügbar oder None| LP["Legacy-Analyse persist=False"]
    LP --> EV["CRYPTO_ANALYSIS_FINISHED"]
    ER --> HS["Service ERROR bei null Ergebnissen"]
    EV --> HS2["OK oder DEGRADED gemäß Zyklusergebnis"]
```

Die projektlokale `.venv` ist Laufzeitisolation, kein Daten- oder Architekturservice. `setup_local_env.bat` legt sie bei Bedarf an, installiert die deklarierte Zeitzonendaten-Abhängigkeit und der Preflight prüft zentrale Dateien, Imports und `America/New_York` vor jedem Batch-Start.

## Bekannte Architekturgrenzen

- Synchroner EventBus ohne allgemeine Backpressure; ausschließlich der NeuroBrain-Dateiconsumer ist inzwischen über eine eigene begrenzte Queue entkoppelt.
- Kein allgemeiner Timeout um jeden Adapterzyklus.
- Ein getesteter fachlicher Decision-Gate-Vertrag existiert, ist aber noch nicht als Observer an den EventBus angeschlossen und greift nicht in Decisions oder Signals ein.
- Telegram liegt nicht strikt hinter finalen Decisions.
- Keine zentrale Retention-Policy für den gesamten Runtime-Bestand.
- Absolute Windows-Pfade begrenzen Portabilität.
- Storage-Scans können trotz inkrementellem Index das Zeitlimit überschreiten.
- `STALE` kann nur für Services mit bekanntem Heartbeat bestimmt werden; heartbeatlose Services behalten ihren sonstigen Status.
- Stop und Restart unterbrechen den Zyklus-Warteabschnitt, nicht einen bereits laufenden Adapterzyklus.
