# Implementierungs-Roadmap

**Status:** verbindlicher Ausfuehrungsplan fuer Spezifikation 1.0  
**Arbeitsform:** autonome Etappen mit kleinen, einzeln committed Inkrementen.  
**Namensquelle:** `docs/domain-model.md` und `docs/domain-model-clarifications.md`.

Roadmaptexte erlauben keine abweichenden Module, Entitaeten, Tabellen, Routen, Entry Points oder Dependencies. Nicht ausdruecklich genannte Zukunftsstrukturen werden nicht vorsorglich angelegt.

## 1. Ausfuehrungsmodell

`tasks/ACTIVE_STAGE.md` aktiviert genau eine Etappe. Innerhalb dieser Etappe gilt:

1. Inkremente exakt in der angegebenen Reihenfolge bearbeiten.
2. Vor jedem Inkrement Baseline und relevante Tests ausfuehren.
3. Nur bei vollstaendigem `AUTO_GREEN` selbststaendig fortfahren.
4. Genau einen Commit pro Inkrement erstellen.
5. Checkpoint im Stage-Bericht dokumentieren.
6. Nach dem letzten Inkrement einen Draft-PR erstellen und stoppen.
7. Keine Folgeetappe autonom aktivieren, beginnen oder vorbereiten.

Statuswerte:

- `PLANNED` – zukuenftig und nicht freigegeben,
- `READY` – aktive Etappe darf beginnen,
- `IN_PROGRESS` – Agent arbeitet daran,
- `AUTO_GREEN` – alle automatischen Gates gruen,
- `MANUAL_PENDING` – automatische Gates gruen, ausdruecklich erlaubter manueller Test offen,
- `BLOCKED` – Stop-Bedingung,
- `REVIEW` – Stage-PR offen,
- `DONE` – reviewed und gemergt.

## 2. Globales automatisches Gate

Vor autonomer Fortsetzung muessen gruen sein:

```text
ruff check .
ruff format --check .
mypy src
pytest -q
```

Zusaetzlich:

- alle inkrementspezifischen Tests,
- betroffene Architektur- und Repository-Guards,
- Migrations-/Persistenztests, falls betroffen,
- keine neue unfreigegebene Dependency,
- keine unerwartete Produktdatei,
- keine Spezifikations-, Domaenenmodell- oder Architekturabweichung,
- kein entferntes oder veraendertes Alarmcast-Bestandsverhalten,
- erklaerter Diff und Checkpoint-Bericht.

`NOT RUN` ist nicht gruen. Nur ein in der aktiven Etappendatei ausdruecklich zugelassenes Hardware-/Windows-Gate darf als `MANUAL_PENDING` die Fortsetzung innerhalb derselben Etappe erlauben.

## 3. Etappenuebersicht

| Etappe | Inkremente | Ergebnis | Autonom bis |
|---|---|---|---|
| STAGE-01 Baseline und Schutz | B00–B03 | Originalstand, CI, Guards, sichere Bestandsconfig | B03 |
| STAGE-02 Alarmcast kapseln | A01–A06 | Fassaden, Runtime, Overlay-Koordinator, gemeinsame Shell | A06 |
| STAGE-03 Serverfundament | S01–S04 | FastAPI/Uvicorn, PostgreSQL/Alembic, Basisvertraege | S04 |
| STAGE-04 Geraete und Identitaet | D01–D08 | Registrierung, Admin/User, Sessions, Presence | D08 |
| STAGE-05 Messaging-Kern | M01–M14 | Conversations, Messages, Zustellung, Offline, persoenlicher Zustand | M14 |
| STAGE-06 Gruppen | G01–G08 | Rollen, Historie, Eigentum, Archivierung | G08 |
| STAGE-07 Desktop-Messaging | U01–U08 | Chat-UIs, Zitate, Reaktionen, Clipboard-Vorschau, Organisation | U08 |
| STAGE-08 Screenshots, Suche und Dringlichkeit | N01–N06 | echter Screenshotversand, Suche, persistente Urgent-Overlays | N06 |
| STAGE-09 Alarmcast-Gesamtintegration | I01–I06 | Mehrquellen, Rechte, Logs, Warnungen, Migration | I06 |
| STAGE-10 Betrieb | O01–O06 | Archiv, Backup/Restore, Windows-Dienst, Installer | O06 |
| STAGE-11 Systemabnahme | R01–R04 | E2E, Ausfalltests, Traceability, Release Candidate | R04 |

