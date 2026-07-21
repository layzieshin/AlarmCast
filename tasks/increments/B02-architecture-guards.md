# B02 – Architektur- und Repository-Guards

**Status innerhalb STAGE-01:** beginnt nur nach `AUTO_GREEN` von B01.

## Ziel

Automatisierte Tests verhindern die typischen autonomen Agentenfehler, bevor spaetere Produktentwicklung beginnt.

## Erlaubte Dateien

- `tests/architecture/**`
- optional `tests/architecture/_fixtures/**`
- bestehende Testkonfiguration in `pyproject.toml`, nur falls fuer Testfindung zwingend
- `docs/stage-reports/STAGE-01.md`

Kein Produktcode darf fuer B02 geaendert werden.

## Zu implementierende Guards

### G-ENTRYPOINT

Erlaubte Produkt-Entry-Points entsprechen dem aktuellen Baselinebestand. Spaetere kanonische Entry-Points duerfen erst in ihrem Roadmap-Inkrement entstehen. Der Guard besitzt eine explizite Allowlist und verbietet neue Dateien oder Skripteintraege mit Entry-Point-Funktion.

### G-PACKAGES

Nur der vorhandene Baseline-Paketbaum ist erlaubt. Spaetere `src/alarmcast_server`- oder neue Fachmodule duerfen erst in ihrem Inkrement entstehen. Keine zusaetzlichen Top-Level-Produktpakete.

### G-IMPORTS

- `alarmcast.core` importiert nicht aus `alarmcast.host` oder `alarmcast.client`.
- `alarmcast.host` und `alarmcast.client` importieren nicht direkt voneinander.
- Tests duerfen Produktgrenzen nicht durch `sys.path`-Manipulation umgehen.

### G-CATCHALL

Verbotene neue Pfade oder Module:

```text
utils.py
helpers.py
common.py
shared.py
base.py
manager.py
managers/
services/
repositories/
models/
schemas/
```

Der Guard muss zwischen bereits vorhandenem Altbestand und neu hinzugefuegten Strukturen unterscheiden. Bestehende legitime Baselinepfade werden nicht blind umbenannt.

### G-ARTIFACTS

Verboten im Repository:

- `__pycache__`, `*.pyc`, `*.egg-info`, Build-/Dist-Verzeichnisse,
- lokale `host.json`, `client.json`, `mode.txt`,
- Logs, Tokens, PSKs, Kennwoerter, private Schluessel,
- offensichtliche interne IP-/Hostname-Konfigurationen ausser dokumentierten Beispielen.

### G-DEPENDENCIES

Die Top-Level-Dependencies werden gegen eine explizite Allowlist aus `pyproject.toml` und ADR 0010 geprueft. Der Test darf keine Online-Abfrage oder Paketinstallation durchfuehren.

## Testdesign

- Jeder Guard besitzt mindestens einen positiven Test.
- Jeder Guard besitzt mindestens eine absichtlich negative Fixture, die den Guard nachweislich fehlschlagen laesst.
- Fixtures liegen ausschliesslich unter `tests/architecture/_fixtures/` und werden nie als Produktpakete importiert.
- Keine neue externe Architekturtestbibliothek; Standardbibliothek plus pytest verwenden.

## Akzeptanzkriterien

- alle Guards sind deterministisch und plattformneutral,
- ein absichtlicher Regelverstoss wird mit konkretem Pfad und Regelname gemeldet,
- bestehender Baselinecode wird nicht veraendert,
- vollstaendiges Green Gate,
- Inkrementcommit exakt: `B02 Add architecture and repository guards`.

## Stop-Bedingungen

- ein Guard kann nur durch Produktcode-Reorganisation gruener werden,
- vorhandener Baselinecode verletzt eine Regel, die nicht als nachvollziehbare Baseline-Ausnahme formulierbar ist,
- eine neue externe Testdependency erscheint erforderlich.
