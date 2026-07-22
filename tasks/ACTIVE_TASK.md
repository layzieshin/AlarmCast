# Aktiver Codex-Task

## Status

`READY`

## Vorgesehenes Inkrement

`B03 – Atomare, schema-versionierte Bestandskonfiguration`

Vollstaendige Anweisung:

- `tasks/increments/B03-atomic-versioned-config.md`

## Freigabe

B02 wurde nach Review, geschaerfter RFC1918-Pruefung, 48 gruenen Architekturtests und erfolgreichem Windows-/Python-3.12-CI-Lauf in `main` gemergt.

B03 darf jetzt ausgefuehrt werden. Es stabilisiert ausschliesslich die bestehenden getrennten Dateien `host.json` und `client.json` durch Schema-Version 1, atomare Schreibvorgaenge, Migration, Sicherung und kontrollierte Wiederherstellung.

Keine gemeinsame `app.json`, keine Migration von `mode.txt`, keine neue Abhaengigkeit und keine UI-, Netzwerk-, Audio- oder Entry-Point-Aenderung sind freigegeben.

## Startprompt

```text
Arbeite im aktuell geoeffneten Repository auf dem Branch agent/b03-atomic-versioned-config.

Lies zuerst AGENTS.md und danach alle dort vorgeschriebenen Dokumente in der festgelegten Reihenfolge.
Bearbeite ausschliesslich den in tasks/ACTIVE_TASK.md freigegebenen Task B03.
Fuehre B03 vollstaendig und selbststaendig bis zum Green Gate aus.
Beginne keine spaeteren Roadmap-Punkte.
Erfuelle alle Tests, den nicht destruktiven Windows-Neustart-Smoke, die Akzeptanzkriterien und Stop-Bedingungen.
Committe und pushe die vollstaendige Umsetzung.
Oeffne danach einen Draft-Pull-Request ueber gh oder den vorhandenen GitHub-Connector und pruefe GitHub Actions bis zum Ergebnis.
```

Codex darf ausschliesslich den freigegebenen Task B03 bearbeiten.
