# B00 – Originalen Alarmcast-Bestand importieren

**Status:** `READY`  
**Freigabegrund:** `bootstrap/alarmcast-baseline.zip` wurde gegen die urspruengliche Alarmcast-Datei verifiziert.  
**Art:** Repository-Baseline, keine Produktentwicklung.

## 1. Ziel

Den unveraenderten urspruenglichen Alarmcast-Projektstand aus dem bereitgestellten ZIP in die Repository-Wurzel uebernehmen. Das Ergebnis ist die nachvollziehbare Baseline fuer alle spaeteren Inkremente.

## 2. Vor Beginn

Lies die in `AGENTS.md` festgelegte Reihenfolge. Pruefe danach:

```text
git status --short
ls bootstrap
sha256sum bootstrap/alarmcast-baseline.zip
```

Unter Windows darf statt `sha256sum` verwendet werden:

```powershell
Get-FileHash bootstrap\alarmcast-baseline.zip -Algorithm SHA256
```

Erwartete Werte stehen in `tasks/ACTIVE_TASK.md`. Bei jeder Abweichung sofort stoppen.

## 3. In Scope

1. Archiv in ein temporaeres Verzeichnis entpacken.
2. Dateiliste vor Uebernahme pruefen.
3. Folgende generierte beziehungsweise lokale Inhalte nicht uebernehmen:
   - `__pycache__/`
   - `*.pyc`
   - `*.egg-info/`
   - `.pytest_cache/`
   - `.mypy_cache/`
   - `.ruff_cache/`
   - `build/`, `dist/`
   - `*.log`
   - `host.json`, `client.json`, `mode.txt`
   - lokale PSKs, Tokens oder Rechneradressen.
4. Alle echten Quell-, Test-, Dokumentations-, Build- und Cursor-Dateien aus dem Archiv in die Repository-Wurzel uebernehmen.
5. Die bereits vorhandenen Governance-Dateien aus dem Roadmap-PR nicht durch aeltere Archivversionen ersetzen:
   - `AGENTS.md`
   - `docs/specification-1.0.md`
   - `docs/target-architecture.md`
   - `docs/implementation-roadmap.md`
   - `docs/test-strategy.md`
   - `docs/definition-of-done.md`
   - `tasks/**`
   - `.cursor/rules/00-agent-workflow.mdc`
6. Bei Namenskonflikten mit anderen vorhandenen Dateien stoppen und den Konflikt dokumentieren, statt Inhalte zusammenzumischen.
7. `bootstrap/alarmcast-baseline.zip` nach erfolgreicher, verifizierter Uebernahme aus dem Repository entfernen.
8. `docs/baseline-report.md` erstellen mit:
   - Archiv-Pruefsumme,
   - uebernommenen Dateipfaden,
   - bewusst ausgeschlossenen Pfaden,
   - gefundenen potenziellen Secrets und Entscheidung,
   - ausgefuehrten Pruefungen,
   - bekannten Baseline-Fehlern.

## 4. Nicht in Scope

- keine Produktcodeaenderung,
- keine Formatierung bestehender Dateien,
- keine Dependency-Aenderung,
- keine Testkorrektur,
- keine Architekturmodernisierung,
- keine atomare Konfiguration,
- keine CI,
- keine Umbenennung oder Reorganisation des Originalcodes,
- keine Anpassung an die Messaging-Spezifikation.

## 5. Verifikation

Nach der Uebernahme:

```text
python --version
python -m compileall src
ruff check .
ruff format --check .
mypy src
pytest -q
```

Falls ein Tool aufgrund fehlender Abhaengigkeit nicht laeuft, darf fuer B00 nichts installiert oder am Projekt geaendert werden, nur um den Test zu erzwingen. Ergebnis als `NOT RUN` beziehungsweise Baseline-Fehler dokumentieren.

Zusaetzlich:

```text
git status --short
git diff --name-only
git diff --stat
```

Pruefe per Suche, dass keine lokalen Konfigurationsdateien, Logs, Buildartefakte oder offensichtlichen Geheimnisse aufgenommen wurden.

## 6. Akzeptanzkriterien

- Das Archiv besitzt die freigegebene Pruefsumme.
- Der echte Alarmcast-Quellcode liegt in der Repository-Wurzel.
- Generierte `*.egg-info`-Verzeichnisse wurden nicht uebernommen.
- Keine Produktdatei wurde inhaltlich veraendert.
- Governance-Dateien bleiben in ihrer neuen Version erhalten.
- Das Bootstrap-ZIP ist nach erfolgreicher Uebernahme entfernt.
- `docs/baseline-report.md` ist vollstaendig.
- Alle moeglichen Baseline-Pruefungen sind ehrlich dokumentiert.

## 7. Stop-Bedingungen

Sofort stoppen bei:

- falscher Pruefsumme,
- verschluesseltem oder beschaedigtem Archiv,
- echtem Secret oder produktiver Konfiguration im Archiv,
- unklarem Namenskonflikt,
- Dateien ausserhalb der erwarteten Alarmcast-Projektstruktur,
- Notwendigkeit, Produktcode zu aendern, damit Tests laufen.

## 8. Abschluss

Erstelle einen Draft-PR mit Titel:

```text
B00 Import original Alarmcast baseline
```

Der PR muss ausdruecklich sagen, dass keine Produktlogik geaendert wurde. Nach dem PR endet der Codex-Task. B01 wird nicht begonnen.
