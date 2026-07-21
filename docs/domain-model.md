# Kanonisches Domaenen- und Datenmodell

**Status:** verbindlich fuer Spezifikation 1.0  
**Zweck:** Diese Datei ist die einzige Namens- und Strukturquelle fuer fachliche Entitaeten, Persistenztabellen, Beziehungen, Rollen, Statuswerte und zentrale Invarianten.

Coding-Agents duerfen keine Synonyme, Parallelentitaeten, generischen Ersatzmodelle oder zusaetzlichen Tabellen erfinden. Eine Abweichung benoetigt einen ausdruecklich freigegebenen ADR und ein eigenes Migrationsinkrement.

## 1. Globale Konventionen

### 1.1 IDs

- Alle fachlichen Primaerschluessel sind UUIDv4.
- Python-Typen verwenden spezifische NewTypes oder Value Objects, keine austauschbaren rohe Strings.
- PostgreSQL-Spaltentyp: `uuid`.
- Fremdschluessel tragen den exakten Entitaetsnamen, z. B. `user_id`, `device_id`, `message_id`.
- Keine sprechenden IDs, zusammengesetzten String-IDs oder Auto-Increment-IDs fuer fachliche Entitaeten.
- Sequenznummern duerfen nur als sortierbare Nummer innerhalb einer Conversation verwendet werden.

### 1.2 Zeit

- PostgreSQL: `timestamptz`.
- Server schreibt UTC.
- Feldnamen enden auf `_at`.
- Keine naive lokale Zeit in Servertabellen.
- Clientzeit ist Diagnoseinformation und nie alleinige Reihenfolgenquelle.

### 1.3 Enums

- Im Domaincode zentral als `StrEnum` definiert.
- In PostgreSQL als `varchar` plus CHECK-Constraint, nicht als PostgreSQL-native Enumtypen.
- Keine duplizierten String-Literale in UI, Transport oder Tests.

### 1.4 Loeschen

- Nachrichten, Gruppenverlaeufe, Lesebestaetigungen, Alarmereignisse und Auditereignisse werden nicht physisch geloescht.
- Nutzer und Geraete werden deaktiviert.
- Gruppen werden archiviert.
- Screenshots wechseln die Speicherstufe; sie werden nicht altersbedingt geloescht.
- Es gibt kein generisches `deleted_at`, `is_deleted` oder Soft-Delete-Mixin.

### 1.5 JSON

JSON/JSONB ist **nicht** erlaubt fuer:

- Rollen oder Capabilities,
- Gruppenmitgliedschaften,
- Nachrichtentext und Nachrichtenstatus,
- Lesebestaetigungen,
- Reaktionen,
- Beziehungen zwischen Kernentitaeten,
- Sitzungszustand.

Ein begrenztes `details_json` ist nur in technischen Audit-/Logtabellen erlaubt und darf niemals fachliche Wahrheit, Chatinhalt, Geheimnisse oder Autorisierungsdaten enthalten.

## 2. Kanonische Enums

```text
UserStatusManual       = AVAILABLE | DO_NOT_DISTURB
UserPresence           = OFFLINE | AVAILABLE | AWAY | DO_NOT_DISTURB
DevicePresence         = OFFLINE | CONNECTION_UNSTABLE | ONLINE
DeviceCapability       = MESSAGING_CLIENT | ALARMCAST_SOURCE | ALARMCAST_MONITOR | ALARMCAST_RESET
UserCapability         = ALARMCAST_MONITOR_START_STOP | ALARMCAST_SOURCE_START_STOP | ALARMCAST_RESET | ALARMCAST_CONFIGURE
ConversationKind       = DIRECT | DEVICE | GROUP
GroupRole              = GROUP_OWNER | GROUP_ADMIN | MEMBER
GroupStatus            = ACTIVE | ARCHIVED
MessageAuthorKind      = USER | SYSTEM
MessageKind            = TEXT | SYSTEM
Urgency                = NORMAL | URGENT
UrgentDisplayMode      = FULL | PREVIEW | HIDDEN
DeliveryRecipientKind  = USER | DEVICE
DeliveryState          = PENDING | DELIVERED
ReactionCode           = THUMBS_UP | THUMBS_DOWN | CHECK | IMPORTANT | HEART | LAUGH
ScreenshotStorageTier  = ACTIVE | ARCHIVE
AlarmRuntimeState      = STOPPED | STARTING | RUNNING | FAULT
AlarmMonitorState      = NOT_CONFIGURED | STOPPED | STARTING | RUNNING | CONNECTION_LOST | FAULT
AlarmSourceState       = NOT_CONFIGURED | STOPPED | STARTING | RUNNING | ALARM_ACTIVE | FAULT
AlarmEventType         = ALARM_ACTIVATED | ALARM_RESET | SOURCE_STARTED | SOURCE_STOPPED | MONITOR_CONNECTED | MONITOR_DISCONNECTED | MONITORING_FAILURE | MONITORING_RECOVERED
CapabilityGrantedBy    = USER_CAPABILITY | DEVICE_CAPABILITY
SessionRevokeReason    = LOGOUT | REPLACED_BY_NEW_LOGIN | USER_DEACTIVATED | DEVICE_DEACTIVATED | ADMIN_REVOKED | EXPIRED
LocalOutboundState     = QUEUED | SENDING | ACCEPTED | FAILED_RETRYABLE | FAILED_PERMANENT
BackupState            = CREATING | VALIDATING | VALID | FAILED
```

