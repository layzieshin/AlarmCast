# Verbindliche Domaenenklarstellungen

**Status:** verbindlich fuer Spezifikation 1.0  
**Zweck:** Diese Datei ergaenzt `docs/domain-model.md` an zwei Stellen, die fuer autonome Coding-Agents sonst Interpretationsspielraum lassen. Bei einem Widerspruch zu aelteren Roadmapformulierungen gilt diese Klarstellung.

## 1. Persoenlicher Conversation-Zustand

Die einzige Persistenz fuer nutzerbezogenes Archivieren, Anheften und Stummschalten ist die bereits definierte Tabelle:

```text
user_conversation_states
```

Es gibt keine getrennten Tabellen oder Felder wie:

```text
direct_chat_archives
group_chat_preferences
device_chat_settings
conversation.is_archived_for_users
user.archived_conversations_json
```

### 1.1 Defaultsemantik

Fehlt fuer ein User-/Conversation-Paar eine Zeile, gelten exakt diese Defaultwerte:

```text
is_archived = false
is_pinned   = false
is_muted    = false
```

Eine Zeile wird nur angelegt, wenn der Nutzer mindestens einen dieser Werte aktiv aendert. Eine neue Nachricht muss nicht vorsorglich Defaultzeilen fuer alle Teilnehmer erzeugen.

### 1.2 Archivieren

- Archivieren ist rein persoenliche Organisation.
- Es aendert weder Conversation, Mitgliedschaft, Verlauf, Berechtigung noch Delivery.
- Archivieren darf keine Nachricht loeschen oder aus der Suche entfernen.
- Ein Nutzer kann eine Conversation explizit archivieren und wieder aktivieren.
- `is_pinned` und `is_muted` bleiben bei Archivieren/Reaktivieren unveraendert.

### 1.3 Automatische Reaktivierung durch eine neue Nachricht

Nach erfolgreichem, serverseitigem Message-Commit werden vorhandene `user_conversation_states` der fachlich betroffenen Nutzer in derselben Transaktion wie folgt aktualisiert:

```text
is_archived = false
```

Betroffene Nutzer:

- `DIRECT`: Absender und anderer DirectConversation-Teilnehmer.
- `GROUP`: Absender und alle zum Sendezeitpunkt aktiven Gruppenmitglieder.
- `DEVICE`: menschlicher Absender sowie der aktuell angemeldete Nutzer des Zielgeraets, falls eine aktive UserSession besteht.

Fehlt eine State-Zeile, ist keine Anlage notwendig, weil der Default bereits `is_archived = false` ist.

Nicht veraendern:

```text
is_pinned
is_muted
```

Eine abgelehnte, lokal nur vorgemerkte oder permanent fehlgeschlagene Nachricht reaktiviert serverseitig nichts.

### 1.4 Tests

Mindestens pruefen:

- DirectConversation: beide vorhandenen Archivzustände werden nach akzeptierter Nachricht reaktiviert.
- GroupConversation: nur aktive Mitglieder werden reaktiviert.
- DeviceConversation: Absender und aktueller Geraetenutzer werden reaktiviert; unbesetztes Geraet erzeugt keinen erfundenen UserState.
- Fehlende State-Zeile bleibt fehlend und entspricht Default aktiv.
- `is_pinned` und `is_muted` bleiben erhalten.
- fehlgeschlagene Sendung aendert keinen Serverzustand.

## 2. Screenshot-Lebenszyklus

Es gibt kein allgemeines Uploadsystem und keine temporaere fachliche Uploadentitaet. Insbesondere nicht einfuehren:

```text
uploads
temporary_uploads
attachment_drafts
pending_files
file_tokens
generic_attachments
```

Die einzige fachliche Screenshotentitaet bleibt:

```text
screenshot_attachments
```

Sie besitzt immer eine gueltige `message_id`.

### 2.1 Trennung der Roadmap-Schritte

- `U07` implementiert ausschliesslich Clipboard-Erkennung, lokale PNG-Kodierung, Vorschau, Entfernen und Abbruch im Composer.
- `U07` sendet noch keinen Screenshot, erzeugt keine Screenshot-Message, legt keine Serverdatei an und fuehrt keinen Versand-Smoke-Test aus.
- Der Screenshot-Sendebutton bleibt bis `N01` fuer Screenshot-Drafts deaktiviert oder zeigt eindeutig „Server-Speicher noch nicht verfuegbar“; normaler Textversand bleibt unveraendert.
- `N01` implementiert Server-Speicher, autorisierten Abruf und die vollstaendige Verdrahtung des bereits vorhandenen U07-Composers bis zum Versand.

