# Phase 6 - Learning Graph Real Data Wiring

## Ziel

Phase 6 verbindet den Learning Graph mit echten Pandorick-Datenquellen.

Es wurden keine Crypto-, Stock-, Brain-, Telegram-, Signal- oder Trade-Berechnungen veraendert.

## Geaenderte Dateien

- `learning_graph/graph_config.py`
  - Oeffentliche Indikatorgruppen um Aktien- und Risiko-relevante Kategorien erweitert.

- `learning_graph/graph_builder.py`
  - Zusaetzliche oeffentliche Indikatorkategorien erkannt:
    - ATR
    - Gap
    - Relative Strength
    - Volatility

- `learning_graph/graph_repository.py`
  - Echte Datenquellen zusammengefuehrt:
    - `data/brain_events.jsonl`
    - `data/crypto_active_trades.json`
    - Stock-Bot `data/stock_history.json`
    - Stock-Bot `data/decisions.json`
  - Quellen werden normalisiert und dedupliziert.
  - Sehr grosse `brain_events.jsonl`-Dateien werden ueber ein Tail-Fenster gelesen, damit der Live-Webserver nicht blockiert.
  - Es werden keine Rohdateien, Secrets oder absoluten Benutzerpfade an den Browser gegeben.

- `learning_graph/graph_service.py`
  - Nutzt jetzt kombinierte echte Quellen statt nur Brain-JSONL.
  - Mischt persistente Analysezaehler aus `storage/statistics/system_statistics.json` in die oeffentlichen Graph-Stats.

- `web/api.py`
  - Uebergibt echte Projektpfade an den LearningGraphService.

- `tests/test_learning_graph_api_phase4.py`
  - Test-Isolation angepasst, damit leere Quellen wirklich leer bleiben.

## Neue Dateien

- `tests/test_learning_graph_phase6_real_data.py`

## Registrierte API-Routen

- `GET /api/v1/learning-graph`
- `GET /api/v1/learning-graph/nodes`
- `GET /api/v1/learning-graph/edges`
- `GET /api/v1/learning-graph/stats`
- `GET /api/v1/learning-graph/recent`
- `GET /api/v1/learning-graph/node/{node_id}`

## Echte erkannte Daten im Workspace

- Crypto-Analysen aus `data/brain_events.jsonl`: 411
- Stock-Analysen aus `data/brain_events.jsonl`: 500
- Stock-History/Decisions aus separatem Stock-Bot: vorhanden
- Symbole in Brain-Events:
  - BTCUSDT
  - ETHUSDT
  - XRPUSDT
  - AAPL
  - MSFT
  - NVDA
  - TSLA
  - SPCX

## Wachstum

Der Graph liest die Datenquellen beim Cache-Refresh erneut.

Neue Events wie `CRYPTO_ANALYSIS_FINISHED`, `STOCK_ANALYSIS_FINISHED`, `DECISION_CREATED`, `SIGNAL_CREATED`, `AI_LEARNING_UPDATED` und `BRAIN_DECISION_RECEIVED` invalidieren den Cache. Dadurch waechst der Graph mit neuen Analysen.

Die Gesamtzahl `analyses_processed` kommt aus der persistenten Systemstatistik, falls diese vorhanden ist. Dadurch zaehlt die Anzeige weiter hoch, auch wenn Knoten und Kanten aus Performancegruenden aus einem aktuellen Datenfenster gebaut werden.

## Tests

Gezielte Graph-Tests:

```text
Ran 18 tests
OK
```

Gesamttests:

```text
Ran 75 tests
OK
```

Hinweis: Die volle Test-Suite zeigt bestehende `DeprecationWarning`-Meldungen aus dem alten Crypto-Projekt wegen `datetime.utcnow()`. Das ist kein neuer Fehler aus Phase 6.

## Bekannte Einschraenkungen

- Der Graph visualisiert weiterhin oeffentliche Kategorien, keine internen Formeln.
- Rohdaten wie Berechnungsschritte, Gewichtungen, Reasoning und Pfade bleiben absichtlich verborgen.
- Web-ControlCenter muss nach Code-Aktualisierung neu gestartet werden.
