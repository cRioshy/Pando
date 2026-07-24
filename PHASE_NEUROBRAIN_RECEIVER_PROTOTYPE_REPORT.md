# Phase NeuroBrain Receiver Prototype

## Ziel

Dieser Prototyp stellt eine sichere Koexistenz zwischen PandoriKi und
NeuroBrain her. PandoriKi bleibt das führende System. NeuroBrain empfängt nur
Kopien ausgewählter Events und speichert sie separat.

## Neue Dateien

- `adapters/neurobrain_receiver_adapter.py`
- `tests/test_neurobrain_receiver_adapter.py`
- `PHASE_NEUROBRAIN_RECEIVER_PROTOTYPE_REPORT.md`

## Geänderte Dateien

- `config.py`
- `orchestrator.py`

## Betriebsart

Der Receiver ist read-only:

- keine Tradinglogik wird verändert
- keine Brainlogik wird verändert
- keine Entscheidungen werden überschrieben
- keine Orders werden ausgeführt
- keine Telegram-Nachrichten werden durch NeuroBrain gesendet

## Aktivierung

Standardmäßig ist der Receiver deaktiviert. Aktivierung:

```powershell
$env:PANDORICKKI_NEUROBRAIN_RECEIVER_ENABLED="1"
python main.py --headless --web
```

## Speicherorte

Standard:

- `data/neurobrain/inbox.jsonl`
- `data/neurobrain/status.json`

Bei gesetztem `PANDORICKKI_DATA_DIR` werden diese Pfade automatisch darunter
angelegt.

## Empfangene Eventarten

- `CRYPTO_MARKET_DATA_UPDATED`
- `STOCK_MARKET_DATA_UPDATED`
- `COMMODITY_MARKET_DATA_UPDATED`
- `CRYPTO_ANALYSIS_FINISHED`
- `STOCK_ANALYSIS_FINISHED`
- `COMMODITY_ANALYSIS_FINISHED`
- `BRAIN_DECISION_RECEIVED`
- `DECISION_CREATED`
- `SIGNAL_CREATED`
- `SIMULATED_TRADE_OPENED`
- `SIMULATED_TRADE_UPDATED`
- `SIMULATED_TRADE_CLOSED`
- `AI_LEARNING_UPDATED`

## Gespeicherte Felder

- `received_at`
- `source_event_id`
- `topic`
- `source`
- `source_created_at`
- `event_type`
- `market_type`
- `symbol`
- `decision_id`
- `signal_id`
- `direction`
- `probability`
- `source_timestamp`
- `payload`

## Schutzmaßnahmen

- Dubletten werden über `event_id` ignoriert.
- Eigene NeuroBrain-Events werden nicht erneut gespeichert.
- Schreibvorgänge laufen über rotierendes JSONL.
- Status wird atomisch als JSON geschrieben.
- Interne PandoriKi-Daten werden nicht verändert.

## Nächster sinnvoller Schritt

NeuroBrain kann später diesen Inbox-Stream lesen und daraus Datenqualität,
Outcome-Simulationen und Lernberichte erzeugen, ohne PandoriKi aktiv zu
steuern.
