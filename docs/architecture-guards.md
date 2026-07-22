# Architektur- und Scope-Guards

Die B02-Tests unter `tests/architecture/` schuetzen die bestehenden Alarmcast-Grenzen und
Repository-Regeln. Sie verwenden ausschliesslich die Python-Standardbibliothek, `pytest` und Git.

## Gepruefte Regeln

### Importgrenzen

- `alarmcast.core` importiert weder `alarmcast.host` noch `alarmcast.client`.
- `alarmcast.host` importiert nicht `alarmcast.client`.
- `alarmcast.client` importiert nicht `alarmcast.host`.
- Host und Client duerfen weiterhin `alarmcast.core` verwenden.
- Absolute und relative `import`- beziehungsweise `from`-Anweisungen werden per Python-AST
  ausgewertet. Statische Stringliterale in offensichtlichen Aufrufen von
  `importlib.import_module(...)` und `__import__(...)` werden ebenfalls geprueft.

Der zentrale Composition-/CLI-Code liegt ausserhalb der drei geschuetzten Bestandsmodule und darf
Host und Client weiterhin lazy laden.

### Entry-Point-Allowlist

Der einzige freigegebene Python-Runtime-Entry-Point ist:

```text
src/alarmcast/__main__.py
```

Weitere `__main__.py`-Dateien und weitere `if __name__ == "__main__"`-Bloecke unter `src/` sind
verboten. Ebenso sind Eintraege in `[project.scripts]` und `[project.gui-scripts]` nicht
freigegeben. Die vorhandenen PyInstaller-Spec-Dateien sind Builddefinitionen und keine weiteren
Python-Runtime-Entry-Points.

### Repository-Sicherheit

Die Dateiliste stammt aus `git ls-files --cached --others --exclude-standard`. Dadurch werden
getrackte und nicht ignorierte ungetrackte Dateien erfasst, waehrend `.git`, `.venv`, Tool-Caches
und andere bewusst ignorierte lokale Artefakte nicht rekursiv gescannt werden.

Der Guard meldet:

- lokale Alarmcast-Konfigurationen (`host.json`, `client.json`, `mode.txt`),
- lokale `.env`-Varianten; nur die dokumentierte `.env.example` ist als Dateiname erlaubt,
- typische Credential- und Private-Key-Dateien,
- Private-Key-Header in Textinhalten,
- GitHub-Tokens mit bekannten produktiven Praefixen,
- RFC1918-Adressen in allen gescannten Textdateien, einschliesslich Dateien unter `tests/`.

Loopback-, Bind- und Multicast-Adressen sowie die offiziellen Dokumentationsnetze sind erlaubt.
Testfixtures verwenden diese Dokumentationsnetze statt privater Adressen. Die drei
RFC1918-Netzdefinitionen mit ihrem Standard-CIDR duerfen zu Dokumentationszwecken genannt werden.

## Lokal ausfuehren

Gezielt:

```powershell
uv run --frozen pytest -q tests/architecture
```

Im vollstaendigen Green Gate:

```powershell
uv lock --check
uv sync --locked --extra dev
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy src
uv run --frozen pytest -q
```

GitHub Actions zeigt die Architekturtests vor dem vollstaendigen Pytest-Lauf als eigenen Schritt
`Architecture guards` an.

## Kontrollierte Erweiterung

Eine legitime neue Modulgrenze oder ein weiterer Entry Point benoetigt zuerst das dafuer
freigegebene spaetere Inkrement beziehungsweise eine erforderliche ADR-Freigabe. Danach werden in
demselben PR die eng gefasste Allowlist, positive und negative Fixture-Tests, der Integrationstest
und diese Dokumentation gemeinsam angepasst. Ein Guard darf nicht pauschal fuer Verzeichnisse oder
Dateitypen deaktiviert werden, um einen Fund zu verdecken.
