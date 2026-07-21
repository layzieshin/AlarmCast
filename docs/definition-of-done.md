# Definition of Done

Es gibt zwei Abschlussstufen:

- **Inkrement `AUTO_GREEN`**: Codex darf innerhalb derselben aktiven Etappe autonom fortfahren.
- **Etappe `REVIEW`**: Draft-PR ist vollstaendig und der Agent stoppt.

## 1. Inkrement: Scope

- Das aktuelle Inkrement ist vollstaendig umgesetzt.
- Kein spaeteres Inkrement wurde vorgezogen oder vorsorglich vorbereitet.
- Nur die in der Inkrementdatei erlaubten Produktmodule wurden geaendert.
- Keine sachfremden Refactorings, Formatierungswellen oder Abhaengigkeitsupdates.
- Alle Nicht-Ziele bleiben unberuehrt.

## 2. Fachliches Verhalten

- Alle Akzeptanzkriterien sind beobachtbar erfuellt.
- Fehler- und Randfaelle sind getestet.
- Bestehende Alarmcast-Funktionen bleiben erhalten.
- Keine Abweichung von Spezifikation 1.0 oder `docs/domain-model.md`.

## 3. Architektur und Struktur

- Nur kanonische Modul-, Datei-, Entitaets-, Tabellen- und Enum-Namen.
- Keine parallele API, kein zweiter Entry Point und kein zweiter Composition Root.
- Keine verbotenen Auffangmodule (`utils`, `helpers`, `common`, generische `services/repositories/models/schemas`).
- Keine direkten GUI-Zugriffe auf Datenbank, Dateispeicher oder Low-Level-Sockets.
- Keine neue oeffentliche API ausserhalb des Inkrements.
- Keine neue Architekturentscheidung ohne freigegebenen ADR.
- Architekturtests sind gruen.

## 4. Daten und Sicherheit

- Keine Secrets, lokalen Konfigurationen oder echten internen Daten committed.
- Passwoerter, PSKs und Tokens erscheinen nicht in Logs.
- Technische Logs enthalten keine vollstaendigen Chattexte.
- Server-/Fachautorisierung ist implementiert; UI-Ausblendung ist nur Ergaenzung.
- Migrationen sind idempotent und gegen Datenverlust getestet.
- Keine neue Tabelle/Spalte ausserhalb des kanonischen Domainmodells oder der Inkrementfreigabe.
- Nachrichten bleiben append-only.

## 5. Automatisierte Tests

Mindestens:

```text
ruff check .
ruff format --check .
mypy src
pytest -q
```

Zusaetzlich alle inkrementspezifischen:

- Unit-Tests,
- Adapter-/Komponententests,
- Persistenz-/Migrations-Integrationstests,
- REST-/WebSocket-Integrationstests,
- Architektur-/Repository-Guards.

Ein Test ist nur bestanden, wenn seine Ausgabe im aktuellen Commit gesehen wurde. `NOT RUN` ist kein Gruen, ausser die aktive Etappendatei klassifiziert den Test ausdruecklich als `MANUAL_PENDING`.

## 6. Manuelle Tests

Windows-/Hardwaretests werden mit festen Schritten dokumentiert:

- Umgebung und Windows-Version,
- Commit/Build,
- Schritte,
- erwartetes Ergebnis,
- tatsaechliches Ergebnis,
- Tester und Datum.

Ein als `MANUAL_PENDING` erlaubter Test blockiert nicht die autonome Fortsetzung innerhalb der Etappe, bleibt aber sichtbar im Stage-PR und kann dessen Merge blockieren.

## 7. Diff-Qualitaet

Vor jedem Inkrementcommit:

```text
git status --short
git diff --name-only
git diff
```

- Jede Datei ist durch das Inkrement erklaert.
- Keine Buildartefakte, Logs, Caches oder lokalen Settings.
- Keine versehentliche Loeschung, Umbenennung oder Re-Export-Kette.
- Keine auskommentierte Altimplementierung, TODOs oder Platzhalter.
- Keine unerklaerte Dependency-Aenderung.

## 8. Inkrementcommit

- Genau ein Commit pro Inkrement.
- Commitname entspricht der aktiven Etappendatei.
- Checkpoint enthaelt Tests, betroffene Dateien und Status `AUTO_GREEN` oder `MANUAL_PENDING`.
- Erst danach darf Codex zum naechsten Inkrement derselben Etappe wechseln.

## 9. Etappen-Draft-PR

Nach dem letzten Inkrement:

- alle vorgesehenen Inkrementcommits vorhanden,
- `tasks/ACTIVE_STAGE.md` auf `REVIEW`,
- Stage-Bericht vorhanden,
- Draft-PR gegen den festgelegten Zielbranch,
- offene manuelle Gates, Baselinefehler und Restrisiken sichtbar,
- keine Folgeetappe begonnen.

Codex darf nicht selbst mergen, `main` veraendern oder die naechste Etappe auf `READY` setzen.

## 10. Review und Freigabe

Erst nach menschlichem/zweitem Review:

1. Green Gates und Diff bestaetigen,
2. manuelle Merge-Gates abschliessen oder bewusst akzeptieren,
3. PR mergen,
4. Etappe auf `DONE` setzen,
5. naechste Etappe separat vorbereiten und aktivieren.
