# Implementierungs-Roadmap

**Status:** verbindlicher Ausfuehrungsplan fuer Spezifikation 1.0  
**Arbeitsform:** autonome Etappen mit kleinen, einzeln committed Inkrementen.

## 1. Ausfuehrungsmodell

Codex bearbeitet nicht die gesamte Roadmap auf einmal. `tasks/ACTIVE_STAGE.md` aktiviert genau eine Etappe.

Innerhalb einer aktiven Etappe gilt:

1. Inkremente exakt in angegebener Reihenfolge.
2. Vor jedem Inkrement Baseline/Gate ausfuehren.
3. Nur bei `AUTO_GREEN` selbststaendig fortfahren.
4. Genau ein Commit pro Inkrement.
5. Am Etappenende Draft-PR erstellen und stoppen.
6. Keine Folgeetappe selbst aktivieren oder beginnen.

Statuswerte:

- `PLANNED` – zukuenftig, nicht freigegeben,
- `READY` – aktive Etappe darf beginnen,
- `IN_PROGRESS` – Agent arbeitet daran,
- `AUTO_GREEN` – automatisches Gate gruen, naechstes Inkrement derselben Etappe erlaubt,
- `MANUAL_PENDING` – automatische Gates gruen, benannter manueller Test steht noch aus,
- `BLOCKED` – Stop-Bedingung,
- `REVIEW` – Etappen-PR ist offen,
- `DONE` – reviewed und gemergt.

Die kanonischen Strukturen und Namen stehen in:

- `docs/domain-model.md`
- `docs/target-architecture.md`
- `AGENTS.md`

Roadmaptexte sind keine Erlaubnis, davon abweichende Strukturen zu erfinden.

## 2. Globales automatisches Gate

Vor Fortsetzung zum naechsten Inkrement derselben Etappe muessen gruen sein:

```text
ruff check .
ruff format --check .
mypy src
pytest -q
```

Zusaetzlich:

- alle inkrementspezifischen Tests,
- Architekturtests,
- Migrations-/Integrationspruefungen, falls betroffen,
- keine neue unfreigegebene Dependency,
- keine unerwartete Produktdatei,
- keine Spezifikations- oder Datenmodellabweichung,
- kein bestehendes Alarmcast-Verhalten entfernt,
- Checkpoint-Bericht erstellt.

Manuelle Windows-Tests duerfen nur dann `MANUAL_PENDING` sein, wenn die aktive Etappendatei dies ausdruecklich als nicht blockierend einstuft. Sie bleiben Etappen-PR-Gate.

## 3. Etappenuebersicht

| Etappe | Inkremente | Ergebnis | Autonom bis |
|---|---|---|---|
| STAGE-01 Baseline und Schutz | B00–B03 | sauberer Originalstand, CI, Guards, sichere Bestandsconfig | B03 |
| STAGE-02 Alarmcast kapseln | A01–A06 | stabile Fassaden, Overlay-Koordinator, gemeinsame Shell | A06 |
| STAGE-03 Serverfundament | S01–S04 | FastAPI/Uvicorn, PostgreSQL/Alembic, Basisvertraege | S04 |
| STAGE-04 Geraete und Identitaet | D01–D08 | Registrierung, Admin/User, exklusive Sessions, Presence | D08 |
| STAGE-05 Messaging-Kern | M01–M13 | Conversations, append-only Messages, Zustellung, Offline | M13 |
| STAGE-06 Gruppen | G01–G08 | Rollen, Historie, Eigentum, Archivierung | G08 |
| STAGE-07 Desktop-Messaging | U01–U07 | Kontaktliste, Chat-UIs, Zitate, Reaktionen, Clipboard | U07 |
| STAGE-08 Dringlichkeit, Screenshots, Suche | N01–N06 | Screenshotstore, Search, persistente Urgent-Overlays | N06 |
| STAGE-09 Alarmcast-Gesamtintegration | I01–I06 | Mehrquellen, Rechte, Logs, Ausfallwarnungen, Migration | I06 |
| STAGE-10 Betrieb | O01–O06 | Archiv, Backup/Restore, Windows-Dienst, Installer | O06 |
| STAGE-11 Systemabnahme | R01–R04 | E2E, Ausfalltests, Traceability, Release Candidate | R04 |

