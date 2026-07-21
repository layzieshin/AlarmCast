# AlarmCast

Interne Windows-Anwendung fuer direkte Alarmuebertragung und persistentes Firmen-Messaging.

## Projektstatus

Spezifikation und Zielarchitektur sind freigegeben. Die Umsetzung erfolgt testgesteuert in autonomen, klar begrenzten Codex-Etappen.

Verbindliche Dokumente:

- [`AGENTS.md`](AGENTS.md) – harte Regeln fuer Codex, Cursor und andere Agents
- [`docs/specification-1.0.md`](docs/specification-1.0.md) – freigegebene Fachanforderungen
- [`docs/domain-model.md`](docs/domain-model.md) – kanonische Entitaeten, Tabellen, Status und Invarianten
- [`docs/target-architecture.md`](docs/target-architecture.md) – fester Stack, Module und Entry Points
- [`docs/implementation-roadmap.md`](docs/implementation-roadmap.md) – Etappen und Inkremente
- [`docs/test-strategy.md`](docs/test-strategy.md) – automatisierte und manuelle Testebenen
- [`docs/definition-of-done.md`](docs/definition-of-done.md) – Green Gates fuer Inkrement und Etappe
- [`tasks/ACTIVE_STAGE.md`](tasks/ACTIVE_STAGE.md) – einzige aktuelle Arbeitsfreigabe

## Arbeitsregel

Codex darf innerhalb der aktiven Etappe nach jedem vollstaendig gruenen Inkrement selbststaendig fortfahren. Pro Inkrement entsteht ein Commit. Nach dem letzten Inkrement der Etappe oeffnet Codex einen Draft-PR und stoppt. Eine Folgeetappe wird niemals autonom aktiviert.

Der originale Alarmcast-Code wird in STAGE-01 unveraendert importiert und durch CI, Architekturguards und sichere Konfigurationspersistenz geschuetzt. Erst danach beginnt die fachliche Erweiterung.
