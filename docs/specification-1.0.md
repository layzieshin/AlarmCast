# Spezifikation 1.0 – Interne Messaging- und Alarmcast-Plattform

**Status:** freigegeben am 21.07.2026  
**Aenderungsregel:** Fachliche Abweichungen benoetigen eine neue ausdrueckliche Freigabe.  
**Zielplattform:** Windows-Desktop-Clients und zentraler Dienst im internen Firmennetz.

## 1. Produktziel

Die bestehende Alarmcast-Anwendung wird zu einer gemeinsamen internen Desktop-App erweitert. Sie kombiniert:

- klassische Kontakt- und Chatkommunikation nach dem Grundprinzip frueherer Desktop-Messenger,
- geraetebezogene Nachrichten,
- Einzel- und Gruppenchats,
- persistente dringliche Nachrichten,
- die vollstaendige bestehende Alarmcast-Funktion.

Messaging und Alarmcast bleiben fachlich getrennte Subsysteme. Alarmcast darf durch die Erweiterung keine bestehende Funktion verlieren.

## 2. Systemgrenzen

- Betrieb ausschliesslich im internen Firmennetz.
- Ein zentraler Messaging-Server laeuft dauerhaft auf einem Windows-Server.
- Kein Messaging-Mesh und keine konkurrierenden Client-Datenbanken.
- Clients duerfen geladene Daten lokal cachen und ungesendete Nachrichten persistent vormerken.
- Alarmcast-Audio, Alarmausloesung und Reset bleiben direkte LAN-Kommunikation zwischen Quelle und Ueberwachern.
- Alarmcast-Ereignislogs duerfen zusaetzlich zentral synchronisiert werden.
- Kein Browserclient, keine Mobile-App und kein oeffentlicher Internetbetrieb in Version 1.

## 3. Rechner und Nutzer

### 3.1 Rechner

- Die App meldet zuerst den Rechner an.
- Der offiziell verwaltete eindeutige Windows-PC-Name ist die sichtbare Geraetekennung.
- Zusaetzlich existiert intern eine stabile technische Geraete-ID.
- Ein Rechner kann online und erreichbar sein, ohne dass ein Nutzer angemeldet ist.
- Rechner koennen als Messaging-Client, Alarmcast-Quelle, Alarmcast-Ueberwacher oder in mehreren dieser Rollen betrieben werden.

### 3.2 Nutzer

- Nutzer werden ausschliesslich administrativ angelegt.
- Nutzernamen sind eindeutig und werden vom Administrator vorgegeben.
- Normale Nutzer koennen ohne oder mit Passwort betrieben werden.
- Konten mit administrativen oder Alarmcast-Steuerrechten muessen passwortgeschuetzt sein.
- Passwoerter werden nicht im Klartext gespeichert.
- Deaktivierte Nutzer bleiben in historischen Nachrichten und Gruppen nachvollziehbar.

### 3.3 Exklusive Sitzung

- Ein Nutzer darf genau eine aktive Sitzung besitzen.
- Meldet sich derselbe Nutzer an einem anderen Rechner an, beendet der Server die alte Sitzung und aktiviert die neue.
- Der bisherige Rechner bleibt als unbesetztes Geraet online.
- Alarmcast-Funktionen des bisherigen Rechners laufen weiter.

## 4. Statusmodell

Nutzerstatus:

- `OFFLINE`
- `AVAILABLE`
- `AWAY`
- `DO_NOT_DISTURB`

`AWAY` wird standardmaessig nach zehn Minuten lokaler Inaktivitaet gesetzt; der Wert ist konfigurierbar.

Geraetestatus wird getrennt modelliert:

- Netzwerkstatus,
- Belegungsstatus,
- Zustand als Alarmcast-Quelle,
- Zustand als Alarmcast-Ueberwacher.

`DO_NOT_DISTURB` unterdrueckt keine dringlichen Nachrichten, Alarmcast-Alarme oder Warnungen ueber eine gestoerte Alarmueberwachung.

## 5. Rollen und Rechte

### 5.1 Systemadministrator

Der `SYSTEM_ADMIN` darf:

- Nutzer, Geraete und Berechtigungen verwalten,
- Passwoerter zuruecksetzen,
- Alarmcast-Berechtigungen vergeben,
- verwaiste Gruppen einem neuen Eigentümer zuordnen oder archivieren,
- Backup-, Archiv- und technische Systemzustaende verwalten,
- technische und administrative Logs einsehen.

Die normale Administrationsoberflaeche darf ihm keine fremden Chatinhalte oder Screenshots anzeigen. Direkter technischer Server- oder Datenbankzugriff durch Serveradministratoren wird organisatorisch akzeptiert.

### 5.2 Alarmcast-Rechte

Rechte werden getrennt vergeben:

- `ALARMCAST_MONITOR_START_STOP`
- `ALARMCAST_SOURCE_START_STOP`
- `ALARMCAST_RESET`
- `ALARMCAST_CONFIGURE`

