# Technische Zielarchitektur

## 1. Migrationsgrundsatz

Die bestehende Alarmcast-Anwendung wird nicht neu geschrieben. Der funktionsfaehige Host-/Client-Kern wird schrittweise hinter stabilen Fassaden gekapselt. Erst danach werden gemeinsame App-Shell, Messaging und Serverfunktionen angebunden.

Jedes Inkrement muss einen lauffaehigen Zwischenzustand hinterlassen. Bestehende Kommandozeilenstarts `--host` und `--client` bleiben waehrend der Migration kompatibel, bis ein spaeteres freigegebenes Inkrement sie ersetzt oder als Kompatibilitaetsmodus festschreibt.

## 2. Auslieferungseinheiten

```text
Windows-Desktop-App
├── gemeinsame PySide6-App-Shell
├── Geraete- und Nutzeranmeldung
├── Kontakt-, Gruppen- und Chatoberflaeche
├── lokaler Cache und Offline-Queue
├── Notification-/Overlay-Koordination
├── Alarmcast-Quelle (optionale Geraetefaehigkeit)
└── Alarmcast-Ueberwacher (optionale Geraetefaehigkeit)

Zentraler Windows-Server-Dienst
├── API und Echtzeitkanal
├── Benutzer-, Geraete- und Sitzungsverwaltung
├── Nachrichten- und Gruppenpersistenz
├── Screenshot- und Archivspeicher
├── Alarmcast-Log-Ingestion
└── Backup- und Restore-Jobs
```

Desktop und Server sind getrennte Prozesse und besitzen getrennte Entry Points. Neue Entry Points werden ausschliesslich in dem dafuer vorgesehenen Inkrement eingefuehrt.

## 3. Technologiewahl als kontrolliertes Gate

Die bestehende Desktop-Technik bleibt bis auf ausdrueckliche Entscheidung:

- Python 3.12,
- PySide6,
- `soundcard`, `sounddevice`, `numpy==1.26.4`,
- TCP-Protokoll und `zeroconf`,
- PyInstaller.

Server-Framework, Echtzeittransport und produktive Datenbank werden nicht beiläufig durch einen Agent gewaehlt. Das Roadmap-Inkrement `S01` erstellt einen ADR mit Kandidaten, Betriebsfolgen, Windows-Eignung, Testbarkeit und Migrationskosten. Erst nach menschlicher Freigabe darf der Servercode beginnen.

## 4. Desktop-Modulstruktur

Zielbild:

```text
src/alarmcast/
  app_shell/
    api.py
    contracts.py
    composition.py
    main_window.py
    tray.py

  settings/
    api.py
    contracts.py
    store.py
    migrations.py

  identity/
    api.py
    contracts.py
    session_controller.py

  devices/
    api.py
    contracts.py
    device_identity.py
    presence_client.py

  messaging/
    api.py
    contracts.py
    cache.py
    offline_queue.py
    sync_client.py
    ui/

  groups/
    api.py
    contracts.py
    permissions.py
    ui/

  notifications/
    api.py
    contracts.py
    overlay_coordinator.py
    urgent_overlay.py

  alarmcast_runtime/
    api.py
    contracts.py
    source_adapter.py
    monitor_adapter.py
    permissions.py

  core/       # bestehender gemeinsamer Alarmcast-Kern
  host/       # bestehende Alarmcast-Quelle
  client/     # bestehender Alarmcast-Ueberwacher
```

Die Struktur wird inkrementell eingefuehrt. Leere Zukunftsmodule oder spekulative Abstraktionen sind verboten.

## 5. Server-Modulstruktur

Nach Freigabe der Server-ADR:

```text
src/alarmcast_server/
  app.py
  composition.py

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
  administration/
  backup/

  infrastructure/
    database/
    realtime/
    filesystem/
    clock/
```

Jedes Fachmodul besitzt eine explizite oeffentliche Grenze. Datenbankmodelle und Repositories sind keine oeffentlichen Quermodul-APIs.

## 6. Oeffentliche Modulgrenzen

Ein Modul darf von anderen Modulen nur ueber folgende Artefakte verwendet werden:

- `api.py` fuer Operationen,
- `contracts.py` fuer unveraenderliche Commands, Queries, Events und DTOs,
- explizit dokumentierte Ports/Protocols.

Verboten:

- direkte Importe aus internen Repositories,
- direkte Nutzung fremder ORM-Modelle,
- GUI-Zugriff auf Datenbank oder Socketobjekte,
- Qt-Widgets in Domain- oder Serververtraegen,
- Datenbankobjekte in Desktopvertraegen,
- zyklische Modulabhaengigkeiten.

## 7. Alarmcast-Fassade

Der bestehende Alarmcast-Code wird hinter einer Fassade gekapselt, ohne das Protokoll zu aendern.

Beispielhafte Verträge:

```python
class AlarmcastRuntimeApi(Protocol):
    def start_source(self) -> None: ...
    def stop_source(self) -> None: ...
    def start_monitor(self) -> None: ...
    def stop_monitor(self) -> None: ...
    def reset_alarm(self, alarm_id: str) -> None: ...
    def snapshot(self) -> AlarmcastRuntimeSnapshot: ...
```

Die Fassade publiziert fachliche Statusereignisse. UI und Messaging kennen keine Low-Level-Sockets, Audiostreams oder Host-/Client-Threads.

## 8. App-Shell und Composition Root

Die App-Shell:

- erzeugt genau eine Qt-Anwendung,
- komponiert Module,
- besitzt Hauptfenster und Tray,
- koordiniert Start und geordnetes Herunterfahren,
- enthaelt keine Fachlogik.

Alle konkreten Implementierungen werden an einem dokumentierten Composition Root verdrahtet. Agents duerfen keine zusaetzlichen parallelen Composition Roots erfinden.

