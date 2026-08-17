# Bekannte Probleme

Stand: 14. August 2026

## Offen

### KP-030 – Historische Verification-Completion-Duplikate bleiben im append-only Ledger

- **Priorität:** mittel für spätere deskriptive Auswertung, keine Laufzeitgefährdung
- **Status:** Ursache für neue Einträge behoben; 194 historische Zusatzzeilen bleiben bewusst unverändert
- **Beobachtung:** Der gestoppte Gesamtbestand vom 17. August 2026 enthält 13.809 `OUTCOME_COMPLETED`-Zeilen für 13.615 eindeutige Verification-IDs. Genau 194 IDs besitzen je eine zweite Completion-Zeile.
- **Ursache:** Der frühere Completion-Pfad kopierte `PENDING`-Kandidaten unter Lock, löste die Sperre und schrieb anschließend. Parallele Quoteereignisse konnten denselben Fall deshalb mehrfach abschließen.
- **Sichere Behandlung:** Neue Completion-Vorgänge prüfen und schreiben vollständig unter derselben Adapter-Sperre; zusätzlich verhindert ein lebenslang gehaltener exklusiver Ledger-Lock mehrere Writer. Bestehende Zeilen werden nicht gelöscht oder umgeschrieben.
- **Nächster Schritt:** Spätere read-only Auswertung nach kanonischer `verification_id` deduplizieren und die 194 Zusatzzeilen separat ausweisen; keine automatische Kalibrierung daraus starten.

### KP-029 – Kontrollierter Stop hing nach bereits gestopptem Orchestrator am Prozessende

- **Priorität:** mittel, Lifecycle/Shutdown
- **Status:** offen zur Beobachtung; beim anschließenden DRAIN-Smoke nicht erneut aufgetreten
- **Beobachtung:** `POST /api/control/stop` wurde um 19:15 Uhr angenommen und `/api/status` meldete `running=false` sowie `stop_requested=true`. Das Verification-Ledger war stabil, aber PID 6184 hielt Port 8000 nach mehr als 45 Sekunden weiter offen. Nach Prüfung der exakten PID und stabiler Writer wurde ausschließlich dieser Prozess beendet; Port und PID waren danach frei und alle geprüften Runtime-Dateien blieben stabil.
- **Abgrenzung:** Kein JSONL-Fehler und kein Datenverlust festgestellt. Der heutige Stabilisierungscode ändert den allgemeinen Orchestrator-/Webserver-Shutdown nicht.
- **DRAIN-Gegenprobe:** Der spätere kontrollierte Stop der neuen DRAIN-Instanz gab Port 8000 in 1,961 Sekunden frei; der Prozess endete vollständig und das Ledger blieb quieszent.
- **Nächster Schritt:** Bei erneuter Reproduktion Thread-/Adapterabschluss gezielt instrumentieren; keinen ungezielten Prozessabbruch verwenden.

### KP-028 – `Compress-Archive` lässt versteckte `.git`-Inhalte aus

- **Priorität:** niedrig, betriebliche Backup-Methode
- **Status:** am 14. August 2026 erkannt und durch geprüfte .NET-ZIP-Erstellung umgangen
- **Beobachtung:** Eine vollständige kontrollierte Staging-Kopie enthielt `.git`, `docs`, `tests` und `AGENTS.md`. Das daraus mit Windows PowerShell `Compress-Archive` erstellte ZIP enthielt jedoch kein `.git` und war deshalb kein vollständiges Repository-Backup.
- **Sichere Behandlung:** Das ungültige, ausschließlich in dieser Aufgabe erzeugte ZIP wurde nach Dokumentation gelöscht. Das endgültige `pandorickbacktooback.zip` wurde mit `.NET ZipFile.CreateFromDirectory` erstellt und durch OpenRead, 1.266 vollständige Datei-Streams sowie Testextraktion einschließlich `.git/HEAD` verifiziert.
- **Nächster Schritt:** Für vollständige Repository-Backups weiterhin 7-Zip bevorzugen. Falls 7-Zip fehlt, kontrolliertes Staging plus .NET-ZIP verwenden und `.git/HEAD` ausdrücklich prüfen; `Compress-Archive` nicht ungeprüft als vollständig akzeptieren.

### KP-027 – PR #23 und #24 besaßen keine GitHub-CI-/Review-Abdeckung

- **Priorität:** mittel
- **Status:** für beide PRs nach vollständiger lokaler Prüfung und jeweiliger ausdrücklicher Mergefreigabe akzeptiert; Prozessrisiko bleibt dokumentiert
- **Beobachtung:** GitHub meldete für beide Branches keine Statuschecks und keine Reviews. PR #23 wurde als `c751fe1`, PR #24 am 14. August 2026 als `e7718c8` nach `main` gemergt. Vor beiden Merges waren Diff und Merge-Simulation konfliktfrei; für den finalen Regime-Head bestand die unmittelbare vollständige Wiederholung mit 318/318 Tests.
- **Lokale Evidenz:** Beide getrennten Diffs und Merge-Simulationen sind konfliktfrei; 0 Runtime-/History-Pfade, 0 Secret-Mustertreffer, 318/318 aktuelle Gesamttests sowie JavaScript- und Python-Syntax bestanden.
- **Sicherheitsregel:** Fehlende GitHub-Checks weiterhin nicht als bestanden darstellen. Für zukünftige PRs nach Möglichkeit unabhängige CI-/Review-Abdeckung einrichten und die lokale Evidenz nicht damit gleichsetzen.
- **Nächster Schritt:** Vor dem nächsten größeren PR entscheiden, ob eine minimale GitHub-Actions-Testmatrix eingerichtet werden soll; keine bestehende Runtime- oder Tradingkonfiguration dafür verändern.

### KP-026 – Regime v1 benötigt reale Coverage und Schwellenvalidierung