UI-Emojis werden ausschliesslich auf `ReactionCode` gemappt:

```text
THUMBS_UP   -> 👍
THUMBS_DOWN -> 👎
CHECK       -> ✅
IMPORTANT   -> ❗
HEART       -> ❤️
LAUGH       -> 😂
```

## 3. Administrative Identitaet

### 3.1 Entitaet `AdminAccount`

Ein `AdminAccount` ist **keine** Chatidentitaet.

PostgreSQL-Tabelle: `admin_accounts`

```text
id                    uuid PK
username_normalized   varchar(100) NOT NULL UNIQUE
display_name          varchar(100) NOT NULL
password_hash         varchar(255) NOT NULL
is_active             boolean NOT NULL DEFAULT true
created_at            timestamptz NOT NULL
deactivated_at        timestamptz NULL
last_login_at         timestamptz NULL
```

Invarianten:

- Passwort ist verpflichtend.
- AdminAccount darf in keiner Conversation- oder Gruppenmitgliedschaft referenziert werden.
- AdminAccount besitzt keine UserCapability.
- Dieselbe Person benoetigt fuer Chatfunktionen ein separates `User`-Konto.
- Die normale Admin-API liefert keine Nachrichtentexte oder Screenshotinhalte.

Es gibt keine `SYSTEM_ADMIN`-Rolle in `users` und kein `is_admin`-Feld in der User-Tabelle.

## 4. Nutzer und Capabilities

### 4.1 Entitaet `User`

PostgreSQL-Tabelle: `users`

```text
id                    uuid PK
username_normalized   varchar(100) NOT NULL UNIQUE
display_name          varchar(100) NOT NULL
password_hash         varchar(255) NULL
is_active             boolean NOT NULL DEFAULT true
created_at            timestamptz NOT NULL
deactivated_at        timestamptz NULL
```

Invarianten:

- `username_normalized` wird serverseitig genau einmal normalisiert; keine zweite Casefold-Logik in UI oder Datenbankadapter.
- Ein Nutzer ohne Passwort darf keine aktive privilegierte UserCapability besitzen.
- Deaktivierung widerruft aktive Session und verhindert neue Logins.
- Historische Referenzen bleiben erhalten.

### 4.2 UserCapabilities

PostgreSQL-Tabelle: `user_capabilities`

```text
user_id       uuid FK users.id
capability    varchar(64) CHECK UserCapability
created_at    timestamptz NOT NULL
granted_by_admin_id uuid FK admin_accounts.id
PRIMARY KEY (user_id, capability)
```

Keine Bitmasken, JSON-Listen oder Capability-Strings direkt in `users`.

## 5. Geraete und Capabilities

### 5.1 Entitaet `Device`

PostgreSQL-Tabelle: `devices`

```text
id                    uuid PK
hostname_normalized   varchar(255) NOT NULL UNIQUE
display_name          varchar(255) NOT NULL
device_token_hash     char(64) NOT NULL
is_active             boolean NOT NULL DEFAULT true
registered_at         timestamptz NOT NULL
last_seen_at          timestamptz NULL
deactivated_at        timestamptz NULL
```

Invarianten:

- `display_name` entspricht in Version 1 dem aktuellen Windows-Hostname.
- Die interne UUID bleibt bei Hostname-Aenderung stabil.
- Klartext-Geraetetoken wird niemals serverseitig gespeichert oder geloggt.
- Ein erkannter UUID-/Token-Konflikt wird abgelehnt; keine automatische Zusammenfuehrung.

### 5.2 DeviceCapabilities

PostgreSQL-Tabelle: `device_capabilities`

```text
device_id      uuid FK devices.id
capability     varchar(64) CHECK DeviceCapability
created_at     timestamptz NOT NULL
granted_by_admin_id uuid FK admin_accounts.id
PRIMARY KEY (device_id, capability)
```

### 5.3 Alarmquellen-Zuordnung