## 4. STAGE-01 – Baseline und Schutzschicht

### B00 – Originalen Alarmcast-Bestand importieren

**Status:** `READY` nach verifizierter ZIP.  
**Detaillierter Task:** `tasks/increments/B00-import-baseline.md`

Erlaubt:

- Dateien aus dem verifizierten Archiv in ihre Originalpfade uebernehmen,
- generierte/lokale Artefakte ausschliessen,
- `docs/baseline-report.md` anlegen,
- Bootstrap-ZIP und Uploadhinweis nach erfolgreicher Pruefung entfernen.

Verboten: Produktcode editieren, formatieren, umbenennen oder reorganisieren.

Gate: Hash korrekt, Quellcode identisch, keine Secrets, Compile-/Test-Baseline dokumentiert.

### B01 – Python-3.12-Entwicklungsumgebung und CI

**Abhaengigkeit:** B00  
**Detaillierter Task:** `tasks/increments/B01-development-ci.md`

Erlaubte Pfade:

```text
pyproject.toml
.github/workflows/ci.yml
README.md
tests/                 # nur testbezogene Konfiguration
```

Nicht anlegen: Poetry/PDM/Hatch/uv-Projektkonfiguration, zweites `pyproject.toml`, Docker-Produktionssetup oder mehrere konkurrierende Requirements-Dateien.

Gate: reproduzierbare Installation mit Python 3.12; Windows-CI fuehrt ruff, Format, mypy und pytest aus.

### B02 – Architektur- und Repository-Guards

**Abhaengigkeit:** B01  
**Detaillierter Task:** `tasks/increments/B02-architecture-guards.md`

Erlaubte Pfade:

```text
tests/architecture/
tests/architecture/_fixtures/
```

Guards:

- `core` importiert nicht `host` oder `client`,
- `host` und `client` importieren nicht direkt voneinander,
- nur kanonische Entry Points,
- keine Auffangmodule wie `utils`, `helpers`, `common`, `shared`,
- keine Secrets, lokalen Configs, Logs oder Buildartefakte,
- kein drittes Top-Level-Produktpaket,
- keine unfreigegebenen Dependencies.

Verboten: Produktcode nur fuer den Guard umbauen oder ein neues Dependency-Lint-Werkzeug einfuehren.

### B03 – Atomare und versionierte Bestandskonfiguration

**Abhaengigkeit:** B02  
**Detaillierter Task:** `tasks/increments/B03-config-persistence.md`

Erlaubte Owner/Pfade:

```text
src/alarmcast/core/config.py
src/alarmcast/core/mode_switch.py     # nur falls im Original vorhanden
zugehoerige Configtests
```

Funktion: Temp-Write plus atomarer Replace, `schema_version`, sequenzielle Migration vorhandener `host.json`/`client.json`, sichtbare Recovery ohne stillen Komplettreset.

Noch nicht anlegen: neues `settings/`-Fachmodul, `app.json`, SQLite, DPAPI oder Messagingconfig.

## 5. STAGE-02 – Alarmcast kapseln, Verhalten erhalten

### A01 – Kanonische Alarmcast-Contracts

Neue Pfade ausschliesslich:

```text
src/alarmcast/alarmcast_runtime/__init__.py
src/alarmcast/alarmcast_runtime/contracts.py
src/alarmcast/alarmcast_runtime/domain.py
```

Contracts: Source-/Monitorzustand, Alarm-ID, Quell-ID, Statussnapshot und typisierte Runtimeevents. Keine Qt-, Socket- oder Audiotypen; kein paralleles `models.py` oder `types.py`.

### A02 – SourceAdapter

Pfad: `src/alarmcast/alarmcast_runtime/source_adapter.py`.

Bestehende Capture-, Detector- und HostServer-Komponenten werden komponiert, nicht kopiert. TCP-Protokoll, Audioformat und Detektion bleiben unveraendert.

### A03 – MonitorAdapter

Pfad: `src/alarmcast/alarmcast_runtime/monitor_adapter.py`.

Bestehende Netzwerk-, Audiooutput-, Discovery- und Overlay-Komponenten werden adaptiert, nicht dupliziert.