- **Priorität:** mittel
- **Status:** Implementierung, Tests und kurzer kontrollierter Live-Observer-Test abgeschlossen; längere Coverage und Schwellenvalidierung bleiben offen
- **Beobachtung:** Der Classifier ist deterministisch und mehrdimensional, seine Parameter sind aber noch nicht gegen ausreichende unabhängige Marktphasen und spätere Outcomes validiert. Stocks besitzen nur `1d`, Crypto nur `15m`; fehlende Timeframes werden sichtbar ausgewiesen.
- **Sicherheitsregel:** Regime-Werte nicht in LONG/SHORT/HOLD, Gate, Telegram oder Orders übersetzen. `UNKNOWN` und `DEGRADED` nicht wegfiltern. Keine Schwellen automatisch anhand kurzer Läufe optimieren.
- **Live-Smoke-Test:** BTCUSDT-`15m` ergab `DOWN + MEDIUM + WEAKENING`, AAPL-`1d` sicher `UNKNOWN + HIGH + UNKNOWN`; 2/2 Snapshots, 0 Drops, 0 Fehler, Queue leer, Worker gestoppt und keine verbotenen Events. Dies ist nur ein technischer Plausibilitätstest und keine Schwellenvalidierung.
- **Produktive Liveprüfung vom 14. August 2026:** Vier vollständige Crypto-/Stockzyklen auf dem gemergten `main` endeten mit allen Services `OK`, 0 Fehlern und 0 STALE. Der Observer hielt acht aktuelle Symbole und 21 append-only Snapshots, Queue 0/512. Crypto lieferte drei `OK`-Regimes auf echten `15m`-Daten; Stocks verwendeten echte `1d`-Daten, wobei `UNKNOWN` und der erwartete `SPCX`-Reject sichtbar blieben. Telegram-/Order-/Decision-Grenzen blieben unverändert.
- **Nächster Schritt:** Nach Review und separater Freigabe eine ausreichend lange read-only Coverage über unabhängige Marktphasen sammeln und später zeitpunktgerecht mit Outcomes auswerten. Keinen automatischen Fit oder Decision-Einfluss aktivieren.

### KP-025 – Stock- und Verification-Consumer blockierten den Gesamtzyklus

- **Priorität:** hoch
- **Status:** am 12. August 2026 technisch behoben und über drei Livezyklen verifiziert
- **Ursache:** Die 45-Sekunden-Grenze umfasste zunächst nur den externen Legacy-Lauf; Quote-, Kerzen-, Feature- und Shadow-Normalisierung folgten synchron. Nach deren Entkopplung schrieb der synchrone Verification-Handler bis zu tausende fällige Outcomes innerhalb eines einzigen Stock-Ereignisses.
- **Umsetzung:** Produktions-Stockpipeline als einzelner nicht wartender Hintergrundlauf; keine Überlappung. Verification-Aufarbeitung chronologisch und auf acht fällige Outcomes je Symbol/Quote begrenzt; append-only und restart-safe.
- **Verifikation:** 299/299 Tests; final genau ein Listener, drei Stock- und drei Cryptozyklen, keine STALE-Dienste, null Sitzungsfehler, Telegram null Sendungen, Runtime-Stderr leer.
- **Restbeobachtung:** Im 7-Tage-Lauf Durchsatz und `PENDING`-Rückstand beobachten. Batchgröße nicht ohne Messung erhöhen.

### KP-024 – Stock-Shadow-Score besitzt noch keine unabhängige Kalibrierung

- **Priorität:** mittel
- **Status:** fachlicher Version-1-Vertrag und Mindestabdeckungen bestätigt; Datenstatus `INSUFFICIENT_DATA`, keine Implementierung und keine Laufzeitfreigabe
- **Beobachtung:** Der öffentliche Shadow liefert einen transparenten `UNVALIDATED_HEURISTIC_SCORE`. Die fünf Marktphasenzyklen vom 10. August erzeugten 20 berechnete Shadows, wiederholten aber dieselben vier unterstützten Symbole und Tageskerzen. Da Stock-Verification im normalen Betrieb deaktiviert war, stehen null abgeschlossene unabhängige 24h-Outcomes für eine Kalibrierung bereit.
- **Auswirkung:** Weder `shadow.probability` noch die aus Probability kopierte Brain-`confidence` dürfen als kalibrierte Erfolgswahrscheinlichkeit oder unabhängige Confidence gelten. Wiederholte Zyklen würden die Stichprobe künstlich aufblasen.
- **Vertrag:** `pandorickki.stock-shadow-calibration` Version 1 trennt Score, `calibrated_probability` und Evidenz-Confidence, dedupliziert nach Symbol/Kerze/Policy/Version/Fingerprint und verlangt chronologische Holdout-Validierung.
- **Sicherheitsregel:** Bei unzureichenden, korrelierten oder unvollständigen Outcomes keine Probability/Confidence erzeugen und niemals Gate, Telegram oder Orders automatisch koppeln.
- **Nächster Schritt:** Den siebentägigen Stock-Verification-Lauf nur nach einer weiteren eigenen Laufzeitfreigabe als technische Datenqualitätsprüfung starten; auch danach nicht automatisch kalibrieren.

### KP-023 – Live-Shadow-Outcome ist zunächst nur Forward-Mark-to-Market

- **Priorität:** mittel
- **Status:** Version-1-Vertrag implementiert; siebentägige Beobachtung ausdrücklich freigegeben und seit 10. August 2026, 19:03:44 Uhr Europe/Berlin aktiv
- **Beobachtung:** Diskrete öffentliche Quotes beweisen keinen vollständigen Intraday-Pfad. Version 1 bewertet deshalb nach 24 Stunden den ersten strikt späteren Quote-Zeitstempel und behauptet keine Stop-/Zielberührung.
- **Auswirkung:** Legacy/Shadow-WIN, LOSS und NEUTRAL sind vergleichbare Richtungs-Mark-to-Market-Ergebnisse, aber kein vollständiger Trade-Backtest. HOLD oder fehlende Daten bleiben `UNKNOWN`; fehlende spätere Quotes bleiben `PENDING`.
- **Kurzlauf:** Drei Zyklen erzeugten 15 eindeutige Stockfälle und 15 Decision-Links. 12 Fälle sind erwartungsgemäß `PENDING`; drei `SPCX`-Fälle bleiben wegen fehlendem öffentlichem Ticker `UNKNOWN`. Es gab 9 `LEGACY_HOLD_SHADOW_ACTION`, 3 `MATCH` und 3 nicht vergleichbare Fälle.
- **Sicherheitsregel:** Aus der Verification keine automatische Regel-, Gate-, Telegram- oder Orderänderung ableiten und keine Aussage „Shadow ist besser“ automatisch erzeugen.
- **Aktiver Lauf:** Fingerprint `3d23f923d6b9d9dc3019457afcb078591b5d8c8b4d1f4f4db55911724fa71747`, 24h-Horizont, 0,05-%-Neutralband. Nach zwei Zyklen zehn neue Fälle; zwölf zugleich abgeschlossene Outcomes stammen aus dem früheren Kurzlauf und werden zeitlich getrennt.
- **Nächster Schritt:** Lauf am 17. August 2026 nach mindestens sieben Tagen kontrolliert stoppen, alte Kurzlaufdaten abgrenzen, unabhängige Fälle deduplizieren und ausschließlich deskriptiv auswerten. Keinen Fit starten.