PostgreSQL-Tabelle: `alarm_monitor_assignments`

```text
monitor_device_id   uuid FK devices.id
source_device_id    uuid FK devices.id
is_enabled          boolean NOT NULL DEFAULT true
created_at          timestamptz NOT NULL
created_by_admin_id uuid FK admin_accounts.id
PRIMARY KEY (monitor_device_id, source_device_id)
CHECK (monitor_device_id <> source_device_id)  # Selbstueberwachung ist Version 1 nicht vorgesehen
```

Invarianten:

- Monitor benoetigt `ALARMCAST_MONITOR`.
- Quelle benoetigt `ALARMCAST_SOURCE`.
- Mehrere Quellen pro Monitor sind erlaubt.
- Standardkonfiguration wird ueber eine einzelne Zuordnung hergestellt, nicht ueber ein separates `default_source_id`.

## 6. Nutzersitzung und Presence

### 6.1 Entitaet `UserSession`

PostgreSQL-Tabelle: `user_sessions`

```text
id                 uuid PK
user_id            uuid FK users.id
device_id          uuid FK devices.id
token_hash         char(64) NOT NULL UNIQUE
created_at         timestamptz NOT NULL
last_seen_at       timestamptz NOT NULL
revoked_at         timestamptz NULL
revoke_reason      varchar(64) NULL CHECK SessionRevokeReason
```

Datenbankinvarianten:

- partieller UNIQUE-Index auf `user_id WHERE revoked_at IS NULL`,
- partieller UNIQUE-Index auf `device_id WHERE revoked_at IS NULL`.

Fachliche Invarianten:

- Neue Anmeldung widerruft bestehende aktive Session desselben Users in derselben Transaktion.
- Eine aktive Session pro Device; ein PC ist nicht gleichzeitig durch zwei Nutzer belegt.
- Session-Token ist opaque; kein JWT.
- Klartexttoken wird nie persistiert oder geloggt.

### 6.2 Presence-Daten

Es gibt **keine** `presence`-Tabelle als zweite Wahrheit.

Persistiert werden:

PostgreSQL-Tabelle: `user_presence_preferences`

```text
user_id               uuid PK FK users.id
manual_status         varchar(32) CHECK UserStatusManual DEFAULT AVAILABLE
away_after_seconds    integer NOT NULL DEFAULT 600
updated_at            timestamptz NOT NULL
```

Abgeleitet werden:

- DevicePresence aus WebSocket/Heartbeat und `devices.last_seen_at`,
- UserPresence aus aktiver UserSession, DevicePresence, lokaler Inaktivitaet und `manual_status`.

WebSocket-Verbindungen sind ephemer im einzigen Serverprozess und keine fachliche DB-Entitaet.

## 7. Conversations – Basistyp und Subtypen

Es gibt genau eine Basistabelle und genau drei Subtyptabellen. Keine generische `conversation_memberships`-Tabelle fuer alle Typen.

### 7.1 Basistabelle `conversations`

```text
id          uuid PK
kind        varchar(16) NOT NULL CHECK ConversationKind
created_at  timestamptz NOT NULL
```

Invariante: Genau eine passende Subtypzeile pro Conversation, entsprechend `kind`.

### 7.2 Dauerhafter Einzelchat

PostgreSQL-Tabelle: `direct_conversations`

```text
conversation_id   uuid PK FK conversations.id
user_low_id       uuid FK users.id
user_high_id      uuid FK users.id
CHECK (user_low_id < user_high_id)
UNIQUE (user_low_id, user_high_id)
```

- Die UUID-Sortierung normalisiert das Paar.
- Genau ein Chat pro Nutzerpaar.
- Kein separates Participant- oder Membership-Modell.
- Beide Nutzer haben Zugriff, solange ihr Konto aktiv oder fuer historischen Zugriff zulaessig ist.

### 7.3 Geraetechat

PostgreSQL-Tabelle: `device_conversations`

```text
conversation_id   uuid PK FK conversations.id
device_id         uuid NOT NULL UNIQUE FK devices.id
```

Es gibt genau einen dauerhaften Geraetechat pro Device.

Zugriffsregel:

- Auf dem Zielgeraet: Der aktuell angemeldete User darf den vollstaendigen Geraetechat lesen.
- Ohne angemeldeten User darf die Desktop-App dringliche Geraetenachrichten anzeigen und als Device bestaetigen, aber keine Nutzer-Lesebestaetigung erzeugen.
- Ein User ausserhalb des Zielgeraets darf eine Nachricht an das Device senden und seine **eigenen** gesendeten Geraetenachrichten sehen, aber nicht den gesamten fremden Geraeteverlauf.
- Antworten auf eine Geraetenachricht werden als Nachricht in der kanonischen DirectConversation zum urspruenglichen User gesendet; es wird kein zweiter User-Device-Chat erzeugt.

