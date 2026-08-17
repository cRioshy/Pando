# Nächste Schritte

Stand: 17. August 2026

## Verification-Stabilisierung und kontrolliertes Drain

- **Erfassung beendet:** finaler API-Snapshot am 17. August 2026 um 19:14 Uhr Europe/Berlin mit Plattform und 13/13 Services `OK`; 7-Tage-Sicht 19.100 Fälle, davon 13.563 `COMPLETED`, 1.692 `PENDING` und 3.845 `UNKNOWN`.
- **Gesamtledger geprüft:** 55.131 gültige Zeilen, null JSON-Fehler, 19.164 eindeutige Fälle; 13.615 `COMPLETED`, 1.692 `PENDING`, 3.857 `UNKNOWN`. 194 historische IDs besitzen je eine zusätzliche Completion-Zeile und bleiben unverändert.
- **Implementiert:** explizites `NORMAL`/`DRAIN`/`STOPPED`, unbekannte Modi fail-closed, DRAIN ohne neue Fälle, gehärtete Outcome-JSON-Persistenz, serialisierte Completion und exklusiver Ledger-Lock.
- **Commits:** `57d63c7 Add verification drain mode`, `c0a881d Harden outcome persistence`, `4472a98 Fix completion idempotency`; vorhandene ältere Übergabedokumente separat als `20069ef` gesichert.
- **Tests:** 47/47 gezielte und 325/325 vollständige Tests bestanden; Python-Kompilierung, JavaScript-Syntax und Diffprüfung bestanden.
- **AFTER-Backup bestanden:** `C:\Users\Admin\Desktop\PandorickBackUp_2026-08-17_19-29-44_AFTER.zip`, 1.587.549.058 Byte, 1.313 Einträge, SHA-256 `E9378D017F235219FA78B84ACEA9DBB0EF738E7EFEADFBEBB9454A21B17B5CAD`; vollständiger Stream-Test und zentrale Testextraktion bestanden.
- **DRAIN-Smoke bestanden:** Fall-/Creation-Zähler konstant 19.164; 32 bestehende Fälle abgeschlossen, `COMPLETED` 13.615 → 13.647, `PENDING` 1.692 → 1.660, historische Zusatz-Completions konstant 194, JSON-Fehler 0. Telegram aus/Dry-Run/0 Sendungen, Orders gesperrt. Stop gab Port in 1,961 Sekunden frei.
- **Jetzt:** Abschlussdokumentation separat committen, Branch pushen und Draft-PR gegen `main` erstellen; nicht mergen.
- **Nächster fachlicher Schritt:** DRAIN nur nach ausdrücklicher Freigabe erneut starten und den verbleibenden Pending-Bestand kontrolliert abbauen. Erst danach eine kanonisch deduplizierte, rein deskriptive Verification-Auswertung planen; noch keine Kalibrierung, Research View, Gate-, Telegram- oder Orderkopplung beginnen.

## Lokaler Wiederherstellungspunkt

- **Erledigt am 14. August 2026:** geprüftes Desktop-Backup `C:\Users\Admin\Desktop\pandorickbacktooback.zip` erstellt.
- 1.538.424.058 Byte, 1.267 Archiveinträge, `.git`, Dokumentation, Tests, `AGENTS.md`, Quellcode und vorhandene Projektdaten enthalten.
- Vollständiger Lesetest aller 1.266 Datei-Streams über 11.142.793.930 unkomprimierte Byte sowie zentrale Testextraktion bestanden.
- `.venv`, bekannte Cache-/Build-Verzeichnisse und vorhandene ZIP-Dateien wurden ausgeschlossen; das laufende PandorickKi wurde nicht gestoppt oder verändert.
- Backup lokal behalten und nicht ungeprüft überschreiben. Nächster fachlicher Schritt bleibt die Verification-Auswertung am 17. August 2026.

## Market Regime Contract v1

- **Phase 0 abgeschlossen:** Stock-/Polling-/Verification-Stand mit 50/50 gezielten und 299/299 vollständigen Tests als Commit `95d5d54` auf `agent/integrate-decision-gate-observer` veröffentlicht.
- **PR #23 integriert:** Merge-Commit `c751fe18e966dc6800d80925c8c7020093c85e8e` liegt auf `main`; der vollständige Head `4f68552` ist enthalten.
- **Implementierung lokal abgeschlossen:** Drei Achsen, stabile Feature-/Regime-IDs, Config-Fingerprint, Quality-Fail-Closed, Queue/Batch/Shutdown, append-only Ledger, vollständige Null-Kategorien in Coverage, GET-only API und read-only UI sind vorhanden. 55/55 gezielte und 318/318 vollständige Tests bestanden.
- **Kurzer Live-Smoke-Test abgeschlossen:** echte BTCUSDT-`15m`- und AAPL-`1d`-Daten, 2/2 persistiert, keine Drops/Fehler, sauberer Shutdown und keine Decision-/Signal-/Shadow-/Trade-/Telegram-/Orderereignisse. Der bestehende Produktionsdienst und seine Runtime-/History-Daten wurden nicht verändert.
- **AFTER-Backup validiert:** `C:\Users\Admin\Desktop\PandorickBackUp_2026-08-12_22-16-19_AFTER.zip`, 1.512.476.762 Byte, 1.201 Einträge, `.git`/Docs/Tests/Quellen enthalten und Testextraktion bestanden.
- **PR #24 aktualisiert:** Basis ist jetzt `main`; der neue `main` wurde ohne Rebase oder Force-Push in den Regime-Branch aufgenommen. Der Diff bleibt auf 29 Regime-Pfade begrenzt und konfliktfrei.
- **Retargeting-Verifikation:** erster Gesamtlauf traf einmal KP-019 (`WinError 145` beim Temp-Cleanup); isoliert 1/1 und unmittelbare vollständige Wiederholung 318/318 bestanden. Syntax, Scope, Secrets und Diff sind sauber.
- **PR #24 integriert:** Nach ausdrücklicher Freigabe am 14. August 2026 als normaler Merge-Commit `e7718c81613957d480653e89a2f82db686958b0d` nach `main` gemergt; GitHub meldet PR #24 `MERGED`.
- **Produktionsneustart und Liveprüfung abgeschlossen:** vier vollständige Crypto-/Stockzyklen, alle Services `OK`, 0 Sitzungsfehler, 0 STALE, Regime-Queue 0/512, acht aktuelle Symbole und 21 append-only Snapshots. Öffentliche Payloads enthalten keine Rohkerzen, Features, `raw_result`, Stock-Shadow-/Auditfelder oder Secrets.
- **Sicherheitsgrenzen bestätigt:** alle Regime-Snapshots observer-only und ohne aktiven Decision-Einfluss; Telegram aus/Dry-Run/0 Sendungen, Orders gesperrt und Stock-Verification-Fingerprint unverändert.
- **Jetzt:** laufenden observer-only Betrieb unverändert lassen und Coverage sammeln. Keine Schwellen automatisch fitten und keine Verbindung zu Decision Core, Shadow Gate, Telegram oder Orders herstellen.
- **Nächster terminierter Schritt:** am 17. August 2026 den freigegebenen siebentägigen Stock-Verification-Lauf kontrolliert beenden und dedupliziert/deskriptiv auswerten; Regime-Coverage dabei getrennt halten.