### KP-001 – Storage-Scan überschreitet das Zeitlimit

- **Priorität:** niedrig
- **Status:** technisch behoben; nach Neustart im Dauerbetrieb beobachten
- **Frühere Beobachtung:** Ein realer Scan endete nach 35,236 Sekunden als `TIMEOUT`; 27 von 94 Dateiverweisen waren abgeschlossen.
- **Messung vom 1. August 2026:** Der schreibgeschützte Ist-Scan erfasste 105 physische Dateien und dauerte mit altem Budget 1,084 Sekunden. Ein Benchmark mit 64 MiB JSONL-Budget verarbeitete rund 68 MB in 2,135 Sekunden, deutlich unter dem 30-Sekunden-Limit.
- **Umsetzung:** Alle relevanten Phasen werden getrennt gemessen; der JSONL-Index meldet Bytes, Prozent, vollständige Dateien und geschätzte Restläufe. Das Standardbudget beträgt jetzt 64 MiB statt 256 KiB.
- **Restbeobachtung:** Bei weiter stark wachsendem Bestand Laufzeiten und Timeoutstatus kontrollieren. Keine Retention oder Löschung als Schnelllösung verwenden.
- **Neustartprüfung:** Nach dem kontrollierten Neustart dauerte ein Produktionsscan 2,416 Sekunden, bearbeitete 106/106 Dateien und erhöhte den JSONL-Fortschritt auf 9,20 %; kein Timeout trat auf.
- **Unabhängige Datenwarnung:** `stock_patterns.json` und dessen Backup `stock_patterns.before_json_repair_20260710_224237.json` enthalten vorhandene JSON-Syntaxfehler und halten den Gesamtstatus auf `DEGRADED`; sie wurden nicht verändert.

### KP-003 – Synchroner EventBus kann Publisher blockieren

- **Priorität:** mittel
- **Status:** offen
- **Beobachtung:** Handler werden synchron im veröffentlichenden Thread ausgeführt.
- **Auswirkung:** Langsame Datei-, Statistik- oder Netzwerkhandler verzögern Produzenten und nachfolgende Handler.
- **Entschärfung:** NeuroBrain-Datei- und Status-I/O wurde am 2. August 2026 über eine begrenzte FIFO-Queue und einen einzelnen Batch-Worker entkoppelt. Andere Handler bleiben synchron.
- **Nächster Fix:** verbleibende langsame Consumer anhand realer Messungen identifizieren und nur bei Befund gezielt entkoppeln; nicht ungeprüft den vollständigen EventBus ersetzen.

### KP-004 – Brain und Decision Core besitzen kein aktives Freigabe-Gate

- **Priorität:** mittel
- **Status:** Vertrag und separater Audit-Observer implementiert; seit 9. August 2026 diagnostisch mit 60/60 und Toleranz 0 aktiv; produktive Freigabe weiterhin offen
- **Beobachtung:** Brain persistiert und reicht weiter; der aktive Decision Core normalisiert deterministisch und erzeugt aus jedem Brain-Ereignis Decision und Signal. Der `decision_gate_observer` prüft dieselben Brain-Ereignisse parallel fail-closed und auditiert begrenzt, beeinflusst aber den aktiven Pfad nicht. Vier Livezyklen ergaben 32/32 `BLOCKED`, null unsichere Freigaben und keinen Observerfehler.
- **Auswirkung:** Modulnamen können eine fachliche Prüfung suggerieren, die nicht implementiert ist.
- **Sicherheitsregel:** Der Vertrag setzt stets `ready_for_telegram=false` und `order_execution_allowed=false`. Daraus niemals automatische oder reale Orders ableiten.
- **Nächster Fix:** Audit über einen längeren Zeitraum auswerten und zuerst die vorgelagerten Stock-Preis-/Qualitäts-/Risikofelder als eigenen Vertrag prüfen. Den bestehenden Signalpfad noch nicht umschalten.

### KP-021 – Confidence ist derzeit keine unabhängige Gate-Messgröße

- **Priorität:** mittel
- **Status:** offen, durch Liveaudit bestätigt
- **Beobachtung:** `BrainAdapter` setzt `confidence` gleich `probability`. Im 272-Kandidaten-Snapshot waren Probability und Confidence deshalb stets identisch; beide 60er-Schwellen prüfen faktisch dieselbe Zahl.
- **Auswirkung:** `DG_CONFIDENCE_CONFLICT` kann im heutigen Brain-Pfad keine Abweichung zweier unabhängiger Bewertungen erkennen. Eine produktive Freigabe würde die Sicherheit der doppelten Prüfung überschätzen.
- **Nächster Fix:** Vor jeder Gate-Umschaltung einen fachlichen Confidence-Vertrag definieren: unabhängige Quelle und Kalibrierung oder ehrliche Entfernung/Umbenennung der redundanten Freigaberegel.

### KP-022 – Stock kann den sicheren Gate-Vertrag derzeit nicht erfüllen

