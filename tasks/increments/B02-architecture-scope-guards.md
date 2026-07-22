# B02 – Architektur- und Scope-Guards

**Status:** `READY`  
**Abhaengigkeit:** B01 ist gemergt.  
**Art:** Test- und Governance-Infrastruktur, keine Produktfunktion.

## 1. Ziel

Automatische, nachvollziehbare Architekturtests einfuehren, die bestehende Alarmcast-Modulgrenzen und zentrale Repository-Sicherheitsregeln bei jedem Pull Request erzwingen.

Ein absichtlicher Regelverstoss muss durch einen gezielten Guard-Test reproduzierbar fehlschlagen. Die Guards muessen ohne neue externe Abhaengigkeit auskommen und duerfen den bestehenden Produktcode nicht reorganisieren.

## 2. Vor Beginn

Lies die in `AGENTS.md` festgelegte Reihenfolge und fuehre die Baseline mit der in B01 eingerichteten, gesperrten Entwicklungsumgebung aus:

```text
git status --short
uv lock --check
uv sync --locked --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q
```

Pruefe vor dem ersten Edit die aktuellen Imports und Entry Points im echten Repository. Bestehende, dokumentierte Strukturen sind nicht eigenmaechtig umzubauen.

## 3. Verbindliche Guard-Regeln

### 3.1 Importgrenzen des Bestands

Unter `src/alarmcast/` gelten weiterhin die harten Bestandsgrenzen:

- `core/` darf nichts aus `alarmcast.host` oder `alarmcast.client` importieren.
- `host/` darf nichts aus `alarmcast.client` importieren.
- `client/` darf nichts aus `alarmcast.host` importieren.
- `host/` und `client/` duerfen aus `alarmcast.core` importieren.
- Der bestehende Composition-/CLI-Entry-Point `src/alarmcast/__main__.py` darf Host und Client weiterhin lazy importieren.

Die Pruefung muss mindestens normale `import`- und `from ... import ...`-Anweisungen erfassen. Relative Importe muessen korrekt aufgeloest werden. Offensichtliche dynamische Importe mit statischem Stringliteral ueber `importlib.import_module(...)` oder `__import__(...)` duerfen die Grenzen nicht umgehen.

### 3.2 Unerlaubte Entry Points

Aktuell ist genau dieser Python-Runtime-Entry-Point freigegeben:

```text
src/alarmcast/__main__.py
```

Der Guard muss mindestens verhindern:

- weitere `__main__.py`-Dateien unter `src/`,
- weitere `if __name__ == "__main__"`-Bloecke unter `src/`,
- neue Eintraege unter `[project.scripts]` oder `[project.gui-scripts]` in `pyproject.toml`.

Die vorhandenen PyInstaller-Spec-Dateien sind keine zusaetzlichen Python-Runtime-Entry-Points und bleiben unveraendert. Spaetere ausdruecklich freigegebene Inkremente duerfen die zentrale Allowlist kontrolliert erweitern; B02 selbst fuegt keinen Entry Point hinzu.

### 3.3 Verbotene lokale Konfigurationen und Geheimnisse

Der Repository-Guard muss versionierte sowie nicht ignorierte unversionierte Dateien pruefen. Mindestens verboten sind:

- `host.json`, `client.json`, `mode.txt`,
- `.env` und echte `.env.*`-Varianten; eine rein dokumentierte `.env.example` darf ausdruecklich erlaubt werden,
- typische private Schluessel-/Credential-Dateien wie `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_rsa`, `id_ed25519`, `credentials.json`, `secrets.json`,
- echte Private-Key-Header in Textdateien,
- GitHub-Tokenmuster mit bekannten produktiven Praefixen,
- private RFC1918-IPv4-Adressen (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).

Loopback-, Bind-, Multicast- und offizielle Dokumentations-/Testadressen sind nicht als interne Produktivadressen zu behandeln. Testdaten bleiben offensichtlich fiktiv. Ein Guard darf nicht durch seine eigenen negativen Testfixtures ausgeloest werden; problematische Fixture-Inhalte sind zur Laufzeit in temporaeren Verzeichnissen zu erzeugen oder sicher aus Teilstrings zusammenzusetzen.

## 4. In Scope

1. Ein kleines, testbares Guard-Modul ausschliesslich im Testbereich anlegen, bevorzugt unter `tests/architecture/`.
2. Die Regeln als reine beziehungsweise weitgehend reine Python-Funktionen umsetzen; Standardbibliothek und vorhandenes `pytest` genuegen.
3. Fuer jede Guard-Kategorie positive und negative Fixture-Faelle schreiben:
   - erlaubte und verbotene absolute Imports,
   - erlaubte und verbotene relative Imports,
   - erlaubter zentraler und verbotener zusaetzlicher Entry Point,
   - erlaubte harmlose Dateien/Adressen und verbotene Konfig-/Secret-/Privatadress-Faelle.