## Wiederaufnahme nach PC-Ausfall

- PandorickKi wurde am 12. August 2026 um 12:51 Uhr Europe/Berlin mit unverändertem Verification-Fingerprint sicher wieder gestartet. Die ungefähr zwölfstündige Erfassungslücke bleibt als reale Laufunterbrechung sichtbar; vorhandene Ledgerdaten wurden nicht verändert.
- Health, Web und Verification sind `OK`; Verification ist aktiv, Telegram aus/Dry-Run und Orderfreigabe `false`.
- Der reproduzierte Stock-/Polling-Freeze ist behoben: Stock läuft nicht wartend im Hintergrund; fällige Verification-Outcomes werden in 8er-Batches je Symbol/Quote nachgearbeitet.
- Live verifiziert: genau ein Listener, drei Stock-/Cryptozyklen, keine STALE-Dienste, null Sitzungsfehler, Telegram aus/Dry-Run/null Sendungen.
- **Nächster Schritt:** Den laufenden 7-Tage-Betrieb unverändert beobachten und beim Abschluss den `PENDING`-Rückstand sowie die kanonisch unabhängigen Fälle auswerten. Batchgröße nicht automatisch optimieren und keinen Fit starten.

## Stock-Shadow-Score- und Confidence-Kalibrierung

- **Vertrag entworfen und gegen Code/Marktphasenmessung reviewt:** `pandorickki.stock-shadow-calibration` Version 1 trennt Rohscore, kalibrierte 24h-Erfolgswahrscheinlichkeit und unabhängige Evidenz-Confidence.
- Wiederholte Zyklen derselben Tageskerze werden als korrelierte Wiederholungen ausgeschlossen; Fit und Holdout müssen chronologisch getrennt sein.
- Heutiger Status: `INSUFFICIENT_DATA`. Es existieren null abgeschlossene unabhängige 24h-Verification-Outcomes; daher keine Kalibrierung, keine Confidence und keine Gate-Wirkung.
- **Bestätigte erste Forschungsgrenze:** mindestens 400 unabhängige LONG-/SHORT-Outcomes, 100 je Richtung, 30 Handelstage, vier unterstützte Symbole und 40 Fälle je ausgewertetem Bucket. Auch `VALIDATED_OBSERVER` bleibt ohne Freigabewirkung.
- **Siebentägiger Lauf aktiv:** ausdrücklich freigegeben und am 10. August 2026 um 19:03:44 Uhr Europe/Berlin mit Fingerprint `3d23f923d6b9d9dc3019457afcb078591b5d8c8b4d1f4f4db55911724fa71747` gestartet. Nach zwei Zyklen zehn neue append-only Fälle; Health und alle zwölf Services `OK`, Telegram-/Orderflags `false`.
- **Exakter nächster Schritt:** Am 17. August 2026 um 19:10 Uhr Abschlusswerte erfassen, kontrolliert stoppen und nur Datenqualität, Outcome-Abdeckung sowie kanonisch unabhängige Fälle auswerten. Frühere Kurzlauf-Outcomes zeitlich trennen; keinen Fit starten.

## Aktueller Betrieb

- **US-Marktphasenprüfung abgeschlossen:** 10. August 2026, 18:05:44 bis 18:11:32 Uhr Europe/Berlin; fünf vollständige Stockzyklen und 25 Audits.
- Ergebnis: 20 Shadows = 10 LONG/5 SHORT/5 HOLD; 15 berechnete und 10 blockierte Risikopläne; Stock-Daten 15 `READY`/10 `BLOCKED`. AAPL/MSFT/NVDA/TSLA hatten 8,737 bis 19,505 Sekunden alte Yahoo-Quotes; `SPCX` blieb ohne belegbaren Quote-Zeitstempel blockiert.
- Sicherheit: Plattform gesund, 0 Sitzungsfehler, 0 STALE, Telegram aus/Dry-Run/0 Sendungen, Verification deaktiviert, keine Orderfreigabe und keine Observerfelder in der aktiven Stock-Projektion.
- Der separate Confidence-/Score-Kalibrierungsvertrag ist entworfen und reviewt; Ergebnis `INSUFFICIENT_DATA`. Keine Gate-Umschaltung, Telegram-/Orderkopplung oder siebentägige Verification gestartet.

