# AGENTS.md

Zentrale, verbindliche Arbeitsanweisung fuer alle Coding-Agents in diesem Repository.

## 1. Arbeitsmodus

- Es wird immer genau **ein** Arbeitspaket bearbeitet.
- Das einzige freigegebene Arbeitspaket steht in `tasks/ACTIVE_TASK.md`.
- Spaetere Roadmap-Punkte duerfen weder begonnen noch vorbereitet werden.
- Keine selbst gewaehlten Folgearbeiten, Refactorings, Aufraeumarbeiten oder UX-Verbesserungen.
- Codex, Cursor Composer oder andere schreibende Agents duerfen nicht parallel am selben Working Tree arbeiten.
- Vor jedem Lauf muss `git status --short` sauber sein. Bei fremden oder unklaren Aenderungen: stoppen.

## 2. Verbindliche Lesereihenfolge

Vor jeder Aenderung lesen:

1. `AGENTS.md`
2. `docs/specification-1.0.md`
3. `docs/target-architecture.md`
4. `docs/implementation-roadmap.md`
5. `docs/test-strategy.md`
6. `docs/definition-of-done.md`
7. `tasks/ACTIVE_TASK.md`
8. die dort referenzierte Inkrementdatei

Die freigegebene Spezifikation hat Vorrang vor Roadmap, Tasktext und bestehendem Code. Bei einem echten Widerspruch nicht raten, sondern stoppen und den Widerspruch benennen.

## 3. Baseline vor Aenderung

Vor dem ersten Edit eines Tasks:

```text
git status --short
python --version
ruff check .
ruff format --check .
mypy src
pytest -q
```

Nicht vorhandene Tools oder nicht installierbare Plattformabhaengigkeiten werden ehrlich als `NOT RUN` dokumentiert. Ein vorhandener Baseline-Fehler darf nicht stillschweigend dem aktuellen Task zugerechnet oder nebenbei repariert werden.

## 4. Scope-Regeln

- Nur Dateien aendern, die fuer den aktiven Task erforderlich sind.
- Bestehende Alarmcast-Funktionalitaet darf nicht stillschweigend entfernt oder veraendert werden.
- Keine neue Top-Level-Abhaengigkeit ohne ausdruecklich freigegebenen ADR oder menschliche Zustimmung.
- Keine neuen Entry Points, Alternativ-APIs, Wrapper oder Re-Exports erfinden, wenn bereits ein vorgesehener Zugang existiert.
- Keine Secrets, echten PSKs, Tokens, Kennwoerter, internen IP-Adressen oder lokalen Konfigurationsdateien committen.
- Keine Chattexte in technische Logs schreiben.
- Keine Tests abschwaechen, loeschen oder umgehen, um ein Green Gate zu erreichen.

## 5. Architekturgrenzen

Die Zielarchitektur arbeitet mit oeffentlichen Modulgrenzen:

- oeffentliche Nutzung eines Fachmoduls nur ueber dessen `api.py`, `contracts.py` oder explizit dokumentierte Fassade,
- keine direkten Quermodulimporte aus internen Implementierungsdateien,
- GUI greift nicht direkt auf Datenbank, Dateispeicher oder Low-Level-Sockets zu,
- Messaging greift nicht direkt auf Alarmcast-Sockets zu,
- Alarmcast schreibt keine Chatnachrichten direkt in die Messaging-Persistenz,
- Administration erhaelt keine inhaltliche Chat-API,
- Nachrichten werden append-only behandelt.

Bestandsmodule `core`, `host` und `client` bleiben bis zu ihrer geplanten Kapselung geschuetzt. Importgrenzen duerfen nur im dafuer vorgesehenen Inkrement angepasst werden.

## 6. Testpflicht

Jede funktionale Aenderung benoetigt passende automatisierte Tests. Je nach Task koennen zusaetzlich erforderlich sein:

- Unit-Tests,
- Integrations-Tests,
- Architekturtests,
- Migrations-Tests,
- Windows-Smoke-Tests,
- manueller Mehrrechner- oder Multi-Monitor-Test.

Tests muessen beobachtbare Anforderungen pruefen und nicht lediglich Implementierungsdetails spiegeln.

## 7. Green Gate

Ein Task ist nur abgeschlossen, wenn alle in seiner Inkrementdatei genannten Kriterien sowie mindestens folgende Punkte erfuellt sind:

- Scope vollstaendig umgesetzt,
- Nicht-Ziele unberuehrt,
- neue und bestehende relevante Tests gruen,
- `ruff check .` gruen,
- `ruff format --check .` gruen,
- `mypy src` gruen oder im Task enger begruendet,
- `pytest -q` gruen,
- erforderliche manuelle Tests dokumentiert,
- keine unerklaerten Dateien im Diff,
- Abschlussbericht erstellt.

Codex darf nicht selbststaendig den naechsten Roadmap-Punkt beginnen. Nach dem Green Gate endet der Task mit einem Draft-PR.

## 8. Stop-Bedingungen

Sofort stoppen und eine konkrete Frage stellen, wenn:

- Spezifikation oder aktiver Task mehrdeutig sind,
- eine neue externe Abhaengigkeit erforderlich erscheint,
- ein Protokoll, Datenmodell oder oeffentlicher Vertrag ausserhalb des Tasks geaendert werden muesste,
- bestehendes Alarmcast-Verhalten nicht erhalten werden kann,
- ein Baseline-Test bereits fehlschlaegt und die Ursache unklar ist,
- ein sicherheits- oder datenschutzrelevanter Trade-off entschieden werden muesste,
- ein Task nur durch Arbeit an einem spaeteren Inkrement abschliessbar waere.

## 9. Abschlussbericht

Der PR-Text beziehungsweise Abschlussbericht enthaelt:

```text
Task:             <ID und Titel>
Geaendert:        <Dateien und Zweck>
Unveraendert:     <wichtige bewusst nicht angefasste Bereiche>
Tests:            <Befehl, Ergebnis, nicht ausgefuehrte Tests>
Manuell:          <Schritte und Ergebnis oder NOT RUN>
Risiken:          <bekannte Restrisiken>
Spezifikationsbezug: <Abschnitte/Kriterien>
Naechster Schritt: Review, nicht selbststaendig naechstes Inkrement
```