- **Priorität:** mittel
- **Status:** Datenvertrag, read-only Kerzen-Audit, öffentlicher Shadow-Kandidat und observer-only ATR-Risikoplan integriert; unabhängige Confidence und aktive Gate-Kopplung weiterhin offen
- **Beobachtung:** Im Snapshot waren 170/170 Stock-Kandidaten `WARN/UNVERIFIED/WARMING`. Alle 31 Stock-LONG-Kandidaten scheiterten zusätzlich an Stop und Take-Profit, weil `StockAdapter._normalize_decision()` keinen normalisierten `risk`-Block erzeugt. SPCX hatte in 34/34 Fällen keinen positiven Livepreis.
- **Auswirkung:** Auch Stock-Kandidaten über Probability 60 bleiben korrekt blockiert. Ein Lockern der Gate-Regeln würde unvollständige Daten freigeben.
- **Vertrag vom 9. August 2026:** `pandorickki.stock-data` Version 1 verlangt eine öffentliche Livequelle, vollständige Zeitstempel, explizite Kerzen-/Warmupgrenzen, eine aktuelle jüngste Kerze, frischen positiven Preis und normalisierten Richtungs-Risikoplan. Die Referenz ist ausschließlich als read-only Audit in den Adapter integriert und nicht mit dem aktiven Feature-/Decision-/Signalpfad gekoppelt.
- **Liveaudit:** AAPL lieferte 260/260 `PASS/VERIFIED/READY`. Im ersten Plattformzyklus wurden vier von fünf Symbolhistorien geladen; `SPCX` blieb ohne Provideraufruf blockiert. 0/5 Kandidaten waren `READY`, weil aktive Richtung/Probability weiter aus Placeholder-Daten stammen und `risk` fehlt.
- **Shadow-Stand:** Version 1 berechnet Fakten, Direction und einen transparenten `UNVALIDATED_HEURISTIC_SCORE` ausschließlich aus öffentlichen Daten. Legacy und Shadow werden mit `affects_active_decision=false` verglichen; die aktive Placeholder-Decision wird nicht aufgewertet. 283/283 Tests bestanden.
- **Risikoplan-Stand:** Version 1 verwendet öffentlichen Entry, ATR14 mit 0,5-%-Mindestdistanz sowie 1R/2R/3R-Ziele. Er bleibt vollständig außerhalb des aktiven Eventpfads. 289/289 Tests bestanden.
- **Liveprüfung:** Zwei Sonntagszyklen lieferten 8 Shadows und 6 gültige Pläne; HOLD und `SPCX` blockierten. Alle Daten-Audits blieben wegen Quote-Freshness beziehungsweise fehlender Eignung sicher blockiert. Plattformfehler, STALE und Telegram-Sendungen blieben null.
- **US-Marktphasenmessung vom 10. August 2026:** Fünf vollständige Zyklen lieferten 20 berechnete Shadows (10 LONG, 5 SHORT, 5 HOLD), 15 gültige Risikopläne und 25 Audits mit 15 `READY`/10 `BLOCKED`. Die vier unterstützten Symbole hatten 8,737 bis 19,505 Sekunden alte Quotes; `SPCX` blieb ohne Quote, HOLD blieb ohne Risikoplan. Keine Health-, STALE-, Telegram- oder Orderabweichung.
- **Nächster Fix:** Über eine echte Marktphase Shadow-/Risikoplan- und Daten-Audit-Verteilungen beobachten. Danach eine unabhängige Confidence beziehungsweise ehrliche Kalibrierungsstrategie definieren; keine Gate-Umschaltung. `SPCX` weiter blockieren.

### KP-019 – Sporadischer Windows-Temp-Verzeichnisfehler in der Gesamtsuite

- **Priorität:** niedrig
- **Status:** sporadisch reproduziert; isolierte und vollständige Wiederholungen jeweils grün
- **Beobachtung:** Der Windows-Fehler `WinError 145` trat am 14. August 2026 nach dem PR-#24-Retargeting erneut ausschließlich beim Aufräumen eines `TemporaryDirectory` nach dem Learning-Cache-Test auf. Derselbe Test bestand direkt danach isoliert mit 1/1.
- **Auswirkung:** Kein Hinweis auf eine fachliche Decision-/Stock-/Regime-Regression; die unmittelbare vollständige Wiederholung bestand mit 318/318 Tests.
- **Nächster Fix:** Nur bei erneuter Reproduktion den noch schreibenden Learning-/Storage-Worker gezielt instrumentieren.

### KP-020 – Sandbox-Starts besitzen keinen Zugriff auf öffentliche Marktdaten

- **Priorität:** niedrig, betriebliche Entwicklungsumgebung
- **Status:** verstanden und durch kontrollierten Netzwerkstart umgangen
- **Beobachtung:** Kontrollierte Startversuche innerhalb der eingeschränkten Codex-Sandbox erzeugten `CRYPTO_SERVICE_ERROR`-Ereignisse mit `WinError 10013` für Binance und Bitget. Der Befund wurde am 14. August 2026 beim Neustart auf dem gemergten Regime-`main` erneut bestätigt; der betroffene Prozess wurde geordnet beendet. Beim anschließend ausdrücklich freigegebenen Netzwerkstart arbeiteten Crypto und Stock über vier Zyklen fehlerfrei; seit dessen Start entstand kein neuer Sitzungsfehler.
- **Auswirkung:** Kein Produktcodefehler und kein Datenverlust. Ein Sandbox-Prozess kann Live-Crypto jedoch nicht sinnvoll verifizieren.
- **Nächster Fix:** Live-Crypto-Starts aus Codex weiterhin nur mit der vorgesehenen Netzwerkfreigabe ausführen; Journalzeilen nicht löschen oder umschreiben.

### KP-005 – Telegram umgeht die finale Entscheidungskette

- **Priorität:** mittel
- **Status:** offen
- **Beobachtung:** Telegram abonniert Crypto-/Stock-Analysen und simulierte Crypto-Trade-Updates direkt.
- **Auswirkung:** Eine Nachricht kann vor oder unabhängig von `DECISION_CREATED`/`SIGNAL_CREATED` entstehen.
- **Sicherheitsregel:** Telegram deaktiviert beziehungsweise im Dry-Run lassen, bis der vorhandene Gate-Vertrag als Observer live ausgewertet und die spätere Kopplung separat freigegeben ist.

