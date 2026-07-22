# B01 – Reproduzierbare Entwicklungsumgebung und CI

**Status:** `READY`  
**Abhaengigkeit:** B00 ist gemergt.  
**Art:** Entwicklungsinfrastruktur und Baseline-Stabilisierung, keine neue Produktfunktion.

## 1. Ziel

Einen frischen Windows-Checkout unter Python 3.12 reproduzierbar einrichten und die vorhandene Baseline in GitHub Actions automatisiert pruefen.

Als menschlich freigegebene Werkzeugentscheidung wird `uv` fuer Python-Version, Lockfile, virtuelle Umgebung und reproduzierbaren Sync verwendet. `uv` ist Entwicklungswerkzeug, keine Laufzeitabhaengigkeit der Anwendung.

## 2. Vor Beginn

Lies die in `AGENTS.md` festgelegte Reihenfolge und fuehre die dort genannte Baseline aus. Dokumentiere den bekannten B00-Ausgangszustand getrennt vom Ergebnis dieses Tasks.

Pruefe insbesondere:

```text
git status --short
python --version
ruff check .
ruff format --check .
mypy src
pytest -q
```

Fehlende lokale Python-3.12- oder Plattformabhaengigkeiten duerfen als Baseline dokumentiert werden. Systemsoftware darf nicht ungefragt installiert werden.

## 3. In Scope

1. Eine eindeutige Python-3.12-Vorgabe fuer das Projekt anlegen, bevorzugt `.python-version`.
2. `uv.lock` aus dem bestehenden `pyproject.toml` erzeugen und versionieren.
3. Den Entwicklungs- und CI-Installationsweg so definieren, dass er ausschliesslich aus versionierten Projektdateien reproduzierbar ist.
4. Die bestehende optionale Dependency-Gruppe `dev` weiterverwenden, sofern keine sachliche Migration erforderlich ist.
5. `README.md` um eine konkrete Windows-Entwicklungsanleitung erweitern:
   - Voraussetzungen,
   - frischer Checkout,
   - Einrichtung mit `uv`,
   - gesperrter Sync,
   - Standardpruefungen,
   - bewusst manuelle Hardwaretests.
6. Einen GitHub-Actions-Workflow unter `.github/workflows/` anlegen.
7. Der Workflow laeuft mindestens bei Pull Requests gegen `main` und bei Pushes nach `main`.
8. Der Workflow verwendet:
   - einen Windows-GitHub-Runner,
   - Python 3.12,
   - eine fest gepinnte stabile `uv`-Version,
   - Actions nach Moeglichkeit per unveraenderlichem Commit-SHA mit Versionskommentar,
   - minimale Berechtigung `contents: read`,
   - gesperrten Dependency-Sync ohne stilles Aktualisieren des Lockfiles.
9. Der CI-Workflow prueft getrennt und sichtbar:
   - Lockfile-Aktualitaet,
   - `ruff check .`,
   - `ruff format --check .`,
   - `mypy src`,
   - `pytest -q`.
10. Den in B00 dokumentierten einzelnen Mypy-Fehler minimal und verhaltensneutral beheben, falls dies fuer ein gruenes Gate erforderlich ist. Keine weitere Produktcodebereinigung.
11. Nur zwingend erforderliche test- oder umgebungsbezogene Anpassungen vornehmen, damit die vorhandene Baseline unter der vorgesehenen Windows-/Python-3.12-Umgebung reproduzierbar laeuft.
12. `docs/implementation-roadmap.md` aktualisieren:
   - B00 auf `DONE`,
   - B01 waehrend der Umsetzung auf `IN_PROGRESS`,
   - im Abschlussstand auf `REVIEW`.

## 4. Nicht in Scope

- keine neue Produktfunktion,
- keine Architektur-Guards aus B02,
- keine Konfigurationsmigration aus B03,
- keine neue Runtime-Abhaengigkeit,
- keine Modernisierung der Alarmcast-Architektur,
- keine UI-, Netzwerk-, Audio- oder Protokollaenderung,
- kein PyInstaller- oder Release-Workflow,
- keine Linux- oder macOS-CI-Matrix,
- keine allgemeinen Refactorings,
- keine Abschwaechung oder Ausblendung bestehender Tests.

## 5. Werkzeug- und Sicherheitsregeln

- `uv` ist fuer B01 ausdruecklich genehmigt.
- Keine andere neue Top-Level-Toolchain ohne erneute menschliche Freigabe.
- Keine Floating-Tags fuer sicherheitsrelevante Actions, wenn ein stabiler Commit-SHA verfuegbar ist.
- Keine Secrets, Tokens oder produktiven Konfigurationen im Workflow.
- CI benoetigt nur Leserechte auf Repository-Inhalte.
- Das Lockfile darf im CI-Lauf nicht automatisch veraendert werden.

## 6. Verifikation

Lokal soweit moeglich und zwingend in GitHub Actions:

```text
uv lock --check
uv sync --locked --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q
```

Falls die konkrete uv-Version fuer optionale Dependencies eine abweichende, dokumentierte Syntax verlangt, darf die semantisch gleichwertige offizielle Syntax verwendet werden.

Zusaetzlich pruefen:

```text
git status --short
git diff --check
git diff --name-only
git diff --stat
```

Der Pull-Request-Workflow muss auf dem aktuellen Branch tatsaechlich ausgeloest werden. Ein lokaler Erfolg allein reicht nicht.

## 7. Akzeptanzkriterien

- Ein frischer Windows-Checkout kann anhand der README ohne implizites Vorwissen eingerichtet werden.
- Python 3.12 ist eindeutig festgelegt.
- `uv.lock` ist vorhanden, aktuell und committed.
- Der gesperrte Sync installiert Runtime- und Dev-Abhaengigkeiten reproduzierbar.
- CI laeuft bei Pull Requests gegen `main`.
- Ruff-Lint, Ruff-Format, Mypy und der vollstaendige Pytest-Lauf sind in CI gruen.
- Der bekannte B00-Mypy-Fehler ist verhaltensneutral behoben oder enger und nachvollziehbar begruendet.
- Keine Produktfunktion und kein spaeteres Inkrement wurden begonnen.
- Keine unerwarteten Dateien, Caches, lokalen Konfigurationen oder Secrets im Diff.
- Abschlussbericht und Draft-PR sind vorhanden.

## 8. Stop-Bedingungen

Sofort stoppen bei:

- erforderlicher neuer Runtime-Abhaengigkeit,
- notwendiger Produktverhaltensaenderung,
- nicht verhaltensneutral behebbaren Baseline-Fehlern,
- unklarer Inkompatibilitaet einer Abhaengigkeit mit Python 3.12 oder Windows,
- notwendiger Erweiterung auf B02 oder spaetere Inkremente,
- erforderlichen Repository-Secrets oder erweiterten GitHub-Berechtigungen,
- CI-Fehlern, deren Ursache nicht eindeutig diesem Task oder der dokumentierten Baseline zugeordnet werden kann.

## 9. Abschluss

Committe die vollstaendige Umsetzung auf dem aktuellen Branch und pushe ihn. Oeffne einen Draft-PR mit dem Titel:

```text
B01 Reproducible development environment and CI
```

Falls `gh` lokal nicht installiert ist, nicht installieren. Pushe den Branch und melde den Draft-PR als `NOT OPENED – gh nicht installiert`; der PR wird anschliessend separat erstellt.

Nach B01 endet der Task. B02 und andere Inkremente werden nicht begonnen.
