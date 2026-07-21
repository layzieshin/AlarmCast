# STAGE-01 – Baseline und Schutzschicht

## Ziel

Den unveraenderten Alarmcast-Ausgangsstand importieren und anschliessend die technischen Leitplanken schaffen, die spaetere autonome Entwicklung begrenzen.

## Inkremente

```text
B00 -> B01 -> B02 -> B03 -> Draft-PR -> STOP
```

## Commitnamen

```text
B00 Import original Alarmcast baseline
B01 Add reproducible Python 3.12 CI
B02 Add architecture and repository guards
B03 Add atomic versioned legacy configuration
```

Jeder Commit enthaelt ausschliesslich sein Inkrement.

## Verbindliche Detailauftraege

- `tasks/increments/B00-import-baseline.md`
- `tasks/increments/B01-development-ci.md`
- `tasks/increments/B02-architecture-guards.md`
- `tasks/increments/B03-config-persistence.md`

## Gemeinsame Nicht-Ziele

- keine Messaging-Funktion,
- kein Serverpaket,
- keine FastAPI-/PostgreSQL-Implementierung,
- keine neue App-Shell,
- keine Alarmcast-Fassade,
- keine Reorganisation der Bestandsmodule,
- kein neues `settings/`-Fachmodul,
- keine neue lokale SQLite-Datenbank,
- keine neuen Entry Points,
- kein Produktinstaller.

## Manueller Gate-Status

Folgende Pruefungen duerfen innerhalb der Etappe als `MANUAL_PENDING` dokumentiert werden:

- Start des bestehenden Hostmodus unter Windows,
- Start des bestehenden Clientmodus unter Windows,
- Erhalt realer Einstellungen nach B03.

Sie blockieren die autonome Fortsetzung nicht, bleiben aber im Draft-PR sichtbar.

## Stage-Bericht

Codex legt nach B00 an:

```text
docs/stage-reports/STAGE-01.md
```

Pro Inkrement wird angehaengt:

```text
## <ID>
Status: AUTO_GREEN | MANUAL_PENDING
Commit: <SHA>
Geaenderte Dateien: <Liste>
Tests: <Befehle und Ergebnisse>
Manuell: <DONE/MANUAL_PENDING>
Abweichungen: <keine oder konkret>
```

## Harte Stop-Bedingungen

Zusaetzlich zu `AGENTS.md` sofort stoppen bei:

- ZIP-Inhalt stimmt nicht mit der verifizierten Datei ueberein,
- echte Secrets oder produktive Konfiguration gefunden,
- Baseline erfordert Produktcodekorrektur,
- CI kann nur durch neue nicht freigegebene Tools hergestellt werden,
- Architekturguard benoetigt eine Produktcode-Reorganisation,
- Konfigurationsmigration kann alte Werte nicht verlustfrei erhalten,
- bestehende `host.json`, `client.json` oder `mode.txt` Bedeutung ist unklar.

## Etappen-Green-Gate

- vier getrennte Inkrementcommits,
- komplette automatisierte Tests gruen,
- Architekturguards besitzen positive und absichtlich negative Fixtures,
- Originalcode ist nachvollziehbar dokumentiert,
- Bootstrap-ZIP und Uploadhinweis sind entfernt,
- keine spaetere Zielstruktur wurde vorsorglich angelegt,
- Draft-PR gegen `main`, danach STOP.
