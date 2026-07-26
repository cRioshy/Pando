# Bekannte Probleme

Stand: 26. Juli 2026

## Offen

### KP-011 – Storage-Worker kann Shutdown überleben

- **Priorität:** hoch
- **Status:** offen, nicht-deterministisch bestätigt
- **Beobachtung:** Der vollständige Testlauf vom 26. Juli 2026 scheiterte einmal mit `WinError 145`, weil ein temporäres `storage/statistics`-Verzeichnis beim Testende noch nicht leer war. Der isolierte Wiederholungslauf bestand.
- **Ursache im Code:** `StorageStatisticsService.close()` setzt das Abbruchsignal, wartet aber nur eine Sekunde. Ein noch lebender Worker kann anschließend Index oder Cache schreiben.
- **Auswirkung:** Flaky Tests; beim schnellen Shutdown kann ein Worker länger als sein Besitzer beziehungsweise dessen temporäres Zielverzeichnis leben.
- **Nächster Fix:** Shutdown-Vertrag festlegen, Worker zuverlässig beenden oder Schreibabschluss synchronisieren und einen deterministischen Regressionstest ergänzen.

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

### KP-010 – Arbeitsbaum ist noch nicht versioniert

- **Priorität:** hoch
- **Status:** offen
- **Beobachtung:** Storage-, UI-, Adapter- und Dokumentationsänderungen liegen lokal und noch nicht als überprüfter Commit im Repository-Verlauf.
- **Auswirkung:** GitHub beziehungsweise ein frischer Checkout enthält diesen Stand noch nicht.
- **Nächster Schritt:** Diff und Secret-/Runtime-Scope prüfen, anschließend nur nach ausdrücklicher Freigabe committen und pushen.

## Behoben oder entschärft

### KP-R01 – Leere Speicheranzeige während langer Scans

- **Status:** entschärft
- Persistenter Cache wird beim Start geladen; Scans laufen im Hintergrund und blockieren den HTTP-Request nicht mehr.

### KP-R02 – Parallele Storage-Abfragen aus der Oberfläche

- **Status:** behoben
- Die UI verwendet einen Single-Flight-Lader für den vollständigen Storage-Snapshot.

### KP-R03 – Unbegrenzte Feature-Payloads aus sehr langen Kerzenreihen

- **Status:** entschärft
- Crypto- und Stock-Adapter begrenzen die Feature-Berechnung auf die letzten 500 Kerzen.
