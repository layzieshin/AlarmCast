# AGENTS.md

Verbindliche Arbeitsanweisung fuer **alle** schreibenden Coding-Agents in diesem Repository, insbesondere Codex, Cursor Agent/Composer und vergleichbare autonome Werkzeuge.

Die Regeln gelten repositoryweit. Untergeordnete `AGENTS.md` duerfen sie nur verschaerfen, niemals lockern.

## 1. Autoritaetsreihenfolge

Bei Widerspruechen gilt strikt:

1. `docs/specification-1.0.md` – freigegebene fachliche Anforderungen,
2. `docs/domain-model.md` – kanonische Entitaeten, Beziehungen, Tabellen und Invarianten,
3. `docs/target-architecture.md` – kanonischer Stack, Module, Entry Points und Abhaengigkeiten,
4. `docs/implementation-roadmap.md` – Reihenfolge und Scope der Inkremente,
5. `docs/test-strategy.md` und `docs/definition-of-done.md`,
6. `tasks/ACTIVE_STAGE.md` und die dort referenzierten Inkrementdateien,
7. bestehender Code.

Bestehender Code ist **keine** Erlaubnis, von einer hoeher priorisierten Vorgabe abzuweichen. Bei einem echten Widerspruch: stoppen, Fundstellen nennen, keine eigene Aufloesung erfinden.

## 2. Arbeitsmodus: autonome Etappe, keine autonome Gesamtentwicklung

- Es darf nur die in `tasks/ACTIVE_STAGE.md` genannte Etappe bearbeitet werden.
- Innerhalb dieser Etappe werden Inkremente exakt in der dort angegebenen Reihenfolge ausgefuehrt.
- Nach einem vollstaendig gruenen automatischen Gate darf der Agent selbststaendig zum naechsten Inkrement **derselben Etappe** wechseln.
- Nach dem letzten Inkrement der Etappe wird ein Draft-PR erstellt und der Lauf beendet.
- Der Agent darf niemals selbststaendig die naechste Etappe aktivieren, den PR mergen oder nach `main` pushen.
- Pro Inkrement entsteht genau ein nachvollziehbarer Commit. Keine Sammelcommits fuer mehrere Inkremente.
- Cursor und Codex duerfen nicht parallel am selben Branch oder Working Tree schreiben.

## 3. Verbindliche Lesereihenfolge vor jedem Lauf

1. `AGENTS.md`
2. `docs/specification-1.0.md`
3. `docs/domain-model.md`
4. `docs/target-architecture.md`
5. `docs/implementation-roadmap.md`
6. `docs/test-strategy.md`
7. `docs/definition-of-done.md`
8. `tasks/ACTIVE_STAGE.md`
9. die dort referenzierte Etappendatei
10. die aktuelle Inkrementdatei
11. vorhandene ADRs unter `docs/decisions/`

Vor dem ersten Edit muss der Agent die relevanten vorhandenen Dateien, Symbole und Tests suchen. Es ist verboten, einen neuen Typ, Service, Entry Point oder Speicherort anzulegen, bevor nach vorhandenen und semantisch aehnlichen Strukturen gesucht wurde.

Mindestpruefung:

```text
git status --short
git branch --show-current
rg -n "<relevanter Begriff|Symbol|Synonym>" src tests docs
find src tests -maxdepth 5 -type f
```

## 4. Branch- und Git-Sicherheit

- Nur auf dem in `tasks/ACTIVE_STAGE.md` genannten Branch arbeiten.
- Bei abweichendem Branch: stoppen.
- Vor Beginn muss `git status --short` sauber sein, abgesehen von explizit als Stage-Input genannten Dateien.
- Verboten: `git reset --hard`, `git clean -fd`, Force-Push, Rebase auf fremde Commits, Aenderungen an `main`.
- Keine fremden Aenderungen ueberschreiben, stashen oder „aufräumen“.
- Vor jedem Inkrementcommit: `git diff --name-only` und `git diff` vollstaendig pruefen.

## 5. Kanonische Struktur – nicht neu erfinden

Die einzig erlaubten Top-Level-Produktpakete sind:

```text
src/alarmcast/          # Windows-Desktop-App und bestehender Alarmcast-Code
src/alarmcast_server/   # zentraler Server
```

Die einzig erlaubten Produkt-Entry-Points sind:

```text
python -m alarmcast
python -m alarmcast_server
```