### KP-006 – Keine zentrale Retention-Policy

- **Priorität:** mittel
- **Status:** offen
- **Beobachtung:** Einzelne Ledger rotieren, der Gesamtbestand wächst weiter.
- **Auswirkung:** Längere Backups, größere Scans und steigender Speicherverbrauch.
- **Sicherheitsregel:** Keine vorhandenen History- oder Lerndaten ohne ausdrückliche Aufbewahrungsentscheidung löschen.

### KP-007 – Feature-Eingänge werden nicht strikt validiert

- **Priorität:** mittel
- **Status:** am 8. August 2026 über PR #22 behoben, nach `main` gemergt und kontrolliert live verifiziert
- **Behoben:** Vertrag `pandorickki.feature-data-quality` Version 1 prüft OHLCV, Non-Finite-Werte und Mindestanzahl, sortiert vollständig zeitgestempelte Reihen, behandelt Duplikate deterministisch mit `keep_last` und weist Warmup sowie unverifizierte Reihenfolge explizit aus.
- **Kompatibilität:** Ein valider Einzelsnapshot bleibt erlaubt, wird aber als `WARMING` gekennzeichnet. Bestehende Legacy-Entscheidungen und History werden nicht verändert.
- **Verifikation:** 30/30 gezielte Tests auf dem gemergten `main`, zuvor 251/251 Gesamttests. Ein direkter Realtest akzeptierte 240/240 Binance-Kerzen mit `PASS`, `VERIFIED`, `READY` und null Verstößen. Vier Produktionszyklen liefen mit allen zehn Services `OK`, null Sitzungsfehlern und aktuellen Crypto-/Aktienwerten.
- **Bewusste Grenze:** Der Stock-Fallback bleibt ein zeitstempelloser Einzelsnapshot und meldet deshalb korrekt `WARN`, `UNVERIFIED` und `WARMING`. Ob solche Daten für eine Meldung genügen, entscheidet erst das noch zu implementierende fachliche Decision Gate.

### KP-009 – Portabilität durch lokale Windows-Pfade eingeschränkt

- **Priorität:** niedrig
- **Status:** offen
- **Beobachtung:** Standard- und Batchpfade verweisen teilweise auf lokale externe Projekte.
- **Auswirkung:** Ein neuer Rechner benötigt explizite Pfadkonfiguration.

### KP-017 – Historische Statistikzähler besitzen keinen gemeinsamen Outcome-Scope

- **Priorität:** mittel
- **Status:** offen; falsche Quote wird seit dem 2. August 2026 verhindert
- **Beobachtung:** Die persistente Statistik rekonstruiert finale LONG-/SHORT-Decisions und geschlossene Outcomes aus historisch unterschiedlich begrenzten Quellen. Der Outcome-Zähler kann deshalb größer als der passende Decision-Zähler sein.
- **Auswirkung:** Aus den Gesamtzählern lässt sich keine belastbare Outcome-Abdeckung berechnen. Version 1 liefert dafür bewusst `null`, `outcome_coverage_scope_consistent=false` und die UI zeigt `nicht vergleichbar`.
- **Verlässliche Sicht:** Der Learning Report lädt Decisions und Outcomes in einem gemeinsamen Fenster und ordnet sie exakt per `decision_id` zu; dort ist die Abdeckung berechenbar.
- **Nächster Fix:** Später eine gemeinsame, versionierte Scope-/Cursor-Identität für Statistikrekonstruktion entwerfen. Bestehende Statistik- und Historydateien nicht zurücksetzen oder migrieren, bevor ein getesteter Migrationsvertrag vorliegt.

### KP-015 – Vollständige Raw Results vergrößern Event-Ledger

- **Priorität:** hoch
- **Status:** für Markt-Payloads implementiert, getestet und am 1. August 2026 live verifiziert
- **Beobachtung:** Brain und Decision Core persistieren und publizieren neue Stufen kompakt. NeuroBrain speichert neben seiner Kopfsicht nur noch die Version-1-Projektion.
- **Auswirkung:** Wiederholte Rohdaten und Kerzen vergrößern Brain-/Decision-/Signal-/NeuroBrain-Ledger und verlängern Storage-Scans.
- **Verifizierte Altpfade:** `CryptoTradeTracker` kann Swing-Werte weiterhin aus `raw_result.market_data.candles` lesen; `LearningGraphBuilder` kann das Ergebnis weiterhin aus `raw_result.result` lesen. Beide Pfade sind jetzt ausschließlich Fallback hinter den kompakten Feldern.
- **Vorbereitung:** `docs/EVENT_PAYLOAD_CONTRACT.md` und `event_payload_contract.py` definieren Version 1. Tracker und Graph bevorzugen die kompakten Ersatzfelder; vier Regressionstests sichern Priorität und Legacy-Kompatibilität.
- **Liveergebnis:** Drei saubere Produktionszyklen bestätigten kompakte Brain-, Decision-, Signal- und marktbezogene NeuroBrain-Zeilen ohne verbotene Bulk-Felder sowie eine vollständige ID-Kette. Bestehende History wurde nicht umgeschrieben oder gelöscht.

### KP-018 – Lokaler Client-Abbruch erzeugt einen lauten Server-Traceback

- **Priorität:** niedrig
- **Status:** offen; einmalig beim kontrollierten Neustart beobachtet
- **Beobachtung:** Eine aggressive lokale Readiness-Abfrage mit kurzem Timeout trennte die Verbindung während der HTTP-Antwort. `ThreadingHTTPServer` protokollierte daraufhin einmal `ConnectionResetError: [WinError 10054]` als vollständigen Traceback.
- **Auswirkung:** Kein fachlicher Dienstfehler: Plattform und alle zehn Services blieben `OK`, der Sitzungsfehlerzähler blieb null, und in mehr als vier anschließenden Marktzyklen trat der Fehler nicht erneut auf.
- **Nächster Fix:** Nur bei erneuter Beobachtung den HTTP-Request-Handler so härten, dass erwartbare lokale Client-Abbrüche kompakt protokolliert werden. Keine Priorität vor dem Feature-Datenqualitätsvertrag.

