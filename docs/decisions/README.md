# Architekturentscheidungen (ADRs)

Hier werden bedeutsame technische Entscheidungen festgehalten. Jeder ADR ist nummeriert, hat einen Status und folgt diesem Schema:

```text
# 000X — Titel

## Status
proposed | accepted | superseded | deprecated

## Kontext
Warum stellt sich diese Frage? Welche Constraints, Erfahrungen, Vorgaben?

## Entscheidung
Was wurde entschieden, konkret?

## Konsequenzen
Was folgt daraus — positive wie negative?

## Alternativen
Was wurde geprueft und verworfen, warum?
```

Wird eine bestehende Entscheidung ersetzt: alten ADR auf `superseded` setzen und im neuen ADR auf den alten verweisen. Niemals einen alten ADR loeschen.

## Index

| Nr. | Titel | Status |
|---|---|---|
| [0001](0001-initial-architecture.md) | Initiale Architektur (Stack, Single-Binary, Protokoll, Discovery, Security) | accepted |