- PandorickKi wurde am 9. August 2026 um 18:23 Uhr nach dem kurzen Verification-Lauf wieder normal gestartet. Health, Webserver, WebSocket, Statistik und alle elf normalen Services sind `OK`.
- Stock-Verification bleibt im normalen Start ausdrücklich deaktiviert; Telegram und Orders bleiben gesperrt. Der siebentägige Lauf wurde nicht gestartet.
- Veröffentlichungskontrolle des lokalen Verification-Stands: 297/297 Tests in 55,246 Sekunden bestanden; Syntax-, Diff- und Secret-Prüfung sauber.
- Implementierungscommit `53f1c8fe650889aff2d867f7f9dc75ac9799184a` ist auf `origin/agent/integrate-decision-gate-observer` veröffentlicht. PR #23 ist wieder `OPEN`, `Draft`, `CLEAN` und `MERGEABLE`; `main` blieb unverändert.

## Stock Live-Shadow-Verification

- **Implementiert und kurz kontrolliert verifiziert:** Version-1-Vertrag, deterministische IDs, append-only/restart-safe Ledger, Decision-/Tracker-Verknüpfung, getrennte Legacy-/Shadow-Outcomes, read-only 7-Tage-Aggregation, Detail-API und Control-Center-Bereich.
- Crypto ist ausdrücklich ausgeschlossen; produktive Stock-, Brain-, Decision-, Signal-, Outcome-, Learning-, Telegram- und Orderlogik blieb unverändert.
- Gezielte Tests: 34/34 bestanden. Der abschließende Gesamtlauf bestand mit 297/297 Tests in 42,693 Sekunden; JavaScript-Syntax und `git diff --check` waren sauber. Ein dazwischenliegender Gesamtlauf traf einmalig den bereits dokumentierten KP-019-Windows-Fehler (`WinError 145`) beim Aufräumen eines temporären Learning-Report-Verzeichnisses; der betroffene Test bestand isoliert mit 1/1 und die unmittelbar folgende vollständige Wiederholung mit 297/297.
- Kontrollierter Lauf: genau drei Zyklen, anschließend automatischer Stop; alle zwölf Dienste `OK`, 15 eindeutige Fälle und 15 Decision-Links, 12 `PENDING`, 3 erwartete `SPCX`-`UNKNOWN`, keine Rohkerzen oder `raw_result`, alle Telegram-/Order-/Active-Decision-Flags `false`, Port 8000 geschlossen.
- Der normale Starter aktiviert die Verification weiterhin nicht automatisch. Der siebentägige Lauf wurde nicht gestartet.
- Draft-PR #23 bleibt offen und Draft; `main` ist unverändert.
- **Nächster Schritt:** Ergebnisbericht prüfen. Erst nach ausdrücklicher Freigabe Verification für ungefähr sieben Tage mit unverändertem Konfigurationsfingerprint aktivieren; keine automatische Optimierung oder Gate-Umschaltung.

## Veröffentlichung der observer-only Stock-Pipeline

- **Veröffentlicht am 9. August 2026:** Commit `4258111ebe51175e06d4ece363bf9c5b7c23f28a` liegt auf `origin/agent/integrate-decision-gate-observer`.
- Vollständige Testsuite: 289/289 bestanden; Diff-, Scope- und Secret-Prüfung ohne Inhalts- oder Sicherheitsfehler.
- Draft-PR #23 gegen `main` ist offen und ausdrücklich nicht gemergt: `https://github.com/cRioshy/Pando/pull/23`.
- `main`, aktiver Legacy-Decision-/Signalpfad, Telegram und Orderausführung wurden nicht verändert.
- **Nächster Schritt:** Die aktive einmalige read-only US-Marktprüfung am 10. August 2026 um 15:40 Uhr Europe/Berlin abwarten und danach mindestens fünf vollständige Stockzyklen auswerten. Erst anschließend unabhängige Confidence beziehungsweise Score-Kalibrierung planen.

## Aktuelle Integrationsphase

