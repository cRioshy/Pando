# Phase 4D - CryptoAdapter

## Ziel

Der CryptoAdapter verbindet die bestehende Crypto-Analyse mit PandorickKi,
ohne `bot.py` zu importieren oder dessen Endlosschleife zu starten.

## Betroffene Dateien

- `adapters/crypto_adapter.py` wurde neu erstellt.
- `adapters/brain_adapter.py` akzeptiert jetzt auch fertige Crypto-Events.
- `orchestrator.py` nutzt den CryptoAdapter statt des Crypto-Noops.
- `tests/test_crypto_adapter.py` wurde neu erstellt.
- `adapters/control_center_adapter.py` zeigt Crypto-Analysen separat an.

## Unverändert

- Das bestehende Crypto-Projekt wurde nicht geändert.
- `bot.py` wird nicht importiert.
- Telegram-Versand aus dem Altprojekt wird nicht gestartet.
- Bestehende Crypto-Daten wie `brain.json`, `history.csv` und
  `precedence.json` werden durch den Adapter standardmäßig nicht beschrieben
  und `brain.json` wird standardmäßig auch nicht migrationsgeladen.

## Verhalten

- Standardmodus: Testdatenmodus, keine Live-Binance-Requests.
- Live-Modus: `PANDORICKKI_LIVE_CRYPTO=1` setzen.
- Legacy-Brain-Laden ist bewusst deaktiviert, bis Schreibzugriff und Backup
  freigegeben sind.
- Der Adapter nutzt `pandorick_pipeline.analyse_market(...)`.
- Er veröffentlicht `CRYPTO_ANALYSIS_FINISHED`.
- Der BrainAdapter speichert fertige Crypto- und Stock-Entscheidungen in
  `data/brain_events.jsonl`.
- Legacy-Modulnamen wie `brain`, `models` und `market` werden nach dem Laden
  wiederhergestellt, damit der Stock-Bot seine eigenen Module importiert.

## Risiken

- Das Crypto-Projekt nutzt globale Modulnamen wie `models`, `brain` und
  `market`. Der Adapter lädt diese gezielt über den Crypto-Projektpfad.
- Live-Modus benötigt Netzwerkzugriff und installierte Abhängigkeiten wie
  `requests` und `pandas`.
- Die vorhandenen Telegram-Credentials im Altprojekt sollten weiterhin als
  Sicherheitsrisiko behandelt und später rotiert werden.

## Tests

- `python -m unittest tests.test_crypto_adapter`
- `python -m unittest discover tests`
- `python -m compileall .`
- `python main.py --once`