### A04 – Einzige AlarmcastRuntimeApi

Pfade:

```text
src/alarmcast/alarmcast_runtime/api.py
src/alarmcast/alarmcast_runtime/service.py
```

Quelle und Monitor sind unabhaengige Capabilities in einem Prozess. Keine konkurrierenden oeffentlichen `SourceApi`-/`MonitorApi`-Fassaden.

### A05 – Einziger OverlayCoordinator

Pfade:

```text
src/alarmcast/notifications/__init__.py
src/alarmcast/notifications/contracts.py
src/alarmcast/notifications/domain.py
src/alarmcast/notifications/service.py
src/alarmcast/notifications/overlay_coordinator.py
```

Bestands-Overlays werden adaptiert. Kanonische Typen dieser Stufe: `ALARMCAST_ALARM`, `ALARMCAST_INFO`, `ALARMCAST_CONFIRMATION`, `MONITORING_FAILURE`. Noch kein Urgent-Messaging-Overlay.

### A06 – Gemeinsame Desktop-App-Shell

Pfade:

```text
src/alarmcast/app_shell/__init__.py
src/alarmcast/app_shell/api.py
src/alarmcast/app_shell/contracts.py
src/alarmcast/app_shell/composition.py
src/alarmcast/app_shell/main_window.py
src/alarmcast/app_shell/tray.py
```

`src/alarmcast/__main__.py` bleibt einziger Desktop-Entry-Point. Bestehende `--host`/`--client`-Wege bleiben kompatibel. Keine zweite QApplication, kein zweites Tray und kein `launcher.py`.

## 6. STAGE-03 – Zentraler Server

Der Stack ist bereits in Zielarchitektur und ADR 0010 entschieden. Es gibt kein Technologieentscheidungsinkrement.

### S01 – Serverpaket, FastAPI-App und Health

Freigegebene Dependencies: `fastapi`, `uvicorn`, `pydantic`.

Exakte Pfade:

```text
src/alarmcast_server/__init__.py
src/alarmcast_server/__main__.py
src/alarmcast_server/app.py
src/alarmcast_server/composition.py
src/alarmcast_server/config.py
src/alarmcast_server/transport/http/health_routes.py
```

Einziger Endpunkt: `GET /api/v1/health`. Noch keine Fachdaten, DB, Auth oder WebSocket-Fachereignisse.

### S02 – PostgreSQL und Alembic-Basis

Freigegebene Dependencies: `sqlalchemy`, `alembic`, `psycopg`.

Exakte Pfade:

```text
migrations/env.py
migrations/versions/
src/alarmcast_server/infrastructure/database/models.py
src/alarmcast_server/infrastructure/database/session_factory.py
src/alarmcast_server/infrastructure/database/unit_of_work.py
```

Noch keine fachlichen Tabellen ausser Alembic-Versionierung. Kein `create_all()` im Produktstart, keine SQLite-Serverdatenbank und kein `BaseRepository`.

### S03 – Clock, IDs und Transaktionsports

Pfade:

```text
src/alarmcast_server/infrastructure/clock.py
src/alarmcast_server/infrastructure/ids.py
```

Fachmodule verwenden injizierbare Ports; keine direkte Systemzeit oder `uuid4()` ausser in Adaptern.

### S04 – Fehlervertrag und ein WebSocket-Hub

Pfade:

```text
src/alarmcast_server/transport/http/error_contracts.py
src/alarmcast_server/transport/realtime/contracts.py
src/alarmcast_server/transport/realtime/connection_hub.py
src/alarmcast_server/transport/realtime/ws_routes.py
```

Einziger WebSocket: `/api/v1/ws`. Ein einziger Event-Envelope. Noch keine fachlichen Events, Auth oder Persistenz.

## 7. STAGE-04 – Geraete, Admin, Nutzer, Sitzungen und Presence

### D01 – Lokale Geraeteidentitaet

Owner Desktop: `alarmcast/devices` und `alarmcast/settings`. Modell: UUID, Windows-Hostname, DPAPI-geschuetztes Geraetetoken. Keine MAC-ID, Registry-Parallelwahrheit oder Maschinenfingerprints.

### D02 – Serverseitige Geraeteregistrierung

Owner: `alarmcast_server/devices`. Tabellen ausschliesslich `devices` und `device_capabilities`. Routes unter `/api/v1/devices`, keine generischen CRUD-Routes.