## Behoben oder entschärft

### KP-R16 – Outcome-Zustandsdatei und Verification-Completion waren kollisionsanfällig

- **Status:** behoben und am 17. August 2026 mit gezielten sowie vollständigen Tests verifiziert
- Der allgemeine `OutcomeTracker` verwendet für `simulated_open_trades.json` jetzt `atomic_write_json`; Snapshot und Dateischreiben bleiben gemeinsam unter derselben Adapter-Sperre. Eindeutige Temp-Dateien, `fsync` und begrenzte Windows-Retries ersetzen den festen `*.tmp`-Pfad.
- Verification-Completion prüft unter Lock erneut `PENDING` und führt Ledger-Append plus Materialized-View-Apply serialisiert aus. Ein exklusiver Prozess-/OS-Dateilock verhindert mehrere aktive Writer für dasselbe Ledger und startet bei Konflikt ohne Subscriptions.
- Tests decken zwei simulierte `PermissionError`-Retries, 24 parallele Outcome-Snapshots, acht parallele doppelte Quoteereignisse, Restart, Lockkonflikt sowie Lockfreigabe ab. 47/47 gezielte und 325/325 vollständige Tests bestanden.
- Bestehende Runtime- und Historydateien wurden nicht umgeschrieben; die 194 historischen Completion-Zusatzzeilen bleiben als KP-030 sichtbar.

### KP-R15 – UI-Reconnect, STALE und Lifecycle waren unvollständig

- **Status:** behoben, getestet und am 2. August 2026 live verifiziert
- Genau ein Polling-Fallback, single-flight Statusabruf, WebSocket-Reconnect mit begrenztem Backoff und Schutz vor alten Socket-Callbacks sind implementiert.
- REST- und WebSocket-Snapshots berechnen Heartbeat-Alter und klassifizieren bekannte Heartbeats nach standardmäßig 150 Sekunden als `STALE`, ohne `ERROR`, `STOPPED` oder `DISABLED` zu überschreiben.
- Stop und Restart unterbrechen den Zyklus-Warteabschnitt im 100-ms-Raster. Restart startet die Adapter im selben Prozess neu; die Liveprüfung meldete `APPLIED` nach rund 104 ms. Ein vollständiger Prozess-Stop gab Port 8000 in 2,326 Sekunden frei.
- Steuerbefehle erzeugen keinen Phantom-Service mehr.
- Der Learning Graph verwendet Frame-Koaleszierung, single-flight Laden, Hidden-Tab-Skip und wiederverwendete Layoutpositionen. 76 Knoten und 179 Kanten wurden live ohne Browserfehler dargestellt.
- Grenze: Ein bereits laufender Adapterzyklus wird nicht hart abgebrochen. Diese sichere Semantik bleibt zu beobachten.

### KP-R14 – Learning-, Outcome- und Trainingsmetriken waren widersprüchlich benannt

- **Status:** behoben, getestet und am 2. August 2026 live verifiziert
- Der Vertrag `pandorickki.learning-metrics` Version 1 vereinheitlicht Hit-Rate als Wins geteilt durch Wins plus Losses und liefert für jede Rate Zähler und Nenner. Breakeven und unbekannte Outcomes bleiben separate Klassen.
- Der Learning Report ordnet Outcomes exakt per `decision_id` zu und zeigt eine scope-konsistente Outcome-Abdeckung. Alte Cachedateien ohne Vertrag werden beim normalen Lesen neu aufgebaut, nicht gelöscht.
- `AI_LEARNING_UPDATED`, Graph-Projektionen und Muster-Buckets werden nicht länger als erfolgreiche Learnings, Modellupdates oder gelernte ML-Muster ausgegeben. API und UI melden ausdrücklich `ml_training.active=false` und `model_updates=0`.
- 239/239 Gesamttests, Syntaxprüfung, Diffprüfung und Runtime-Preflight bestanden. Live waren Report-Hit-Rate und -Abdeckung samt Bruch sichtbar; historische Aggregate zeigten wegen KP-017 korrekt `nicht vergleichbar`.
- Nach finalem kontrolliertem Neustart meldeten Plattform und alle zehn Services `OK`, Crypto und Stock jeweils zwei Zyklen, NeuroBrain null Queue-/Drop-/Workerfehler, Telegram aus/Dry-Run und null versendete Nachrichten.
- Commit `e09c187` wurde auf `agent/unify-learning-metrics` veröffentlicht; der gestapelte Draft-PR #16 gegen `agent/queue-neurobrain-receiver` ist offen, Draft und ungemergt.
- Bestehende Statistik-, Learning-, Graph- und Historydaten wurden weder gelöscht noch umgeschrieben.

### KP-R13 – NeuroBrain-Datei-I/O blockierte den synchronen Publisher

- **Status:** behoben, getestet und am 2. August 2026 live verifiziert
- Der EventBus-Handler projiziert und reiht nur noch per `put_nowait` ein. Ein einzelner FIFO-Worker schreibt standardmäßig maximal 64 Datensätze je Batch aus einer Queue mit Kapazität 2048.
- Bei Überlauf wird ausschließlich das neueste Ereignis abgelehnt; `dropped_events`, Queue-Tiefe, Batchzähler sowie Ledger-, Status- und Benachrichtigungsfehler sind sichtbar und beeinflussen Health.
- `stop()` entfernt zuerst das Abonnement, leert alle akzeptierten Einträge, joint den nicht-daemonisierten Worker und ist wiederholt sicher. Nach Rückkehr finden keine Queue-Schreibvorgänge mehr statt.
- Vor dem Fix fehlten Queueparameter und Batch-API vollständig. Danach bestanden 20/20 gezielte sowie 235/235 vollständige Tests, `py_compile`, Runtime-Preflight und Diffprüfung.
- Live: 231 eindeutige neue Zeilen in 48 Batches, keine FIFO-/Schemafehler, null Drops/Workerfehler; Shutdownstatus `worker_running=false`, `queue_depth=0`. Alle zehn Services `OK`, Journal unverändert 180, Telegram aus/Dry-Run.
- Commit `0fe5bd6` wurde auf `agent/queue-neurobrain-receiver` veröffentlicht; der gestapelte Draft-PR #15 gegen `agent/fix-neurobrain-observer-schema` bleibt offen und ungemergt.
- Bestehende NeuroBrain-Inbox- und Historyzeilen wurden weder migriert noch umgeschrieben.

