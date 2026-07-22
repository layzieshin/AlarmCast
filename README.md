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

## Windows-Entwicklungsumgebung

### Voraussetzungen

- Windows 10 oder Windows 11
- Git
- [`uv` 0.11.16](https://docs.astral.sh/uv/getting-started/installation/)

Eine separate Python-Installation ist nicht erforderlich. `uv` liest die
versionierte Vorgabe aus `.python-version` und installiert bei Bedarf Python
3.12. Die Projektabhaengigkeiten stammen aus `pyproject.toml`; `uv.lock`
schreibt die aufgeloesten Versionen fest.

### Frischer Checkout

```powershell
git clone https://github.com/layzieshin/AlarmCast.git
Set-Location AlarmCast
uv python install 3.12
uv sync --locked --extra dev
```

`uv sync --locked` bricht ab, falls `pyproject.toml` und `uv.lock` nicht
uebereinstimmen. Das Lockfile wird dabei nicht stillschweigend aktualisiert.
Die virtuelle Umgebung liegt anschliessend lokal unter `.venv`.

### Standardpruefungen

Vor einem Commit werden dieselben Pruefungen wie in GitHub Actions ausgefuehrt:

```powershell
uv lock --check
uv sync --locked --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q
```

### Manuelle Windows- und Hardwaretests

CI deckt keine echte Audiohardware, WASAPI-Loopback-Aufnahme,
Ausgabegeraetewechsel, Windows-Autostart, Tray-/Always-on-top-Verhalten oder
Multi-Monitor-Overlays ab. Die dafuer vorgesehenen manuellen Schritte stehen
in [`tests/manual_smoke.md`](tests/manual_smoke.md) und werden nur bei einem
Inkrement mit entsprechendem Produkt- oder Plattformbezug ausgefuehrt und
dokumentiert.