- **Abgeschlossen am 8. August 2026.** Der vollständig getestete Entwicklungsstand wurde über PR #18 nach `main` integriert: `https://github.com/cRioshy/Pando/pull/18`.
- Die Abschlussdokumentation aus PR #19 ist ebenfalls gemergt. `origin/main` steht auf `381229a`; der vollständige Integrations-Head `3853d41` ist enthalten.
- Vor der Veröffentlichung bestanden Runtime-Preflight, 243/243 Tests, JavaScript-Syntax, `git diff --check`, Merge-Simulation sowie Runtime-/Secret-Scopeprüfung.
- PR #4 bis #17 wurden als ersetzt geschlossen. PR #3 wurde durch die vollständige Commit-Erreichbarkeit automatisch als gemergt markiert; es gab keinen zusätzlichen Einzel-Merge.
- Nach Abschluss der alten Kette und Merge von PR #19 sind keine offenen Pull Requests verblieben.
- **Post-Merge-Liveprüfung abgeschlossen:** kontrollierter Stop ohne harten Prozessabbruch, Start aus `.venv`, sechs vollständige Crypto-/Stock-Zyklen, Plattform und zehn Services `OK`, Sitzungsfehler null, aktuelle Crypto-Preise, NeuroBrain Queue/Drops/Fehler null und Telegram aus/Dry-Run.
- Storage meldete 145 physische Dateien, 2.548.436 Datensätze und 10,52 GB als `VERIFIED`. `DEGRADED` stammt ausschließlich aus zwei bekannten beschädigten historischen Stock-Backup-JSONs.
- Die Abschlussdokumentation aus PR #20 wurde nach ausdrücklicher Freigabe gemergt; `origin/main` steht auf `b8af62f`.
- Draft-PR #21 enthält ausschließlich den Merge-Abschlussnachtrag und bleibt offen sowie ungemergt: `https://github.com/cRioshy/Pando/pull/21`.
- Der Feature-Datenqualitätsvertrag Version 1 wurde über PR #22 nach `main` gemergt; `origin/main` steht auf `14e19bf`. Nach kontrolliertem Neustart liefen vier vollständige Crypto-/Stock-Zyklen mit allen zehn Services `OK`, null Sitzungsfehlern, NeuroBrain Queue/Drops null sowie Telegram aus/Dry-Run.
- Direkte Qualitätsprüfung: Crypto `PASS/VERIFIED/READY` mit 240/240 Binance-Kerzen und null Verstößen; Stock-Einzelsnapshot erwartungsgemäß `WARN/UNVERIFIED/WARMING` ohne Featurefehler.
- Der fachliche Decision-Gate-Vertrag `pandorickki.decision-gate` Version 1 ist lokal implementiert und mit zehn Vertragstests sowie 261/261 Gesamttests geprüft. Er arbeitet ausschließlich als aufrufbare Observer-Referenz, verlangt explizite Schwellen, blockiert unvollständige Qualität/Fakten/Risiken fail-closed und kann weder Telegram noch Orders freigeben.
- **Lokal und live umgesetzt:** Die kompakte `feature_quality`-Projektion erreicht Brain, Decision und Signal. Der separate `decision_gate_observer` ist im Web-Starter nach ausdrücklicher Freigabe diagnostisch mit Probability 60, Confidence 60 und Toleranz 0 aktiv; der bestehende Decision-/Signalpfad ist unverändert.
- **Verifikation:** Gezielte Suite 35/35 und vollständige Wiederholung 265/265 bestanden. Der einmalige Windows-Temp-Cleanupfehler war nicht reproduzierbar.
- **Liveverifikation:** Vier vollständige Zyklen, 11/11 Services `OK`, 32 eindeutige Audits (12 Crypto, 20 Stock), 0 `QUALIFIED`, 32 `BLOCKED`, null Telegram-/Orderfreigaben, Telegram aus/Dry-Run und keine neuen Dienstfehler seit dem freigegebenen Netzwerkstart.
- **Historischer Gate-Audit-Schritt abgeschlossen:** Reason Codes wurden ausgewertet und der Stock-Datenvertrag anschließend um öffentliche Kerzen, Shadow und observer-only Risikoplan ergänzt. Aktiver Signal- und Telegrampfad blieben unverändert.
- **Erste erweiterte Auswertung abgeschlossen:** eingefrorener 39-Minuten-Snapshot mit 272 Kandidaten, 2 technisch qualifizierten ETHUSDT-LONG-Fällen, 270 Blockierungen und null unsicheren Freigaben. Bericht: `docs/DECISION_GATE_AUDIT_REPORT.md`.
- **Weiterhin nachgewiesene Grenzen:** Confidence dupliziert derzeit Probability; `SPCX` besitzt keinen belegten öffentlichen Ticker. Der öffentliche Stockpfad bleibt am Wochenende wegen Quote-Freshness korrekt blockiert.
- **Stock-Datenvertrag integriert:** `pandorickki.stock-data` Version 1 prüft den getrennten öffentlichen Shadow einschließlich Risikoplan mit expliziter Policy und Reason Codes. Telegram und Orders bleiben immer gesperrt.
- **Read-only Tageskerzenprovider und Audit erledigt:** Yahoo query1/query2, 15-Minuten-Cache, Tickerblock für `SPCX`, kompakte Service-Telemetrie und strikt lokale Kerzenprüfung sind aktiv. Echt: AAPL 260/260 `PASS/VERIFIED/READY`; erster Plattformzyklus 4 erfolgreiche Historien, 1 erwarteter SPCX-Block, 0/5 `READY`. 44/44 gezielte und 278/278 Gesamttests bestanden.
- **Stock-Shadow-Kandidat erledigt und live geprüft:** `pandorickki.stock-shadow-candidate` Version 1 berechnet kompakte Fakten, Direction und einen ausdrücklich unkalibrierten Heuristikscore vollständig aus öffentlichen Kerzen und Kurs. Legacy und Shadow bleiben getrennt vergleichbar; `affects_active_decision=false`, keine Publikation/Persistenz und keine Telegram-/Orderfreigabe. Der Risikoplan wird ausschließlich durch den separaten Shadow-Risikovertrag ergänzt.
- **Observer-only Stock-Risikoplan erledigt:** `pandorickki.stock-shadow-risk` Version 1 verwendet öffentlichen Entry, ATR14/0,5-%-Mindestdistanz, Stop bei 1R und Ziele bei 1R/2R/3R. HOLD/ungültige Daten blockieren. Shadow-, Risiko- und Auditfelder werden vor dem aktiven Event entfernt. 37/37 gezielte und 289/289 Gesamttests bestanden.
- **Liveprüfung abgeschlossen:** Zwei vollständige Zyklen lieferten 8 öffentliche Shadows, 6 gültige LONG-/SHORT-Risikopläne, 2 HOLD-Blocks und 2 erwartete `SPCX`-Blocks. Plattform/Services gesund, 0 Sitzungsfehler, 0 STALE, NeuroBrain Queue/Drops 0 und Telegram-Sendungen 0. Die Daten-Audits blieben am Sonntag aufgrund Quote-Freshness/HOLD/SPCX sicher blockiert.
- **Marktphasenprüfung vorbereitet:** Einmalige lokale Automation für Montag, 10. August 2026, 15:40 Uhr Europe/Berlin ist als App-Bestätigungskarte vorbereitet. Nach Bestätigung beobachtet sie mindestens fünf Zyklen read-only und verändert weder Code noch Prozesse, Gate, Telegram oder Orders.
- **Nächster Schritt:** Automationskarte bestätigen und die Messung abwarten. Danach anhand der frischen Marktwerte eine unabhängige Confidence oder ehrliche Score-Kalibrierung planen. Keine Gate-, Telegram- oder Orderkopplung.

## Verbindliche Reihenfolge