## 4. STAGE-01 – Baseline und Schutzschicht

### B00 – Originalen Alarmcast-Bestand importieren

**Status:** `READY` nach verifizierter ZIP.  
**Detaillierter Task:** `tasks/increments/B00-import-baseline.md`

**Erlaubte Aenderungen:**

- Dateien aus dem verifizierten Archiv in kanonische Originalpfade uebernehmen,
- generierte Artefakte ausschliessen,
- `docs/baseline-report.md`,
- Bootstrap-ZIP/Uploadhinweis entfernen.

**Verboten:** Produktcode editieren, formatieren, umbenennen oder reorganisieren.

**Gate:** Archivhash korrekt; Quellcode identisch; keine Secrets; Compile/Test-Baseline dokumentiert.

### B01 – Python-3.12-Entwicklungsumgebung und CI

**Abhaengigkeit:** B00.  
**Detaillierter Task:** `tasks/increments/B01-development-ci.md`

**Exakte Owner/Pfade:**

- `pyproject.toml`,
- `.github/workflows/ci.yml`,
- `README.md`,
- optional ausschliesslich testbezogene Konfiguration unter `tests/`.

**Nicht anlegen:** Poetry/PDM/Hatch/uv-Konfiguration, Docker-Produktionssetup, zweites pyproject, requirements-Wildwuchs.

**Tests:** Windows CI mit Python 3.12; ruff, format, mypy, pytest; Build nicht erforderlich.

### B02 – Architektur- und Repository-Guards

**Abhaengigkeit:** B01.  
**Detaillierter Task:** `tasks/increments/B02-architecture-guards.md`

**Exakte Owner/Pfade:**

- `tests/architecture/`,
- nur falls erforderlich kleine Test-Helfer unter `tests/architecture/_fixtures/`.

**Guards:**

- `core` importiert nicht `host/client`,
- `host` und `client` importieren nicht direkt voneinander,
- nur kanonische Entry Points,
- keine verbotenen Auffangmodule,
- keine Secrets/Config/Logs/Buildartefakte,
- kein zweites Top-Level-Produktpaket,
- keine nicht freigegebenen Dependencies.

**Verboten:** Produktcode fuer die Tests umbauen, generischen Dependency-Linter einfuehren, neues Tool ohne Freigabe.

### B03 – Atomare und versionierte Bestandskonfiguration

**Abhaengigkeit:** B02.  
**Detaillierter Task:** `tasks/increments/B03-config-persistence.md`

**Exakte Owner/Pfade:**

- `src/alarmcast/core/config.py`,
- falls im Original vorhanden: `src/alarmcast/core/mode_switch.py`,
- zugehoerige Configtests.

**Noch nicht anlegen:** neues `settings/`-Modul, `app.json`, SQLite, DPAPI, Messagingconfig.

**Funktion:** atomarer Temp-Write + Replace, `schema_version`, sequenzielle Migration vorhandener `host.json/client.json`, Recovery ohne stillen Reset.

## 5. STAGE-02 – Alarmcast kapseln, Verhalten erhalten

### A01 – Kanonische Alarmcast-Contracts

**Abhaengigkeit:** B03.

**Exakte neue Pfade:**

```text
src/alarmcast/alarmcast_runtime/__init__.py
src/alarmcast/alarmcast_runtime/contracts.py
src/alarmcast/alarmcast_runtime/domain.py
```

**Contracts:** Source-/Monitorzustand, Alarm-ID, Quell-ID, Statussnapshot, typisierte Runtimeevents.

**Nicht anlegen:** `models.py`, `types.py`, zweite Fassade, Qt-/Socket-/Audio-Typen in Contracts.

### A02 – SourceAdapter

**Abhaengigkeit:** A01.

**Exakte Pfade:**

```text
src/alarmcast/alarmcast_runtime/source_adapter.py
```

Bestehende `host.capture`, `host.detector`, `host.server` werden komponiert, nicht kopiert.

**Gate:** bestehende Hosttests gruen; keine Protokollaenderung.

### A03 – MonitorAdapter

**Abhaengigkeit:** A01.

**Exakte Pfade:**

