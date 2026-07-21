# Technische Zielarchitektur

**Status:** verbindlich fuer Spezifikation 1.0  
**Aenderungsregel:** Abweichungen benoetigen einen ausdruecklich freigegebenen ADR. Coding-Agents duerfen keine Alternative auf Verdacht einfuehren.

## 1. Migrationsgrundsatz

Die bestehende Alarmcast-Anwendung wird **nicht neu geschrieben**. Der vorhandene funktionsfaehige Code unter `src/alarmcast/core`, `src/alarmcast/host` und `src/alarmcast/client` wird schrittweise hinter stabilen Fassaden gekapselt.

Bis zum dafuer vorgesehenen Inkrement bleiben unveraendert:

- TCP-Frameformat,
- Port- und mDNS-Verhalten,
- Audioformat,
- WASAPI-Loopback,
- Alarmdetektion,
- PSK-Handshake,
- bestehende Host-/Client-Bedienung,
- `python -m alarmcast --host` und `python -m alarmcast --client`.

Kein Big-Bang-Rewrite, keine zweite parallele Alarmcast-Implementierung und kein neues Protokoll.

## 2. Verbindlicher Technologie-Stack

### 2.1 Gemeinsame Grundlagen

- Sprache: Python **3.12**.
- Repository: Monorepo.
- Packaging: bestehendes `pyproject.toml` mit **setuptools** und `pip`.
- Kein Poetry, PDM, Hatch oder uv als alternatives Projekt-/Buildsystem.
- Codequalitaet: `ruff`, `mypy`, `pytest`.
- Zeitwerte: UTC intern; Darstellung lokal am Client.
- IDs: UUIDv4 ueber einen injizierbaren ID-Provider; keine sprechenden Primärschluessel.

### 2.2 Windows-Desktop-App

- GUI und Tray: **PySide6**.
- Serverkommunikation vom Desktop:
  - HTTPS/REST ueber `PySide6.QtNetwork.QNetworkAccessManager`,
  - WSS ueber `PySide6.QtWebSockets.QWebSocket`.
- Kein zweiter Desktop-HTTP-/WebSocket-Stack (`requests`, `httpx`, `aiohttp`, `websockets`, `websocket-client`).
- Lokaler Cache und Offline-Queue: Python-stdlib `sqlite3`; keine Server-ORM-Klassen im Desktop.
- Alarmcast-Audio: bestehend `soundcard`, `sounddevice`, `numpy==1.26.4`.
- Discovery: bestehend `zeroconf`.
- Lokale Windows-Geheimnisse: Windows DPAPI ueber den spaeter freigegebenen Windows-Adapter; keine selbst entwickelte Verschluesselung.
- Build: PyInstaller.
- Installer: Inno Setup in der Betriebsphase.
- Kein Electron, Browser-Frontend oder zweiter UI-Stack.

### 2.3 Zentraler Server

- Framework: **FastAPI**.
- ASGI-Server: **Uvicorn**, Version 1 mit genau **einem Worker**.
- API:
  - REST unter `/api/v1`,
  - WebSocket unter `/api/v1/ws`.
- Verträge/Validierung: Pydantic v2 als FastAPI-Transportmodell.
- Produktivdatenbank: **PostgreSQL**.
- ORM: **SQLAlchemy 2**.
- Migrationen: **Alembic**.
- PostgreSQL-Treiber: **psycopg 3**.
- Passwort-Hash: **Argon2id** ueber `argon2-cffi`.
- Sitzungen: opaque zufaellige Session-Tokens; **kein JWT**.
- Volltextsuche: PostgreSQL-Volltextsuche; kein Elasticsearch/OpenSearch.
- Kein Redis, RabbitMQ, Kafka, Celery oder sonstiger Message Broker in Version 1.
- Kein Docker als Produktionsvoraussetzung. Container duerfen nur fuer lokale/CI-Testdatenbanken verwendet werden.
- Windows-Dienst in der Betriebsphase ueber `pywin32`; kein zweiter Serverwrapper.

### 2.4 Transportverschluesselung

- Produktiver Messaging-Verkehr verwendet HTTPS und WSS.
- Es wird keine eigene TLS- oder Nachrichtenverschluesselung entwickelt.
- Ende-zu-Ende-Verschluesselung ist kein Ziel von Version 1.
- Alarmcast bleibt beim bestehenden direkten LAN-TCP mit PSK, bis eine spaetere freigegebene Spezifikation dies aendert.

