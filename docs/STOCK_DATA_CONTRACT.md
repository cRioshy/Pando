# Stock-Datenvertrag

Stand: 9. August 2026

Vertragsname: `pandorickki.stock-data`, Version `1`

## Zweck und Status

Der Vertrag beschreibt die sichere Eingangsgrenze, die ein Aktienkandidat erfüllen muss, bevor seine Daten als gate-tauglich gelten können. Die ausführbare Referenz liegt in `stock_data_contract.py`. `StockAdapter` verwendet sie inzwischen ausschließlich als getrennten read-only Audit. EventBus, Brain, Decision Core, Telegram und Tracker erhalten weder die Rohkerzen noch eine Freigabe aus diesem Audit.

Ein Ergebnis `READY` ist nur eine Datenfreigabe für die spätere Feature- und Gate-Verarbeitung. Es ist keine Signal-, Telegram- oder Orderfreigabe. Die Referenz setzt deshalb immer `ready_for_telegram=false` und `order_execution_allowed=false`.

## Nachgewiesener Ist-Zustand

- Der Legacy-Provider `PlaceholderStockDataProvider` erzeugt deterministische, realistisch aussehende Snapshots, aber keine öffentlichen Live-Marktdaten.
- `StockAdapter` bekommt vom Legacy-Lauf nur `Decision`-Objekte zurück. Sie enthalten eine qualitative Risikoentscheidung (`approved`, `risk_level`, `max_position_risk_percent`), aber keine Stop-/Take-Profit-Level.
- Der Legacy-Lauf berechnet zwar separat einen ATR-basierten `StockRiskPlan` mit Entry, Stop und drei Zielen. Dieser liegt nur in den Engine-Records und wird nicht mit dem zurückgegebenen `Decision`-Objekt verbunden.
- Für die Feature Engine fällt `StockAdapter` deshalb auf genau eine aus den aktuellen Fakten gebaute Kerze ohne Zeitstempel zurück. Das ergibt korrekt `WARN/UNVERIFIED/WARMING`.
- `StockPriceService` liefert für unterstützte Börsenticker einen öffentlichen Yahoo-Chart-Preis mit Provider-Zeitstempel. `SPCX`/`SPACEX` sind ausdrücklich nicht unterstützt und besitzen deshalb keinen verlässlichen positiven Livepreis.
- Der kompakte Eventvertrag verbietet vollständige `candles`. Historische Kerzen dürfen daher nur innerhalb der Adapter-/Feature-Grenze verwendet und nicht in Brain-, Decision- oder NeuroBrain-History kopiert werden.

## Version-1-Eingang

Die Referenz erwartet:

- `market_type=stock`
- nicht leeres, normalisiertes `symbol`
- ausdrücklich erlaubtes `timeframe`, zunächst `1d`
- `source_kind=PUBLIC_LIVE`; Placeholder- oder Testdaten bleiben blockiert
- `direction=LONG` oder `SHORT`
- eine Liste vollständiger OHLCV-Kerzen mit eindeutigen Zeitstempeln
- positiven aktuellen Preis, erlaubte Preisquelle und prüfbaren Preiszeitstempel
- normalisierten Richtungs-Risikoplan mit `entry_price`, `stop_loss` und mindestens einem `take_profit`

Kerzen werden über den bestehenden Vertrag `pandorickki.feature-data-quality` geprüft. Version 1 verlangt vollständige Zeitstempel, `PASS`, `VERIFIED` und `READY`. Mindestkerzenzahl, Warmup, maximales Alter der jüngsten Kerze, maximale Quote-Alterung und Entry-/Preis-Toleranz müssen beim Aufruf ausdrücklich als `StockDataPolicy` gesetzt werden.

## Risikoplan

Der normalisierte Risikoplan besitzt mindestens:

```json
{
  "action": "LONG",
  "entry_price": 120.0,
  "stop_loss": 117.0,
  "take_profit": [123.0, 126.0]
}
```

