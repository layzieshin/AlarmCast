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
git branch --show-current
ls bootstrap
sha256sum bootstrap/alarmcast-baseline.zip
```

Unter Windows darf statt `sha256sum` verwendet werden:

```powershell
Get-FileHash bootstrap\alarmcast-baseline.zip -Algorithm SHA256
```

Erwartete Werte und der erlaubte Branch stehen in `tasks/ACTIVE_STAGE.md`. Bei jeder Abweichung sofort stoppen.

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
4. Alle echten Quell-, Test-, Dokumentations- und Builddateien aus dem Archiv in die Repository-Wurzel uebernehmen.
5. Die bereits vorhandenen Governance-Dateien nicht durch Archivversionen ersetzen:
   - `AGENTS.md`
   - `README.md`
   - `docs/specification-1.0.md`
   - `docs/domain-model.md`
   - `docs/target-architecture.md`
   - `docs/implementation-roadmap.md`
   - `docs/test-strategy.md`
   - `docs/definition-of-done.md`
   - `docs/decisions/**`
   - `tasks/**`
   - `.cursor/rules/00-agent-workflow.mdc`
6. Weitere Cursor-Dateien aus dem Archiv nur uebernehmen, sofern sie den aktuellen Governance-Regeln nicht widersprechen. Bei Widerspruch stoppen und dokumentieren.
7. Bei sonstigen Namenskonflikten stoppen, statt Inhalte zusammenzumischen.
8. `bootstrap/alarmcast-baseline.zip` und `bootstrap/UPLOAD-HERE.md` nach erfolgreicher Verifikation entfernen.
9. `docs/baseline-report.md` erstellen mit:
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
- Bootstrap-ZIP und Uploadhinweis sind entfernt.
- `docs/baseline-report.md` ist vollstaendig.
- Alle moeglichen Baseline-Pruefungen sind ehrlich dokumentiert.

## 7. Stop-Bedingungen

Sofort stoppen bei:

- falscher Pruefsumme,
- falschem Branch,
- verschluesseltem oder beschaedigtem Archiv,
- echtem Secret oder produktiver Konfiguration im Archiv,
- widerspruechlicher Cursor-/Agentenregel im Archiv,
- unklarem Namenskonflikt,
- Dateien ausserhalb der erwarteten Alarmcast-Projektstruktur,
- Notwendigkeit, Produktcode zu aendern, damit Tests laufen.

## 8. Abschluss innerhalb STAGE-01

Bei erfuelltem Gate:

1. `docs/baseline-report.md` fertigstellen.
2. Genau einen Commit erstellen:

```text
B00 Import original Alarmcast baseline
```

3. Checkpoint in `tasks/stages/STAGE-01-baseline-and-guards.md` eintragen.
4. Status `AUTO_GREEN` beziehungsweise den erlaubten Baseline-Sonderstatus dokumentieren.
5. Direkt mit B01 derselben Etappe fortfahren.

Nach B00 keinen Pull Request erstellen und keine Arbeit ausserhalb von STAGE-01 beginnen.