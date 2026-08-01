# Bekannte Probleme

Stand: 1. August 2026

## Offen

### KP-012 – Historische Service-Exceptions werden nicht dauerhaft journalisiert

- **Priorität:** mittel
- **Status:** offen; durch aktuelle Health-Details teilweise entschärft
- **Beobachtung:** Der erste konkrete Crypto-Fehler vom 27. Juli war am 31. Juli nicht mehr vorhanden, weil vollständige Service-Events nur in einer begrenzten In-Memory-Historie lagen.
- **Aktueller Schutz:** Crypto-Events enthalten jetzt Fehlerart, Stufe, Symbol und Provider-Versuche. `SharedState` hält `last_error` und `last_error_details`, solange der Fehler aktuell ist.
- **Restproblem:** Eine länger zurückliegende erste Exception kann weiterhin aus dem In-Memory-Bestand verschwinden.
- **Nächster Fix:** Kleines größenbegrenztes, rotierendes Service-Fehlerjournal entwerfen; keine Tokens, Antwortinhalte oder unbegrenzte Logs persistieren.

### KP-001 – Storage-Scan überschreitet das Zeitlimit

- **Priorität:** hoch
- **Status:** offen
- **Beobachtung:** Der reale Scan endete zuletzt nach 35,236 Sekunden als `TIMEOUT`; 27 von 94 erkannten Dateien waren abgeschlossen.
- **Auswirkung:** Der Cache verhindert eine leere Speicheranzeige, aber Scanfortschritt und Indexaufbau können über mehrere Intervalle unvollständig bleiben.
- **Bereits vorhanden:** Hintergrund-Worker, Einzelscan-Sperre, 30-Sekunden-Timeout, 256-KiB-JSONL-Budget, persistente Offsets und Metadatenmodus für große Dateien.
- **Nächste Diagnose:** Dauer getrennt für Dateiermittlung, `stat`/Fingerprint, Indexladen, Dateiartbehandlung und Cache-Schreiben instrumentieren; keine Retention oder Löschung als Schnelllösung verwenden.

### KP-002 – WebSocket-Fallback und Reconnect sind unvollständig

- **Priorität:** hoch
- **Status:** offen
- **Beobachtung:** `close` startet ungeprüft ein neues Polling-Intervall, `error` setzt nur den Textstatus, Nachrichten werden ohne lokalen JSON-/Render-Fehlerpfad verarbeitet und ein Reconnect fehlt.
- **Auswirkung:** Die Oberfläche kann „Polling“ anzeigen, ohne zuverlässig weiterzuladen, oder mehrere Polling-Timer erzeugen.
- **Nächster Fix:** genau einen Polling-Timer verwalten, `error` und `close` idempotent behandeln, begrenzten Backoff-Reconnect ergänzen und mit Webtests absichern.

### KP-003 – Synchroner EventBus kann Publisher blockieren

- **Priorität:** mittel
- **Status:** offen
- **Beobachtung:** Handler werden synchron im veröffentlichenden Thread ausgeführt.
- **Auswirkung:** Langsame Datei-, Statistik- oder Netzwerkhandler verzögern Produzenten und nachfolgende Handler.
- **Hinweis:** Eine Entkopplung ist eine Architekturänderung und benötigt eigene Freigabe und Reihenfolgeverträge.

### KP-004 – Brain und Decision Core besitzen kein unabhängiges Freigabe-Gate

- **Priorität:** mittel
- **Status:** offen
- **Beobachtung:** Brain persistiert und reicht weiter; Decision Core normalisiert deterministisch.
- **Auswirkung:** Modulnamen können eine fachliche Prüfung suggerieren, die nicht implementiert ist.
- **Sicherheitsregel:** Daraus niemals automatische oder reale Orders ableiten.

### KP-005 – Telegram umgeht die finale Entscheidungskette

- **Priorität:** mittel
- **Status:** offen
- **Beobachtung:** Telegram abonniert Crypto-/Stock-Analysen und simulierte Crypto-Trade-Updates direkt.
- **Auswirkung:** Eine Nachricht kann vor oder unabhängig von `DECISION_CREATED`/`SIGNAL_CREATED` entstehen.
- **Sicherheitsregel:** Telegram deaktiviert beziehungsweise im Dry-Run lassen, bis ein explizites Gate entworfen und freigegeben ist.

### KP-006 – Keine zentrale Retention-Policy

- **Priorität:** mittel
- **Status:** offen
- **Beobachtung:** Einzelne Ledger rotieren, der Gesamtbestand wächst weiter.
- **Auswirkung:** Längere Backups, größere Scans und steigender Speicherverbrauch.
- **Sicherheitsregel:** Keine vorhandenen History- oder Lerndaten ohne ausdrückliche Aufbewahrungsentscheidung löschen.

### KP-007 – Feature-Eingänge werden nicht strikt validiert

- **Priorität:** mittel
- **Status:** offen
- **Beobachtung:** Keine verbindliche Sortierungs-, Duplikat-, OHLC-Konsistenz-, Non-Finite- oder Mindestkerzenprüfung.
- **Auswirkung:** Ungültige Eingangsdaten können Zwischenrechnungen und Warmup-Werte beeinflussen.

### KP-008 – Heartbeats werden nicht als veraltet klassifiziert

- **Priorität:** niedrig
- **Status:** offen
- **Beobachtung:** Zeitstempel werden angezeigt, aber es existiert keine zentrale `STALE`-Schwelle.

### KP-009 – Portabilität durch lokale Windows-Pfade eingeschränkt

- **Priorität:** niedrig
- **Status:** offen
- **Beobachtung:** Standard- und Batchpfade verweisen teilweise auf lokale externe Projekte.
- **Auswirkung:** Ein neuer Rechner benötigt explizite Pfadkonfiguration.

## Behoben oder entschärft

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
- Der spätere Crypto-Reparaturstand wurde als Commit `b0379c3` auf denselben Arbeitsbranch gepusht und liegt separat in Draft-PR #3: `https://github.com/cRioshy/Pando/pull/3`.
- Draft-PR #3 bleibt ungemergt.

### KP-R01 – Leere Speicheranzeige während langer Scans

- **Status:** entschärft
- Persistenter Cache wird beim Start geladen; Scans laufen im Hintergrund und blockieren den HTTP-Request nicht mehr.

### KP-R02 – Parallele Storage-Abfragen aus der Oberfläche

- **Status:** behoben
- Die UI verwendet einen Single-Flight-Lader für den vollständigen Storage-Snapshot.

### KP-R03 – Unbegrenzte Feature-Payloads aus sehr langen Kerzenreihen

- **Status:** entschärft
- Crypto- und Stock-Adapter begrenzen die Feature-Berechnung auf die letzten 500 Kerzen.