Für `LONG` muss der Stop unter dem aktuellen Preis liegen und mindestens ein Ziel darüber. Für `SHORT` gilt die umgekehrte Richtung. Entry und aktueller Preis dürfen nur um die explizit konfigurierte Toleranz voneinander abweichen. Die qualitative Legacy-Risikoampel ist ergänzende Fachinformation, ersetzt diese Preislevel aber nicht.

## Reason Codes

| Bereich | Reason Codes |
|---|---|
| Identität | `SD_MARKET_NOT_STOCK`, `SD_SYMBOL_MISSING`, `SD_TIMEFRAME_NOT_ALLOWED`, `SD_SOURCE_NOT_LIVE`, `SD_DIRECTION_NOT_ELIGIBLE` |
| Kerzen | `SD_CANDLES_MISSING`, `SD_CANDLES_INVALID`, `SD_QUALITY_MISSING`, `SD_QUALITY_NOT_PASS`, `SD_ORDER_NOT_VERIFIED`, `SD_WARMUP_NOT_READY`, `SD_LATEST_CANDLE_TIMESTAMP_INVALID`, `SD_LATEST_CANDLE_IN_FUTURE`, `SD_CANDLES_STALE` |
| Preis | `SD_PRICE_INVALID`, `SD_PRICE_SOURCE_NOT_ALLOWED`, `SD_PRICE_TIMESTAMP_INVALID`, `SD_PRICE_TIMESTAMP_IN_FUTURE`, `SD_PRICE_STALE` |
| Risiko | `SD_RISK_MISSING`, `SD_RISK_DIRECTION_CONFLICT`, `SD_RISK_ENTRY_INVALID`, `SD_RISK_ENTRY_PRICE_MISMATCH`, `SD_STOP_LOSS_INVALID`, `SD_TAKE_PROFIT_INVALID` |
| Erfolg | `SD_READY` |

## Sichere spätere Integration

1. **Erledigt:** Read-only öffentlichen Tageskerzen-Provider mit query1/query2-Fallback und begrenztem In-Memory-Cache im PandorickKi-Adapter ergänzen; den externen Legacy-Bot nicht verändern.
2. Ticker vor Provideraufrufen validieren. `SPCX` bleibt blockiert, bis ein belegbarer öffentlicher Ticker existiert.
3. Kerzen ausschließlich intern an Feature Engine und Vertrag geben; keine Rohkerzen persistieren oder über den kompakten EventBus-Vertrag senden.
4. **Erledigt:** Den ATR-basierten observer-only Risikoplan in PandorickKi aus derselben validierten Preis-/Kerzensicht ableiten. Keine qualitative Risikoampel als Stop/TP ausgeben.
5. Zunächst ausschließlich auditieren. Den aktiven Decision-/Signalpfad nicht umschalten.
6. Erst nach Livevergleich, Tests und separater Freigabe die Stock-Kandidaten dem Decision Gate zuführen. Telegram bleibt deaktiviert/Dry-Run; Orderausführung bleibt ausgeschlossen.

## Liveverifikation

Der öffentliche AAPL-Test lieferte 260 Tageskerzen: 260 akzeptiert, keine Duplikate oder Verletzungen, `PASS/VERIFIED/READY`. Nach kontrolliertem Plattformneustart meldeten alle elf Services `OK`. Der Stock-Audit verarbeitete fünf Symbole, lud vier Historien und blockierte `SPCX` erwartungsgemäß ohne Provideraufruf. Der aktuelle Audit bewertet den getrennten öffentlichen Shadow einschließlich observer-only Risikoplan; er bewertet nicht mehr die Legacy-Placeholder-Richtung. Telegram bleibt deaktiviert/Dry-Run und bei null gesendeten Nachrichten.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_stock_data_contract -v
```

Die Tests prüfen einen vollständigen Referenzfall, den heutigen Einzelsnapshot-Fallback, Placeholder-/Preis-/Risikofehler, Kerzen- und Quote-Alterung, Richtungsfehler und die unveränderliche Telegram-/Order-Sperre.