- Desktop: `src/alarmcast/__main__.py` delegiert an den einzigen Desktop-Composition-Root.
- Server: `src/alarmcast_server/__main__.py` delegiert an den einzigen Server-Composition-Root.
- Keine weiteren `main.py`, `run.py`, `launcher.py`, `bootstrap.py`, Konsolenskripte oder alternative App-Fabriken anlegen, ausser das aktive Inkrement nennt den exakten Pfad.
- Bestehende `--host`- und `--client`-Starts bleiben Kompatibilitaetswege innerhalb des Desktop-Entry-Points; sie werden nicht als neue Anwendungen dupliziert.

Verbotene Auffangstrukturen:

```text
utils.py
helpers.py
common.py
shared.py
base.py
manager.py
managers/
services/        # als generischer Sammelordner
repositories/    # als generischer Sammelordner
models/          # als projektweiter Sammelordner
schemas/         # parallel zu contracts.py
dto.py           # parallel zu contracts.py
service_locator.py
global event bus
```

Gemeinsam nutzbare Logik wird dem fachlich verantwortlichen Modul zugeordnet. Ist kein Owner eindeutig, ist das eine Stop-Bedingung – kein Anlass fuer `utils` oder `common`.

## 6. Exakte Dateibedeutung innerhalb eines Fachmoduls

Soweit ein Inkrement ein neues Fachmodul einfuehrt, gelten ausschliesslich diese Rollen:

```text
<module>/api.py          # einzige oeffentliche programmatische Fassade
<module>/contracts.py    # oeffentliche Commands, Queries, Events und DTOs
<module>/domain.py       # interne fachliche Entitaeten und Invarianten
<module>/ports.py        # interne Protocols fuer Infrastrukturabhaengigkeiten
<module>/service.py      # interne Use-Case-Orchestrierung, falls tatsaechlich benoetigt
```

- Kein paralleles `schemas.py`, `types.py`, `entities.py`, `interfaces.py` oder zweites Contract-Modul.
- `__init__.py` bleibt leer oder enthaelt nur Paketdokumentation. Keine Wildcard-Re-Exports und keine alternative oeffentliche API.
- SQLAlchemy-Modelle verbleiben ausschliesslich unter `alarmcast_server/infrastructure/database/`.
- Transportmodelle werden nicht zu Domainobjekten und ORM-Modelle werden nicht aus Repositories herausgegeben.
- Mapping erfolgt explizit im jeweiligen Adapter. Kein generischer Auto-Mapper.

## 7. Abhaengigkeitsrichtung

Erlaubt:

```text
UI/Transport -> api.py/contracts.py -> service.py/domain.py -> ports.py
Infrastrukturadapter -> ports.py/domain.py
Composition Root -> alle konkreten Implementierungen
```

Verboten:

- Domain importiert Qt, FastAPI, SQLAlchemy, Alembic, Socket-, Audio- oder Dateisystemimplementierungen.
- GUI greift direkt auf Datenbank, SQLite, REST-Details, WebSocket-Objekte oder Alarmcast-Low-Level-Sockets zu.
- Messaging greift direkt auf `host/`, `client/`, Audio-Capture oder Alarmcast-Protokoll zu.
- Alarmcast schreibt direkt in Messaging-Tabellen oder erzeugt Chatnachrichten ausserhalb einer expliziten oeffentlichen Messaging-API.
- Fachmodule importieren interne Dateien anderer Fachmodule.
- Servermodule verwenden ORM-Klassen eines anderen Fachmoduls als oeffentlichen Vertrag.
- Zyklische Importe, Laufzeit-Importtricks, `sys.path`-Manipulation oder dynamisches `getattr` zur Umgehung von Grenzen.

## 8. Eine Quelle der Wahrheit

Folgende Dinge duerfen jeweils nur einmal definiert werden:

- Enums und Statuswerte,
- Rollen und Capabilities,
- Tabellen- und Spaltennamen,
- API-Pfade und WebSocket-Eventtypen,
- Audioformatkonstanten,
- Konfigurationsschluessel und Schema-Versionen,
- Zeit- und ID-Erzeugung,
- Berechtigungsregeln.

Vor einer neuen Definition muss nach der kanonischen Definition gesucht werden. Keine lokalen Kopien von Enums, String-Literalen oder Permission-Matrizen in UI, Tests oder Adaptern.

