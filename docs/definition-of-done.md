# Definition of Done

Ein Inkrement ist nicht fertig, sobald der Code „funktioniert“, sondern erst nach bestaetigtem Green Gate.

## 1. Scope

- Der aktive Task ist vollstaendig umgesetzt.
- Kein spaeteres Roadmap-Inkrement wurde begonnen oder vorbereitet.
- Keine sachfremden Refactorings, Formatierungswellen oder Abhaengigkeitsupdates.
- Alle im Task genannten Nicht-Ziele sind unberuehrt.

## 2. Fachliches Verhalten

- Alle Akzeptanzkriterien sind beobachtbar erfuellt.
- Fehler- und Randfaelle sind behandelt.
- Bestehende Alarmcast-Funktionen bleiben erhalten.
- Keine Abweichung von Spezifikation 1.0 ohne neue Freigabe.

## 3. Architektur

- Modul- und Importgrenzen sind eingehalten.
- Keine neue oeffentliche API ausserhalb des freigegebenen Taskumfangs.
- Keine direkten GUI-Zugriffe auf Datenbank, Dateispeicher oder Low-Level-Sockets.
- Keine alternative Composition Root oder erfundener Entry Point.
- Neue Architekturentscheidung ist als freigegebener ADR dokumentiert.

## 4. Daten und Sicherheit

- Keine Secrets, lokalen Konfigurationen oder echten internen Daten committed.
- Passwoerter und PSKs werden nicht in Logs ausgegeben.
- Technische Logs enthalten keine vollstaendigen Chattexte.
- Berechtigungen werden server- beziehungsweise fachseitig geprueft, nicht nur in der UI.
- Migrationen sind idempotent und gegen Datenverlust getestet.

## 5. Tests

Mindestens:

```text
ruff check .
ruff format --check .
mypy src
pytest -q
```

Zusaetzlich alle taskbezogenen:

- Unit-Tests,
- Integrationstests,
- Architekturtests,
- Migrations-Tests,
- Windows-Smoke-Tests,
- manuelle Mehrclient-/Multi-Monitor-Tests.

Nicht ausgefuehrte Tests werden als `NOT RUN` mit Grund dokumentiert und duerfen nicht als bestanden gelten.

## 6. Dokumentation

- Oeffentliche Verträge und ungewoehnliche Invarianten sind dokumentiert.
- Roadmap- oder ADR-Verweise sind korrekt.
- Manuelle Testschritte sind aktualisiert, wenn sich Bedienung oder Betrieb geaendert haben.
- Keine veralteten oder widerspruechlichen Anweisungen bleiben bewusst liegen.

## 7. Diff-Qualitaet

Vor Abschluss pruefen:

```text
git status --short
git diff --name-only
git diff
```

- Jede geaenderte Datei ist durch den Task erklaert.
- Keine Buildartefakte, Logs, Caches oder lokale Settings.
- Keine versehentliche Loeschung oder Umbenennung.
- Keine auskommentierten Altimplementierungen ohne ausdruecklichen Grund.

## 8. Pull Request

- Draft-PR pro Inkrement.
- Titel nennt Task-ID und fachliches Ziel.
- PR-Text verwendet das Abschlussbericht-Schema aus `AGENTS.md`.
- Bekannte Restrisiken und manuelle Pruefungen sind sichtbar.
- Der PR startet keinen Folgepunkt.

## 9. Abschluss und Freigabe

Codex setzt ein Inkrement nicht selbst auf `DONE` und nicht den naechsten Punkt auf `READY`.

Nach Review:

1. Reviewer bestaetigt Green Gate,
2. PR wird gemergt,
3. Roadmapstatus wird separat aktualisiert,
4. naechster Task wird ausdruecklich aktiviert.