1. **Funktionierenden Crypto-Stand sichern und veröffentlichen.**
   - **Erledigt am 1. August 2026.**
   - BEFORE-Backup, Scope-/Secret-Prüfung, Preflight, 10 Crypto-Tests, 200 Gesamttests und zwei Livezyklen erfolgreich.
   - Commit `b0379c3` auf `agent/add-market-feature-engine` gepusht.
   - Draft-PR #3 gegen `main` erstellt; ausdrücklich nicht mergen.

2. **Storage-Worker-Shutdown deterministisch machen.**
   - **Erledigt am 1. August 2026.**
   - Regressionstest reproduzierte die verfrühte Rückkehr und `WinError 145` vor dem Fix.
   - Nach `close()` werden neue Scans abgelehnt und laufende Worker beziehungsweise synchrone Refreshes vollständig abgewartet.
   - 201/201 Gesamttests bestanden; keine Runtime-Daten gelöscht.
   - Commit `610b4a9` veröffentlicht; gestapelter Draft-PR #4 gegen `agent/add-market-feature-engine` erstellt und nicht gemergt.

3. **Storage-Anzeige korrigieren.**
   - **Erledigt am 1. August 2026.**
   - Überlappende logische Ziele bleiben getrennt sichtbar, physische Dateien werden aber nur einmal gescannt und summiert.
   - API und UI unterscheiden physisch eindeutige Werte, logische Kategorieverweise und Überlappungen.
   - Alte Caches werden bis zum nächsten vollständigen Scan als nicht physisch verifiziert markiert.
   - Commit `a15770b` veröffentlicht; gestapelter Draft-PR #5 gegen `agent/fix-storage-worker-shutdown` erstellt und nicht gemergt.

4. **Storage-Scanner instrumentieren und reparieren.**
   - **Erledigt am 1. August 2026.**
   - Phasenlaufzeiten, kumulativer JSONL-Fortschritt, Restbytes sowie geschätzte Restläufe/-zeit werden pro Scan erfasst und im Control Center angezeigt.
   - Zwei schreibgeschützte Realmessungen ergaben 1,084 Sekunden mit altem Budget und 2,135 Sekunden bei 64 MiB; das Standardbudget wurde deshalb von 256 KiB auf 64 MiB erhöht.
   - Der reale JSONL-Index lag bei 5,69 %; mit dem neuen Budget waren bei der Messung ungefähr 82 weitere Minutenläufe erforderlich.
   - 39/39 gezielte und 204/204 vollständige Tests bestanden; keine History-Datei wurde gelöscht oder verändert.
   - Commit `cc6e92d` veröffentlicht; gestapelter Draft-PR #6 gegen `agent/fix-storage-physical-totals` erstellt und nicht gemergt.

5. **Dauerhaftes begrenztes Service-Fehlerjournal ergänzen.**
   - **Erledigt am 1. August 2026.**
   - Kompakte versionierte Fehlerprojektion mit Erst-/Letztbeobachtung und Fehleranzahl umgesetzt.
   - Secret-Filter und Ausschluss vollständiger Payloads beziehungsweise externer Antwortinhalte getestet.
   - Aktives Journal auf 5 MiB, Archive auf vier und Zusammenfassung auf 500 Fingerprints begrenzt.
   - Commit `8a0a78d` veröffentlicht; gestapelter Draft-PR #7 gegen `agent/instrument-storage-scanner` erstellt und nicht gemergt.

6. **Vertrag für kompakte Event-Payloads definieren.**
   - **Erledigt und veröffentlicht am 1. August 2026.**
   - Tatsächliche Producer und Feldleser in Brain, Decision Core, Trackern, Learning, Control Center, Telegram und NeuroBrain geprüft.
   - Vertrag `pandorickki.compact-market-event` Version 1, ausführbare Projektion, Validator und Kompatibilitätstests ergänzt.
   - Zwei echte Legacy-Abhängigkeiten ausdrücklich erfasst: Crypto-Swings aus Kerzen und Learning-Ergebnis aus `raw_result`.
   - Produktionspayloads und bestehende History bewusst noch nicht verändert.
   - Commit `311dd38` veröffentlicht; gestapelter Draft-PR #9 gegen `agent/fix-outcome-timestamp-normalization` erstellt und nicht gemergt.

7. **Brain- und NeuroBrain-Payloads verkleinern.**
   - **Consumer-Vorbereitung am 1. August 2026 abgeschlossen und veröffentlicht.**
   - Crypto Trade Tracker bevorzugt `market_context.recent_swing_low/high`, Learning Graph bevorzugt `public_result`; alte Raw-Payloads bleiben lesbar.
   - Vier neue Regressionstests und 221/221 Gesamttests bestanden.
   - Commit `1550d07` veröffentlicht; gestapelter Draft-PR #10 gegen `agent/define-compact-event-payload-contract` erstellt und nicht gemergt.
   - **Brain-Migration am 1. August 2026 implementiert und veröffentlicht.**
   - Neue Brain-History und `BRAIN_DECISION_RECEIVED` verwenden ausschließlich Version 1 mit erhaltener Quell-ID.
   - 28/28 gezielte und 222/222 vollständige Tests bestanden.
   - Commit `5b59fa2` veröffentlicht; gestapelter Draft-PR #11 gegen `agent/prepare-compact-payload-consumers` erstellt und nicht gemergt.
   - **Decision-/Signal-Migration am 1. August 2026 implementiert und veröffentlicht.**
   - Neue Decision-/Signal-Events und beide Ledger verwenden Version 1 ohne `raw_result`; alle IDs bleiben erhalten.
   - 32/32 gezielte und 223/223 vollständige Tests bestanden.
   - Commit `ed89a01` veröffentlicht; gestapelter Draft-PR #12 gegen `agent/compact-brain-payloads` erstellt und nicht gemergt.
   - **NeuroBrain-Persistenz am 1. August 2026 implementiert und veröffentlicht.**
   - Neue Inboxzeilen behalten ihre Kopfsicht und enthalten als Detailpayload nur Version 1; alte Inboxzeilen bleiben unverändert.
   - 18/18 gezielte und 224/224 vollständige Tests bestanden.
   - Commit `5d32bc7` veröffentlicht; gestapelter Draft-PR #13 gegen `agent/compact-decision-signal-payloads` erstellt und nicht gemergt.
   - **Liveverifikation am 1. August 2026 abgeschlossen:** drei saubere Produktionszyklen, alle zehn Services `OK`, echte Crypto-Preise, vollständige ID-Kette und keine Bulk-Felder in den geprüften neuen Zeilen.
   - **Schemaabgrenzung `KP-016` am 2. August 2026 behoben und live verifiziert:** Observer-Vertrag für Learning/Aggregate, Markt-Typ-Ergänzung für einzelwertige Preisupdates; 231/231 Tests und 152/152 neue Livezeilen ohne Verstoß.
   - Commit `e94c988` veröffentlicht; gestapelter Draft-PR #14 gegen `agent/compact-neurobrain-payloads` erstellt und nicht gemergt.
   - Bestehende History unverändert lesbar lassen.

