# Arbeitsregeln für Codex

Diese Datei gilt für das gesamte Repository `PandorickKi`.

## Verbindlicher Start jeder Aufgabe

Vor jeder Analyse, Planung, Änderung oder Ausführung muss Codex in dieser Reihenfolge vollständig lesen:

1. `docs/CURRENT_SYSTEM_STATE.md`
2. `docs/SESSION_HANDOVER.md`
3. `docs/ARCHITECTURE.md`
4. `docs/KNOWN_PROBLEMS.md`
5. `docs/NEXT_STEPS.md`

Danach muss Codex die tatsächliche Repository-Struktur und die für die Aufgabe relevanten Codepfade prüfen. Frühere Chats und Übergabedokumente sind Orientierung, aber niemals alleinige Wahrheitsquelle. Bei Widersprüchen haben der aktuelle Code, die aktuelle Konfiguration und reproduzierbare Testergebnisse Vorrang.

Vor Änderungen an Markt-, Brain-, Decision-, Signal- oder NeuroBrain-Payloads muss zusätzlich `docs/EVENT_PAYLOAD_CONTRACT.md` gelesen und gegen die tatsächlichen Consumer geprüft werden.

Vor Änderungen an Learning-, Outcome-, Hit-Rate-, Pattern- oder Trainingsmetriken muss zusätzlich `docs/LEARNING_METRICS_CONTRACT.md` gelesen und gegen die tatsächlichen Produzenten, Ledger und UI-Nenner geprüft werden.

Vor Änderungen an OHLCV-Normalisierung, Feature-Eingängen, Sortierung, Kerzenduplikaten, Warmup oder `FeatureEngine` muss zusätzlich `docs/FEATURE_DATA_QUALITY_CONTRACT.md` gelesen und gegen Crypto-/Stock-Producer sowie alle Feature-Consumer geprüft werden.

Vor Änderungen am Decision Core, an fachlichen Freigaberegeln, `ready_for_telegram`, Signal-/Meldungsfreigaben oder einer späteren Telegram-Kopplung muss zusätzlich `docs/DECISION_GATE_CONTRACT.md` gelesen und gegen Feature-Qualität, Brain-, Decision-, Tracker- und Telegram-Consumer geprüft werden.

Vor Änderungen an Aktien-Kerzenquellen, Livepreisen, Stock-Zeitstempeln oder normalisierten Stock-Risikoplänen muss zusätzlich `docs/STOCK_DATA_CONTRACT.md` gelesen und gegen `StockAdapter`, den externen Legacy-Producer, Feature-Qualität, kompakten Eventvertrag und Decision Gate geprüft werden.

Vor Änderungen am öffentlichen Aktien-Shadow-Kandidaten, seiner Direction, Probability oder seinen Score-Komponenten muss zusätzlich `docs/STOCK_SHADOW_CANDIDATE.md` gelesen werden. Der Shadow bleibt observer-only, unkalibriert und strikt vom aktiven Legacy-Pfad getrennt.

Vor Änderungen am öffentlichen Stock-Shadow-Risikoplan, an ATR-, Stop-, Ziel-, Chance-Risiko- oder Rundungsregeln muss zusätzlich `docs/STOCK_SHADOW_RISK.md` gelesen werden. Der Plan bleibt observer-only und darf nicht in den aktiven Event-, Telegram- oder Orderpfad gelangen.

Vor Änderungen an Stock-Live-Shadow-Verification, deren IDs, Persistenz, Outcome-Horizont, Aggregaten oder Control-Center-Projektion muss zusätzlich `docs/STOCK_SHADOW_VERIFICATION_CONTRACT.md` gelesen werden. Die Verification bleibt stock-only, append-only und observer-only; Crypto, produktive Decisions, bestehende Outcomes, Telegram und Orders dürfen dadurch nicht verändert werden.

Vor Änderungen an Stock-Shadow-Score-Kalibrierung, Confidence, Reliability-Buckets, Kalibrierungsartefakten oder deren Mindestabdeckung muss zusätzlich `docs/STOCK_SHADOW_CALIBRATION_CONTRACT.md` gelesen werden. Kalibrierung bleibt offline, stock-only und observer-only; unzureichende oder korrelierte Daten dürfen keine Probability oder Confidence erzeugen.

## Verbindlicher Abschluss jeder Aufgabe

- Nach jeder abgeschlossenen Aufgabe `docs/SESSION_HANDOVER.md` aktualisieren.
- Bei Architekturänderungen zusätzlich `docs/CURRENT_SYSTEM_STATE.md` und `docs/ARCHITECTURE.md` aktualisieren.
- Neue sowie weiterhin bestehende Fehler in `docs/KNOWN_PROBLEMS.md` eintragen oder aktualisieren.
- Erledigte, verworfene und neue Aufgaben in `docs/NEXT_STEPS.md` nachführen.
- Testergebnisse nur als bestanden dokumentieren, wenn die genannten Befehle tatsächlich ausgeführt wurden.
- Nicht abgeschlossene oder nicht verifizierte Arbeiten ausdrücklich kennzeichnen.

`docs/SESSION_HANDOVER.md` muss mindestens enthalten:

- Datum und Uhrzeit
- Ziel der Aufgabe
- durchgeführte Arbeiten
- veränderte Dateien
- neue Dateien
- ausgeführte Befehle
- ausgeführte Tests
- tatsächliche Testergebnisse
- bekannte Fehler
- getroffene Architekturentscheidungen
- nicht abgeschlossene Punkte
- exakter nächster sinnvoller Arbeitsschritt

## Sicherheits- und Änderungsregeln

- Keine bestehenden Projektdaten, History-Dateien, Lerndaten, Tokens, Secrets oder lokalen Konfigurationen löschen, leeren oder überschreiben.
- Keine echten Trades und keine automatische Orderausführung aktivieren oder ergänzen.
- Telegram bleibt ohne ausdrückliche Freigabe deaktiviert beziehungsweise im Dry-Run.
- Runtime-Verzeichnisse wie `data/`, `storage/`, `runtime_logs/` und `backups/` nur lesen, wenn dies für die konkrete Aufgabe erforderlich ist; niemals ungefragt bereinigen.
- Keine Zugangsdaten in Dokumentation, Tests, Logs, Commits oder Browser-Payloads übernehmen.
- Änderungen klein, nachvollziehbar und mit passenden Tests durchführen.
- Bestehende fremde Änderungen im Arbeitsbaum erhalten und nicht zurücksetzen.
- Externe Legacy-Projekte nur über Adapter anbinden; nicht ungefragt verändern.
- Vor destruktiven Aktionen Ziel und Umfang eindeutig verifizieren und erforderliche Freigaben einholen.

## Projektgrenzen

PandorickKi ist eine lokale Analyse-, Integrations-, Simulations- und Beobachtungsplattform. Der Kern führt keine Börsenorders aus. Modulnamen wie `Brain`, `Decision Core` oder `Learning` dürfen nicht als Beleg für nicht implementierte KI-, Freigabe- oder Trainingslogik interpretiert werden. Dokumentation muss die tatsächliche Implementierung beschreiben.
