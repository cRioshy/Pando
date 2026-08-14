# Sicherheitsgrenzen

Stand: 12. August 2026

Market Regime v1 ist eine einseitige Beobachtungsgrenze:

```text
Marktdaten -> Feature Quality -> Feature Engine -> Regime Observer -> Ledger/API/UI
```

Es existiert keine Verbindung vom Regime-Observer zu Decision Core, Shadow Gate, Outcome-Entscheidung, Trade Tracker, Telegram oder Orderausführung. Jeder Snapshot setzt die drei Sicherheitsflags auf `false`. Nur kompakte Snapshots verlassen den Worker; Kerzen und vollständige Feature-Reihen bleiben im Speicher. Queue-Überlauf verwirft sichtbar den neuesten Input, niemals bestehende History. Telegram bleibt deaktiviert beziehungsweise Dry-Run; echte Orders bleiben ausgeschlossen.