Diese Regel wird in der Query-/Berechtigungsschicht umgesetzt. Es gibt keine zusaetzliche `DeviceChatParticipant`-Tabelle.

### 7.4 Gruppenchat

PostgreSQL-Tabelle: `group_conversations`

```text
conversation_id      uuid PK FK conversations.id
title                varchar(200) NOT NULL
status               varchar(16) NOT NULL CHECK GroupStatus DEFAULT ACTIVE
created_by_user_id   uuid NOT NULL FK users.id
archived_at          timestamptz NULL
archived_by_user_id  uuid NULL FK users.id
archived_by_admin_id uuid NULL FK admin_accounts.id
```

Invarianten:

- `archived_at` ist genau dann gesetzt, wenn `status = ARCHIVED`.
- Nur eine der Spalten `archived_by_user_id`, `archived_by_admin_id` darf gesetzt sein.
- Archivierte Gruppe ist read-only.
- Keine Delete-Operation.

## 8. Gruppenmitgliedschaften

PostgreSQL-Tabelle: `group_memberships`

```text
group_conversation_id uuid FK group_conversations.conversation_id
user_id                uuid FK users.id
role                   varchar(32) NOT NULL CHECK GroupRole
joined_at              timestamptz NOT NULL
added_by_user_id       uuid NULL FK users.id
removed_at             timestamptz NULL
removed_by_user_id     uuid NULL FK users.id
PRIMARY KEY (group_conversation_id, user_id, joined_at)
```

Indizes/Constraints:

- partieller UNIQUE-Index auf `(group_conversation_id, user_id) WHERE removed_at IS NULL`,
- partieller UNIQUE-Index auf `group_conversation_id WHERE role = 'GROUP_OWNER' AND removed_at IS NULL`.

Rechte:

| Operation | GROUP_OWNER | GROUP_ADMIN | MEMBER |
|---|---:|---:|---:|
| Nachricht lesen/senden | ja | ja | ja |
| Screenshot/Reaktion/Zitat | ja | ja | ja |
| Gruppe umbenennen | ja | ja | nein |
| Mitglied hinzufuegen | ja | ja | nein |
| Hilfsadmin ernennen/zurueckstufen | ja | ja, ausser Owner | nein |
| Mitglied entfernen | ja | nein | nein |
| Eigentuemlichkeit uebertragen | ja | nein | nein |
| Gruppe archivieren | ja | nein | nein |
| Selbst austreten | nein | nein | nein |

Weitere Invarianten:

- Owner kann nicht entfernt werden; zuerst Eigentuemlichkeit uebertragen oder Gruppe archivieren.
- Deaktivierung eines Owners ist blockiert, solange aktive Gruppen nicht uebertragen/archiviert wurden.
- Neue aktive Mitglieder sehen den gesamten historischen Verlauf.
- Entfernte Mitglieder erhalten keine neuen Nachrichten und keinen neuen Serverzugriff; bereits lokal gecachte Inhalte werden nicht nachtraeglich vom Client geloescht.
- Mitgliedschaftshistorie bleibt erhalten.

## 9. Nachrichten

### 9.1 Entitaet `Message`

PostgreSQL-Tabelle: `messages`

```text
id                    uuid PK
conversation_id       uuid NOT NULL FK conversations.id
conversation_sequence bigint NOT NULL
author_kind           varchar(16) NOT NULL CHECK MessageAuthorKind
author_user_id        uuid NULL FK users.id
origin_device_id      uuid NOT NULL FK devices.id
client_message_id     uuid NOT NULL
message_kind          varchar(16) NOT NULL CHECK MessageKind
content_text          text NULL
urgency               varchar(16) NOT NULL CHECK Urgency DEFAULT NORMAL
urgent_display_mode   varchar(16) NULL CHECK UrgentDisplayMode
reply_to_message_id   uuid NULL FK messages.id
thread_root_message_id uuid NULL FK messages.id
client_created_at     timestamptz NULL
created_at            timestamptz NOT NULL
UNIQUE (conversation_id, conversation_sequence)
UNIQUE (origin_device_id, client_message_id)
```

Autor-Constraints:

- `author_kind = USER` -> `author_user_id IS NOT NULL`.
- `author_kind = SYSTEM` -> `author_user_id IS NULL`.
- `origin_device_id` ist auch bei SYSTEM gesetzt und bezeichnet den Ursprung oder den Server-System-Device-Datensatz, falls spaeter explizit eingefuehrt.

Content-Invarianten:

- `message_kind = TEXT`: `content_text` darf leer sein, wenn mindestens ein ScreenshotAttachment zur Message existiert; diese Invariante prueft der Service transaktional.
- `message_kind = SYSTEM`: nur definierte Systemnachrichten-Contracts; kein freier technischer Logtext als Chatinhalt.
- `urgency = NORMAL` -> `urgent_display_mode IS NULL`.
- `urgency = URGENT` -> `urgent_display_mode IS NOT NULL`.
- `reply_to_message_id` muss in derselben Conversation liegen.
- `thread_root_message_id` ist bei einer Antwort die Wurzel derselben Conversation; keine sichtbare Thread-UI in Version 1.

Append-only-Invarianten:

- Keine Update- oder Delete-API fuer Message.
- Keine Spalten `edited_at`, `deleted_at`, `is_deleted`, `version` oder `replacement_message_id`.
- Korrekturen sind neue Messages.
- DB-Benutzer der Anwendung erhaelt fuer `messages` nach Moeglichkeit kein UPDATE-/DELETE-Recht; mindestens wird dies durch Repository-/Architekturtests abgesichert.

### 9.2 Conversation-Sequenz

`conversation_sequence` wird serverseitig innerhalb derselben Transaktion monoton vergeben.

- Pagination sortiert nach `(conversation_sequence, id)` beziehungsweise ausschliesslich nach der eindeutigen Sequenz.
- Keine Pagination nur anhand von Zeitstempeln.
- Die initiale Sieben-Tage-Abfrage verwendet `created_at` als Filter und `conversation_sequence` als stabile Sortierung.

## 10. Zustellung, Lesen und Bestaetigen

### 10.1 MessageDelivery

PostgreSQL-Tabelle: `message_deliveries`

```text
id                    uuid PK
message_id            uuid NOT NULL FK messages.id
recipient_kind        varchar(16) NOT NULL CHECK DeliveryRecipientKind
recipient_user_id     uuid NULL FK users.id
recipient_device_id   uuid NULL FK devices.id
state                 varchar(16) NOT NULL CHECK DeliveryState DEFAULT PENDING
created_at            timestamptz NOT NULL
delivered_at          timestamptz NULL
```

Constraints:

- USER -> nur `recipient_user_id` gesetzt.
- DEVICE -> nur `recipient_device_id` gesetzt.
- UNIQUE fuer die konkrete Message/Recipient-Kombination.
- `DELIVERED` erfordert `delivered_at`.

Semantik:

- `SENT` ist abgeleitet: Message wurde serverseitig gespeichert.
- Delivery wird nach erfolgreichem Message-Commit live versucht.
- Offline bleibt `PENDING`.
- Aktive Gruppenmitglieder zum Sendezeitpunkt erhalten User-Deliveries. Spaeter hinzugefuegte Nutzer sehen Historie, erhalten aber keine rueckwirkend erfundenen Delivery-Zeitpunkte.

### 10.2 MessageReadReceipt

PostgreSQL-Tabelle: `message_read_receipts`

```text
message_id       uuid FK messages.id
user_id          uuid FK users.id
read_via_device_id uuid FK devices.id
read_at          timestamptz NOT NULL
PRIMARY KEY (message_id, user_id)
```

- Chat-Oeffnung erzeugt idempotent Receipts fuer alle bis dahin ungelesenen, fuer den User sichtbaren Messages.
- Gruppenleserliste wird aus dieser Tabelle gebildet.
- Kein Device als Gruppenleser.
- Spaetere Oeffnung ueberschreibt `read_at` nicht.

### 10.3 MessageDeviceAcknowledgement

PostgreSQL-Tabelle: `message_device_acknowledgements`

```text
message_id                uuid FK messages.id
device_id                 uuid FK devices.id
acknowledged_by_user_id   uuid NULL FK users.id
acknowledged_at           timestamptz NOT NULL
PRIMARY KEY (message_id, device_id)
```

- Nur fuer DeviceConversation/Device-Delivery.
- Ohne User bleibt `acknowledged_by_user_id` NULL.
- Wenn ein User den Devicechat oeffnet, kann zusaetzzlich ein User-ReadReceipt entstehen.

### 10.4 Dringlichkeitszustand

Es gibt **keine** separate generische `urgent_messages`-Tabelle.

Der Overlayzustand wird abgeleitet:

- User-Empfaenger offen, solange kein `message_read_receipts`-Datensatz existiert.
- Device-Empfaenger offen, solange kein `message_device_acknowledgements`-Datensatz existiert.
- `HIDDEN` darf ueber UI nicht direkt bestaetigt werden; nur Oeffnen erzeugt den zulaessigen Receipt/Acknowledgement.
- FULL/PREVIEW duerfen Oeffnen oder explizites Gelesen verwenden.