Start und Stopp erfolgen in Version 1 nur lokal am jeweiligen Rechner. Eine zentrale Fernsteuerung anderer PCs ist nicht vorgesehen. Reset darf an berechtigte Nutzer oder ausgewaehlte Geraete gebunden sein.

## 6. Einzelchats

- Fuer jedes Nutzerpaar existiert genau ein dauerhafter Einzelchat.
- Beim Oeffnen werden zunaechst die letzten sieben Tage geladen.
- Aeltere Nachrichten werden beim Hochscrollen oder ueber eine explizite Aktion nachgeladen.
- Chats koennen nutzerbezogen archiviert werden.
- Eine neue Nachricht reaktiviert einen archivierten Chat.

## 7. Geraetechats

- Jeder Nutzer darf jeden registrierten Rechner anschreiben.
- Jeder Rechner besitzt einen dauerhaften Geraetechat.
- Jeder Nutzer, der sich an diesem Rechner anmeldet, sieht den vollstaendigen bisherigen Geraetechat.
- Antworten auf eine Rechnernachricht gehen standardmaessig an den urspruenglichen menschlichen Absender.
- Geraetebestaetigung und Nutzer-Lesestatus werden getrennt gespeichert.

## 8. Gruppen

- Jeder Nutzer darf eine private Gruppe erstellen.
- Gruppen sind nur fuer bereits hinzugefuegte Mitglieder sichtbar.
- Es gibt kein oeffentliches Gruppenverzeichnis und keine frei beitretbaren Kanaele.
- Neue Mitglieder sehen den vollstaendigen bisherigen Verlauf.
- Mitglieder koennen eine Gruppe nicht selbst verlassen.
- Gruppen koennen archiviert, aber nicht uneinsehbar geloescht werden.

Gruppenrollen:

### `GROUP_OWNER`

Darf Mitglieder hinzufuegen und entfernen, Hilfsadministratoren verwalten, die Gruppe umbenennen, Eigentuemlichkeit uebertragen und die Gruppe archivieren.

### `GROUP_ADMIN`

Darf innerhalb der Gruppe Mitglieder hinzufuegen, Gruppeninformationen und Namen aendern sowie Hilfsadministratoren verwalten. Darf keine Mitglieder entfernen, den Eigentümer ersetzen oder die Gruppe archivieren.

### `MEMBER`

Darf lesen, schreiben, zitieren, reagieren und Screenshots senden.

Vor Deaktivierung eines Gruppeneigentuemers muss der Systemadministrator einen neuen Eigentümer bestimmen oder die Gruppe archivieren. Dabei sieht der Systemadministrator nur Metadaten, nicht den Chatinhalt.

## 9. Nachrichten

Empfängertypen:

- `USER`
- `DEVICE`
- `GROUP`

Version 1 unterstuetzt:

- Textnachrichten,
- Inline-Zitate,
- Reaktionen,
- Screenshots aus der Windows-Zwischenablage,
- normale und dringliche Nachrichten,
- technische Systemmeldungen,
- Alarmcast-bezogene Systemmeldungen.

Gesendete Nachrichten sind unveraenderlich. Sie koennen nicht bearbeitet, geloescht, zurueckgezogen oder ueberschrieben werden. Korrekturen erfolgen durch eine neue Nachricht.

Der Server vergibt den verbindlichen Zeitstempel. Zeitpunkte werden neutral beziehungsweise in UTC gespeichert und lokal dargestellt.

## 10. Lesestatus

Eine Nachricht gilt als gelesen, sobald der zugehoerige Chat geoeffnet wird.

- Einzelchat: `SENT`, `DELIVERED`, `READ`.
- Gruppe: Der Absender kann eine vollstaendige Leserliste mit Zeitstempeln oeffnen.
- Rechner gelten in Gruppen nicht als Leser.
- Geraetechat: `ACKNOWLEDGED_BY_DEVICE` und `READ_BY_USER` werden getrennt gefuehrt.

## 11. Inline-Zitate und Threads

Version 1 zeigt Inline-Zitate und verweist technisch auf die Ursprungsnachricht. Das Datenmodell wird threadfaehig aufgebaut, eine separate Thread-Oberflaeche gehoert jedoch nicht zu Version 1.

## 12. Reaktionen

Feste Auswahl:

`👍 👎 ✅ ❗ ❤️ 😂`

Ein Nutzer kann pro Nachricht eine eigene Reaktion setzen, aendern oder entfernen. Per Klick ist sichtbar, welche Nutzer reagiert haben.

## 13. Screenshots

- Unterstuetzt werden ausschliesslich Bilder aus der Windows-Zwischenablage.
- Einfuegen in den Nachrichteneditor zeigt vor dem Versand eine Vorschau.
- Kein allgemeiner Dateiupload, kein Office-Dateiversand und keine Virenscan-Funktion in Version 1.
- Screenshots liegen in einem verwalteten serverseitigen Dateispeicher; Metadaten und Zuordnung liegen in der Datenbank.