### 2.2 Exakter Versandweg in N01

Screenshotversand verwendet genau einen dedizierten REST-Endpunkt:

```text
POST /api/v1/conversations/{conversation_id}/messages/screenshot
Content-Type: multipart/form-data
```

Multipart-Teile:

```text
command  application/json  typisierter SendScreenshotMessageCommand
image    image/png         genau eine PNG-Datei
```

Der Command enthaelt dieselben kanonischen Identitaets-/Idempotenzdaten wie Textversand, insbesondere:

```text
client_message_id
origin_device_id
content_text          # optionaler Begleittext
urgency
urgent_display_mode
reply_to_message_id
thread_root_message_id
client_created_at
```

Nicht einfuehren:

- generischen `/uploads`-Endpunkt,
- Pre-Signed-URLs,
- Base64 in JSON oder WebSocket,
- Screenshotbytes in PostgreSQL,
- Dateinamen als fachliche Wahrheit,
- zweite Message- oder Attachmentart neben `Message` und `ScreenshotAttachment`.

### 2.3 Validierung Version 1

Der Desktop kodiert Clipboard-Bilder als PNG. Der Server akzeptiert genau:

```text
MIME-Type:         image/png
Maximale Groesse:  20 MiB
Maximale Breite:   16384 Pixel
Maximale Hoehe:    16384 Pixel
Maximale Flaeche:  100000000 Pixel
```

Leere, nicht dekodierbare, abgeschnittene oder Grenzwerte ueberschreitende Bilder werden vor Message-Commit abgelehnt.

### 2.4 Atomare fachliche Anlage

Verbindliche Reihenfolge:

1. Berechtigung und Command validieren.
2. PNG in einen serverseitigen Temp-Pfad streamen und dabei SHA-256 sowie Bytegroesse bestimmen.
3. Bild dekodieren und Dimensionen/Grenzen pruefen.
4. Datenbanktransaktion oeffnen.
5. kanonische `Message` mit Idempotenzpruefung anlegen.
6. finalen `storage_key` bestimmen und Temp-Datei atomar in den ACTIVE-Speicher verschieben.
7. `screenshot_attachments` in derselben Datenbanktransaktion anlegen.
8. Transaktion committen.
9. Bei Fehler vor Commit: verschobene Datei bestmoeglich entfernen und Fehler protokollieren.

Ein Prozessabsturz kann eine nicht referenzierte Datei hinterlassen. N01 implementiert deshalb einen eng begrenzten Orphan-Check fuer Dateien ohne `screenshot_attachments`-Zeile. Es wird keine generische File-Garbage-Collection erfunden.

Die Datenbank darf nach erfolgreichem Commit niemals auf einen nur temporaeren Pfad zeigen.

### 2.5 Zustellung und Abruf

- WebSocket-Ereignisse enthalten nur Message- und Attachmentmetadaten, niemals Bildbytes.
- Autorisierter Abruf erfolgt ausschliesslich ueber:

```text
GET /api/v1/screenshots/{attachment_id}
```

- Der Server prueft den Conversation-Zugriff des anfragenden Nutzers beziehungsweise die zulaessige DeviceConversation-Sicht.
- Systemadministratoren erhalten durch ihre Rolle keinen Screenshotinhalt.
- Der Client cached empfangene Screenshots innerhalb der einen kanonischen SQLite-/Cache-Struktur; keine zweite Screenshotdatenbank oder JSON-Indexdatei.

### 2.6 Idempotenz

Wird derselbe `client_message_id` erneut gesendet:

- entsteht keine zweite Message,
- entsteht kein zweites ScreenshotAttachment,
- wird keine zweite Datei dauerhaft abgelegt,
- liefert der Server die bereits akzeptierte Message-/Attachmentantwort.

### 2.7 Tests und Windows-Smoke

N01 prueft mindestens:

- gueltiges PNG mit und ohne Begleittext,
- Idempotenz bei Wiederholung und konkurrierender Wiederholung,
- falscher MIME-Type,
- ungueltige PNG-Daten,
- Byte-/Dimensions-/Flaechengrenzen,
- fehlende Conversation-Berechtigung,
- DB-Rollback und Dateibereinigung,
- absichtlich erzeugte Orphan-Datei und eng begrenzter Orphan-Check,
- autorisierter und verweigerter Abruf,
- keine Bildbytes im WebSocket.

Der Windows-Smoke-Test gehoert zu N01, nicht U07:

```text
Win+Shift+S -> in Composer einfuegen -> Vorschau -> senden ->
Empfaenger erhaelt Message -> Bild wird autorisiert geladen und angezeigt
```