## 11. Reaktionen

PostgreSQL-Tabelle: `message_reactions`

```text
message_id      uuid FK messages.id
user_id         uuid FK users.id
reaction_code   varchar(32) NOT NULL CHECK ReactionCode
created_at      timestamptz NOT NULL
updated_at      timestamptz NOT NULL
PRIMARY KEY (message_id, user_id)
```

- Genau eine Reaktion pro User/Message.
- Aendern aktualisiert ausschliesslich die Reaction-Zeile.
- Entfernen loescht die Reaction-Zeile; dies ist kein Loeschen der Message und kein Auditnachweis mit Langzeitpflicht.
- System/AdminAccount/Device koennen nicht reagieren.

## 12. Screenshots

PostgreSQL-Tabelle: `screenshot_attachments`

```text
id                 uuid PK
message_id         uuid NOT NULL FK messages.id
content_sha256     char(64) NOT NULL
mime_type          varchar(64) NOT NULL DEFAULT 'image/png'
byte_size          bigint NOT NULL
pixel_width        integer NOT NULL
pixel_height       integer NOT NULL
storage_tier       varchar(16) NOT NULL CHECK ScreenshotStorageTier DEFAULT ACTIVE
storage_key        varchar(500) NOT NULL UNIQUE
created_at         timestamptz NOT NULL
archived_at        timestamptz NULL
```

Invarianten:

- Version 1 akzeptiert nur Bilddaten aus der Windows-Zwischenablage.
- Kein allgemeiner Dateiname, Dateidialog oder beliebiger MIME-Typ.
- Keine Binaerdaten in `messages` oder WebSocket-Payloads.
- `ARCHIVE` erfordert `archived_at`.
- Umzug zwischen Speicherstufen veraendert nicht `message_id` oder fachliche Message.

## 13. Nutzerbezogener Conversation-Zustand

PostgreSQL-Tabelle: `user_conversation_states`

```text
user_id          uuid FK users.id
conversation_id  uuid FK conversations.id
is_archived      boolean NOT NULL DEFAULT false
is_pinned        boolean NOT NULL DEFAULT false
is_muted         boolean NOT NULL DEFAULT false
updated_at       timestamptz NOT NULL
PRIMARY KEY (user_id, conversation_id)
```

- Dies ist nur persoenliche UI-/Benachrichtigungsorganisation.
- Kein Lesecursor; Lesen liegt in `message_read_receipts`.
- Gruppenstatus `ARCHIVED` liegt in `group_conversations`, nicht hier.
- Neue Nachricht setzt persoenliches `is_archived` fuer berechtigte Empfaenger auf false; `is_pinned` und `is_muted` bleiben unveraendert.

## 14. Alarmcast-Ereignisse

### 14.1 AlarmEvent

PostgreSQL-Tabelle: `alarm_events`

```text
id                    uuid PK
source_device_id      uuid NOT NULL FK devices.id
source_event_id       uuid NOT NULL
occurred_at_client    timestamptz NOT NULL
received_at_server    timestamptz NOT NULL
created_at            timestamptz NOT NULL
UNIQUE (source_device_id, source_event_id)
```

- `source_event_id` ermoeglicht idempotentes Nachliefern nach Serverausfall.
- Ein AlarmEvent repraesentiert die Aktivierung; Reset ist eigene Entitaet.
- Kein Audio oder Nachrichtentext.

### 14.2 AlarmReset

PostgreSQL-Tabelle: `alarm_resets`

```text
id                    uuid PK
alarm_event_id        uuid NOT NULL FK alarm_events.id
reset_device_id       uuid NOT NULL FK devices.id
reset_user_id         uuid NULL FK users.id
capability_granted_by varchar(32) NOT NULL CHECK CapabilityGrantedBy
reset_at_client       timestamptz NOT NULL
received_at_server    timestamptz NOT NULL
UNIQUE (alarm_event_id)  # ein fachlich gueltiger Reset beendet den Alarm
```

- Reset ohne User ist nur ueber DeviceCapability erlaubt.
- Reset mit User dokumentiert User und Device.
- Doppelte Offline-Nachlieferung bleibt idempotent.

### 14.3 AlarmcastLogEvent

PostgreSQL-Tabelle: `alarmcast_log_events`

```text
id                   uuid PK
origin_device_id     uuid NOT NULL FK devices.id
client_event_id      uuid NOT NULL
event_type           varchar(64) NOT NULL CHECK AlarmEventType
related_source_device_id uuid NULL FK devices.id
occurred_at_client   timestamptz NOT NULL
received_at_server   timestamptz NOT NULL
details_json         jsonb NULL
UNIQUE (origin_device_id, client_event_id)
```

