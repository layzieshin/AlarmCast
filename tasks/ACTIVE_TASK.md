# Aktiver Codex-Task

## Status

`BLOCKED`

## Vorgesehenes Inkrement

`B00 – Originalen Alarmcast-Bestand importieren`

Vollstaendige Anweisung:

- `tasks/increments/B00-import-baseline.md`

## Blocker

Die originale Projektdatei muss nach Merge dieses Planungs-PRs als

```text
bootstrap/alarmcast-baseline.zip
```

auf einem neuen Arbeitsbranch bereitgestellt werden.

Erwartete SHA-256-Pruefsumme:

```text
879e12eacbc7102b45952069c5582d456b55d4cfa12d3f55ea9e77e77334b99e
```

Erwartete Archivgroesse:

```text
80584 Bytes
```

Der Task darf erst auf `READY` gesetzt werden, nachdem Pfad, Dateigroesse und SHA-256 im Repository geprueft wurden.

## Startprompt nach Freigabe

```text
Arbeite im Repository layzieshin/AlarmCast.

Lies zuerst AGENTS.md und danach alle dort vorgeschriebenen Dokumente.
Bearbeite ausschliesslich den in tasks/ACTIVE_TASK.md freigegebenen Task.
Beginne keine spaeteren Roadmap-Punkte.
Erfuelle alle Tests, Akzeptanzkriterien und Stop-Bedingungen.
Oeffne danach einen Draft-Pull-Request und beende den Task.
```

Solange der Status `BLOCKED` ist, darf Codex keine Dateien aendern.