```text
src/alarmcast/alarmcast_runtime/monitor_adapter.py
```

Bestehende `client.net`, `client.output`, Discovery und Overlay-Anbindung werden adaptiert, nicht kopiert.

### A04 – Einzige AlarmcastRuntimeApi

**Abhaengigkeit:** A02, A03.

**Exakte Pfade:**

```text
src/alarmcast/alarmcast_runtime/api.py
src/alarmcast/alarmcast_runtime/service.py
```

Quelle und Monitor sind unabhaengige Capabilities in einem Prozess. Keine `SourceApi` und `MonitorApi` als konkurrierende oeffentliche Fassaden.

### A05 – Einziger OverlayCoordinator

**Abhaengigkeit:** A04.

**Exakte neue Pfade:**

```text
src/alarmcast/notifications/__init__.py
src/alarmcast/notifications/contracts.py
src/alarmcast/notifications/domain.py
src/alarmcast/notifications/service.py
src/alarmcast/notifications/overlay_coordinator.py
```

Bestehende Client-Overlays werden adaptiert. Noch kein Urgent-Messaging-Overlay.

**Kanonische Typen:** `ALARMCAST_ALARM`, `ALARMCAST_INFO`, `ALARMCAST_CONFIRMATION`, `MONITORING_FAILURE`.

### A06 – Gemeinsame Desktop-App-Shell

**Abhaengigkeit:** A04, A05.

**Exakte neue Pfade:**

```text
src/alarmcast/app_shell/__init__.py
src/alarmcast/app_shell/api.py
src/alarmcast/app_shell/contracts.py
src/alarmcast/app_shell/composition.py
src/alarmcast/app_shell/main_window.py
src/alarmcast/app_shell/tray.py
```

`src/alarmcast/__main__.py` bleibt einziger Entry Point und delegiert. Bestehende `--host/--client`-Wege bleiben gruen.

**Nicht anlegen:** zweite QApplication, zweites Tray, `launcher.py`, neuer CLI-Entry-Point.

## 6. STAGE-03 – Zentraler Server

Der Stack ist bereits in Zielarchitektur und ADR 0010 entschieden. Es gibt kein Technologieentscheidungsinkrement mehr.

### S01 – Serverpaket, FastAPI-App und Health

**Abhaengigkeit:** STAGE-01.

**Freigegebene neue Dependencies:** `fastapi`, `uvicorn`, `pydantic` als transitive/direkte FastAPI-Grundlage. Keine weiteren Serverframeworks.

**Exakte Pfade:**

```text
src/alarmcast_server/__init__.py
src/alarmcast_server/__main__.py
src/alarmcast_server/app.py
src/alarmcast_server/composition.py
src/alarmcast_server/config.py
src/alarmcast_server/transport/http/health_routes.py
```

**Einziger Endpunkt:** `GET /api/v1/health`.

**Nicht anlegen:** Fachdaten, DB-Modelle, Auth, WebSocket, zweite App-Fabrik.

### S02 – PostgreSQL und Alembic-Basis

**Abhaengigkeit:** S01.

**Freigegebene Dependencies:** `sqlalchemy`, `alembic`, `psycopg`.

**Exakte Pfade:**

```text
migrations/env.py
migrations/versions/
src/alarmcast_server/infrastructure/database/models.py
src/alarmcast_server/infrastructure/database/session_factory.py
src/alarmcast_server/infrastructure/database/unit_of_work.py
```

Noch keine fachlichen Tabellen ausser technischer Alembic-Versionierung.

**Verboten:** `create_all()` im Produktstart, SQLite als Serverdatenbank, generisches BaseRepository.

### S03 – Clock, IDs und Transaktionsports

**Abhaengigkeit:** S02.

**Exakte Pfade:**

```text
src/alarmcast_server/infrastructure/clock.py
src/alarmcast_server/infrastructure/ids.py
```

Fachmodule verwenden injizierbare Ports; keine direkte Systemzeit/uuid4 ausser Adapter.

### S04 – Fehlervertrag und ein WebSocket-Hub

**Abhaengigkeit:** S03.

**Exakte Pfade:**

