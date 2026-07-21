# AlarmCast

Interne Windows-Anwendung fuer Alarmuebertragung und persistentes Firmen-Messaging.

## Projektstatus

Das Repository wird aktuell fuer eine inkrementelle, testgesteuerte Umsetzung mit Codex vorbereitet.

Verbindliche Dokumente:

- [`AGENTS.md`](AGENTS.md) – Regeln fuer alle Coding-Agents
- [`docs/specification-1.0.md`](docs/specification-1.0.md) – freigegebene fachliche Spezifikation
- [`docs/target-architecture.md`](docs/target-architecture.md) – technische Zielarchitektur
- [`docs/implementation-roadmap.md`](docs/implementation-roadmap.md) – kleine, abhaengige Entwicklungsinkremente
- [`docs/test-strategy.md`](docs/test-strategy.md) – automatisierte und manuelle Testebenen
- [`docs/definition-of-done.md`](docs/definition-of-done.md) – Green Gate
- [`tasks/ACTIVE_TASK.md`](tasks/ACTIVE_TASK.md) – einziger aktuell ausfuehrbarer Codex-Task

## Arbeitsregel

Codex bearbeitet pro Task und Draft-Pull-Request genau ein freigegebenes Inkrement. Ein Folgeinkrement wird erst nach Review und bestaetigtem Green Gate aktiviert.

Der urspruengliche Alarmcast-Quellcode wird im Baseline-Inkrement B00 unveraendert importiert. Erst danach beginnen CI, Architektur-Guards und die kontrollierte Erweiterung.
