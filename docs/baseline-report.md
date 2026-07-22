# B00 Baseline-Importbericht

## Archiv

- Pfad vor der Uebernahme: `bootstrap/alarmcast-baseline.zip`
- Groesse: `80584 Bytes`
- SHA-256: `879e12eacbc7102b45952069c5582d456b55d4cfa12d3f55ea9e77e77334b99e`
- Ergebnis: Pfad, Groesse und Pruefsumme entsprachen der Freigabe in
  `tasks/ACTIVE_TASK.md`. Das Archiv liess sich fehlerfrei entpacken und wurde
  nach der bytegleichen Verifikation der Uebernahme entfernt.

## Uebernommene Dateien

Die folgenden 60 Dateien wurden unveraendert aus dem Archiv in die
Repository-Wurzel uebernommen. Die SHA-256-Pruefsumme jeder Zieldatei wurde
gegen die jeweilige Archivdatei verifiziert.

- `.cursor/plans/initial-project-setup.md`
- `.cursor/rules/code-style.mdc`
- `.cursor/rules/project-architecture.mdc`
- `.cursor/rules/safe-existing-file-edits.mdc`
- `.cursor/rules/verification.mdc`
- `.gitignore`
- `alarmcast.spec`
- `alarmcast-debug.spec`
- `docs/architecture.md`
- `docs/decisions/0001-initial-architecture.md`
- `docs/decisions/0002-host-event-log.md`
- `docs/decisions/README.md`
- `docs/project-brief.md`
- `hooks/pyi_rth_alarmcast.py`
- `pyproject.toml`
- `scripts/build_exe.ps1`
- `src/alarmcast/__init__.py`
- `src/alarmcast/__main__.py`
- `src/alarmcast/client/__init__.py`
- `src/alarmcast/client/app.py`
- `src/alarmcast/client/message_overlay.py`
- `src/alarmcast/client/net.py`
- `src/alarmcast/client/output.py`
- `src/alarmcast/client/overlay.py`
- `src/alarmcast/client/ui/__init__.py`
- `src/alarmcast/client/ui/main_window.py`
- `src/alarmcast/core/__init__.py`
- `src/alarmcast/core/alarm_logic.py`
- `src/alarmcast/core/audio_format.py`
- `src/alarmcast/core/autostart.py`
- `src/alarmcast/core/config.py`
- `src/alarmcast/core/discovery.py`
- `src/alarmcast/core/event_log.py`
- `src/alarmcast/core/logging_setup.py`
- `src/alarmcast/core/mode_switch.py`
- `src/alarmcast/core/protocol.py`
- `src/alarmcast/core/security.py`
- `src/alarmcast/core/single_instance.py`
- `src/alarmcast/core/ui_theme.py`
- `src/alarmcast/host/__init__.py`
- `src/alarmcast/host/app.py`
- `src/alarmcast/host/capture.py`
- `src/alarmcast/host/detector.py`
- `src/alarmcast/host/server.py`
- `src/alarmcast/host/ui/__init__.py`
- `src/alarmcast/host/ui/main_window.py`
- `tests/manual_smoke.md`
- `tests/test_alarm_logic.py`
- `tests/test_client_net.py`
- `tests/test_client_output.py`
- `tests/test_config.py`
- `tests/test_event_log.py`
- `tests/test_host_capture.py`
- `tests/test_host_detector.py`
- `tests/test_host_server.py`
- `tests/test_main.py`
- `tests/test_main_startup.py`
- `tests/test_protocol.py`
- `tests/test_security.py`
- `tests/test_single_instance.py`

## Bewusst ausgeschlossene Dateien

- `AGENTS.md`: vorhandene verbindliche Governance-Datei blieb erhalten.
- `README.md`: ausdruecklich genehmigte Konfliktaufloesung; die vorhandene
  README gehoert zur neuen Repository-Governance und Roadmap und blieb
  unveraendert. Die Archivversion wurde nicht uebernommen.
- `src/alarmcast.egg-info/dependency_links.txt`: generiertes Paketmetadatum.
- `src/alarmcast.egg-info/PKG-INFO`: generiertes Paketmetadatum.
- `src/alarmcast.egg-info/requires.txt`: generiertes Paketmetadatum.
- `src/alarmcast.egg-info/SOURCES.txt`: generiertes Paketmetadatum.
- `src/alarmcast.egg-info/top_level.txt`: generiertes Paketmetadatum.

Weitere geschuetzte Governance-Pfade aus B00 waren im Archiv nicht vorhanden
und wurden nicht veraendert. Das Archiv enthielt keine lokalen
`host.json`-, `client.json`- oder `mode.txt`-Dateien, keine Logs, Caches,
Build-/Dist-Verzeichnisse oder kompilierten Python-Dateien.

## Pruefung auf Secrets und lokale Daten

Dateinamen und Inhalte wurden auf private Schluessel, Zugangsdatenmuster,
PSKs, Tokens und Rechneradressen geprueft. Es wurden keine echten Secrets und
keine produktive lokale Konfiguration gefunden.

Die Treffer auf sicherheitsbezogene Begriffe sind Bestandteil des Quellcodes,
der Dokumentation und offensichtlich fiktiver Tests: Host-PSKs werden zur
Laufzeit zufaellig erzeugt, Client-Standardwerte sind leer, und Testwerte sind
als einfache Beispieldaten erkennbar. Gefundene Adressen sind Loopback-,
Bind-, Dokumentations-/Test- oder oeffentliche Probeadressen; es wurden keine
internen produktiven Rechneradressen uebernommen.