### D03 – Heartbeat und DevicePresence

Owner: Server `devices/presence`, Desktop `devices`. Keine Presence-Tabelle; Status wird aus Verbindung/Heartbeat und `last_seen_at` abgeleitet.

### D04 – AdminAccount

Owner: `alarmcast_server/administration`. Tabelle `admin_accounts`. Dependency `argon2-cffi`. Kein `is_admin` in User, keine Admin-Gruppenmitgliedschaft und keine Admin-Chatinhalt-API.

### D05 – User und UserCapabilities

Owner: `alarmcast_server/identity`. Tabellen `users`, `user_capabilities`, `user_presence_preferences`. Keine Self-Signup-Route.

### D06 – User-Login und opaque Token

Owner: Server `sessions`, Desktop `identity`. Tabelle `user_sessions`. Kein JWT; Token nur gehasht serverseitig.

### D07 – Exklusive Session

Partielle Unique-Indizes fuer aktive Session je User und Device. Neue Anmeldung widerruft die alte Session atomar und sendet `session.revoked`.

### D08 – UserPresence

Status exakt `OFFLINE`, `AVAILABLE`, `AWAY`, `DO_NOT_DISTURB`. Keine zusaetzlichen Busy-/Invisible-Statuswerte und keine zweite Presence-Wahrheit im Client.

## 8. STAGE-05 – Messaging-Kern

### M01 – Conversation-Basis und Subtypen

Tabellen exakt:

```text
conversations
direct_conversations
device_conversations
group_conversations
```

Keine generische `conversation_memberships`-Tabelle und noch keine Messages/UI.

### M02 – Append-only Message

Tabelle exakt `messages`. Keine Edit-, Delete-, Recall-, Soft-Delete- oder Versionsfelder. `conversation_sequence` wird transaktional vergeben.

### M03 – Idempotentes Senden

Eindeutigkeit `(origin_device_id, client_message_id)`. Message-Commit vor Live-Zustellung. Kein Server-Broker und keine Server-Outbox in Version 1.

### M04 – Live-Zustellung

Nutzt ausschliesslich den einen WebSocket-Hub. Reconnect-Reconciliation bleibt REST-basiert; WebSocket ist keine dauerhafte Wahrheit.

### M05 – MessageDelivery

Tabelle exakt `message_deliveries`. Zustand nur `PENDING` oder `DELIVERED`; `SENT` ist aus erfolgreichem Message-Commit abgeleitet.

### M06 – ReadReceipt und DeviceAcknowledgement

Tabellen exakt:

```text
message_read_receipts
message_device_acknowledgements
```

Kein generisches Receipt-/Notification-Modell.

### M07 – Dauerhafter DirectConversation

Genau ein normalisiertes Userpaar. Kein zweiter Einzelchat und kein „neuen Chat starten“, das eine weitere Conversation erzeugt.

### M08 – Sieben-Tage-Abfrage und stabile Pagination

Filter nach Serverzeit; Sortierung und Cursor nach `conversation_sequence`. Keine Timestamp-only-Pagination.

### M09 – Einzige lokale SQLite-Datei und Cache

Datei exakt:

```text
%APPDATA%\AlarmCast\client-state.sqlite3
```

Tabellen exakt nach Domainmodell. Keine JSON-Cachedateien und keine zweite SQLite-Datei.

### M10 – Explizite Offline-Queues

Lokale Tabellen exakt:

```text
outbound_messages
pending_read_receipts
pending_device_acknowledgements
pending_reaction_changes
pending_alarmcast_log_events
```

Kein generischer Command-Bus und keine JSON-Datei als zweite Queue.

### M11 – DeviceConversation-Zugriff

Ein Devicechat pro Device. Vollverlauf nur am Zieldevice; externer Sender sieht nur eigene Device-Messages. Antwort an den urspruenglichen Nutzer erfolgt in der kanonischen DirectConversation.

### M12 – Inline-Referenz und Thread-Wurzel

Nur `reply_to_message_id` und `thread_root_message_id`. Keine Thread-Tabelle und keine sichtbare Thread-UI.

### M13 – Reaktionen

Tabelle exakt `message_reactions`. Feste `ReactionCode`; keine freien Emojis und keine Reaktion durch Device/Admin/System.