`details_json` darf nur nicht-sensitive technische Zusatzwerte enthalten. Verboten: Chatinhalt, PSK, Token, Passwort, Rollen- oder Berechtigungswahrheit.

## 15. Administrative Auditereignisse

PostgreSQL-Tabelle: `administration_audit_events`

```text
id               uuid PK
admin_account_id uuid NOT NULL FK admin_accounts.id
action_code      varchar(100) NOT NULL
target_kind      varchar(50) NOT NULL
target_id        uuid NOT NULL
occurred_at      timestamptz NOT NULL
details_json     jsonb NULL
```

- Append-only.
- `action_code` stammt aus einem zentralen Enum/Registry-Contract.
- `details_json` enthaelt nur alte/neue nicht-sensitive Metadaten, keine Chatinhalte oder Geheimnisse.
- Diese Tabelle ersetzt keine fachlichen Tabellen und steuert keine Autorisierung.

## 16. Backup-Metadaten

PostgreSQL-Tabelle: `backup_sets`

```text
id                uuid PK
state             varchar(16) NOT NULL CHECK BackupState
started_at        timestamptz NOT NULL
completed_at      timestamptz NULL
target_path       varchar(1000) NOT NULL
manifest_sha256   char(64) NULL
error_summary     text NULL
```

- `VALID` erfordert `completed_at` und `manifest_sha256`.
- Geheimnisse und Chattexte erscheinen nicht in `error_summary`.
- Rotation arbeitet nur mit `VALID`-Saetzen.

## 17. Serverseitige Ableitungen – keine zusaetzlichen Entitaeten

Folgende Dinge werden abgeleitet und erhalten keine parallele Wahrheitstabelle:

- `SENT`: Message existiert.
- UserPresence: Session + DevicePresence + Aktivitaet + manuelle Praeferenz.
- Device-Belegung: aktive UserSession fuer Device.
- Dringlichkeits-Overlay offen: fehlendes ReadReceipt/DeviceAcknowledgement.
- Gruppenleserliste: MessageReadReceipts.
- SearchDocument: PostgreSQL-Index/Ausdruck aus berechtigten Message-Daten, keine zweite bearbeitbare Messagekopie.
- Anzahl ungelesener Messages: Query aus sichtbaren Messages und ReadReceipts.

## 18. Kanonisches lokales SQLite-Modell

Datei:

```text
%APPDATA%\AlarmCast\client-state.sqlite3
```

Genau diese Tabellen sind vorgesehen:

### `local_schema_versions`

```text
component TEXT PRIMARY KEY
version INTEGER NOT NULL
applied_at TEXT NOT NULL  # UTC ISO-8601
```

### `cached_users`

```text
user_id TEXT PRIMARY KEY
display_name TEXT NOT NULL
presence TEXT NOT NULL
updated_at TEXT NOT NULL
```

### `cached_devices`

```text
device_id TEXT PRIMARY KEY
hostname TEXT NOT NULL
presence TEXT NOT NULL
occupant_user_id TEXT NULL
updated_at TEXT NOT NULL
```

### `cached_conversations`

```text
conversation_id TEXT PRIMARY KEY
kind TEXT NOT NULL
title TEXT NOT NULL
last_sequence INTEGER NOT NULL
updated_at TEXT NOT NULL
```

### `cached_messages`

```text
message_id TEXT PRIMARY KEY
conversation_id TEXT NOT NULL
conversation_sequence INTEGER NOT NULL
author_user_id TEXT NULL
origin_device_id TEXT NOT NULL
message_kind TEXT NOT NULL
content_text TEXT NULL
urgency TEXT NOT NULL
urgent_display_mode TEXT NULL
reply_to_message_id TEXT NULL
thread_root_message_id TEXT NULL
created_at TEXT NOT NULL
UNIQUE (conversation_id, conversation_sequence)
```

### `cached_group_memberships`

```text
group_conversation_id TEXT NOT NULL
user_id TEXT NOT NULL
role TEXT NOT NULL
is_active INTEGER NOT NULL
PRIMARY KEY (group_conversation_id, user_id)
```

### `outbound_messages`

```text
client_message_id TEXT PRIMARY KEY
origin_device_id TEXT NOT NULL
conversation_id TEXT NOT NULL
payload_json TEXT NOT NULL
state TEXT NOT NULL CHECK LocalOutboundState
attempt_count INTEGER NOT NULL DEFAULT 0
last_error_code TEXT NULL
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
```

`payload_json` ist hier ein versionierter Transportpayload fuer den bereits typisierten SendMessage-Command, kein generisches Domainmodell.

### `pending_read_receipts`