### KP-R12 – NeuroBrain verwendete das Markt-Schema für nicht marktbezogene Topics

- **Status:** behoben, getestet und am 2. August 2026 live verifiziert
- `AI_LEARNING_UPDATED` und das aggregierte `STOCK_MARKET_DATA_UPDATED` verwenden für neue Inboxzeilen `pandorickki.compact-observer-event` Version 1. Der Vertrag verlangt `event_type`, erhält die benötigten Zähler-/Learning-Felder und verbietet rekursiv dieselben Bulk-Felder wie der Marktvertrag.
- Einzelwertige `CRYPTO_MARKET_DATA_UPDATED`- und `COMMODITY_MARKET_DATA_UPDATED`-Ereignisse bleiben Marktprojektionen; NeuroBrain ergänzt den aus dem Topic eindeutigen `market_type`.
- Drei neue Adapterregressionen reproduzierten den Fehler vor dem Fix. Danach bestanden 15/15 gezielte und 231/231 vollständige Tests, `py_compile` und `git diff --check`.
- Live wurden 152 ausschließlich neu angehängte Inboxzeilen geprüft: beide Schemagruppen, alle Pflichtfelder und der Bulk-Ausschluss waren fehlerfrei. Alle zehn Services meldeten `OK`, das Fehlerjournal blieb bei 180 und Telegram aus/Dry-Run.
- Commit `e94c988` wurde auf `agent/fix-neurobrain-observer-schema` veröffentlicht; der gestapelte Draft-PR #14 gegen `agent/compact-neurobrain-payloads` bleibt ungemergt.
- Bestehende Inbox- und Historyzeilen wurden weder migriert noch umgeschrieben.

### KP-R11 – Feste Temp-Dateien kollidierten bei atomaren Runtime-Schreibvorgängen

- **Status:** behoben, getestet und am 2. August 2026 live verifiziert
- **Beobachtung:** NeuroBrain-Status und aktive Crypto-Trades verwendeten jeweils einen festen `*.tmp`-Pfad. Im Dauerbetrieb traten `WinError 5` beim `os.replace()` auf; der Crypto-Trade-Tracker-Fingerprint erreichte drei und der NeuroBrain-Fingerprint ebenfalls drei Vorkommen.
- **Ursache:** Parallele Schreiber konnten denselben Temp-Pfad verwenden; zusätzlich konnte ein kurzer Windows-Dateizugriff das Replace der Zieldatei blockieren. Zustandssnapshot und Dateischreiben waren nicht über dieselbe Adapter-Sperre geordnet.
- **Fix:** `atomic_json.py` verwendet eindeutige Temp-Dateien im Zielverzeichnis, eine pro aufgelöstem Zielpfad geteilte Prozesssperre, `fsync`, atomaren Replace und einen kurzen begrenzten Retry ausschließlich für transiente Berechtigungs-/Sharing-Fehler. NeuroBrain und Crypto Trade Tracker halten ihre Zustandssperre bis zum abgeschlossenen Schreiben.
- **Tests:** Die zwei neuen Regressionstests scheiterten vor der Implementierung wegen des fehlenden Helfers. Danach bestanden Retry mit zwei simulierten `PermissionError`-Fehlern, 24 parallele Schreibvorgänge, 13/13 gezielte Tests, `py_compile` und 226/226 Gesamttests.
- **Liveergebnis:** Nach zwei vollständigen Produktionszyklen alle zehn Services `OK`; Fehlerjournal weiterhin insgesamt 180, beide Ziel-Fingerprints unverändert, keine verwaisten Temp-Dateien, aktuelle Crypto-Preise vorhanden und Telegram aus/Dry-Run.
- **Veröffentlichung:** Commit `ed2a83e` auf `origin/agent/compact-neurobrain-payloads`; bestehender Draft-PR #13 aktualisiert und nicht gemergt.
- **Abgrenzung:** Bestehende Runtime- und History-Dateien wurden nicht umgeschrieben oder gelöscht. Andere atomare JSON-Schreiber bleiben zunächst unverändert und werden nur bei eigenem reproduzierbarem Befund migriert.

### KP-R10 – Outcome Tracker mischte naive und UTC-Zeitstempel

- **Status:** behoben, getestet und live verifiziert am 1. August 2026
- `_duration_seconds()` versieht ausschließlich geparste Zeitstempel ohne `tzinfo` mit UTC. Bereits offset-bewusste Werte behalten ihren tatsächlichen Offset.
- Bestehende offene Trades, Outcomes und andere Historydateien werden weder umgeschrieben noch gelöscht.
- Der öffentliche Regressionstest reproduzierte vor dem Fix das reale `OUTCOME_TRACKER_ERROR`; nach dem Fix wird der Legacy-Trade geschlossen, es entsteht kein Fehlerereignis und Tracker-Health bleibt gesund.
- Reine naive, reine offset-bewusste, gemischte und unterschiedlich offset-bewusste Zeitpaare sind abgedeckt.
- 12/12 Outcome-Tracker-Tests und 212/212 Gesamttests bestanden.
- Nach kontrolliertem Neustart und vier vollständigen Crypto-Heartbeats blieb der bekannte Journalfingerprint unverändert bei 158 Vorkommen; letztes Auftreten weiterhin 17:13:29 UTC. Alle zehn Services meldeten `OK`.

### KP-R09 – Historische Service-Exceptions verschwanden aus der In-Memory-Historie

