# Feature-Datenqualitätsvertrag

Stand: 8. August 2026

Vertragsname: `pandorickki.feature-data-quality`, Version `1`

## Zweck

Der Vertrag ist die verbindliche Eingangsgrenze zwischen OHLCV-Daten und `FeatureEngine`. Er verhindert, dass nicht endliche, fachlich widersprüchliche oder zeitlich uneindeutige Kerzen stillschweigend als verlässliche Features erscheinen. Er verändert keine Legacy-Analyse, keine bestehende History und keine Decision-/Signal-Payloads.

Die ausführbare Referenz liegt in `feature_data_quality_contract.py`. `prepare_feature_candles()` liefert normalisierte Kerzen und einen JSON-sicheren Qualitätsbericht. `FeatureEngine.compute()` veröffentlicht diesen Bericht unter `metadata.data_quality`.

## Version-1-Regeln

### OHLCV-Normalisierung

- Unterstützte Preisaliase: `open`/`open_price`, `high`/`high_price`, `low`/`low_price`, `close`/`close_price`/`price` und `adj_close`/`adjClose`.
- Fehlendes Volumen wird als `0.0` behandelt; negatives Volumen ist ungültig.
- Open, High, Low und Close müssen vorhanden, endlich und größer als null sein.
- Ein vorhandenes Adjusted Close muss ebenfalls endlich und größer als null sein.
- `high` muss mindestens dem Maximum aus Open, Close und Low entsprechen.
- `low` darf das Minimum aus Open, Close und High nicht überschreiten.
- Ungültige Zeilen werden entfernt und pro Verletzungsart gezählt. Bleiben weniger als die konfigurierte Mindestanzahl übrig, schlägt die Feature-Berechnung mit `FeatureEngineError` fehl.

### Zeitstempel, Sortierung und Duplikate

Unterstützte Zeitstempelaliase sind `timestamp`, `open_time`, `openTime`, `time`, `datetime` und `date`. Numerische Providerwerte und ISO-8601-Zeitstempel werden akzeptiert.

- Besitzt jede akzeptierte Kerze einen gültigen Zeitstempel, wird aufsteigend sortiert.
- Gleiche Zeitstempel werden deterministisch mit `keep_last` behandelt: Die letzte Providerzeile bleibt erhalten.
- Fehlen Zeitstempel vollständig oder teilweise, wird die Providerreihenfolge nicht geraten oder verändert. Der Bericht setzt `order.status=UNVERIFIED` und nennt `timestamps_missing` beziehungsweise `timestamps_partial`.
- Eine strengere spätere Grenze kann mit `require_timestamps=True` nicht vollständig zeitgestempelte Daten ablehnen.
- Der interne Crypto-Marktdatenservice erhält jetzt den von Binance beziehungsweise Bitget gelieferten Kerzenzeitstempel, sodass der Live-Crypto-Pfad vollständig geprüft werden kann.

### Mindestkerzen und Warmup

- Version 1 erlaubt aus Rückwärtskompatibilitätsgründen mindestens eine valide Kerze. Dadurch bleibt der vorhandene Aktien-Fallback auf einen aktuellen Fakten-Snapshot funktionsfähig.
- `minimum_candles` ist konfigurierbar und wird strikt erzwungen.
- Vollständiger Standard-Warmup entspricht dem größten aktiven Langfenster, derzeit 200 Kerzen.
- Weniger Kerzen sind kein erfundener Volltreffer: `warmup.status=WARMING`, und noch nicht berechenbare Indikatoren bleiben `null`.
- Ab Erreichen der Grenze meldet der Bericht `warmup.status=READY`.
- Ein späteres Decision Gate kann `READY`, verifizierte Reihenfolge oder eine höhere Mindestanzahl verlangen, ohne den heutigen additiven Featurepfad vorzeitig abzuschalten.

### Non-Finite-Schutz

`NaN`, positive oder negative Unendlichkeit sind in OHLCV und Adjusted Close ungültig. Nicht endliche optionale Kontextwerte werden nicht in die öffentliche Feature-Sicht übernommen. Die bestehende abschließende JSON-Bereinigung bleibt als zweite Schutzschicht erhalten.

## Qualitätsbericht

Der Bericht enthält mindestens:

- `schema_name` und `schema_version`
- Gesamtstatus `PASS`, `WARN` oder `DEGRADED`
- Eingangs-, akzeptierte, ausgegebene, entfernte und duplizierte Zeilen
- Anzahl zeitgestempelter Zeilen
- Zähler je Verletzungsart
- Sortierstatus, Grund, Richtung, Umsortierung und Duplikatstrategie
- Warmupstatus, verfügbare Kerzen, Mindestanzahl und Voll-Warmup-Grenze
- kompakte Warntexte

`PASS` bedeutet strukturell valide, vollständig zeitgestempelte Daten ohne entfernte Zeilen oder Duplikate. `WARN` bedeutet valide Daten mit nicht verifizierbarer Reihenfolge. `DEGRADED` bedeutet, dass ungültige oder doppelte Zeilen kontrolliert entfernt wurden. Ein Fehler entsteht, wenn nach Bereinigung die Mindestanzahl nicht erreicht ist oder eine aktiv verlangte Zeitstempelpflicht verletzt wird.

## Integrationsgrenzen

- `CryptoAdapter` und `StockAdapter` bleiben die einzigen heutigen Feature-Consumer.
- Beide begrenzen externe Historien weiterhin vor der Feature-Berechnung auf höchstens 500 Kerzen.
- Live-Aufrufe bleiben `include_targets=False`; Trainingsziele gelangen nicht in den Livepfad.
- Der Vertrag ist additiv in `features.metadata.data_quality`. Bestehende Featurefelder bleiben erhalten.
- Brain, Decision Core, Outcome Tracker, NeuroBrain, Telegram und bestehende History werden nicht migriert oder umgeschrieben.
- Der Vertrag ist noch kein fachliches Decision Gate und aktiviert weder Nachrichtenversand noch Orderausführung.

## Verifikation

Gezielte Tests:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_feature_data_quality_contract tests.test_feature_engine tests.test_crypto_market_data_service tests.test_feature_engine_adapters -v
```

Die Regressionen decken Sortierung, `keep_last`-Duplikate, OHLC-Konsistenz, Non-Finite-Werte, negatives Volumen, Mindestkerzen, Zeitstempelpflicht, unverifizierte Providerreihenfolge, Warmup-Metadaten, optionale Kontextwerte und die Crypto-Zeitstempelweitergabe ab.

Der isolierte Realtest vom 8. August 2026 lud 240 öffentliche BTCUSDT-Kerzen von Binance. Alle 240 Zeilen wurden akzeptiert; Reihenfolge `VERIFIED`, Warmup `READY`, null Duplikate, null entfernte Zeilen und null Regelverstöße.