`docs/domain-model.md` ist die Namensquelle fuer Entitaeten und Persistenztabellen. Abweichende Synonyme wie `Account` statt `User`, `ChatRoom` statt `Conversation` oder `Machine` statt `Device` sind verboten, sofern kein freigegebenes Migrationsinkrement sie explizit einfuehrt.

## 9. Datenmodell- und Persistenzregeln

- Keine neue Entitaet, Tabelle, Spalte, Relation oder Enum ausserhalb von `docs/domain-model.md` oder der aktiven Inkrementdatei.
- Keine generischen JSON-/JSONB-Felder fuer Kerndomaene, Berechtigungen, Nachrichtenstatus oder Beziehungen.
- Keine polymorphen „object_type/object_id“-Universaltabellen, wenn das kanonische Modell konkrete Fremdschluessel vorgibt.
- Keine generischen CRUD-Repositories oder `BaseRepository`.
- Jede DB-Aenderung erfolgt ausschliesslich ueber Alembic-Migrationen.
- Keine Schemaerzeugung per `create_all()` im Produktivstart.
- Keine direkte SQL-Ausfuehrung ausser im zuständigen Datenbankadapter oder in Migrationen.
- PostgreSQL ist serverseitige Wahrheit; SQLite ist ausschliesslich lokaler Clientcache und Offline-Queue.
- Der Clientcache darf keine serverseitigen Berechtigungen ersetzen.

Nachrichten sind append-only:

- kein Update des Nachrichtentextes,
- kein Delete-Pfad,
- kein Soft-Delete-Feld,
- keine `edited_at`, `deleted_at` oder `is_deleted`-Spalten,
- Status, Lesen, Bestaetigungen und Reaktionen sind getrennte Datensaetze.

## 10. Fester Technologie-Stack

Der Stack ist in `docs/target-architecture.md` und ADR `docs/decisions/0010-fixed-technology-stack.md` festgelegt.

Ohne ausdrueckliches Inkrement verboten:

- Wechsel von setuptools/pip zu Poetry, PDM, Hatch oder uv,
- anderes GUI-Framework als PySide6,
- anderes Serverframework als FastAPI/Uvicorn,
- andere Serverdatenbank als PostgreSQL,
- anderes ORM/Migrationswerkzeug als SQLAlchemy 2/Alembic,
- Redis, RabbitMQ, Kafka, Celery oder sonstiger Broker,
- Elasticsearch/OpenSearch,
- Electron, Web-Frontend oder zweiter Clientstack,
- Docker als Produktionsvoraussetzung,
- `requests`, `aiohttp`, `websocket-client` oder ein zweiter Desktop-Netzwerkstack; Desktop nutzt QtNetwork/QWebSocket,
- JWT; Sitzungen verwenden opaque serverseitige Tokens.

Eine neue Top-Level-Abhaengigkeit ist immer eine Stop-Bedingung, sofern sie nicht im aktiven Inkrement mit exaktem Paketnamen freigegeben ist.

## 11. Typische autonome Agentenfehler – ausdruecklich verboten

- Kein „vorsorgliches“ Scaffolding fuer spaetere Inkremente.
- Keine leeren Module, Platzhalterklassen, `pass`, `TODO`, `NotImplementedError` oder Fake-Implementierungen, sofern der Task sie nicht ausdruecklich verlangt.
- Keine zweite Implementierung neben der bestehenden „zur Sicherheit“.
- Keine Compatibility-Wrapper oder Re-Exports, nur um Imports schnell gruen zu machen.
- Keine breiten `except Exception` mit stillen Defaults.
- Keine Ruecksetzung defekter Konfiguration auf Standardwerte ohne sichtbaren Fehler und getestete Recovery-Regel.
- Keine In-Memory-Ersatzpersistenz im Produktionspfad, wenn PostgreSQL oder SQLite vorgesehen ist.
- Keine Mock-Daten, Demo-Nutzer oder automatische Seed-Daten im Produktivstart.
- Keine hardcodierten Hostnamen, Ports, PSKs, Tokens oder Dateipfade ausser kanonischen Defaultkonstanten.
- Keine Synchronisierung durch `sleep()` oder polling, wenn das kanonische Event-/Heartbeat-Modell vorgesehen ist.
- Keine UI-Logik, die serverseitige Autorisierung ersetzt.
- Keine Tests, die private Implementierungsdetails fixieren, wenn ein oeffentlicher Vertrag pruefbar ist.
- Keine Aenderung bestehender Tests, bevor geklaert ist, ob der Code oder der Test von der Spezifikation abweicht.
- Keine Formatierung oder Umbenennung unbeteiligter Dateien.
- Keine Performance-Optimierung ohne Messung und aktiven Scope.

