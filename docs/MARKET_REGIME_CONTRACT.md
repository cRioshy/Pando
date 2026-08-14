# Market Regime Contract v1

Stand: 12. August 2026

Vertragsname: `pandorickki.market-regime-snapshot`, Schema-Version `1`, Classifier `regime-v1`

## Zweck und Sicherheitsgrenze

Market Regime v1 beschreibt beobachtete Marktbedingungen. Es erzeugt keine Handelsentscheidung. Die drei Achsen sind unabhängig:

- Trendrichtung: `STRONG_UP`, `UP`, `SIDEWAYS`, `DOWN`, `STRONG_DOWN`, `UNKNOWN`
- Volatilität: `LOW`, `MEDIUM`, `HIGH`, `EXTREME`, `UNKNOWN`
- Trendphase: `STABLE`, `WEAKENING`, `REVERSAL`, `BREAKOUT`, `UNKNOWN`

Eine Kombination wie `UP + HIGH + WEAKENING` ist eine Beobachtung und niemals automatisch LONG, SHORT, HOLD oder NO-TRADE. Jeder Snapshot setzt unveränderlich `mode=OBSERVER_ONLY`, `affects_active_decision=false`, `ready_for_telegram=false` und `order_execution_allowed=false`.

## Tatsächlicher Datenfluss

CryptoAdapter verwendet die bereits vorhandene echte `15m`-Kerzenserie. StockAdapter verwendet ausschließlich die öffentliche Yahoo-`1d`-Serie aus dem internen Stock-Observer. Der Legacy-Einzeilenfallback ist keine Stock-Regime-Grundlage. Die Adapter reichen Kerzen nur als interne In-Memory-Kopie an die begrenzte Observer-Queue. Weder Rohkerzen noch vollständige Features gelangen in EventBus, Ledger, API oder UI.

Der Queue-Worker validiert die Kerzen erneut über `pandorickki.feature-data-quality`, berechnet die bestehende Feature Engine, klassifiziert, persistiert append-only über `RotatingJsonlLedger` und publiziert ausschließlich den kompakten Snapshot als `MARKET_REGIME_OBSERVED`. Queue-Verhalten ist Drop-newest mit sichtbarem Fehlerzähler; ein sauberer Shutdown drainiert alle akzeptierten Inputs.

## MarketRegimeSnapshot

Pflichtfelder:

- Identität: `regime_id`, `symbol`, `asset_type`, `source_event_id`, `feature_snapshot_id`, `timestamp`
- Trend: `trend_direction`, `trend_confidence`, `trend_reasons`
- Volatilität: `volatility_regime`, `volatility_score`, `volatility_reasons`
- Phase: `trend_phase`, `phase_confidence`, `phase_reasons`
- Qualität: `data_quality_status`, `data_quality_score`
- Zeitrahmen: `timeframes_used`, `missing_timeframes`
- Version: `classifier_version`, `config_fingerprint`, `schema_version`, `created_at`

Alle Scores sind endlich und liegen zwischen `0.0` und `1.0`. NaN, Infinity und Werte außerhalb des Bereichs werden nicht akzeptiert.

## Deterministische Identitäten

`feature_snapshot_id` ist SHA-256 über Assetklasse, Symbol, Timeframe, letzten validen Kerzenzeitstempel, den SHA-256-Fingerprint aller normalisierten OHLCV-Zeilen einschließlich Zeitstempel, `feature-engine-v1` sowie Name und Version des Feature-Quality-Vertrags.

`regime_id` ist SHA-256 über Assetklasse, Symbol, Timeframe, letzten Kerzenzeitstempel, `feature_snapshot_id`, `classifier_version` und `config_fingerprint`. `source_event_id` bleibt für Rückverfolgung erhalten, ist aber ausdrücklich nicht Teil der primären Identität. Ein Neustart oder dupliziertes Quellereignis erzeugt für dieselbe Kerze und Konfiguration keinen zweiten Snapshot.

## Config Fingerprint

Der Fingerprint ist SHA-256 über `classifier_version` und sämtliche Felder von `MarketRegimePolicy`. Alte und neue Konfigurationen erhalten dadurch verschiedene `regime_id`-Räume und werden nicht still vermischt.

## Feature Quality

- `OK`: Feature Quality `PASS`, Reihenfolge `VERIFIED`, Warmup `READY`.
- `DEGRADED`: bereinigte/duplizierte Eingänge bei weiterhin verifizierter Reihenfolge und vollständigem Warmup. Confidence ist auf `0.60` begrenzt; starke Trendklassen werden zu `UP`/`DOWN` herabgestuft.
- `REJECTED`: fehlende/ungültige Zeitstempel, zu wenig Warmup, ungültiger letzter Providerdatensatz oder nicht belastbare Feature-Berechnung. Alle drei Achsen werden `UNKNOWN` und alle Scores `0.0`.

