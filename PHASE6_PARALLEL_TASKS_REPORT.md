# Phase 6 - Asyncio Parallelisierung

## Ziel

Der Orchestrator fuehrt Services jetzt pro Zyklus als echte `asyncio`-Tasks
aus. CryptoService, StockService, Brain und ControlCenter werden nicht mehr
sequentiell abgearbeitet, sondern parallel gestartet und ueber den EventBus
verbunden.

## Betroffene Dateien

- `orchestrator.py` wurde auf parallele Task-Ausfuehrung umgestellt.
- `event_bus.py` nutzt einen Lock fuer Subscriber- und History-Zugriffe.
- `shared_state.py` nutzt einen Lock fuer Service- und Value-Zugriffe.
- `tests/test_parallel_orchestrator.py` wurde neu erstellt.

## Race-Condition-Schutz

- EventBus kopiert Handlerlisten unter Lock und ruft Handler danach auf.
- SharedState schreibt und liest unter Lock.
- Jeder Adapter laeuft in einem isolierten Task.
- Fehler eines Adapters werden abgefangen und brechen andere Tasks nicht ab.
- ControlCenter erzeugt nach den parallelen Tasks einen finalen Snapshot.

## Testabdeckung

- Parallelitaetstest: zwei langsame Adapter laufen schneller als sequentiell.
- Stabilitaetstest: ein fehlerhafter Adapter stoppt andere Adapter nicht.
- Bestehende Phase-5-Integration bleibt aktiv.

## Hinweis

Die Adapter selbst behalten ihre Schnittstellen. Dadurch bleiben die bestehenden
Crypto-, Stock-, Brain- und ControlCenter-Adapter kompatibel.