```text
src/alarmcast_server/transport/http/error_contracts.py
src/alarmcast_server/transport/realtime/contracts.py
src/alarmcast_server/transport/realtime/connection_hub.py
src/alarmcast_server/transport/realtime/ws_routes.py
```

**Einziger WebSocket:** `/api/v1/ws`.  
**Einziger Event-Envelope:** gemaess Zielarchitektur.  
Noch keine fachlichen Events, Auth oder Persistenz.

## 7. STAGE-04 – Geraete, Admin, Nutzer, Sitzungen und Presence

### D01 – Lokale Geraeteidentitaet

**Owner Desktop:** `alarmcast/devices` und `alarmcast/settings`.  
**Modell:** UUID + Windows-Hostname + DPAPI-geschuetztes Geraetetoken.  
**Nicht anlegen:** MAC-basierte ID, Registry als zweite Wahrheit, Maschinenfingerprint.

### D02 – Serverseitige Geraeteregistrierung

**Owner Server:** `alarmcast_server/devices`.  
**Tabellen:** nur `devices`, `device_capabilities` nach Domainmodell.  
**Routes:** unter `/api/v1/devices`; keine generischen CRUD-Routes.

### D03 – Heartbeat und DevicePresence

**Owner:** Server `devices/presence`, Desktop `devices`.  
**Keine Presence-Tabelle:** Status wird abgeleitet und `last_seen_at` aktualisiert.

### D04 – AdminAccount

**Owner:** `alarmcast_server/administration`.  
**Tabelle:** `admin_accounts`.  
**Freigegebene Dependency:** `argon2-cffi`.  
**Nicht:** `is_admin` an User, Admin als GroupMember, Admin-Chat-API.

### D05 – User und UserCapabilities

**Owner:** `alarmcast_server/identity`.  
**Tabellen:** `users`, `user_capabilities`, `user_presence_preferences`.  
**Keine Self-Signup-Route.**

### D06 – User-Login und opaque Token

**Owner:** `alarmcast_server/sessions`, Desktop `identity`.  
**Tabelle:** `user_sessions`.  
**Kein JWT.**

### D07 – Exklusive Session

Partielle Unique-Indizes fuer aktive Session pro User und Device. Neue Anmeldung widerruft alte Session atomar und sendet `session.revoked`.

### D08 – UserPresence

Status exakt `OFFLINE/AVAILABLE/AWAY/DO_NOT_DISTURB`; keine zusaetzlichen Busy/Invisible-Statuswerte.

## 8. STAGE-05 – Messaging-Kern

### M01 – Conversation-Basis und Subtypen

**Tabellen exakt:**

- `conversations`,
- `direct_conversations`,
- `device_conversations`,
- `group_conversations`.

Noch keine `conversation_memberships`, Messages oder UI.

### M02 – Append-only Message

**Tabelle exakt:** `messages`.  
**Keine Edit-/Delete-/Soft-Delete-Spalten.**  
Conversation-Sequenz transaktional.

### M03 – Idempotentes Senden

Eindeutigkeit `(origin_device_id, client_message_id)`.  
Persistenz vor Live-Zustellung.  
Keine Server-Outbox oder Broker.

### M04 – Live-Zustellung

Nutzt den einzigen WebSocket-Hub. Reconnect-Synchronisation bleibt REST-basiert.

### M05 – MessageDelivery

**Tabelle exakt:** `message_deliveries`.  
Status nur `PENDING/DELIVERED`; `SENT` ist abgeleitet.

### M06 – ReadReceipt und DeviceAcknowledgement

**Tabellen exakt:**

- `message_read_receipts`,
- `message_device_acknowledgements`.

Kein generisches Notification-/Receipt-Modell.

### M07 – Dauerhafter DirectConversation

Genau ein normalisiertes Userpaar. Kein zweiter Chat und kein „neuen Einzelchat starten“ als neue Conversation.

### M08 – Sieben-Tage-Abfrage und stabile Pagination

Filter nach Serverzeit, Sortierung/Pagination nach `conversation_sequence`; nicht nur Timestamp-Cursor.

### M09 – Einzige lokale SQLite-Datei und Cache

**Datei:** `%APPDATA%\AlarmCast\client-state.sqlite3`.  
**Tabellen:** exakt nach Domainmodell.  
Keine JSON-Cachedateien.