## 3. Auslieferungseinheiten und einzige Entry Points

```text
Windows-Desktop-App
└── python -m alarmcast

Zentraler Server
└── python -m alarmcast_server
```

### 3.1 Desktop

- Einziger Python-Entry-Point: `src/alarmcast/__main__.py`.
- Einziger neuer Desktop-Composition-Root: `src/alarmcast/app_shell/composition.py`.
- `--host` und `--client` bleiben Kompatibilitaetsoptionen desselben Entry-Points.
- Es werden keine weiteren `main.py`, `run.py`, `launcher.py` oder separaten Host-/Client-Anwendungen erzeugt.

### 3.2 Server

- Einziger Server-Entry-Point: `src/alarmcast_server/__main__.py`.
- Einzige FastAPI-App-Fabrik: `src/alarmcast_server/app.py::create_app`.
- Einziger Server-Composition-Root: `src/alarmcast_server/composition.py`.
- Keine zweite App-Fabrik in Tests, `server.py`, `bootstrap.py` oder `main.py`.

## 4. Kanonische Repository-Struktur

Nur die folgenden neuen Produktpfade sind vorgesehen. Sie werden erst in ihrem Roadmap-Inkrement angelegt; keine leeren Zukunftsmodule.

```text
src/
  alarmcast/
    __main__.py
    app_shell/
      api.py
      contracts.py
      composition.py
      main_window.py
      tray.py

    settings/
      api.py
      contracts.py
      domain.py
      ports.py
      service.py
      adapters/
        json_store.py
        dpapi_secret_store.py

    identity/
      api.py
      contracts.py
      domain.py
      ports.py
      service.py

    devices/
      api.py
      contracts.py
      domain.py
      ports.py
      service.py

    server_connection/
      api.py
      contracts.py
      qt_rest_client.py
      qt_websocket_client.py

    messaging/
      api.py
      contracts.py
      domain.py
      ports.py
      service.py
      local_store.py
      sync_controller.py
      ui/

    groups/
      api.py
      contracts.py
      domain.py
      ports.py
      service.py
      ui/

    notifications/
      api.py
      contracts.py
      domain.py
      service.py
      overlay_coordinator.py
      urgent_overlay.py

    alarmcast_runtime/
      api.py
      contracts.py
      domain.py
      source_adapter.py
      monitor_adapter.py
      permissions.py

    core/       # bestehender Alarmcast-Kern
    host/       # bestehende Alarmcast-Quelle
    client/     # bestehender Alarmcast-Ueberwacher

  alarmcast_server/
    __main__.py
    app.py
    composition.py
    config.py

    administration/
    identity/
    devices/
    sessions/
    presence/
    conversations/
    groups/
    messages/
    delivery/
    reactions/
    screenshots/
    search/
    archive/
    alarmcast_events/
    backup/

    transport/
      http/
      realtime/

    infrastructure/
      database/
        models.py
        unit_of_work.py
        *_repository.py
      filesystem/
      clock.py
      ids.py
      security/

migrations/
  env.py
  versions/
```

### 4.1 Verbotene Alternativstrukturen

Nicht anlegen:

- `src/server`, `src/backend`, `src/common`, `src/shared`,
- projektweite `models/`, `schemas/`, `repositories/` oder `services/`,
- zweites Desktoppaket wie `messenger`, `client_app` oder `alarmcast_gui`,
- zweites Serverpaket wie `api`, `backend` oder `web`,
- generische `utils.py`, `helpers.py`, `manager.py`, `base.py`,
- eine zweite lokale Datenbank ausser der kanonischen SQLite-Datei,
- einen zweiten Screenshot-, Archiv- oder Konfigurationsspeicher.

## 5. Standardaufbau eines Fachmoduls

Ein Fachmodul darf nur die Dateien anlegen, die sein aktives Inkrement benoetigt. Die Bedeutungen sind fest:

```text
api.py        einzige oeffentliche Fassade
contracts.py  oeffentliche Commands, Queries, Events und DTOs
domain.py     interne Entitaeten, Value Objects, Enums und Invarianten
ports.py      interne Infrastruktur-Protocols
service.py    interne Use-Case-Orchestrierung
```

