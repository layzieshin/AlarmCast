# B03 – Atomare, schema-versionierte Bestandskonfiguration

**Status:** `READY`  
**Abhaengigkeit:** B02 ist gemergt.  
**Art:** Stabilisierung der bestehenden lokalen Konfigurationspersistenz; keine neue Produktfunktion.

## 1. Ziel

Die bestehenden getrennten Dateien `host.json` und `client.json` unter `%APPDATA%\AlarmCast` werden atomar, schema-versioniert und migrationsfaehig gespeichert.

Bestehende unversionierte Dateien muessen ohne stillen Datenverlust auf Schema-Version 1 migriert werden. Defekte Dateien und Schreibabbrueche duerfen weder zu einem stillen Komplettreset noch zu einer teilweise geschriebenen Zieldatei fuehren.

B03 behaelt die bestehenden Runtime-Dataclasses `HostConfig` und `ClientConfig`, die bestehenden Dateinamen und das bisherige fachliche Verhalten bei. Es entsteht keine gemeinsame `app.json`.

## 2. Vor Beginn

Lies die in `AGENTS.md` festgelegte Reihenfolge und fuehre die Baseline mit der gesperrten B01-Umgebung aus:

```text
git status --short
uv lock --check
uv sync --locked --extra dev
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy src
uv run --frozen pytest -q
```

Untersuche vor dem ersten Edit mindestens:

- `src/alarmcast/core/config.py`,
- alle Aufrufer von `load_host_config`, `save_host_config`, `load_client_config` und `save_client_config`,
- `tests/test_config.py`,
- die bestehende Behandlung von `mode.txt`.

Bestehende UI-, Host-, Client- und Entry-Point-Strukturen werden nicht eigenmaechtig umgebaut.

## 3. Verbindliches Persistenzformat

### 3.1 Getrennte Dateien

Die bestehenden Dateien bleiben erhalten:

```text
%APPDATA%\AlarmCast\host.json
%APPDATA%\AlarmCast\client.json
```

B03 fuehrt weder eine gemeinsame Konfigurationsdatei noch einen neuen Konfigurationsordner ein.

### 3.2 Schema-Version 1

Beide JSON-Objekte erhalten auf oberster Ebene:

```json
{
  "schema_version": 1
}
```

`schema_version` ist Persistenzmetadatum. Es soll nicht als fachliches Feld in `HostConfig` oder `ClientConfig` erscheinen, sofern kein zwingender, im PR begruendeter Grund besteht.

Die heute vorhandenen Host- und Client-Felder bleiben inhaltlich erhalten. B03 fuehrt keine neue Benutzereinstellung ein und aendert keine Defaultwerte.

### 3.3 Legacy-Version 0

Eine vorhandene JSON-Objektdatei ohne `schema_version` oder mit expliziter ganzzahliger Version `0` gilt als Legacy-Version 0.

Sie wird beim Laden auf Version 1 migriert:

- bekannte Werte werden mit dem bisherigen Konvertierungs- und Defaultverhalten geladen,
- fehlende bekannte Werte erhalten die bisherigen Defaults,
- unbekannte Top-Level-Felder werden unveraendert erhalten,
- das Ergebnis wird atomar als Version 1 gespeichert,
- ein wiederholter Lauf ist idempotent.

### 3.4 Aktuelle und zukuenftige Versionen

- Version `1` wird geladen und bei fehlenden beziehungsweise normalisierungsbeduerftigen bekannten Feldern kontrolliert kanonisiert.
- Eine boolesche, negative oder anderweitig ungueltige Versionsangabe ist ein Konfigurationsfehler.
- Eine Version groesser als `1` ist eine nicht unterstuetzte Zukunftsversion.
- Eine Zukunftsversion darf nicht durch Defaults, eine aeltere Sicherung oder eine Rueckmigration ueberschrieben werden.

## 4. Erhalt unbekannter Werte

Unbekannte Top-Level-Felder einer gueltigen bestehenden Datei muessen erhalten bleiben:

- bei der Migration von Version 0 auf Version 1,
- bei der Normalisierung fehlender bekannter Felder,
- bei einem spaeteren expliziten `save_host_config` oder `save_client_config`.

Bekannte Felder und `schema_version` werden durch die aktuelle Anwendung kontrolliert gesetzt. Unbekannte Felder werden nicht in die Runtime-Dataclasses aufgenommen und nicht stillschweigend verworfen.

B03 muss dokumentieren, dass sich diese Garantie auf unbekannte Top-Level-Felder des heute flachen JSON-Formats bezieht.

## 5. Atomarer Schreibweg

Jeder Schreibvorgang fuer Hauptdatei und Sicherung muss mindestens folgende Eigenschaften besitzen:

1. temporaere Datei im selben Verzeichnis wie die Zieldatei,
2. UTF-8-JSON mit stabiler, lesbarer Formatierung und abschliessendem Zeilenumbruch,
3. `flush` und `fsync` vor dem Ersetzen,
4. atomarer Austausch ueber `os.replace`,
5. Aufraeumen temporaerer Dateien bei Erfolg und Fehler,
6. bei einem Fehler bleibt die zuvor gueltige Zieldatei bytegenau erhalten,
7. ein Fehler wird als konkrete Konfigurationsausnahme weitergegeben und nicht verschluckt.

Keine neue externe Abhaengigkeit ist erlaubt.

## 6. Letzte gueltige Sicherung und Wiederherstellung

Fuer jede Konfiguration wird eine benachbarte letzte gueltige Sicherung gefuehrt:

```text
host.json.bak
client.json.bak
```

Verbindliches Verhalten:

- Nach dem ersten erfolgreichen Erstellen existieren eine gueltige Hauptdatei und eine gueltige Sicherung.
- Vor beziehungsweise waehrend eines spaeteren Speicherns darf eine gueltige Sicherung niemals durch ungueltige oder teilweise Daten ersetzt werden.
- Bei einer syntaktisch defekten, nicht als JSON-Objekt lesbaren oder anderweitig unbrauchbaren Hauptdatei wird eine gueltige Sicherung verwendet.
- Die defekte Hauptdatei wird vor der Wiederherstellung unter einem kollisionssicheren `.corrupt`-Namen erhalten; sie wird nicht still geloescht.
- Die Hauptdatei wird aus der gueltigen Sicherung atomar wiederhergestellt und anschliessend normal geladen.
- Ist auch die Sicherung nicht gueltig oder fehlt sie, wird eine konkrete Ladeausnahme ausgelöst. Es werden keine Defaults erzeugt und keine vorhandenen Dateien ueberschrieben.
- Eine nicht unterstuetzte Zukunftsversion wird nicht durch eine aeltere Sicherung ersetzt.

Die konkrete interne Struktur darf klein und testbar gestaltet werden. Es darf kein allgemeines neues Settings-Modul aus einem spaeteren Inkrement vorweggenommen werden.

## 7. In Scope

1. `src/alarmcast/core/config.py` gezielt ueberarbeiten oder in eng begruendete interne Hilfsdateien innerhalb von `core` aufteilen.
2. Eine kleine Hierarchie konkreter Konfigurationsausnahmen einfuehren, damit Lade-, Versions-, Recovery- und Schreibfehler unterscheidbar sind.
3. Schema-Version 1 fuer Host und Client einfuehren.
4. Unversionierte Bestandsdateien migrieren.
5. Unbekannte Top-Level-Felder erhalten.
6. Atomare Haupt- und Backup-Schreibvorgaenge implementieren.
7. Recovery und kollisionssichere Sicherung defekter Dateien implementieren.
8. Bestehende Aufrufer ohne UI- oder Protokollumbau kompatibel halten.
9. Die Konfigurationsdokumentation unter `docs/` ergaenzen.
10. Einen nicht destruktiven Windows-Neustart-Smoke-Test mit temporaerem `APPDATA` dokumentieren und ausfuehren.
11. `docs/implementation-roadmap.md` aktualisieren:
    - B02 auf `DONE`,
    - B03 waehrend der Umsetzung auf `IN_PROGRESS`,
    - im Abschlussstand auf `REVIEW`.

## 8. Nicht in Scope

- keine gemeinsame `app.json`,
- keine Migration oder Aenderung von `mode.txt`,
- keine Bereinigung der doppelten Mode-Logik,
- kein neues `settings/`-Fachmodul,
- keine neue UI und keine Aenderung bestehender Bedienelemente,
- keine Aenderung von Host-/Client-Laufzeitverhalten,
- keine Aenderung des Netzwerkprotokolls, der PSK-Logik oder der Audiofunktionen,
- keine neue Runtime- oder Dev-Abhaengigkeit,
- keine neue Entry-Point- oder Buildlogik,
- keine allgemeine Validierungs- oder Refactoringwelle,
- kein Beginn von A01, S01 oder anderen spaeteren Inkrementen.

## 9. Pflicht-Tests

Mindestens folgende automatisierte Faelle sind fuer Host und Client beziehungsweise passend parametrisiert abzudecken:

1. Erststart erzeugt Version 1 und eine gueltige Sicherung.
2. Roundtrip aller heute vorhandenen bekannten Felder.
3. Migration einer gueltigen unversionierten Datei.
4. Migration mit fehlenden bekannten Feldern und bisherigen Defaults.
5. Unbekannte Top-Level-Felder bleiben bei Migration erhalten.
6. Unbekannte Top-Level-Felder bleiben bei einem spaeteren expliziten Speichern erhalten.
7. Ein zweites Laden einer bereits migrierten kanonischen Datei veraendert deren Inhalt nicht erneut.
8. Explizite Legacy-Version `0` wird migriert.
9. Ungueltige Versionswerte werden ohne Ueberschreiben abgelehnt.
10. Zukunftsversionen werden ohne Backup-Fallback und ohne Ueberschreiben abgelehnt.
11. Defekte Hauptdatei plus gueltige Sicherung wird wiederhergestellt; die defekte Datei bleibt als `.corrupt` erhalten.
12. Defekte Hauptdatei ohne gueltige Sicherung erzeugt eine konkrete Ausnahme und keinen Defaultreset.
13. Defekte Sicherung wird nicht als gueltig akzeptiert.
14. Simulierter Fehler vor beziehungsweise bei `os.replace` laesst die alte Hauptdatei bytegenau unveraendert.
15. Temporaere Dateien werden nach einem simulierten Schreibfehler entfernt.
16. Sicherungsdateien enthalten nur gueltiges, vollstaendiges JSON.
17. Der echte Repository-Integrationsguard aus B02 bleibt gruen.

Negative Testdaten werden zur Laufzeit in temporaeren Verzeichnissen erzeugt. Keine echten PSKs, internen Adressen oder produktiven Altdateien werden committed.

## 10. Windows-Neustart-Smoke

Der Smoke-Test verwendet ein temporaeres `APPDATA` und beruehrt keine echte Benutzerkonfiguration.

Er muss mindestens zwei getrennte Python-Prozesse verwenden:

1. Prozess A erzeugt beziehungsweise migriert Host- und Clientwerte und beendet sich sauber.
2. Prozess B startet mit demselben temporaeren `APPDATA`, laedt die Werte erneut und bestaetigt:
   - Einstellungen sind erhalten,
   - `schema_version` ist `1`,
   - Haupt- und Sicherungsdateien sind gueltig,
   - keine echte `%APPDATA%\AlarmCast`-Konfiguration wurde veraendert.

Die genauen PowerShell-Schritte, das erwartete Ergebnis, Datum, getesteter Commit und Tester werden in einer B03-spezifischen Datei unter `tests/` dokumentiert.

Ein zusaetzlicher interaktiver UI-Neustarttest darf dokumentiert werden, ist aber kein Anlass fuer UI-Aenderungen.

## 11. Verifikation

Gezielt:

```text
uv run --frozen pytest -q tests/test_config.py
uv run --frozen pytest -q tests/architecture
```

Gesamtes Green Gate:

```text
uv lock --check
uv sync --locked --extra dev
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy src
uv run --frozen pytest -q
git diff --check
git status --short
git diff --name-only
git diff --stat
```

Der Pull-Request-Workflow muss auf dem aktuellen Branch tatsaechlich erfolgreich laufen.

## 12. Akzeptanzkriterien

- Beide Bestandsdateien besitzen Schema-Version 1.
- Eine unversionierte gueltige Bestandsdatei wird automatisch und idempotent migriert.
- Bekannte Werte und unbekannte Top-Level-Felder gehen weder bei Migration noch bei spaeterem Speichern verloren.
- Jeder Schreibweg ist atomar und hinterlaesst bei Fehlern die letzte gueltige Hauptdatei.
- Eine letzte gueltige Sicherung ist vorhanden und kontrolliert nutzbar.
- Defekte Hauptdateien werden nicht still geloescht oder durch Defaults ersetzt.
- Zukunftsversionen werden sicher abgelehnt und nicht herabgestuft.
- Die bisherigen Host- und Client-Aufrufer bleiben kompatibel.
- Der nicht destruktive Windows-Neustart-Smoke ist erfolgreich dokumentiert.
- Alle bestehenden Tests, Architekturguards und CI-Gates sind gruen.
- `mode.txt`, UI, Protokoll, Audio, Entry Points und Abhaengigkeiten sind unveraendert.
- A01 und andere spaetere Inkremente wurden nicht begonnen.

## 13. Stop-Bedingungen

Sofort stoppen bei:

- einer notwendigen Aenderung des bestehenden UI- oder Netzwerkverhaltens,
- einer notwendigen Migration von `mode.txt` oder Einfuehrung einer gemeinsamen `app.json`,
- einer erforderlichen neuen externen Abhaengigkeit,
- einer nicht aufloesbaren Mehrdeutigkeit vorhandener Bestandsfelder,
- einem Datenverlust, der nur durch Verwerfen unbekannter Felder vermeidbar waere,
- einer erforderlichen Aenderung oeffentlicher Entry Points,
- einem Baseline- oder CI-Fehler unklarer Herkunft,
- notwendiger Arbeit an A01, S01 oder einem anderen spaeteren Inkrement.

## 14. Abschluss

Committe und pushe die vollstaendige Umsetzung. Oeffne einen Draft-PR mit dem Titel:

```text
B03 Make legacy configuration atomic and versioned
```

Falls `gh` lokal fehlt, nicht installieren. Der Draft-PR darf ueber den vorhandenen GitHub-Connector geoeffnet und der CI-Lauf damit geprueft werden.

Nach B03 endet der Task. A01, S01 und andere Inkremente werden nicht begonnen.