## 14. Dringliche Nachrichten

Jeder Nutzer darf eine Nachricht als dringlich markieren. Der Absender waehlt eine Darstellungsform:

1. vollstaendiger Text,
2. begrenzte Vorschau,
3. verdeckte Nachricht ohne Inhaltsvorschau.

Dringliche Nachrichten:

- erscheinen auf allen Monitoren am Bildschirmrand,
- bleiben dauerhaft im Vordergrund,
- verschwinden nicht automatisch,
- werden bei mehreren Nachrichten wie persistente Windows-Benachrichtigungen gestapelt,
- bleiben als normale Nachricht im Chatverlauf gespeichert.

Volltext und Vorschau bieten `Oeffnen` und `Gelesen`. Verdeckte Nachrichten bieten nur `Oeffnen`; erst nach dem Oeffnen koennen sie als gelesen gelten.

## 15. Alarmcast-Bestandsschutz

Folgende bestehende Funktionen muessen erhalten bleiben:

- WASAPI-Loopback-Aufnahme des Windows-Systemtons,
- direkte TCP-Audiouebertragung,
- mDNS-Discovery und manuelle Hostadresse,
- PSK-basierte Verbindung,
- konfigurierbare Signalmusterkennung,
- Multi-Monitor-Alarmoverlay,
- lokale Lautstaerke, Mute und Ausgabegeraet,
- Testton,
- Start, Stopp und Reset,
- Auto-Reconnect und Windows-Autostart,
- Status-, Informations- und bestaetigungspflichtige Meldungen,
- lokales Ereignisprotokoll.

Mehrere Alarmquellen werden unterstuetzt. Ein Ueberwacher kann mehreren Quellen zugeordnet sein; Standard ist eine Quelle.

## 16. Overlay-Regeln

- Alarmcast-Alarm: gross, pulsierend und zentral auf jedem Monitor.
- Dringliche Nachricht: persistent am Bildschirmrand.
- Beide Meldungstypen haben getrennte Bestaetigungen und duerfen einander nicht verdecken.
- Ein Alarmcast-Alarm besitzt hoechste visuelle Prioritaet.
- Der Ausfall einer konfigurierten Alarmueberwachung erzeugt eine dauerhafte, nicht durch `DO_NOT_DISTURB` unterdrueckbare Warnung.

## 17. Persistenz und Offlinebetrieb

- Jede bestaetigte Einstellung gilt nach Neustart weiter.
- Konfigurationen muessen atomar, schema-versioniert und migrationsfaehig gespeichert werden.
- Bestehende Daten unter `%APPDATA%\AlarmCast\` werden migriert, nicht ungefragt geloescht.
- Bei Messaging-Serverausfall bleiben geladene Chats lesbar.
- Neue Nachrichten werden persistent lokal vorgemerkt und nach Wiederverbindung idempotent uebertragen.
- Es gibt keinen Peer-to-Peer-Ersatzversand fuer Messaging.
- Alarmcast arbeitet bei Messaging-Serverausfall direkt weiter.
- Alarmcast-Logs werden spaeter nachgeliefert.

## 18. Aufbewahrung, Archiv und Suche

- Nachrichten werden unbegrenzt aufbewahrt.
- Nachrichtentexte und Suchindex bleiben zentral verfuegbar.
- Alte Screenshots werden standardmaessig nach zwoelf Monaten in einen getrennten Archivspeicher ausgelagert; die Frist ist administrativ anpassbar.
- Archivierung ist keine Loeschung.
- Suche darf nur Inhalte liefern, fuer die der suchende Nutzer fachlich berechtigt ist.

## 19. Backup

- Automatische Sicherung auf ein konfigurierbares Netzlaufwerk.
- Standardaufbewahrung: sieben taegliche, vier woechentliche und zwoelf monatliche Generationen.
- Datenbank, Dateispeicher, Archivindex, Alarmcast-Logs und Konfiguration bilden einen konsistenten Sicherungssatz.
- Unvollstaendige Sicherungen duerfen nicht als gueltig angeboten werden.
- Fehler werden protokolliert und dem Systemadministrator angezeigt.
- Ein dokumentierter und getesteter Wiederherstellungsweg ist erforderlich.

## 20. Nicht-Ziele Version 1

- Messaging-Mesh,
- Browserclient,
- Mobile-App,
- oeffentlicher Internetbetrieb,
- Audio- oder Videoanrufe,
- Sprachnachrichten,
- allgemeiner Dateiversand,
- Bearbeiten, Loeschen oder Rueckrufen gesendeter Nachrichten,
- sichtbare Thread-Oberflaeche,
- zentrale Fernsteuerung von Alarmcast-PCs,
- Aufzeichnung des Alarmcast-Audiostreams,
- Ende-zu-Ende-Verschluesselung.