- Transportmodelle liegen nicht in `domain.py`.
- ORM-Klassen liegen nicht im Fachmodul.
- Keine parallelen Dateien `schemas.py`, `dto.py`, `types.py`, `entities.py`.
- `__init__.py` re-exportiert keine oeffentliche API.

## 6. Abhaengigkeitsrichtung

```text
Desktop UI -> Desktop api/contracts -> Desktop service/domain -> Desktop ports
Server Transport -> Server api/contracts -> Server service/domain -> Server ports
Infrastrukturadapter -> jeweilige ports/domain
Composition Root -> konkrete Adapter und Fassaden
```

Verboten:

- Domain kennt Qt, FastAPI, SQLAlchemy, Alembic oder konkrete Sockets.
- Desktop kennt SQLAlchemy-Modelle oder PostgreSQL.
- Server kennt Qt-Widgets.
- Fachmodul A importiert interne Dateien von Fachmodul B.
- GUI importiert `sqlite3`, QNetworkReply-Verarbeitung oder Alarmcast-Low-Level-Threads direkt.
- SQLAlchemy-Modelle werden als API-Response zurueckgegeben.
- Ein globaler Event Bus oder Service Locator verbindet beliebige Module.

## 7. Kommunikationsarchitektur

```text
Desktop-App
├── HTTPS REST /api/v1 -> Historie, Commands, Suche, Administration, Screenshots
├── WSS /api/v1/ws    -> Presence, Session-Revocation, neue Nachrichten und Status
└── direktes Alarmcast-TCP -> Audio, Alarm, Reset
```

### 7.1 REST

- Commands, die Persistenz aendern, werden serverseitig transaktional verarbeitet.
- REST-Routen liegen ausschliesslich unter `alarmcast_server/transport/http/`.
- Route-Handler enthalten keine Fachlogik und greifen nicht direkt auf SQLAlchemy-Sessions zu.

### 7.2 WebSocket

Ein einziger WebSocket pro Desktopprozess. Kein WebSocket pro Chat oder Modul.

Kanonisches Event-Envelope:

```json
{
  "event_id": "uuid",
  "event_type": "message.created",
  "occurred_at": "UTC timestamp",
  "payload": {}
}
```

Zulaessige Eventtypen werden zentral in `alarmcast_server/transport/realtime/contracts.py` registriert. Freie String-Erfindungen in einzelnen Modulen sind verboten.

Version 1 verwendet einen In-Process-Connection-Hub und einen Uvicorn-Worker. Nach Reconnect gleicht der Client den Zustand ueber REST ab; es gibt keinen Broker und keine Garantie, dass ein WebSocket-Event dauerhaft gespeichert ist.

## 8. Authentifizierung und Sitzungen

### 8.1 Normale Nutzer

- `User` ist eine Chatidentitaet.
- Login mit eindeutigem Nutzernamen und optionalem Passwort.
- Privilegierte Nutzer-Capabilities erfordern ein Passwort.

### 8.2 Systemadministratoren

- `AdminAccount` ist eine getrennte administrative Identitaet und **kein User**.
- Ein AdminAccount kann nicht Mitglied einer Conversation oder Gruppe sein und keine Chatnachricht senden.
- Dieselbe Person kann zusaetzlich ein separates User-Konto besitzen.

### 8.3 Session-Token

- Server erzeugt mindestens 256 Bit Zufall.
- Client erhaelt den opaque Token einmalig.
- Datenbank speichert nur den SHA-256-Hash des Tokens.
- Session-Token wird als Bearer-Token fuer REST und beim WebSocket-Handshake verwendet.
- Kein JWT, keine selbst signierten Tokenpayloads.
- Genau eine aktive UserSession pro User und genau eine aktive UserSession pro Device.

## 9. Geraeteidentitaet und Presence

- Sichtbarer Name: administrierter Windows-Hostname.
- Technische Identitaet: lokal erzeugte stabile UUID.
- Server speichert einen Hash des Geraete-Tokens, nicht den Klartext.
- Erstregistrierung darf im internen Netz ohne manuelle Freigabe erfolgen; spaetere Verbindungen muessen Geraete-ID und Token nachweisen.
- Eine kopierte lokale Geraeteidentitaet wird als Konflikt abgelehnt, nicht automatisch zusammengefuehrt.

