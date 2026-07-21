# B01 – Python-3.12-Entwicklungsumgebung und CI

**Status innerhalb STAGE-01:** beginnt nur nach `AUTO_GREEN` von B00.

## Ziel

Ein frischer Checkout kann reproduzierbar mit Python 3.12 eingerichtet und auf Pull Requests automatisiert geprueft werden.

## Erlaubte Dateien

- `pyproject.toml`
- `.github/workflows/ci.yml`
- `README.md`
- bestehende testbezogene Konfigurationsabschnitte
- `docs/stage-reports/STAGE-01.md`

Andere Produktdateien duerfen nicht geaendert werden.

## Verbindliche Entscheidungen

- Build-/Dependency-Metadaten bleiben in genau einem `pyproject.toml`.
- Kein Poetry, PDM, Hatch, uv, Pipenv oder zweites Requirements-System.
- Python-Version exakt 3.12 in CI.
- CI laeuft auf Windows, weil PySide6 und Alarmcast Windows-Zielcode sind.
- CI-Kommandos exakt in dieser Reihenfolge:

```text
ruff check .
ruff format --check .
mypy src
pytest -q
```

- Keine automatische Formatierung oder Auto-Fix im CI.
- Kein Docker, kein Serverdienst, keine PostgreSQL-Instanz in B01.

## Umsetzung

1. Bestehendes `pyproject.toml` analysieren; nicht neu erzeugen, wenn vorhanden.
2. Fehlende Entwicklungsabhaengigkeiten nur dort ergaenzen, sofern sie bereits durch die Governance vorgesehen sind: `pytest`, `ruff`, `mypy` und bestehende Testplugins.
3. `.github/workflows/ci.yml` mit einem Windows-Job erstellen.
4. Editable-Installation beziehungsweise den bereits vorhandenen Installationsweg verwenden; keinen zweiten Weg schaffen.
5. README nur um reproduzierbare Setup- und Testbefehle ergaenzen.

## Tests

- YAML syntaktisch plausibel und alle referenzierten Befehle lokal ausfuehrbar.
- Vollstaendiges Green Gate.
- Keine neue Produktdependency ausserhalb des vorhandenen Alarmcast-Stacks.

## Akzeptanzkriterien

- genau ein Python-Projektmanifest,
- genau ein CI-Workflow fuer die Baselinepruefung,
- Windows/Python 3.12 festgelegt,
- keine Produktfunktion geaendert,
- Setup aus README ist eindeutig,
- Inkrementcommit exakt: `B01 Add reproducible Python 3.12 CI`.

## Stop-Bedingungen

- bestehendes Manifest widerspricht dem vorgesehenen Installationsweg,
- Tests lassen sich nur durch Produktcodeaenderungen gruener machen,
- eine neue nicht freigegebene Top-Level-Dependency erscheint erforderlich.