8. **NeuroBrain gezielt entkoppeln.**
   - **Erledigt und am 2. August 2026 live verifiziert.**
   - **Vorgelagerte Schreibkonflikte am 2. August 2026 behoben und live verifiziert:** eindeutige Temp-Dateien, Pfadsperre, begrenzter Windows-Retry und geordnete Zustandssnapshots für NeuroBrain-Status und aktive Crypto-Trades.
   - 13/13 gezielte und 226/226 vollständige Tests bestanden; zwei Produktionszyklen ohne neue Ziel-Fingerprints oder Temp-Reste.
   - Commit `ed2a83e` auf dem bestehenden Branch veröffentlicht und Draft-PR #13 aktualisiert; nicht gemergt.
   - **Voraussetzung `KP-016` erledigt:** Markt- und Observer-Topics sind eindeutig getrennt und getestet.
   - FIFO-Queue mit Kapazität 2048, sichtbarem Drop-newest, Batchgröße 64, 250-ms-Flush, atomarem Status und vollständigem Shutdown-Drain umgesetzt.
   - 20/20 gezielte und 235/235 vollständige Tests; live 231 Zeilen in 48 Batches, null Drops/Fehler und sauberer Worker-Shutdown.
   - Ausschließlich NeuroBrain entkoppelt; der vollständige EventBus blieb unverändert.
   - Commit `0fe5bd6` veröffentlicht; gestapelter Draft-PR #15 gegen `agent/fix-neurobrain-observer-schema` erstellt und nicht gemergt.

9. **Learning-Metriken vereinheitlichen.**
   - **Erledigt am 2. August 2026.**
   - Vertrag Version 1 mit eindeutigen Begriffen, expliziten Zählern/Nennern, einheitlicher Hit-Rate und scope-geprüfter Outcome-Abdeckung umgesetzt.
   - Learning Report verwendet exakte `decision_id`-Zuordnung; nicht vergleichbare historische Aggregate liefern `null` statt einer erfundenen Quote.
   - UI, Statistik und Graph kennzeichnen Learning-Updates als Projektionen und melden ausdrücklich, dass kein ML-Modell trainiert wird.
   - 239/239 Gesamttests, Syntax-, Diff- und Runtime-Prüfung bestanden; zwei Livezyklen mit allen zehn Services `OK`, Crypto-Preisen, NeuroBrain ohne Drops und Telegram aus/Dry-Run verifiziert.
   - Commit `e09c187` veröffentlicht; gestapelter Draft-PR #16 gegen `agent/queue-neurobrain-receiver` erstellt und nicht gemergt.

10. **UI härten.**
    - **Erledigt und am 2. August 2026 live verifiziert.**
    - Genau ein Polling-Fallback, single-flight Statusabruf und WebSocket-Reconnect mit begrenztem Backoff umgesetzt.
    - REST- und Live-WebSocket-Snapshots liefern Heartbeat-Alter und zentrale `STALE`-Klassifikation mit konfigurierbarer 150-Sekunden-Standardschwelle.
    - Stop/Restart unterbrechen den Zyklus-Warteabschnitt im 100-ms-Raster; Restart startet die Adapter im selben Prozess. Kein Phantom-Service durch Steuerbefehle.
    - Learning Graph koalesziert Interaktionen per Browser-Frame, lädt single-flight, pausiert in ausgeblendeten Tabs und berechnet das Force-Layout nur bei Strukturänderung neu.
    - 243/243 Gesamttests, JavaScript-Syntax und Diffprüfung bestanden. Live: Reconnect ohne Reload, zehn Services, Health `OK`, Restart `APPLIED` nach rund 104 ms, Prozess-Stop 2,326 s, 76 Knoten/179 Kanten, keine Browserfehler, Telegram aus/Dry-Run.
    - Commit `2f779e9` veröffentlicht; gestapelter Draft-PR #17 gegen `agent/unify-learning-metrics` erstellt und nicht gemergt.

## Erst anschließend

- **Feature-Datenqualitätsvertrag erledigt, nach `main` gemergt und live verifiziert:** Sortierung, `keep_last`-Duplikate, OHLC-Konsistenz, Non-Finite-Werte, Mindestkerzen und Warmup sind versioniert und als Metadaten sichtbar.
- **Decision-Gate-Vertrag lokal erledigt und getestet:** Fakten-, Risiko-, Confidence-, Datenqualitäts- und Konfliktregeln sind fail-closed mit eindeutigen Reason Codes definiert. Noch nicht aktiv in den EventBus integrieren oder als Freigabe verwenden.
- Kompakte `feature_quality`-Projektion ohne vollständige Features in den Marktvertrag aufnehmen und über Brain bis zu einem späteren Observer erhalten.
- Danach einen begrenzten Decision-Gate-Audit-Observer integrieren und live auswerten; Decision-/Signal-Consumer noch nicht umschalten.
- Telegram ausschließlich an freigegebene finale Ereignisse anbinden und bis dahin deaktiviert beziehungsweise im Dry-Run lassen.
- Aufbewahrungs-/Archivkonzept und Portabilität der Legacy-Pfade separat planen, ohne bestehende History zu löschen.