Geraete-Presence:

- WebSocket verbunden + aktueller Heartbeat -> `ONLINE`,
- verzoegerte Heartbeats im definierten Zwischenfenster -> `CONNECTION_UNSTABLE`,
- Ablaufzeit ueberschritten -> `OFFLINE`.

Nutzer-Presence wird aus aktiver Session, Geraete-Presence, lokaler Aktivitaet und manuellem DND abgeleitet. Es gibt keine zweite unabhaengige Presence-Wahrheit in der Datenbank.

## 10. Nachrichten- und Zustellungsarchitektur

Das kanonische Datenmodell steht in `docs/domain-model.md`.

Grundsaetze:

- `Message` ist append-only.
- `Conversation.kind` bestimmt `DIRECT`, `DEVICE` oder `GROUP`; Message speichert keinen zweiten konkurrierenden Empfaengertyp.
- Zustellung, Lesen, Geraetebestaetigung und Reaktionen sind eigene Tabellen.
- Idempotenzschluessel ist `(origin_device_id, client_message_id)`.
- Nachricht wird zuerst persistent gespeichert; Live-Zustellung erfolgt nach erfolgreichem Commit.
- Fehlschlagende Live-Zustellung macht die gespeicherte Nachricht nicht rueckgaengig.
- Reconnect synchronisiert per REST anhand serverseitiger IDs/Zeitpunkte.
- Kein Message Broker und keine zweite Queue auf dem Server.

## 11. Lokaler Cache und Offline-Queue

Eine einzige SQLite-Datei im benutzerspezifischen Anwendungsdatenverzeichnis:

```text
%APPDATA%\AlarmCast\client-state.sqlite3
```

Sie enthaelt ausschliesslich:

- geladene Conversations und Messages als Cache,
- Offline-Ausgangswarteschlange,
- noch nicht synchronisierte Alarmcast-Logereignisse,
- lokale Synchronisationscursor.

Nicht enthalten:

- serverseitige Rollenwahrheit,
- globale Nutzerverwaltung,
- Masterkopie von Gruppenmitgliedschaften,
- produktive Backups,
- Alarmcast-Audio.

Es gibt keine zweite SQLite-Datei pro Modul und keine JSON-Offline-Queue.

## 12. Alarmcast-Fassade

Kanonische oeffentliche Fassade:

```python
class AlarmcastRuntimeApi(Protocol):
    def start_source(self) -> None: ...
    def stop_source(self) -> None: ...
    def start_monitor(self) -> None: ...
    def stop_monitor(self) -> None: ...
    def reset_alarm(self, alarm_id: str) -> None: ...
    def snapshot(self) -> AlarmcastRuntimeSnapshot: ...
```

Die konkrete Signatur darf im A01-Inkrement praezisiert, aber nicht durch mehrere Source-/Monitor-APIs dupliziert werden.

- UI und Messaging kennen keine Capture-, Detector-, Socket- oder AudioOutput-Objekte.
- Bestehender Host und Client werden adaptiert, nicht kopiert.
- Alarmcast-Ereignisse werden ueber typisierte Contracts an den zentralen Log-Sync gegeben.
- Audio wird niemals an den Messaging-Server gesendet oder gespeichert.

## 13. Overlay-Koordination

Ein einziger `OverlayCoordinator` im Desktop besitzt alle Bildschirm- und Z-Order-Entscheidungen.

Domänentypen:

- `ALARMCAST_ALARM` – Bildschirmmitte, hoechste Prioritaet,
- `URGENT_MESSAGE` – Bildschirmrand, persistenter Stapel,
- `ALARMCAST_INFO` – zeitlich begrenzte Bestandsmeldung,
- `ALARMCAST_CONFIRMATION` – bestaetigungspflichtige Bestandsmeldung,
- `MONITORING_FAILURE` – dauerhafte technische Warnung.

Keine Fachdomäne erzeugt eigene topmost Fenster ausser ueber den Koordinator. Bestehende Alarmcast-Overlays werden im vorgesehenen Inkrement adaptiert.

## 14. Konfiguration und Geheimnisse

Ein Settings-Modul besitzt alle lokalen Konfigurationsdateien.

