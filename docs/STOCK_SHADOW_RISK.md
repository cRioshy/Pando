# Stock-Shadow-Risikoplan

Stand: 9. August 2026

Vertragsname: `pandorickki.stock-shadow-risk`, Version `1`

## Zweck und Sicherheitsgrenze

Der Vertrag erzeugt ausschließlich observer-only Preislevel aus einem bereits berechneten öffentlichen Stock-Shadow-Kandidaten. Er verändert weder die aktive Legacy-Entscheidung noch den aktiven Feature-, Brain-, Decision-, Signal-, Telegram- oder Orderpfad.

Risikoplan, Shadow-Kandidat, Daten-Audit und Vergleich werden vor `STOCK_ANALYSIS_FINISHED` ausdrücklich aus dem aktiven Event-Payload entfernt. Sie werden nicht an den EventBus, Brain, Decision Core, NeuroBrain oder Telegram publiziert und nicht in History persistiert. `ready_for_telegram` und `order_execution_allowed` bleiben immer `false`.

## Version-1-Policy

Die Regel übernimmt das nachgewiesene Grundprinzip des vorhandenen Legacy-`stock_risk.py`, verwendet aber ausschließlich öffentliche PandorickKi-Daten:

- Entry: aktueller öffentlicher Kurs
- ATR: `ATR14` aus genau derselben validierten öffentlichen Tageskerzenreihe wie der Shadow-Kandidat
- Risikodistanz: `max(ATR14 × 1,0; Entry × 0,5 %)`
- LONG-Stop: Entry minus 1 Risikodistanz
- SHORT-Stop: Entry plus 1 Risikodistanz
- Ziele: 1R, 2R und 3R in Entscheidungsrichtung
- Rundung: vier Dezimalstellen

Alle Werte sind über explizite Konfiguration änderbar. Die Standardwerte stehen im Web-Starter und in `.env.example`.

## Fail-closed Regeln

- Nur ein Shadow mit `status=CALCULATED` ist zulässig.
- Nur `LONG` und `SHORT` erhalten einen Plan; `HOLD` bleibt blockiert.
- Entry und ATR müssen endlich und positiv sein.
- Stop und Ziele müssen nach Rundung positiv, vom Entry verschieden und richtungskonsistent sein.
- Zielmultiplikatoren müssen positiv, eindeutig und streng aufsteigend sein.

Reason Codes: `SSR_SHADOW_NOT_CALCULATED`, `SSR_DIRECTION_NOT_ELIGIBLE`, `SSR_ENTRY_INVALID`, `SSR_ATR_INVALID`, `SSR_STOP_INVALID`, `SSR_TARGET_INVALID`, `SSR_DIRECTIONAL_LEVEL_INVALID`, `SSR_CALCULATED`.

## Normalisierte Ausgabe

```json
{
  "action": "LONG",
  "entry_price": 100.0,
  "stop_loss": 98.0,
  "take_profit": [102.0, 104.0, 106.0],
  "take_profit_1": 102.0
}
```

Der Stock-Datenvertrag darf diese Level im getrennten Audit prüfen. Dessen `READY` bedeutet nur, dass die öffentliche Datensicht vollständig ist. Es ist ausdrücklich keine Decision-, Telegram- oder Orderfreigabe.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_stock_shadow_risk -v
```

Abgedeckt sind LONG, SHORT, Mindestdistanz, HOLD, ungültiger Shadow, ungültiger ATR, unmöglicher Stop, Policyvalidierung und unveränderliche Sicherheitsflags.