### M14 – Persoenlicher Conversation-Zustand und Reaktivierung

Tabelle exakt:

```text
user_conversation_states
```

Felder ausschliesslich `is_archived`, `is_pinned`, `is_muted` plus Schluessel/Zeitpunkt gemaess Domainmodell. Keine Direct-/Group-/Device-spezifischen Parallelmodelle.

Neue akzeptierte Message reaktiviert vorhandene archivierte States exakt nach `docs/domain-model-clarifications.md`:

- Direct: Absender und anderer Teilnehmer,
- Group: Absender und aktive Mitglieder,
- Device: Absender und aktueller Geraetenutzer, falls belegt.

`is_pinned` und `is_muted` bleiben unveraendert. Fehlende Zeile bedeutet Default aktiv und wird nicht vorsorglich angelegt. Abgelehnte oder nur lokale Nachrichten veraendern keinen Serverzustand.

Tests: explizites Archivieren/Reaktivieren, automatische Reaktivierung, Gruppenmitgliedschaft, unbesetztes Device, Erhalt von Pin/Mute und keine Aenderung bei fehlgeschlagener Sendung.

## 9. STAGE-06 – Gruppen

### G01 – Private GroupConversation

Erstellt `group_conversations` und erste `group_memberships`-Ownerzeile in einer Transaktion.

### G02 – Rollen und Hinzufuegen

Rechtematrix exakt nach Domainmodell; Serverautorisation ist verpflichtend.

### G03 – Entfernen und Hilfsadminverwaltung

Nur Owner entfernt Mitglieder. GroupAdmin darf Mitglieder hinzufuegen und Hilfsadmins verwalten, aber keinen Owner/Member entfernen, Eigentum uebertragen oder archivieren.

### G04 – Vollhistorie fuer neue Mitglieder

Keine Messagekopie und keine rueckwirkend erfundenen Delivery-Zeitpunkte.

### G05 – Kein Selbstaustritt

Keine Leave-Route und kein Leave-Button fuer Member, Admin oder Owner.

### G06 – Eigentumsuebergabe vor Deaktivierung

Genau ein aktiver Owner. User-Deaktivierung blockiert bis Transfer oder Archivierung.

### G07 – Gruppenarchivierung

`ACTIVE -> ARCHIVED`, read-only, kein Delete. Reaktivierung nur Adminprozess mit gueltigem aktivem Owner.

### G08 – Admin-Metadatenansicht

Admin sieht Gruppenname, Rollen, Mitglieder, Zeiten und Status; keine Message-/Screenshotfelder und keine inhaltliche Suche.

## 10. STAGE-07 – Desktop-Messaging

### U01 – Shell-Navigation und eigener Status

Erweitert ausschliesslich die bestehende `app_shell`; kein zweites Hauptfenster- oder Navigationsframework.

### U02 – Kontakt- und Geraeteliste

ViewModel liest typisierte Contracts. Widgets berechnen Presence nicht selbst.

### U03 – DirectChat-UI

Sieben Tage initial, aeltere Sequenzen nachladen, Sendestatus und ReadReceipt. Kein Edit/Delete/Recall. Archiv-/Pin-/Mute-Bedienung kommt erst in U08.

### U04 – DeviceChat-UI

Vollverlauf nur auf dem Zieldevice. Externer Senderbereich darf fremde Device-Messages nicht anzeigen. Device-ACK und User-READ getrennt darstellen.

### U05 – GroupChat-UI

Aktionen nach Gruppenrolle; Server bleibt Autoritaet. Archivierte Gruppe ist read-only.

### U06 – Inline-Zitat und Reaktion

Keine sichtbare Threadansicht und kein freier Emoji-Picker.

### U07 – Clipboard-Erfassung und lokale Screenshot-Vorschau

Dieses Inkrement ist **ausdruecklich preview-only**.

Implementiert:

- Windows-Clipboard auf Bilddaten pruefen,
- Bild lokal als PNG kodieren,
- Vorschau im Composer,
- Vorschau entfernen/ersetzen,
- Abbruch ohne Seiteneffekt,
- lokale Validierungsanzeige.

Nicht implementieren:

- keinen Screenshotversand,
- keine Screenshot-Message,
- keinen Serverupload,
- keine `screenshot_attachments`-Persistenz,
- keinen generischen Upload-/TemporaryUpload-/AttachmentDraft-Typ,
- keinen Windows-Smoke „bis Empfaenger“.

