# Aktiver Codex-Task

## Status

`READY`

## Vorgesehenes Inkrement

`A01 – Alarmcast-Vertragsmodell`

Vollstaendige Anweisung:

- `tasks/increments/A01-alarmcast-contract-model.md`

## Verbindliche Freigabe

B03 wurde nach bestaetigtem Review, 48 gruenen Konfigurationstests, erfolgreichem nicht destruktivem Windows-Neustart-Smoke und gruenem Windows-/Python-3.12-CI-Lauf in `main` gemergt. B03 ist damit `DONE`.

A01 ist das einzige zur Umsetzung freigegebene Inkrement und besitzt ab diesem Branch den verbindlichen Status `READY`.

Die noch auf `PLANNED` stehende A01-Zeile in `docs/implementation-roadmap.md` ist eine bekannte vorbereitende Statusinkonsistenz und keine fachliche Sperre. Nach erfolgreicher Baseline muss Codex als erste A01-Aenderung ausschliesslich folgende Roadmapkorrekturen vornehmen:

- B03: `REVIEW` -> `DONE`
- A01: `PLANNED` -> `IN_PROGRESS`

Im Abschlussstand des Inkrements wird A01 auf `REVIEW` gesetzt. Keine andere Roadmapzeile darf geaendert werden.

A01 fuehrt ausschliesslich unveraenderliche, von Qt, Sockets, Threads und Audioimplementierungen freie Contracts fuer die bestehenden Alarmcast-Zustaende ein.

Keine Fassade, keine Adapter, keine API-Protocols, keine Event-Bus-Integration und keine Aenderung an `core`, `host`, `client`, UI, Protokoll, Konfiguration, Entry Points oder Buildlogik sind freigegeben.

## Startprompt

```text
Arbeite im aktuell geoeffneten Repository auf dem Branch agent/a01-alarmcast-contract-model.

Lies zuerst AGENTS.md und danach alle dort vorgeschriebenen Dokumente in der festgelegten Reihenfolge.
Bearbeite ausschliesslich den in tasks/ACTIVE_TASK.md freigegebenen Task A01.
Fuehre zuerst die unveraenderte Baseline aus. Korrigiere danach als erste A01-Aenderung ausschliesslich die in ACTIVE_TASK.md genannten beiden Roadmapstatus.
Fuehre A01 vollstaendig und selbststaendig bis zum Green Gate aus.
Beginne keine spaeteren Roadmap-Punkte.
Erfuelle alle Tests, Akzeptanzkriterien und Stop-Bedingungen.
Committe und pushe die vollstaendige Umsetzung.
Oeffne danach einen Draft-Pull-Request ueber gh oder den vorhandenen GitHub-Connector und pruefe GitHub Actions bis zum Ergebnis.
```

Codex darf ausschliesslich den freigegebenen Task A01 bearbeiten.
