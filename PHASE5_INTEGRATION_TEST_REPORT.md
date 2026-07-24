# Phase 5 - Vollstaendiger Integrationstest

## Ziel

Phase 5 prueft die neue PandorickKi-Plattform mit Testdaten ueber alle vier
Bereiche:

- BotPy/Krypto
- Stock/Aktien
- KI/Brain
- ControlCenter

## Betroffene Dateien

- `tests/test_integration_full.py` wurde neu erstellt.
- `PHASE5_INTEGRATION_TEST_REPORT.md` wurde neu erstellt.

## Unveraendert

- Der bestehende Crypto-Bot wurde nicht geaendert.
- Der bestehende Stock-Bot wurde nicht geaendert.
- Das bestehende Assistant-Core-Projekt wurde nicht geaendert.
- Telegram wird in Phase 5 nicht live versendet.

## Gepruefte Punkte

- Krypto-Daten kommen als `CRYPTO_ANALYSIS_FINISHED` an.
- Aktien-Daten kommen als `STOCK_ANALYSIS_FINISHED` an.
- Beide Marktarten laufen im selben Orchestrator-Zyklus.
- Events werden ueber den EventBus uebertragen.
- Der BrainAdapter erhaelt Crypto- und Stock-Entscheidungen.
- Das Brain speichert beide Marktarten in einer JSONL-Testdatei.
- Das ControlCenter zaehlt Crypto-, Stock- und Brain-Events.
- Telegram erhaelt keine halbfertigen oder direkten Live-Events.
- Das System faehrt alle Adapter sauber herunter.

## Testmodus

- CryptoAdapter nutzt deterministische Testkerzen.
- StockAdapter nutzt `test_mode=True` und temporäre Datenpfade.
- BrainAdapter schreibt in eine temporaere JSONL-Datei.
- ControlCenter druckt im Test nicht auf die Konsole.

## Hinweis

Der Test prueft die Integration in einem gemeinsamen Orchestrator-Zyklus.
Echte nebenlaeufige Ausfuehrung kann als separater Phase-6-Schritt umgesetzt
werden, falls die Marktadapter tatsaechlich zeitgleich per `asyncio.gather`
laufen sollen.

## Testbefehle

- `python -m unittest tests.test_integration_full`
- `python -m unittest discover tests`
- `python -m compileall .`
- `python main.py --once`