Bis N01 ist der Screenshot-Sendepfad deaktiviert oder eindeutig als noch nicht verfuegbar gekennzeichnet. Normaler Textversand bleibt funktionsfaehig.

Tests: Bild/kein Bild, Ersetzen, Entfernen, Abbruch, lokale PNG-Kodierung; Netzwerkadapter wird nicht aufgerufen.

### U08 – Persoenliche Chat-Organisation

UI fuer Archive, Pin und Mute nutzt ausschliesslich M14/`user_conversation_states`.

- Direct-, Group- und DeviceConversation koennen persoenlich archiviert, angeheftet und stummgeschaltet werden.
- Archivieren entfernt keine Historie und keine Suchberechtigung.
- Eine neue akzeptierte Nachricht laesst den Chat entsprechend M14 wieder in der aktiven Liste erscheinen.
- Pin/Mute bleiben bei Reaktivierung erhalten.
- Gruppenarchivierung nach G07 ist fachlich getrennt und darf nicht mit persoenlichem `is_archived` vermischt werden.

Tests: Archivliste, manuelles Reaktivieren, automatische Reaktivierung, Pin-/Mute-Erhalt und getrennte Darstellung archivierter Gruppen.

## 11. STAGE-08 – Screenshots, Suche und Dringlichkeit

### N01 – Server-Screenshotstore und echter End-to-End-Versand

**Abhaengigkeit:** U07, M02, M03, M06.  
**Verbindlicher Ablauf:** exakt `docs/domain-model-clarifications.md`.

Tabelle exakt:

```text
screenshot_attachments
```

Routen exakt:

```text
POST /api/v1/conversations/{conversation_id}/messages/screenshot
GET  /api/v1/screenshots/{attachment_id}
```

Der POST ist multipart mit genau einem typisierten `command`-Teil und einem `image/png`-Teil. Kein `/uploads`, kein Pre-Upload-Token, kein Base64-JSON/WebSocket und keine temporaere fachliche Uploadtabelle.

N01 verdrahtet den vorhandenen U07-Composer jetzt bis zum Versand und Empfaengerabruf. WebSocket enthaelt nur Metadaten.

Grenzen Version 1:

```text
20 MiB
16384 x 16384 Pixel
maximal 100000000 Pixel
nur gueltiges image/png
```

Tests: Idempotenz, MIME/PNG/Grenzen, Berechtigung, Rollback-Dateibereinigung, eng begrenzter Orphan-Check, autorisierter/verweigerter Abruf und keine Bildbytes im WebSocket.

Windows-Smoke gehoert hierher:

```text
Win+Shift+S -> einfuegen -> Vorschau -> senden ->
Empfaenger erhaelt Message -> Bild wird autorisiert geladen
```

### N02 – PostgreSQL-Suche

PostgreSQL-Volltextsuche mit serverseitigen Conversation-Zugriffsfiltern. Keine zweite Suchdatenbank und keine Admin-Fremdinhaltsuche.

### N03 – Urgency und DisplayMode

Nur Felder in `messages`: `urgency`, `urgent_display_mode`. Keine `urgent_messages`-Tabelle.

### N04 – Persistenter Urgent-Status

Abgeleitet aus `message_read_receipts` und `message_device_acknowledgements`. Keine parallele Notification-State-Tabelle. `HIDDEN` darf vor Oeffnen nicht als gelesen gelten.

### N05 – Rand-Overlay auf allen Monitoren

Erweitert den einzigen OverlayCoordinator um `URGENT_MESSAGE`. Alarmcast-Zentrum bleibt frei; Stapelung und Multi-Monitor-Geometrie sind getestet.

### N06 – Aktionen Oeffnen/Gelesen

`HIDDEN` bietet nur Oeffnen. FULL/PREVIEW bieten Oeffnen und Gelesen. Aktionen sind idempotent, autorisiert und navigieren zur kanonischen Conversation.

## 12. STAGE-09 – Alarmcast-Gesamtintegration

### I01 – Mehrquellen-Zuordnung

Tabelle exakt `alarm_monitor_assignments`. Keine `default_source_id`-Parallelwahrheit.

### I02 – Lokale Capability-Pruefung

