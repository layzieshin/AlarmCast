# Aktive Codex-Etappe

## Status

`READY`

## Etappe

`STAGE-01 – Baseline und Schutzschicht`

Vollstaendige Etappenanweisung:

- `tasks/stages/STAGE-01-baseline-and-guards.md`

## Branch und Ziel

```text
Arbeitsbranch: agent/B00-import-baseline
Zielbranch:    main
```

Codex arbeitet ausschliesslich auf diesem Branch. Kein neuer Arbeitsbranch innerhalb der Etappe.

## Erlaubte Inkremente in exakter Reihenfolge

1. `B00 – Originalen Alarmcast-Bestand importieren`
2. `B01 – Python-3.12-Entwicklungsumgebung und CI`
3. `B02 – Architektur- und Repository-Guards`
4. `B03 – Atomare und versionierte Bestandskonfiguration`

Kein anderes Roadmap-Inkrement ist freigegeben.

## Verifizierter Stage-Input

```text
Pfad:        bootstrap/alarmcast-baseline.zip
SHA-256:     879e12eacbc7102b45952069c5582d456b55d4cfa12d3f55ea9e77e77334b99e
Groesse:     80584 Bytes
Git-Blob:    0d544aded3af0513d344273db5f0e2fa564cd460
```

## Autonome Fortsetzung

Nach jedem Inkrement:

1. alle automatischen Gates ausfuehren,
2. bei `AUTO_GREEN` genau einen Commit mit dem vorgegebenen Namen erstellen,
3. Checkpoint in `docs/stage-reports/STAGE-01.md` ergaenzen,
4. direkt zum naechsten Inkrement dieser Liste wechseln.

Manuelle Windows-Pruefungen aus STAGE-01 duerfen als `MANUAL_PENDING` dokumentiert werden und blockieren die Fortsetzung nicht, solange alle automatischen Tests gruen sind.

## Etappenende

Nach B03:

- Status dieses Dokuments auf `REVIEW` setzen,
- Draft-PR gegen `main` erstellen,
- keine Folgeetappe aktivieren,
- Agentenlauf beenden.