## Zuletzt erledigt

- Decision-Gate-Vertrag `pandorickki.decision-gate` Version 1 als rein beobachtende, fail-closed Referenz implementiert.
- Explizite Probability-/Confidence-Schwellen ohne versteckte Defaults, Qualitäts-/Warmup-/Order-/Fakten-/Risiko-/Konfliktregeln und deterministische Reason Codes definiert.
- Zehn Vertragstests und 261/261 Gesamttests bestanden. Das Modul ist nicht an den EventBus angeschlossen, setzt stets `ready_for_telegram=false` und `order_execution_allowed=false` und verändert den laufenden Dienst nicht.
- Nächster Schritt: kompakte `feature_quality`-Projektion durch die bestehende Payloadkette erhalten; danach separaten Audit-Observer integrieren.

- Feature-Datenqualitätsvertrag `pandorickki.feature-data-quality` Version 1 implementiert und in `FeatureEngine` integriert.
- Sortierung, `keep_last`-Duplikate, OHLCV-/Non-Finite-Prüfung, Mindestkerzen, Zeitstempelpflicht und Warmup-Metadaten mit 30/30 gezielten sowie 251/251 vollständigen Tests verifiziert.
- Isolierter Realtest: 240/240 Binance-BTCUSDT-Kerzen, `PASS`, Reihenfolge `VERIFIED`, Warmup `READY`, null Verstöße. Vollständiger Plattformneustart erst nach Merge.

- UI-Härtung abgeschlossen: idempotentes Polling, Backoff-Reconnect, zentrale STALE-Projektion, echter In-Process-Restart, schneller Stop-Wartepfad und Graph-Koaleszierung.
- 243/243 Gesamttests bestanden; Browser reconnectete nach Prozessneustart ohne Reload und zeigte zehn korrekte Services mit Heartbeat-Alter.
- Commit `2f779e9` auf `agent/harden-control-center-ui` veröffentlicht; Draft-PR #17 ist offen, Draft und ungemergt.
- Nächster Arbeitsschritt ist der Feature-Datenqualitätsvertrag. Noch keine Umsetzung von Decision Gate oder Telegram-Kette beginnen.

- Learning-Metrikvertrag `pandorickki.learning-metrics` Version 1 eingeführt; Hit-Rate, Outcome-Abdeckung, Projektionszähler und fehlendes ML-Training in Report, Statistik, Graph und UI eindeutig ausgewiesen.
- 239/239 Gesamttests bestanden; lokale Oberfläche zeigte Brüche, `nicht vergleichbar` bei inkompatiblem Aggregatscope und keine Browser-Konsolenfehler.
- Kontrollierter Neustart mit zwei vollständigen Crypto-/Stock-Zyklen: alle zehn Services `OK`, NeuroBrain Queue/Drops/Fehler null, Telegram aus/Dry-Run und null Nachrichten.
- Commit `e09c187` auf `agent/unify-learning-metrics` veröffentlicht; Draft-PR #16 ist offen, Draft und ungemergt.
- Nächster Arbeitsschritt ist ausschließlich Punkt 10: UI-Lebenszyklus, WebSocket-Reconnect, idempotentes Polling, STALE-Heartbeats und Graph-Performance.

