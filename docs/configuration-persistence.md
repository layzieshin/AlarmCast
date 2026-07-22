# Konfigurationspersistenz B03

AlarmCast speichert die bestehenden Laufzeitkonfigurationen weiterhin getrennt unter
`%APPDATA%\AlarmCast\host.json` und `%APPDATA%\AlarmCast\client.json`. `mode.txt` bleibt
unveraendert und ist nicht Teil dieses Persistenzformats.

## Format und Migration

Beide JSON-Objekte tragen auf oberster Ebene `"schema_version": 1`. Die Versionsangabe ist
reines Persistenzmetadatum und kein Feld von `HostConfig` oder `ClientConfig`.

Eine Objektdatei ohne `schema_version` oder mit der ganzzahligen Version `0` wird beim Laden
auf Version 1 migriert. Bekannte Felder verwenden dabei dieselben Konvertierungen und Defaults
wie bisher. Fehlende bekannte Felder werden kanonisch ergaenzt. Die Migration ist idempotent.

Unbekannte Top-Level-Felder werden bei Migration, Normalisierung und spaeterem explizitem
Speichern erhalten. Diese Garantie gilt fuer die unbekannten Top-Level-Felder des derzeit
flachen JSON-Formats; unbekannte Werte werden nicht in die Runtime-Dataclasses aufgenommen.

Boolesche, negative und sonstige nicht ganzzahlige Versionen werden als ungueltig abgelehnt.
Versionen groesser als 1 werden als Zukunftsversionen abgelehnt und weder aus einer aelteren
Sicherung ersetzt noch heruntergestuft.

## Atomarer Schreibweg

Jeder Schreibvorgang erzeugt eine temporaere Datei im Zielverzeichnis, schreibt lesbares
UTF-8-JSON mit abschliessendem Zeilenumbruch, fuehrt `flush` und `fsync` aus und ersetzt das
Ziel mit `os.replace`. Temporaere Dateien werden auch nach Fehlern entfernt. Dadurch bleibt
das jeweilige vorhandene Ziel bei einem fehlgeschlagenen Replace bytegenau erhalten.

Zu jeder Hauptdatei wird eine vollstaendige, gueltige letzte Sicherung gefuehrt:

- `host.json.bak`
- `client.json.bak`

Ein erfolgreicher Speichervorgang aktualisiert Sicherung und Hauptdatei mit demselben
kanonischen Dokument. Es wird keine neue externe Abhaengigkeit verwendet.

## Recovery und Fehler

Ist eine Hauptdatei syntaktisch defekt oder kein JSON-Objekt, wird zuerst die Sicherung
vollstaendig gelesen und validiert. Nur eine gueltige Sicherung darf die Hauptdatei atomar
wiederherstellen. Vorher wird der defekte Byteinhalt unter einem kollisionssicheren Namen wie
`host.json.<id>.corrupt` erhalten. Fehlt die Hauptdatei bei vorhandener Sicherung, wird sie
ebenfalls aus der Sicherung wiederhergestellt.

Fehlt eine gueltige Sicherung, bleiben vorhandene Dateien unveraendert und der Ladevorgang
schlaegt fehl. Es gibt in diesem Fall keinen stillen Defaultreset. Die Ausnahmen sind nach
Fehlerart unterscheidbar:

- `ConfigLoadError` fuer Ladefehler,
- `InvalidConfigVersionError` und `UnsupportedConfigVersionError` fuer Versionsfehler,
- `ConfigRecoveryError` fuer nicht moegliche Wiederherstellung,
- `ConfigWriteError` fuer Serialisierungs- und atomare Schreibfehler.

Alle Ausnahmen leiten von `ConfigError` ab.