### M10 – Explizite Offline-Queues

Tabellen `outbound_messages`, `pending_read_receipts`, `pending_device_acknowledgements`, `pending_reaction_changes`, `pending_alarmcast_log_events`. Kein generischer Command-Bus.

### M11 – DeviceConversation-Zugriff

Ein Devicechat pro Device. Vollverlauf nur am Zieldevice; externer Sender sieht eigene Device-Messages. Antwort an User erfolgt in DirectConversation.

### M12 – Inline-Referenz und Thread-Wurzel

Nur `reply_to_message_id` und `thread_root_message_id`; keine Thread-Tabelle und keine Thread-UI.

### M13 – Reaktionen

**Tabelle exakt:** `message_reactions`.  
Feste `ReactionCode`; keine freien Emojis.

## 9. STAGE-06 – Gruppen

### G01 – Private GroupConversation

Erstellt `group_conversations` plus erste `group_memberships`-Ownerzeile in einer Transaktion.

### G02 – Rollen und Hinzufuegen

Rechtematrix exakt nach Domainmodell; keine UI-only-Pruefung.

### G03 – Entfernen und Adminverwaltung

Nur Owner entfernt Mitglieder. Hilfsadmin darf keinen Owner oder Member entfernen.

### G04 – Vollhistorie fuer neue Mitglieder

Keine Messagekopie und keine rueckwirkend erfundenen Delivery-Zeitpunkte.

### G05 – Kein Selbstaustritt

Keine Leave-Route und kein Leave-Button fuer Member/Admin/Owner.

### G06 – Eigentumsuebergabe vor Deaktivierung

Genau ein aktiver Owner. Deaktivierung blockiert bis Transfer oder Archivierung.

### G07 – Gruppenarchivierung

`ACTIVE -> ARCHIVED`, read-only, kein Delete. Reaktivierung nur Adminprozess mit aktivem Owner.

### G08 – Admin-Metadatenansicht

Admin sieht Gruppenname, Rollen, Mitglieder, Zeiten und Status; keine Message-/Screenshotfelder und keine inhaltliche Suche.

## 10. STAGE-07 – Desktop-Messaging

### U01 – Shell-Navigation und eigener Status

Erweitert ausschliesslich bestehende `app_shell`; kein zweites Hauptfensterframework.

### U02 – Kontakt- und Geraeteliste

ViewModel liest nur typisierte Contracts. Keine eigene Presenceberechnung in Widgets.

### U03 – DirectChat-UI

Kein Edit/Delete/Recall. Sieben Tage initial, aeltere Sequenzen nachladen.

### U04 – DeviceChat-UI

Vollverlauf nur auf Zieldevice; externer Senderbereich darf fremde Device-Messages nicht anzeigen.

### U05 – GroupChat-UI

Rechtebasierte Aktionen; Server bleibt Autoritaet. Archivgruppe read-only.

### U06 – Inline-Zitat und Reaktion

Keine sichtbare Threadansicht. Keine freien Emoji-Picker.

### U07 – Screenshot aus Windows-Zwischenablage

Nur Clipboard-Image, kein Dateidialog. Vorschau vor Versand. Noch kein Server-Archiv.

## 11. STAGE-08 – Screenshots, Suche und Dringlichkeit

### N01 – Screenshot-Speicher

**Tabelle:** `screenshot_attachments`.  
Binaerdatei ausserhalb DB, SHA-256 und Dimensionen. Kein Base64 in Message/WebSocket.

### N02 – PostgreSQL-Suche

PostgreSQL-Volltext, serverseitige Zugriffsfilter. Kein Elasticsearch und keine zweite Suchdatenbank.

### N03 – Urgency und DisplayMode

Nur Felder in `messages`: `urgency`, `urgent_display_mode`. Keine `urgent_messages`-Tabelle.

### N04 – Persistenter Urgent-Status

Abgeleitet aus ReadReceipt/DeviceAcknowledgement. Keine parallele Notification-State-Tabelle.

### N05 – Rand-Overlay auf allen Monitoren

Erweitert einzigen OverlayCoordinator um `URGENT_MESSAGE`. Alarmcast-Mitte bleibt frei.