- **Status:** behoben und getestet am 1. August 2026
- Ein standardmäßig aktives `ServiceErrorJournal` persistiert kompakte versionierte Projektionen von `SYSTEM_ERROR`, `service.error` und allen Themen mit Suffix `_ERROR`.
- Das aktive JSONL rotiert bei 5 MiB und behält höchstens vier Archive. Die atomar geschriebene Zusammenfassung behält höchstens 500 Fehlerfingerprints samt Anzahl sowie erster und letzter Beobachtung.
- Schlüssel- und Textfilter entfernen Tokens, API-Keys, Authorization-, Cookie-, Passwort-, Secret- und Chat-ID-Werte. Rohe Payloads und externe Response-Inhalte werden nicht kopiert.
- Journal-Schreibfehler brechen den Event-Publisher nicht und werden über `service_error_journal` als fehlerhafter Health-Zustand sichtbar.
- Der begrenzte Bestand ist bewusst kein vollständiges Langzeitarchiv; bestehende andere History-Dateien bleiben unverändert.
- 17/17 gezielte und 210/210 vollständige Tests bestanden.
- Live verifiziert: drei wiederkehrende Outcome-Tracker-Fehler wurden als ein Fingerprint mit erster/letzter Beobachtung erfasst; Journal-Health blieb `OK` und `failed_writes=0`.

### KP-R08 – Scannerfortschritt war nicht messbar und praktisch zu langsam

- **Status:** behoben und am realen Bestand schreibgeschützt vermessen am 1. August 2026
- Phasenlaufzeiten für Zielermittlung, Pfadauflösung, Metadaten, Fingerprint, Dateiverarbeitung, Index- und Cachepersistenz sind im Scanstatus enthalten.
- Der kumulative JSONL-Fortschritt bleibt über Läufe erhalten und zeigt Bytes, Prozent, vollständige Dateien, Restläufe und Restzeit.
- Das 64-MiB-Standardbudget blieb im Realbenchmark mit 2,135 Sekunden weit unter dem 30-Sekunden-Limit.
- 39/39 gezielte und 204/204 vollständige Tests bestanden.

### KP-R07 – Storage-Gesamtsummen zählten überlappende Ziele mehrfach

- **Status:** behoben und getestet am 1. August 2026
- `platform_data` umfasst vorhandene Dateien unter `data/`, während Brain-Events, rotierte Brain-Dateien und Shared State zusätzlich als eigene logische Kategorien erscheinen können.
- Der Scanner dedupliziert jetzt jeden aufgelösten physischen Pfad, scannt ihn nur einmal und verwendet das Ergebnis in allen zutreffenden Kategorien wieder.
- `total_*` und `physical_total_*` liefern physisch eindeutige Werte; `logical_total_*` beschreibt bewusst die Summe der Kategorieverweise und `overlapping_file_references` macht Überschneidungen sichtbar.
- Alte Cachedateien werden bis zum nächsten vollständigen Scan als `LEGACY_CACHE` markiert und beanspruchen keine verifizierten physischen Werte.
- 44/44 gezielte Storage-/Web-/Rick-API-Tests sowie 203/203 Gesamttests bestanden.

### KP-R06 – Storage-Worker schrieb nach `close()` weiter

- **Status:** behoben und deterministisch getestet am 1. August 2026
- Ein Regressionstest blockiert einen laufenden Cache-/Index-Schreibvorgang und reproduzierte vor dem Fix sowohl die verfrühte Rückkehr von `close()` als auch `WinError 145` beim anschließenden Entfernen des Testverzeichnisses.
- `close()` setzt jetzt einen dauerhaften geschlossenen Zustand, signalisiert Abbruch und wartet vollständig auf den aktiven Worker sowie einen gegebenenfalls synchron laufenden Refresh.
- Neue Scans werden nach `close()` mit `CLOSED` abgelehnt; wiederholtes `close()` bleibt sicher.
- Nach dem Fix bestanden der isolierte Regressionstest, 27/27 Storage-Tests, 36/36 Storage-/Webtests und 201/201 Gesamttests.

### KP-R05 – Crypto-Analyse seit 27. Juli ohne Ergebnisse

- **Status:** behoben und live verifiziert am 31. Juli 2026
- Externes `market.py` mit nicht verfügbarer `requests`-Abhängigkeit wird vom PandorickKi-Livepfad nicht mehr importiert.
- Interner Standardbibliotheks-Client verwendet Binance-Kerzen mit Bitget-Fallback und Retry.
- Open Interest und Funding sind optional und verwerfen keine gültigen Kerzen mehr.
- Service-Health meldet null Ergebnisse bei Fehlern als `ERROR` statt `OK`.
- 200/200 Tests bestanden; ein Live-Diagnoselauf und zwei Produktionszyklen lieferten insgesamt neun erfolgreiche Symbolanalysen ohne neuen Crypto-Fehler.

### KP-R04 – Arbeitsstand war nicht auf GitHub veröffentlicht

- **Status:** behoben
- Commit `38e1ddf` wurde auf `origin/agent/add-market-feature-engine` veröffentlicht.
- PR #2 wurde am 26. Juli 2026 nach `main` gemergt.
- Der spätere Crypto-Reparaturstand wurde als Commit `b0379c3` auf denselben Arbeitsbranch gepusht und war in PR #3 dokumentiert.
- Der gesamte validierte Entwicklungsstand wurde am 8. August 2026 über PR #18 in `main` integriert. GitHub markierte PR #3 wegen der vollständigen Commit-Erreichbarkeit automatisch als gemergt; PR #4 bis #17 wurden als ersetzt geschlossen.

### KP-R01 – Leere Speicheranzeige während langer Scans

- **Status:** entschärft
- Persistenter Cache wird beim Start geladen; Scans laufen im Hintergrund und blockieren den HTTP-Request nicht mehr.

### KP-R02 – Parallele Storage-Abfragen aus der Oberfläche

- **Status:** behoben
- Die UI verwendet einen Single-Flight-Lader für den vollständigen Storage-Snapshot.

### KP-R03 – Unbegrenzte Feature-Payloads aus sehr langen Kerzenreihen

- **Status:** entschärft
- Crypto- und Stock-Adapter begrenzen die Feature-Berechnung auf die letzten 500 Kerzen.