## 9. Nachrichtenmodell

Kernobjekte:

- `User`
- `Device`
- `UserSession`
- `Conversation`
- `ConversationMembership`
- `GroupRole`
- `Message`
- `MessageDelivery`
- `ReadReceipt`
- `Acknowledgement`
- `Reaction`
- `ScreenshotAttachment`

`Message` ist append-only. Lesestatus, Zustellung, Bestaetigung und Reaktionen sind eigene Datensaetze und veraendern den Nachrichtentext nicht.

Eine Nachricht besitzt mindestens:

- serverseitige opaque ID,
- clientseitige Idempotenz-ID,
- Conversation-ID,
- Absender-Nutzer und Absender-Geraet,
- Empfaengertyp,
- unveraenderlichen Inhalt,
- Dringlichkeits- und Vorschaumodus,
- optionalen Verweis auf eine zitierte Nachricht,
- Serverzeitpunkt,
- optionalen lokalen Entstehungszeitpunkt fuer Diagnose.

## 10. Idempotenz und Offline-Queue

```text
Client erstellt Nachricht
→ lokal persistent als QUEUED
→ sendet mit client_message_id
→ Server validiert Berechtigung und speichert atomar
→ Server bestaetigt message_id und server_timestamp
→ Client markiert ACCEPTED
```

Eine wiederholte Uebertragung derselben `client_message_id` darf keine doppelte Nachricht erzeugen.

Moegliche lokale Zustaende:

- `QUEUED`
- `SENDING`
- `ACCEPTED`
- `DELIVERED`
- `READ`
- `FAILED_RETRYABLE`
- `FAILED_PERMANENT`

## 11. Sitzungen und Presence

Der Server ist alleinige Quelle fuer aktive Nutzersitzungen. Eine neue Anmeldung erzeugt atomar eine neue Sitzung und widerruft eine bestehende Sitzung desselben Nutzers. Der alte Client erhaelt ein serverseitiges Logout-Ereignis.

Geraete-Presence basiert auf Heartbeats und Ablaufzeiten, nicht nur auf ordnungsgemaesser Abmeldung. Nutzer-Presence kombiniert aktive Sitzung, lokale Aktivitaet und manuell gesetzten Status.

## 12. Berechtigungspruefung

Berechtigungen werden serverseitig geprueft. Die GUI darf Schaltflaechen ausblenden oder deaktivieren, ersetzt aber keine serverseitige Autorisierung.

Besonders geschuetzt:

- Chatinhalte gegenueber Systemadministrations-APIs,
- Gruppenoperationen nach `GROUP_OWNER`, `GROUP_ADMIN`, `MEMBER`,
- lokale Alarmcast-Operationen nach Nutzer- oder Geraetecapability,
- Suche und Screenshotabruf nur innerhalb eigener Conversations.

## 13. Overlay-Koordination

Ein gemeinsamer technischer Overlay-Koordinator verwaltet getrennte Domänentypen:

- zentraler Alarmcast-Alarm,
- dringliche Nachricht am Bildschirmrand,
- Alarmcast-Status-/Informationsmeldung,
- dauerhafte Ueberwachungsausfallwarnung.

Der Koordinator entscheidet Position, Z-Order, Stapelung und Multi-Monitor-Verteilung. Fachliche Bestaetigungsregeln verbleiben in den jeweiligen Modulen.

## 14. Konfiguration

Das Settings-Modul ist alleiniger Besitzer lokaler Konfigurationsdateien.

Anforderungen:

- atomare Schreibvorgaenge,
- Schema-Version,
- explizite Migrationen,
- Backup beziehungsweise Wiederherstellung einer letzten gueltigen Konfiguration,
- keine stillen Komplettresets,
- Migration vorhandener `host.json`, `client.json` und `mode.txt`.

Andere Module duerfen keine eigenen JSON-Dateien ausserhalb dokumentierter Stores schreiben.

## 15. Speicherung, Archiv und Backup

- Nachrichtentexte und Metadaten liegen in der zentralen Datenbank.
- Screenshots liegen in einem verwalteten Dateispeicher; die Datenbank enthaelt Metadaten und Pruefsumme.
- Archivierung verschiebt alte Screenshots, nicht die fachliche Nachrichtenhistorie.
- Backup erzeugt einen konsistenten Satz aus Datenbank, Dateispeicher, Archivindex, Logs und Konfiguration.
- Restore wird als eigener, getesteter Betriebsweg umgesetzt.

## 16. Testarchitektur

Jede oeffentliche Grenze muss ohne GUI und echte Netzwerk- oder Audiogeraete testbar sein. Infrastruktur wird ueber Ports beziehungsweise austauschbare Adapter eingebunden.

Erforderliche Testarten:

- reine Domain-Unit-Tests,
- Persistenz- und Migrations-Integrationstests,
- API-/Realtime-Integrationstests,
- Architekturtests fuer Import- und Berechtigungsgrenzen,
- Windows-Smoke-Tests fuer WASAPI, Tray, Autostart, Zwischenablage und Multi-Monitor-Overlays,
- Mehrclient-End-to-End-Tests.

## 17. Aenderungsregeln

Folgende Entscheidungen benoetigen vor Umsetzung eine explizite ADR-Freigabe:

- neue Top-Level-Abhaengigkeiten,
- Server-Framework und Echtzeittransport,
- produktive Datenbank,
- Aenderung des Alarmcast-Netzwerkprotokolls,
- neue oeffentliche Modulgrenzen,
- Verschluesselungs- oder Authentifizierungsmodell,
- Installer- und Updateverfahren,
- Aenderung der Aufbewahrungs- oder Loeschregeln.