### N06 – Aktionen Oeffnen/Gelesen

HIDDEN nur Oeffnen. Aktionen idempotent und autorisiert.

## 12. STAGE-09 – Alarmcast-Gesamtintegration

### I01 – Mehrquellen-Zuordnung

**Tabelle:** `alarm_monitor_assignments`.  
Keine `default_source_id`-Parallelwahrheit.

### I02 – Lokale Capability-Pruefung

Exakte User-/DeviceCapabilities. Start/Stop/Configure nicht als Fernsteuerungsroute.

### I03 – AlarmEvent, AlarmReset und LogSync

**Tabellen exakt:** `alarm_events`, `alarm_resets`, `alarmcast_log_events`.  
Kein Audiostream und keine generische All-Events-Tabelle.

### I04 – Persistente MonitoringFailure

Ein Overlaytyp im Koordinator; Quelle/Fehlerart eindeutig. DND unterdrueckt nicht.

### I05 – Parallele Alarm-/Urgent-Anzeige

Getrennte Z-Order, Lifecycle und Bestaetigung. Kein gegenseitiges Clear.

### I06 – Migration alter Alarmcast-Einstellungen

Migriert `host.json`, `client.json`, `mode.txt` in kanonisches Settingsmodell. Quelldateien bleiben bis verifizierter erfolgreicher Migration erhalten.

## 13. STAGE-10 – Archiv, Backup und Windows-Betrieb

### O01 – Screenshot-Archivierung

Nur `ScreenshotStorageTier ACTIVE -> ARCHIVE`; Message und Suchmetadaten bleiben.

### O02 – Konsistenter Backup-Satz

`pg_dump` Custom Format + Dateispeicher + Manifest auf UNC-Netzlaufwerk. Tempverzeichnis bis Validierung.

### O03 – Rotation

Standard 7 taeglich / 4 woechentlich / 12 monatlich, administrativ anpassbar. Nie einzigen gueltigen Satz loeschen.

### O04 – Integritaet und Restore

Separater Betriebscommand im **Server-Entry-Point-Konzept**, kein dritter Produktentrypoint. Falls CLI-Subcommand erforderlich, wird er unter `python -m alarmcast_server restore` eingefuehrt.

### O05 – Windows-Dienst

`pywin32`, genau ein Serverdienst. Kein NSSM/WinSW als zweite offizielle Betriebsart.

### O06 – Desktop-Build und Installer

PyInstaller + Inno Setup. Manueller/administrativer Updateprozess Version 1; kein selbst erfundener Auto-Updater.

## 14. STAGE-11 – Systemabnahme

### R01 – Mehrclient-E2E

Server, zwei Userdevices, ein unbesetztes Device, Direct/Group/Device, Offline-Queue, Urgent, Alarmcast.

### R02 – Ausfall und Wiederanlauf

Server, Netzwerk, Clientprozess, Alarmquelle, Audiooutput, Netzlaufwerk. Keine Doppelmessages nach Recovery.

### R03 – Traceability gegen Spezifikation

Jeder Spezifikationsabschnitt -> Inkrement -> automatisierter Test -> manueller Test -> Ergebnis.

### R04 – Release Candidate

Versionierte Artefakte, Release Notes, Installations-, Backup- und Restore-Dokumentation. Kein neues Feature.

## 15. Stop- und Reviewregeln

Codex stoppt innerhalb einer Etappe bei allen `AGENTS.md`-Stop-Bedingungen, insbesondere wenn:

- ein nicht gelistetes Modul oder eine nicht gelistete Tabelle erforderlich erscheint,
- eine neue Dependency ausserhalb des Inkrements erforderlich ist,
- ein manuelles Hardwaregate fachliche Grundlage des naechsten Inkrements ist,
- ein Test nach zwei zielgerichteten Reparaturversuchen nicht gruen wird,
- bestehendes Alarmcast-Verhalten nicht bewahrt werden kann.

Nach Etappenabschluss:

1. `tasks/ACTIVE_STAGE.md` auf `REVIEW` setzen,
2. Draft-PR gegen den dort genannten Zielbranch,
3. keine Folgeetappe aktivieren,
4. Lauf beenden.
