# Aktiver Codex-Task

## Status

`READY`

## Vorgesehenes Inkrement

`B02 – Architektur- und Scope-Guards`

Vollstaendige Anweisung:

- `tasks/increments/B02-architecture-scope-guards.md`

## Freigabe

B01 wurde nach bestaetigtem Review, gruenem Windows-/Python-3.12-CI-Lauf und Green Gate in `main` gemergt.

B02 darf jetzt ausgefuehrt werden. Fuer die Guards ist keine neue externe Abhaengigkeit freigegeben; Standardbibliothek und die bereits vorhandene Testumgebung sind zu verwenden.

Die verbindlichen Regeln umfassen die bestehenden Importgrenzen von `core`, `host` und `client`, den einzigen freigegebenen Python-Entry-Point sowie den Schutz vor lokalen Konfigurationsdateien, offensichtlichen Geheimnissen und privaten Produktivadressen.

## Startprompt

```text
Arbeite im aktuell geoeffneten Repository auf dem Branch agent/b02-architecture-scope-guards.

Lies zuerst AGENTS.md und danach alle dort vorgeschriebenen Dokumente in der festgelegten Reihenfolge.
Bearbeite ausschliesslich den in tasks/ACTIVE_TASK.md freigegebenen Task B02.
Fuehre B02 vollstaendig und selbststaendig bis zum Green Gate aus.
Beginne keine spaeteren Roadmap-Punkte.
Erfuelle alle Tests, Akzeptanzkriterien und Stop-Bedingungen.
Committe und pushe die vollstaendige Umsetzung.
Oeffne danach einen Draft-Pull-Request ueber gh oder den vorhandenen GitHub-Connector und beende den Task.
```

Codex darf ausschliesslich den freigegebenen Task B02 bearbeiten.
