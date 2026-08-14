# Lokale API

Stand: 12. August 2026

## Market Regime v1

Alle Regime-Endpunkte sind lokal und read-only:

- `GET /api/v1/regime/current` – aktuelle Snapshots; optionale Filter `asset_type`, `symbol`
- `GET /api/v1/regime/{symbol}` – aktueller Snapshot eines Symbols
- `GET /api/v1/regime/history` – History mit `asset_type`, `symbol`, `days`, `limit` (1–500), `offset`
- `GET /api/v1/regime/statistics` – Coverage nach Achse, Kombination und Assetklasse; Filter `asset_type`, `symbol`, `days`

POST, PUT, PATCH und DELETE unter `/api/v1/` werden mit HTTP 405 abgelehnt. Antworten enthalten keine Kerzen, vollständigen Features, `raw_result`, Secrets oder Schreibfreigaben.