- Atomarer Write-to-temp + `os.replace`.
- Jede Datei enthaelt `schema_version`.
- Migrationen sind explizit, sequenziell und idempotent.
- Letzte gueltige Konfiguration bleibt bei Schreib-/Parsefehler erhalten.
- Keine stillen Komplettresets.
- Bestehende `host.json`, `client.json`, `mode.txt` werden migriert und nicht ungefragt geloescht.
- Neue Fachmodule duerfen keine eigenen JSON-Dateien erfinden.
- Session- und Geraete-Tokens werden nicht im Klartext in JSON gespeichert.

## 15. Serverseitige Persistenz

- Eine PostgreSQL-Datenbank fuer alle Serverfachmodule.
- Tabellen und Namen exakt nach `docs/domain-model.md`.
- SQLAlchemy-Modelle zentral unter `infrastructure/database/models.py` bis eine begruendete Aufteilung nach fachlichen Dateien im entsprechenden Inkrement erforderlich wird.
- Alembic ist die einzige Schemaaenderung.
- Kein `Base.metadata.create_all()` im Produktivstart.
- Keine generischen CRUD-Endpunkte.
- Keine JSONB-Ersatzmodelle fuer Kernentitaeten.

## 16. Screenshots, Suche und Archiv

- Screenshots werden als Dateien gespeichert; Metadaten/Hash in PostgreSQL.
- Kanonischer aktiver Dateispeicher und kanonischer Archivspeicher werden serverseitig konfiguriert.
- Kein Base64-Bild in Message-Text oder WebSocket-Event.
- PostgreSQL-Volltextsuche indexiert berechtigte Nachrichtentexte.
- Archivierung alter Screenshots veraendert oder loescht die Message nicht.
- Keine automatische Altersloeschung.

## 17. Backup und Restore

Ein Backup-Satz umfasst:

- `pg_dump` im Custom-Format,
- aktiven Screenshot-Speicher,
- Archivindex und erforderliche Archivdateien,
- zentrale Serverkonfiguration ohne Klartextgeheimnisse,
- Alarmcast-Ereignislogs.

Ablauf:

1. temporaeres Backupverzeichnis auf dem Ziel,
2. Datenbankdump,
3. dateibasierte Inhalte und Manifest mit SHA-256,
4. Integritaetspruefung,
5. atomare Umbenennung zum gueltigen Backup-Satz.

Kein Backup gilt vor Schritt 5 als restore-faehig.

## 18. Logging

- Strukturierte Logs ueber Python `logging`.
- Keine `print()`-Diagnosen im Produktcode.
- Keine vollstaendigen Chattexte, Passwoerter, PSKs, Session- oder Geraete-Tokens.
- Fachliche Auditdaten liegen in ihren kanonischen Tabellen, nicht nur im Textlog.
- Keine generische „alles als JSON“-Audit-Tabelle fuer Nachrichteninhalte.

## 19. Testarchitektur

Jede oeffentliche Fassade ist ohne echte GUI, Netzwerk-, Audio- oder Datenbankhardware testbar.

- Domain: reine Unit-Tests.
- Ports: Fakes in Tests, keine Produktions-InMemory-Adapter.
- PostgreSQL: echte Integrationstests und Alembic-Migrationen.
- Desktop-SQLite: temporaere echte SQLite-Datei.
- REST/WebSocket: FastAPI-Testserver.
- Qt: pytest-qt und Controller/ViewModel-Tests.
- Windows: dokumentierte Smoke-Gates fuer WASAPI, Audiooutput, Tray, Autostart, Zwischenablage, Multi-Monitor und Dienstbetrieb.

## 20. Entscheidungen, die weiterhin explizite Freigabe benoetigen

Nur echte Abweichungen vom festgelegten Zielbild:

- Aenderung des Alarmcast-Protokolls oder Audioformats,
- neue Top-Level-Abhaengigkeit ausserhalb der Roadmap,
- zweite Serverinstanz/Mehrworkerbetrieb oder Message Broker,
- anderes Authentifizierungsmodell,
- neue Loesch-/Aufbewahrungsregeln,
- neuer Clienttyp oder oeffentlicher Internetbetrieb,
- neuer Produkt-Entry-Point,
- Abweichung von den kanonischen Tabellen oder Modulnamen.