4. Einen Integrationstest gegen den echten Repository-Stand ausfuehren.
5. Fuer die Repository-Dateiliste einen nachvollziehbaren Git-basierten Weg verwenden, der mindestens getrackte und nicht ignorierte ungetrackte Dateien erfasst, ohne `.git`, `.venv`, Tool-Caches oder andere ignorierte lokale Artefakte zu scannen.
6. Fehlermeldungen so ausgeben, dass Regel, Datei, Zeile beziehungsweise Fundart direkt erkennbar sind.
7. Die Architekturtests in `.github/workflows/ci.yml` als eigenen sichtbaren Schritt vor dem vollstaendigen Pytest-Lauf ausfuehren.
8. Eine kurze Dokumentation unter `docs/` anlegen, die Regeln, Allowlist, lokale Ausfuehrung und das kontrollierte Vorgehen fuer spaetere legitime Erweiterungen beschreibt.
9. `docs/implementation-roadmap.md` aktualisieren:
   - B01 auf `DONE`,
   - B02 waehrend der Umsetzung auf `IN_PROGRESS`,
   - im Abschlussstand auf `REVIEW`.

## 5. Nicht in Scope

- keine Produktcodeaenderung,
- keine Verschiebung oder Kapselung von `core`, `host` oder `client`,
- keine Fassaden aus Phase A,
- keine Konfigurationsmigration aus B03,
- keine neue Runtime- oder Dev-Abhaengigkeit,
- keine neuen Entry Points,
- keine neue Top-Level-Paketstruktur,
- keine allgemeinen Refactorings oder Formatierungswellen,
- keine inhaltliche Aenderung bestehender Alarmcast-Tests,
- kein Pre-Commit-Framework und kein zusaetzlicher externer Scanner.

## 6. Verifikation

Gezielt:

```text
uv run pytest -q tests/architecture
```

Gesamtes Green Gate:

```text
uv lock --check
uv sync --locked --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q
git diff --check
git status --short
git diff --name-only
git diff --stat
```

Der Pull-Request-Workflow muss auf dem aktuellen Branch tatsaechlich laufen. Der eigene CI-Schritt fuer Architekturtests und der vollstaendige Testlauf muessen gruen sein.

## 7. Akzeptanzkriterien

- Jede in Abschnitt 3 definierte Regel besitzt mindestens einen positiven und einen negativen Testfall.
- Die Guards erkennen absolute und relative verbotene Quermodulimporte.
- Ein absichtlich erzeugter verbotener Import laesst den Test mit konkreter Fundstelle fehlschlagen.
- Der zentrale bestehende Entry Point ist erlaubt; ein zusaetzlicher Entry Point wird erkannt.
- Verbotene lokale Konfigurations-, Credential-, Private-Key-, Token- und RFC1918-Faelle werden erkannt.
- Harmlose Dokumentations-/Testadressen und erlaubte Dateien erzeugen keinen Fehlalarm.
- Der echte Repository-Stand besteht alle Guards.
- CI zeigt Architekturtests als eigenen erfolgreichen Schritt und bleibt insgesamt gruen.
- Keine Produktdatei, Runtime-Abhaengigkeit oder spaetere Architektur wurde veraendert.
- Dokumentation und Abschlussbericht sind vollstaendig.
- B03 und alle spaeteren Inkremente wurden nicht begonnen.

## 8. Stop-Bedingungen

Sofort stoppen bei:

- einem bereits bestehenden echten Architekturverstoss im aktuellen `main`, der nur durch Produktcodeaenderung behebbar waere,
- notwendiger neuer Abhaengigkeit,
- erforderlicher Aenderung eines bestehenden Entry Points,
- unklarer Ausnahme, die eine neue Architekturentscheidung oder breite Allowlist benoetigt,
- Guard-Regeln, die legitime bestehende Produktdateien nur durch pauschales Ausblenden bestehen lassen,
- erforderlicher Erweiterung auf B03 oder ein spaeteres Inkrement,
- CI-Fehlern, deren Ursache nicht eindeutig B02 oder der dokumentierten Baseline zugeordnet werden kann.

## 9. Abschluss

Committe und pushe die vollstaendige Umsetzung. Oeffne einen Draft-PR mit dem Titel:

```text
B02 Add architecture and scope guards
```

Falls `gh` lokal fehlt, nicht installieren. Pushe den Branch; der Draft-PR darf ueber den vorhandenen GitHub-Connector geoeffnet werden.

Nach B02 endet der Task. B03 und andere Inkremente werden nicht begonnen.