## Ausgefuehrte Pruefungen

### Vor der Uebernahme

- `git status --short`: bestanden, Working Tree sauber.
- `python --version`: `Python 3.9.6`.
- `ruff check .`: bestanden; vor dem Import waren keine Python-Dateien
  vorhanden.
- `ruff format --check .`: bestanden; vor dem Import waren keine
  Python-Dateien vorhanden.
- `mypy src`: Baseline-Fehler, weil `src` vor dem Import noch nicht existierte.
- `pytest -q`: Baseline-Fehler, weil vor dem Import noch keine Tests vorhanden
  waren.

### Archiv und Uebernahme

- Archivpfad, Dateigroesse und SHA-256 gegen `tasks/ACTIVE_TASK.md`: bestanden.
- Entpacken in ein isoliertes temporaeres Verzeichnis: bestanden, 67 Dateien.
- Vollstaendige Pfadklassifikation und Konfliktpruefung: bestanden; nur der
  ausdruecklich entschiedene Konflikt `README.md` lag vor.
- Bytevergleich per SHA-256 fuer alle 60 uebernommenen Dateien: bestanden.
- Suche nach `*.egg-info`: bestanden, kein solches Verzeichnis uebernommen.

### Nach der Uebernahme

- `python --version`: `Python 3.9.6`; die vorgesehene Zielversion ist Python
  3.12.
- `python -m compileall src`: bestanden.
- `ruff check .`: bestanden.
- `ruff format --check .`: bestanden, 44 Dateien bereits formatiert.
- `mypy src`: Baseline-Fehler; ein Fehler in
  `src/alarmcast/host/capture.py:102` (`no-any-return`).
- `pytest -q`: Baseline-Fehler bei der Collection:
  - `tests/test_client_net.py`: `zeroconf` ist nicht installiert.
  - `tests/test_event_log.py`: `datetime.UTC` ist unter Python 3.9 nicht
    verfuegbar.
  - `tests/test_host_server.py`: indirekt derselbe `datetime.UTC`-Fehler.
- `pytest -q --ignore=tests/test_client_net.py --ignore=tests/test_event_log.py
  --ignore=tests/test_host_server.py`: 31 Tests bestanden; zwei
  `test_single_instance.py`-Tests konnten wegen fehlendem `PySide6` nicht
  eingerichtet werden. Beim Aufraeumen des Pytest-Tempverzeichnisses erschien
  zusaetzlich eine lokale `WinError 5`-Meldung.
- `pytest -q --ignore=tests/test_client_net.py --ignore=tests/test_event_log.py
  --ignore=tests/test_host_server.py --ignore=tests/test_single_instance.py`:
  31 Tests bestanden; der Prozess endete erfolgreich. Beim abschliessenden
  Pytest-Temp-Cleanup erschien erneut die lokale `WinError 5`-Meldung.

## NOT RUN

- Tests, die `zeroconf` oder `PySide6` benoetigen: nicht vollstaendig
  ausfuehrbar, weil die Abhaengigkeiten in der vorhandenen Umgebung fehlen.
  Fuer B00 wurden keine Abhaengigkeiten installiert.
- Python-3.12-spezifische Testausfuehrung: nicht ausfuehrbar, weil lokal nur
  Python 3.9.6 vorhanden ist.
- Manueller Windows-/Audio-/Multi-Monitor-Smoke-Test: `NOT RUN`; B00 importiert
  ausschliesslich den unveraenderten Bestand und veraendert keine Produktlogik.

## Bekannte Baseline-Fehler und Restrisiken

- Die lokale Python-Version weicht von der in der Zielarchitektur genannten
  Python-Version 3.12 ab.
- Der importierte Originalbestand besteht den aktuellen Mypy-Lauf wegen eines
  `no-any-return`-Fehlers nicht.
- Der vollstaendige Pytest-Lauf ist in der vorhandenen Umgebung wegen fehlender
  Abhaengigkeiten und Python 3.9 nicht ausfuehrbar.
- Hardware-, Audio-, Netzwerk-, Autostart-, PyInstaller- und Multi-Monitor-
  Verhalten wurde in B00 nicht manuell validiert.
- Diese Baseline-Abweichungen wurden gemaess B00 nicht durch Code-, Test- oder
  Dependency-Aenderungen behoben.

## Abschlussbericht

```text
Task:             B00 - Originalen Alarmcast-Bestand importieren
Geaendert:        60 Originaldateien unveraendert importiert,
                  docs/baseline-report.md erstellt und Bootstrap-ZIP entfernt
Unveraendert:     Produktlogik, vorhandene README und Governance-Dateien;
                  B01 und alle spaeteren Inkremente nicht begonnen
Tests:            compileall, Ruff Lint und Ruff Format bestanden;
                  31 ausfuehrbare Pytests bestanden; Mypy und der vollstaendige
                  Pytest-Lauf mit dokumentierten Baseline-/Umgebungsfehlern
Manuell:          NOT RUN - keine Produktlogikaenderung in B00
Risiken:          Python 3.9 statt 3.12, fehlende optionale Laufzeitpakete,
                  bestehender Mypy-Fehler und nicht ausgefuehrte Hardwaretests
Spezifikationsbezug: Spezifikation 1.0 Abschnitt 15 Bestandsschutz;
                  B00-Akzeptanzkriterien und Roadmap Phase B
Naechster Schritt: Review, nicht selbststaendig B01 beginnen
```