Exakte User-/DeviceCapabilities. Start/Stop/Configure bleiben lokal; keine Fernsteuerungsroute.

### I03 – AlarmEvent, AlarmReset und LogSync

Tabellen exakt:

```text
alarm_events
alarm_resets
alarmcast_log_events
```

Kein Audiostream und keine generische All-Events-Tabelle.

### I04 – Persistente MonitoringFailure

Ein fachlicher Overlaytyp im Koordinator; Quelle und Fehlerart eindeutig. DND unterdrueckt nicht.

### I05 – Parallele Alarm-/Urgent-Anzeige

Getrennte Z-Order, Lifecycle und Bestaetigung. Kein gegenseitiges Clear oder Verdecken.

### I06 – Migration alter Alarmcast-Einstellungen

Migriert `host.json`, `client.json`, `mode.txt`, Autostart und Audioeinstellungen in das kanonische Settingsmodell. Quelldateien bleiben bis zur verifizierten erfolgreichen Migration erhalten.

## 13. STAGE-10 – Archiv, Backup und Windows-Betrieb

### O01 – Screenshot-Archivierung

Nur `ScreenshotStorageTier ACTIVE -> ARCHIVE`; Message und Suchmetadaten bleiben erhalten. Keine Altersloeschung.

### O02 – Konsistenter Backup-Satz

`pg_dump` Custom Format plus Datei-/Archivspeicher, Logs, Konfiguration und Manifest auf UNC-Netzlaufwerk. Tempbereich bis zur Validierung; unvollstaendiger Satz ist nicht restore-faehig.

### O03 – Rotation

Standard 7 taeglich, 4 woechentlich, 12 monatlich; administrativ anpassbar. Nie den einzigen gueltigen Satz loeschen.

### O04 – Integritaet und Restore

Restore als Subcommand im bestehenden Server-Entry-Point-Konzept, beispielsweise `python -m alarmcast_server restore`; kein dritter Produktentrypoint.

### O05 – Windows-Dienst

`pywin32`, genau ein Serverdienst. Kein NSSM/WinSW als zweite offizielle Betriebsart.

### O06 – Desktop-Build und Installer

PyInstaller und Inno Setup. Manueller/administrativer Updateprozess in Version 1; kein autonom erfundener Auto-Updater.

## 14. STAGE-11 – Systemabnahme

### R01 – Mehrclient-End-to-End

Server, zwei Userdevices, ein unbesetztes Device, Direct/Group/Device, persoenliches Archivieren/Reaktivieren, Offline-Queue, Screenshot, Urgent und Alarmcast.

### R02 – Ausfall und Wiederanlauf

Server, Netzwerk, Clientprozess, Alarmquelle, Audiooutput und Netzlaufwerk. Alarmcast bleibt direkt funktionsfaehig; keine Doppelmessages oder Doppelattachments nach Recovery.

### R03 – Traceability gegen Spezifikation

Jeder Spezifikationsabschnitt wird einem Inkrement, automatisierten Test, manuellen Test und Ergebnis zugeordnet. Besonders explizit: Screenshot-Versand erst N01 und persoenliches Chatarchiv M14/U08.

### R04 – Release Candidate

Versionierte Artefakte, Release Notes, Installations-, Backup- und Restore-Dokumentation. Kein neues Feature in diesem Inkrement.

## 15. Stop- und Reviewregeln

Codex stoppt innerhalb einer Etappe insbesondere, wenn:

- ein nicht gelistetes Modul, Typ, Route oder eine nicht gelistete Tabelle erforderlich erscheint,
- eine neue Dependency ausserhalb des Inkrements erforderlich ist,
- ein manuelles Hardwaregate fachliche Grundlage des naechsten Inkrements ist,
- ein Test nach zwei zielgerichteten Reparaturversuchen nicht gruen wird,
- bestehendes Alarmcast-Verhalten nicht bewahrt werden kann,
- Screenshotversand vor N01 erforderlich erscheint,
- fuer Archiv/Pin/Mute ein anderes Modell als `user_conversation_states` erforderlich erscheint.

Nach Etappenabschluss:

1. `tasks/ACTIVE_STAGE.md` auf `REVIEW` setzen,
2. Draft-PR gegen den dort genannten Zielbranch erstellen,
3. keine Folgeetappe aktivieren,
4. Agentenlauf beenden.