Ein verworfener neuester Datensatz wird nicht durch stilles Zurückfallen auf eine ältere Kerze verdeckt.

## Trendrichtung

Die Trendrichtung kombiniert Preis/SMA20, SMA20/SMA50, SMA50/SMA200, EMA20/EMA50, normalisierte SMA20-Steigung, Higher-/Lower-Struktur, Netto-Bewegung relativ zum Preisweg sowie MACD-Histogramm, ROC und KAMA. ADX ist nur zusätzliche Stärkeanforderung für `STRONG_*`.

`STRONG_UP`/`STRONG_DOWN` verlangen mindestens fünf bestätigende Gruppen, ausreichend Gesamtscore und ADX. `UP`/`DOWN` verlangen mindestens drei Gruppen. `SIDEWAYS` ist ein eigenes Regime aus niedriger Bewegungseffizienz, flacher Steigung, wiederholten SMA20-Kreuzungen und fehlender Trenddominanz. Widersprüchliche oder schwache Evidenz wird `UNKNOWN`.

## Volatilität

Volatilität verwendet `ATR / Close`; absolute ATR-Schwellen zwischen Assets sind verboten. Der aktuelle Wert wird ausschließlich gegen eine rückwärtsgerichtete Baseline der vorherigen 60 gültigen Werte eingeordnet. Die konfigurierten Perzentile sind 25 %, 75 % und 95 %. Bei unzureichender Baseline lautet das Ergebnis `UNKNOWN`.

## Trendphase

- `BREAKOUT`: nachweisbarer Ausbruch aus der vorherigen Range plus mindestens zwei weitere Bestätigungen aus vorheriger niedriger Effizienz, ATR-bezogener Bewegung, Volumen und steigendem ADX.
- `REVERSAL`: mindestens drei Bestätigungen aus Momentum-, MACD-, ROC-, Folgekerzen- und EMA-Steigungswechsel.
- `WEAKENING`: mindestens zwei Abschwächungen aus Momentum, MACD-Histogramm, ADX und EMA-Steigung.
- `STABLE`: bestehende Trend-/Seitwärtsstruktur ohne hinreichende Breakout-, Reversal- oder Weakening-Evidenz.
- `UNKNOWN`: unzureichende oder verworfene Daten und widersprüchliche Evidenz.

## Timeframe-Grenzen

- Crypto v1: tatsächlich `15m`; `1m`, `5m`, `1h`, `4h` werden als fehlend dokumentiert.
- Stocks v1: tatsächlich `1d`; `1m`, `5m`, `15m`, `1h` und `4h` werden als fehlend dokumentiert und nicht künstlich erzeugt.

Multi-Timeframe-Architektur ist vorbereitet, aber v1 kombiniert keine erfundenen Zeitrahmen.

## Persistenz, Event und Coverage

- Ledger: `data/market_regime.jsonl`, append-only, rotierend, restart-safe.
- Event: `MARKET_REGIME_OBSERVED`; technischer Heartbeat `MARKET_REGIME_HEARTBEAT`.
- Coverage zählt ausschließlich Schema `pandorickki.market-regime-snapshot` v1, getrennt nach Assetklasse sowie filterbar nach Symbol und Zeitraum.
- Statistik enthält alle zulässigen Klassen einschließlich expliziter Nullzähler und die häufigsten Drei-Achsen-Kombinationen. Legacy-/Placeholder-Labels zählen nicht als v1-Coverage.

## Read-only API und UI

- `GET /api/v1/regime/current`
- `GET /api/v1/regime/{symbol}`
- `GET /api/v1/regime/history?asset_type=&symbol=&days=&limit=&offset=`
- `GET /api/v1/regime/statistics?asset_type=&symbol=&days=`

Alle Schreibmethoden unter `/api/v1/` werden abgelehnt. Das Control Center zeigt ausschließlich Symbol, Assetklasse, drei Achsen, Quality, Confidence, tatsächliche Timeframes und Classifier-Version. Es enthält keine LONG-/SHORT-Empfehlung, Tradebuttons oder Bearbeitungsfunktion.

## Outcome- und Stimpy-Vorbereitung

`regime_id`, `feature_snapshot_id`, `source_event_id` und Zeitstempel ermöglichen später eine zeitpunktgerechte Verknüpfung mit Decision, Shadow Decision und Outcome. v1 führt diese Verbindung nicht aktiv aus, schreibt keine Outcome-Daten zurück und besitzt keinen Look-ahead-Pfad. Stimpy, Ren und das separate PANDO-Token-Projekt bleiben unverändert.