- NeuroBrain-Datei-I/O über begrenzte FIFO-Queue und einzelnen Batch-Worker vom Publisher entkoppelt; Drop-newest, Healthmetriken und vollständiger Flush-Shutdown getestet.
- 20/20 gezielte und 235/235 vollständige Tests; live 231 neue Zeilen in 48 Batches ohne Drops, FIFO-/Schema- oder Workerfehler. Dienst nach erfolgreichem Stop erneut sicher gestartet.
- Commit `0fe5bd6` auf `agent/queue-neurobrain-receiver` veröffentlicht; Draft-PR #15 ist offen, Draft und ungemergt.
- NeuroBrain-Schemaabgrenzung behoben: kompakter Observer-Vertrag für Learning-/Aggregatereignisse, Markt-Typ-Inferenz für einzelwertige Crypto-/Commodity-Updates.
- 15/15 gezielte und 231/231 vollständige Tests bestanden; 152 neue Livezeilen ohne Schema-, Pflichtfeld- oder Bulk-Verstoß, alle Services `OK`, Telegram aus/Dry-Run.
- Commit `e94c988` auf `agent/fix-neurobrain-observer-schema` veröffentlicht; Draft-PR #14 bleibt offen, Draft und ungemergt.
- Wiederkehrende `WinError 5`-Konflikte bei NeuroBrain-Status und aktiven Crypto-Trades mit einem konfliktresistenten atomaren JSON-Schreibpfad behoben.
- Retry- und Parallelitätsregressionen, 13/13 gezielte sowie 226/226 vollständige Tests bestanden; zwei Livezyklen ohne neue Fehlerfingerprints oder Temp-Reste.
- Vollständigen gestapelten Payloadstand kontrolliert live gestartet und drei saubere Produktionszyklen verifiziert.
- Neue Brain-, Decision-, Signal- und marktbezogene NeuroBrain-Zeilen verwenden Version 1, enthalten keine Bulk-Felder und behalten die vollständige ID-Kette.
- Die zunächst als `KP-016` dokumentierte Live-Vertragslücke wurde am 2. August 2026 behoben; die darauf aufbauende Queue-/Batch-Entkopplung ist ebenfalls abgeschlossen und veröffentlicht.
- Neue NeuroBrain-Inboxzeilen auf Version 1 umgestellt; Kopfsicht, ID-Kette, Duplikatschutz und alte Inboxzeilen erhalten.
- 18/18 gezielte und 224/224 vollständige Tests bestanden; Commit `5d32bc7` und gestapelter Draft-PR #13 veröffentlicht.
- Neue Decision-/Signal-Events und beide Ledger auf Version 1 umgestellt; IDs und Legacy-Eingangskompatibilität erhalten.
- 32/32 gezielte und 223/223 vollständige Tests bestanden; Commit `ed89a01` und gestapelter Draft-PR #12 veröffentlicht.
- Neue Brain-History und `BRAIN_DECISION_RECEIVED` auf die kompakte Version-1-Projektion umgestellt; bestehende History unangetastet gelassen.
- 28/28 gezielte und 222/222 vollständige Tests bestanden; Commit `5b59fa2` und gestapelter Draft-PR #11 veröffentlicht.
- Crypto Trade Tracker und Learning Graph auf kompakte Ersatzfelder vorbereitet; Legacy-Raw-Payloads bleiben lesbar.
- 20/20 gezielte und 221/221 vollständige Tests bestanden; Commit `1550d07` und gestapelter Draft-PR #10 veröffentlicht.
- Kompakten Event-Payload-Vertrag Version 1 mit tatsächlicher Consumer-Matrix, Validator und fünf Kompatibilitätstests definiert; Produktionspayloads noch unverändert gelassen.
- 217/217 Gesamttests bestanden; Commit `311dd38` und gestapelter Draft-PR #9 veröffentlicht.
- Outcome-Zeitstempel-Fix kontrolliert live verifiziert: vier Crypto-Heartbeats, alle Services `OK`, bekannter Fehlerzähler unverändert bei 158, Telegram aus/Dry-Run.
- Commit `a2a139f` veröffentlicht und gestapelten Draft-PR #8 gegen den Fehlerjournal-Branch erstellt.
- Outcome-Tracker-Zeitnormalisierung rückwärtskompatibel umgesetzt: naive historische Werte gelten beim Lesen als UTC, vorhandene History bleibt unverändert.
- Regressionstest reproduzierte den Livefehler vor dem Fix; danach 12/12 Outcome-Tracker-Tests und 212/212 Gesamttests bestanden.
- Neuen Journalstand kontrolliert live gestartet: alle zehn Services `OK`, Journal gesund, Telegram aus/Dry-Run und 110/110 Storage-Dateien ohne Scannerfehler verarbeitet.
- Das Journal machte drei Wiederholungen eines zuvor flüchtigen Outcome-Tracker-Zeitstempelfehlers dauerhaft sichtbar; als `KP-014` dokumentiert, noch nicht behoben.
- Begrenztes, secret-gefiltertes Service-Fehlerjournal mit atomarer Erst-/Letzt-Zusammenfassung ergänzt.
- PandorickKi nach Scanner-Veröffentlichung kontrolliert neu gestartet und zwei Produktionszyklen verifiziert: alle Services `OK`, keine neuen Sessionfehler, Telegram aus/Dry-Run.
- Produktions-Storage-Scan mit 106/106 Dateien in 2,416 Sekunden und 9,20 % kumulativem JSONL-Fortschritt bestätigt; Control Center ohne Browser-Konsolenfehler geprüft.
- Storage-Scanner phasenweise instrumentiert und kumulativen JSONL-Indexfortschritt samt Restschätzung sichtbar gemacht.
- Standardbudget anhand schreibgeschützter Realmessungen auf 64 MiB pro Lauf eingestellt; 204/204 Gesamttests bestanden.
- Storage-Ziele pro physischem Pfad dedupliziert und Scanbudget nur einmal je Datei verbraucht.
- Physische und logische Summen samt Überlappungsanzahl in API und Control Center getrennt ausgewiesen.
- 44/44 gezielte und 203/203 vollständige Tests nach der Storage-Summenkorrektur bestanden.
- Storage-Worker-Shutdown mit deterministischem Race-Test und eindeutigem `close()`-Vertrag behoben.
- 27/27 Storage-, 36/36 Storage-/Web- und 201/201 Gesamttests nach dem Fix bestanden.
- Crypto-Reparaturstand mit verifiziertem BEFORE-Backup, 200/200 Tests und zwei erfolgreichen Livezyklen gesichert.
- Commit `b0379c3` veröffentlicht und Draft-PR #3 gegen `main` erstellt.
- Persistenter Storage-Cache und Dateiindex.
- Einzelner Hintergrundscanner mit Timeout, Sperre und Abbruch.
- Inkrementelle JSONL-Offsets und Schutz unvollständiger letzter Zeilen.
- Metadatenmodus für große Dateien und globales JSONL-Bytebudget.
- Asynchroner Storage-Refresh mit HTTP `202`.
- Scanstatus und Single-Flight-Storage-Lader im Control Center.
- Broadcast-Drosselung und Browser-Payload-Sanitizing.
- Begrenzung der Crypto-/Stock-Feature-Berechnung auf 500 Kerzen.
- Ergänzte Storage-, Timeout-, Parallelitäts- und UI-Tests.
- Dauerhafte lokale Übergaberegeln und Ist-Dokumentation angelegt.
- Öffentlichen Branch `agent/add-market-feature-engine` aktualisiert und Draft-PR #2 eröffnet.
- Crypto-Ausfall behoben: interner Binance/Bitget-Marktdatenclient, optionale Futures-Daten und korrekte ERROR-/DEGRADED-Projektion.
- Projektlokale `.venv`, reproduzierbares Setup und Runtime-Preflight eingeführt.
- 200/200 Tests sowie zwei aufeinanderfolgende Live-Produktionszyklen erfolgreich verifiziert.