## 12. Baseline und Tests vor jedem Inkrement

Vor dem ersten Edit eines Inkrements:

```text
git status --short
python --version
ruff check .
ruff format --check .
mypy src
pytest -q
```

Nicht vorhandene Werkzeuge oder echte Plattformgrenzen werden als `NOT RUN` dokumentiert. Ein bereits vorhandener Baseline-Fehler wird nicht nebenbei repariert.

Jede funktionale Aenderung benoetigt passende Tests gemaess Inkrementdatei und `docs/test-strategy.md`.

## 13. Automatisches Green Gate und Fortsetzung

Ein Inkrement ist `AUTO_GREEN`, wenn:

- alle Scopepunkte umgesetzt sind,
- alle expliziten Nicht-Ziele unberuehrt sind,
- taskbezogene Tests gruen sind,
- relevante Regressionstests gruen sind,
- `ruff check .`, `ruff format --check .`, `mypy src` und `pytest -q` gruen sind,
- Architekturtests gruen sind,
- keine neue nicht freigegebene Abhaengigkeit entstanden ist,
- Diff und Dateiliste ausschliesslich erklaerte Aenderungen enthalten,
- ein Checkpoint-Bericht erstellt wurde.

Dann:

1. exakt einen Inkrementcommit erstellen,
2. Checkpoint in der aktiven Etappendatei dokumentieren,
3. zum naechsten Inkrement derselben Etappe wechseln.

Ein manueller Windows-/Audio-/Multi-Monitor-Test darf als `MANUAL_PENDING` markiert werden, wenn die Etappendatei ausdruecklich erlaubt, dass er kein Blocker fuer das naechste Inkrement ist. Er bleibt zwingendes PR-/Release-Gate.

## 14. Stop-Bedingungen

Sofort stoppen und keine weiteren Dateien aendern, wenn:

- Branch, Stage-Input oder Pruefsumme nicht stimmen,
- Spezifikation, Datenmodell, Zielarchitektur und Task nicht eindeutig zusammenpassen,
- ein benoetigter Typ, Tabellenname, API-Pfad oder Owner nicht kanonisch festgelegt ist,
- eine neue externe Abhaengigkeit noetig erscheint,
- ein oeffentlicher Vertrag ausserhalb des aktuellen Inkrements geaendert werden muesste,
- das Alarmcast-Protokoll oder Audioformat geaendert werden muesste,
- bestehendes Alarmcast-Verhalten nicht erhalten werden kann,
- eine Migration Daten verlieren koennte,
- ein Sicherheits-/Datenschutz-Trade-off entschieden werden muesste,
- ein Test nur durch Abschwaechung oder Loeschung gruen wuerde,
- derselbe Gate-Fehler nach zwei zielgerichteten Reparaturversuchen weiterhin besteht,
- ein spaeteres Inkrement vorgezogen werden muesste,
- mehr als die in der Inkrementdatei erwarteten Produktmodule betroffen waeren.

Der Stop-Bericht nennt: beobachtetes Problem, betroffene Dateien, bereits ausgefuehrte Versuche, kleinste konkrete Entscheidungsfrage.

## 15. Stage-Abschluss und PR

Am Ende der aktiven Etappe:

- keine naechste Etappe aktivieren,
- keine Roadmapstatus ausserhalb der aktiven Etappe veraendern,
- Draft-PR gegen den in `tasks/ACTIVE_STAGE.md` genannten Zielbranch erstellen,
- alle Inkrementcommits beibehalten,
- offene manuelle Gates sichtbar auffuehren,
- Agentenlauf beenden.

PR-/Abschlussbericht:

```text
Stage:                 <ID und Titel>
Inkremente:            <IDs, Commit-SHAs, AUTO_GREEN/MANUAL_PENDING>
Geaendert:             <Dateien/Module und Zweck>
Bewusst unveraendert:  <wichtige Grenzen>
Tests:                 <Befehl und Ergebnis>
Manuelle Gates:        <DONE oder MANUAL_PENDING>
Datenmigrationen:      <Migrationen und Rueckweg>
Abhaengigkeiten:       <keine oder exakt freigegebene>
Risiken:               <Restrisiken>
Spezifikationsbezug:   <Abschnitte>
Naechster Schritt:     Review; keine autonome Folgeetappe
```
