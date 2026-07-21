# B03 – Atomare und versionierte Bestandskonfiguration

**Status innerhalb STAGE-01:** beginnt nur nach `AUTO_GREEN` von B02.

## Ziel

Die bestehende Alarmcast-Konfiguration wird ohne neue Produktarchitektur robust gegen Schreibabbrueche und zukuenftige Schemaaenderungen gemacht.

## Erlaubte Produktdateien

- `src/alarmcast/core/config.py`
- `src/alarmcast/core/mode_switch.py`, nur falls im Baselinebestand fuer `mode.txt` verantwortlich
- direkt zugehoerige bestehende Tests oder neue Tests mit eindeutigem Konfigurationsbezug
- `docs/stage-reports/STAGE-01.md`

Keine anderen Produktmodule duerfen geaendert werden.

## Verbindliche Struktur

- Kein neues `settings/`-Fachmodul in B03.
- Keine `app.json`.
- Keine SQLite-Datenbank.
- Keine DPAPI-/Credential-Manager-Integration.
- Keine generische Config-Framework-Abhaengigkeit.
- Bestehende Dateien bleiben:

```text
%APPDATA%\AlarmCast\host.json
%APPDATA%\AlarmCast\client.json
%APPDATA%\AlarmCast\mode.txt
```

- JSON-Dateien erhalten exakt ein Top-Level-Feld `schema_version` als positive Ganzzahl.
- Aktuelle Version fuer diese erste Migration: `1`.
- Fachfelder bleiben auf derselben Ebene; kein neues generisches `data`, `payload` oder `settings`-Objekt.
- Unbekannte vorhandene Felder werden beim Lesen und erneuten Schreiben erhalten, sofern sie serialisierbar sind.

## Atomarer Schreibvorgang

1. Zielordner sicherstellen.
2. Inhalt in eine temporaere Datei im selben Verzeichnis schreiben.
3. Datei flushen und nach Moeglichkeit `fsync` ausfuehren.
4. Gueltigkeit durch erneutes Parsen pruefen.
5. Mit `os.replace` atomar auf den Zielpfad ersetzen.
6. Bei Fehler Zielbestand unberuehrt lassen und konkrete Exception an den bestehenden Aufrufer weitergeben beziehungsweise nach bestehendem Fehlervertrag behandeln.

Keine stille Ruecksetzung auf Defaults.

## Lese- und Migrationsregeln

- Fehlende Datei: bestehendes Erststartverhalten bleibt bestehen.
- Unversionierte gueltige JSON-Datei: als Schema 0 behandeln und in Memory nach Schema 1 migrieren.
- Schema 1: normal lesen.
- Zukuenftige unbekannte Schema-Version: sichtbarer Fehler; nicht als Defaults behandeln.
- Defekte JSON-Datei: sichtbarer Fehler und keine Ueberschreibung.
- Migration wird erst beim naechsten bestaetigten Speichern persistiert; Lesen allein veraendert keine Datei.
- `mode.txt` bleibt ein einfacher explizit validierter Moduswert; keine JSON-Duplizierung.

## Tests

Mindestens:

- fehlende Datei,
- bestehende unversionierte Hostdatei,
- bestehende unversionierte Clientdatei,
- Schema-1-Roundtrip,
- Erhalt unbekannter Felder,
- defektes JSON,
- unbekannte zukuenftige Schema-Version,
- simulierter Fehler vor `os.replace`,
- simulierter Fehler bei Replace,
- Zielbestand bleibt bei Fehler byteidentisch,
- gueltige Modewerte und ungueltiger Modewert,
- vollstaendiges Green Gate.

## Manueller Test

Unter Windows mit Kopie einer realen vorhandenen Konfiguration starten, Einstellungen speichern, Anwendung neu starten und Werte vergleichen. Darf als `MANUAL_PENDING` dokumentiert werden.

## Akzeptanzkriterien

- kein stiller Datenverlust,
- kein zweiter Konfigurationsspeicher,
- keine Veraenderung des Alarmcast-Netzwerk-/Audioverhaltens,
- alle Alt-Konfigurationstests und neuen Migrationstests gruen,
- Inkrementcommit exakt: `B03 Add atomic versioned legacy configuration`.

## Stop-Bedingungen

- Bedeutung eines bestehenden Feldes ist unklar,
- der Baselinecode besitzt mehrere konkurrierende Owner fuer dieselbe Datei,
- unbekannte Werte koennen nicht erhalten werden,
- erforderliche Aenderungen reichen ausserhalb der erlaubten Produktdateien.