```text
message_id TEXT NOT NULL
user_id TEXT NOT NULL
read_via_device_id TEXT NOT NULL
read_at TEXT NOT NULL
PRIMARY KEY (message_id, user_id)
```

### `pending_device_acknowledgements`

```text
message_id TEXT NOT NULL
device_id TEXT NOT NULL
acknowledged_by_user_id TEXT NULL
acknowledged_at TEXT NOT NULL
PRIMARY KEY (message_id, device_id)
```

### `pending_reaction_changes`

```text
message_id TEXT NOT NULL
user_id TEXT NOT NULL
reaction_code TEXT NULL  # NULL bedeutet entfernen
updated_at TEXT NOT NULL
PRIMARY KEY (message_id, user_id)
```

### `pending_alarmcast_log_events`

```text
client_event_id TEXT PRIMARY KEY
payload_json TEXT NOT NULL
created_at TEXT NOT NULL
attempt_count INTEGER NOT NULL DEFAULT 0
```

### `sync_cursors`

```text
scope_key TEXT PRIMARY KEY
cursor_value TEXT NOT NULL
updated_at TEXT NOT NULL
```

Nicht anlegen:

- separate SQLite-Datei pro Modul,
- lokale User-/Admin-Passwortdatenbank,
- lokale Masterkopie von Capabilities,
- lokale PostgreSQL-Spiegelung,
- JSON-Datei als zweite Offline-Queue.

## 19. Zugriffsregeln nach ConversationKind

### DIRECT

- Lesen/Senden nur `user_low_id` und `user_high_id`.
- AdminAccount nie.
- Kein dritter Teilnehmer und kein „Person hinzufuegen“; dafuer neue Gruppe.

### GROUP

- Aktive Mitglieder duerfen gesamten Verlauf lesen.
- Senden nur bei `GroupStatus.ACTIVE` und aktiver Mitgliedschaft.
- Rollenrechte exakt nach Matrix.
- AdminAccount sieht nur Gruppenmetadaten ueber Administration-API.

### DEVICE

- Jeder aktive User darf senden.
- Vollstaendiger Verlauf nur fuer aktuelle UserSession auf dem Zieldevice.
- Sender ausserhalb des Device sieht nur eigene gesendete Device-Messages, nicht fremde Inhalte.
- Unbesetztes Device kann DeviceDelivery empfangen und DeviceAcknowledgement erzeugen.

## 20. Zustandsuebergaenge

### UserSession

```text
ACTIVE -> REVOKED(LOGOUT)
ACTIVE -> REVOKED(REPLACED_BY_NEW_LOGIN)
ACTIVE -> REVOKED(USER_DEACTIVATED)
ACTIVE -> REVOKED(DEVICE_DEACTIVATED)
ACTIVE -> REVOKED(ADMIN_REVOKED)
ACTIVE -> REVOKED(EXPIRED)
```

Keine Reaktivierung derselben Sessionzeile.

### GroupConversation

```text
ACTIVE -> ARCHIVED
ARCHIVED -> ACTIVE  # nur Systemadmin-Reaktivierung mit gueltigem neuem/aktivem Owner
```

Keine Loeschung.

### MessageDelivery

```text
PENDING -> DELIVERED
```

Keine Rueckstufung.

### ScreenshotAttachment

```text
ACTIVE -> ARCHIVE
ARCHIVE -> ACTIVE  # nur kontrollierter Restore/Rehydration-Fall
```

### LocalOutboundMessage

```text
QUEUED -> SENDING -> ACCEPTED
SENDING -> FAILED_RETRYABLE -> SENDING
SENDING -> FAILED_PERMANENT
```

`ACCEPTED` wird nach erfolgreicher Cache-Uebernahme spaeter entfernt; es entsteht keine zweite serverseitige Message.

## 21. Explizit verbotene Alternativmodelle

Nicht einfuehren:

- `Account` als Oberklasse fuer User und AdminAccount,
- `Actor`-Universaltabelle,
- `Participant` oder generische ConversationMembership fuer alle ConversationKinds,
- `Chat`, `ChatRoom`, `Channel` neben `Conversation`,
- User-Device-Paar-Conversations neben dem einen DeviceConversation pro Device,
- Nachrichtenversionen, Soft Delete oder Edit-Historie,
- generische `Notification`-Tabelle als Ersatz fuer Delivery/Receipt/Acknowledgement,
- generische `Activity`-/`Event`-Tabelle als Ersatz fuer Fachentitaeten,
- JSONB fuer Gruppenmitglieder oder Capabilities,
- `is_admin` in Users,
- Session-JWT-Payloads,
- ein zweites Presence-Modell im Client oder Server,
- ein serverseitiger Message Broker/Outbox in Version 1,
- eine zweite Suchdatenbank.
