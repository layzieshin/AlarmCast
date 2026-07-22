# Implementierungs-Roadmap

## 1. Zweck

Diese Roadmap zerlegt Spezifikation 1.0 in kleine, fachlich zusammenhaengende und einzeln pruefbare Codex-Inkremente. Codex bearbeitet pro Task und Draft-PR genau ein Inkrement.

Statuswerte:

- `PLANNED` – fachlich vorgesehen, aber noch nicht ausfuehrbar,
- `BLOCKED` – Voraussetzung oder menschliche Entscheidung fehlt,
- `READY` – einziges zur Umsetzung freigegebenes Inkrement,
- `IN_PROGRESS` – Codex-Task beziehungsweise PR laeuft,
- `REVIEW` – Umsetzung ist abgeschlossen und wird geprueft,
- `DONE` – Green Gate bestaetigt und gemergt.

Nur `tasks/ACTIVE_TASK.md` darf auf ein `READY`-Inkrement zeigen. Codex springt nach Abschluss niemals selbststaendig weiter.

## 2. Globales Green Gate

Jedes Inkrement muss zusaetzlich zu seinen eigenen Kriterien erfuellen:

1. sauberer Working Tree vor Beginn,
2. Baseline-Pruefung dokumentiert,
3. Scope und Nicht-Ziele eingehalten,
4. passende neue Tests vorhanden,
5. relevante Alt-Tests gruen,
6. `ruff check .` gruen,
7. `ruff format --check .` gruen,
8. `mypy src` gruen oder taskbezogen enger begruendet,
9. `pytest -q` gruen,
10. erforderlicher Windows-Smoke-Test dokumentiert,
11. keine unerwarteten Dateien oder Abhaengigkeiten,
12. Draft-PR mit Abschlussbericht.

## 3. Phase B – Baseline und Governance

### B00 – Originalen Alarmcast-Bestand importieren

**Status:** `DONE`
**Ziel:** Den originalen hochgeladenen Alarmcast-Stand unveraendert als Repository-Baseline herstellen.  
**Scope:** ZIP entpacken, generierte `*.egg-info`-Dateien ausschliessen, Bootstrap-ZIP entfernen, Dateiliste und SHA-256 dokumentieren. Keine Produktcodeaenderung.  
**Tests:** vorhandene Befehle ausfuehren; Abweichungen als Baseline dokumentieren; `python -m compileall src`.  
**Green Gate:** Inhalt entspricht dem Archiv; keine Secrets oder lokalen Konfigurationen; App-Quellcode, Tests und Builddateien liegen im Repo.

### B01 – Reproduzierbare Entwicklungsumgebung und CI

**Status:** `REVIEW`
**Abhaengigkeit:** B00.  
**Ziel:** Python-3.12-Umgebung und GitHub Actions fuer Baseline-Pruefungen.  
**Scope:** Lock-/Installationsweg dokumentieren, Windows-CI fuer Lint, Format, Typen und Tests; keine Produktfunktion.  
**Tests:** Workflow lokal soweit moeglich validieren; CI muss auf Pull Requests laufen.  
**Green Gate:** frischer Checkout kann anhand README eingerichtet werden; CI meldet Baseline reproduzierbar.

### B02 – Architektur- und Scope-Guards

**Status:** `PLANNED`  
**Abhaengigkeit:** B01.  
**Ziel:** Automatische Schutztests fuer bestehende und kuenftige Modulgrenzen.  
**Scope:** Tests gegen `core -> host/client`, `host <-> client`, verbotene Secrets/Configdateien und unerlaubte Entry Points.  
**Tests:** positive und negative Fixture-Faelle fuer jeden Guard.  
**Green Gate:** absichtlicher Regelverstoss laesst den Guard-Test fehlschlagen.

### B03 – Atomare, schema-versionierte Bestandskonfiguration

**Status:** `PLANNED`  
**Abhaengigkeit:** B02.  
**Ziel:** `host.json` und `client.json` sicher, versioniert und rueckwaertskompatibel speichern.  
**Scope:** atomarer Replace, Schema-Version, Migration unversionierter Dateien, Erhalt unbekannter oder dokumentiert verworfener Werte. Keine gemeinsame `app.json`.  
**Tests:** Erststart, Altdatei, defekte JSON-Datei, Schreibabbruch, Roundtrip.  
**Windows-Smoke:** bestehende Einstellungen bleiben nach Neustart erhalten.  
**Green Gate:** kein stiller Datenverlust; alte Konfiguration wird korrekt migriert.

## 4. Phase A – Alarmcast kapseln, Verhalten erhalten

### A01 – Alarmcast-Vertragsmodell

**Status:** `PLANNED`  
**Abhaengigkeit:** B03.  
**Ziel:** Unveraenderliche Contracts fuer Quelle, Ueberwacher, Alarmstatus, Verbindung und Reset.  
**Scope:** nur Contracts und Tests; keine UI- oder Laufzeitaenderung.  
**Tests:** Enum-/Dataclass-Invarianten, keine Qt-/Sockettypen in Contracts.  
**Green Gate:** Contracts bilden vorhandene Zustaende ohne Low-Level-Typen ab.

### A02 – Fassade der Alarmcast-Quelle

**Status:** `PLANNED`  
**Abhaengigkeit:** A01.  
**Ziel:** Capture, Detector und HostServer hinter einer Source-Fassade kapseln.  
**Scope:** Start, Stopp, Reset, Snapshot und fachliche Events; Netzwerkprotokoll unveraendert.  
**Tests:** Adaptertests mit Fakes; bestehende Hosttests gruen.  
**Windows-Smoke:** echter Host startet, erkennt Testsignal und resettiert.  
**Green Gate:** Host-UI benoetigt keine direkten Low-Level-Aufrufe ausserhalb der Fassade.

### A03 – Fassade des Alarmcast-Ueberwachers

**Status:** `PLANNED`  
**Abhaengigkeit:** A01.  
**Ziel:** Discovery, ClientNetwork, AudioOutput und Alarmanzeige hinter Monitor-Fassade kapseln.  
**Tests:** Reconnect, Mute, Lautstaerke, Hostwechsel, Statusmapping.  
**Windows-Smoke:** Audio, manuelle Adresse, mDNS, Testton und Reset funktionieren.  
**Green Gate:** Client-UI kennt keine Low-Level-Sockets oder Audio-Callbackobjekte.

### A04 – Gemeinsamer Alarmcast-Runtime-Service

**Status:** `PLANNED`  
**Abhaengigkeit:** A02, A03.  
**Ziel:** Quelle und Ueberwacher koennen als unabhaengige Geraetefaehigkeiten in einem Prozess komponiert werden.  
**Scope:** Lifecycle und Konfliktbehandlung; bestehende `--host`/`--client`-Starts bleiben kompatibel.  
**Tests:** Source-only, Monitor-only, beide, geordnetes Shutdown, Doppeltstart.  
**Green Gate:** keine gegenseitige Importabhaengigkeit zwischen Bestands-Host und -Client.

### A05 – Overlay-Koordinator-Grundgeruest

**Status:** `PLANNED`  
**Abhaengigkeit:** A04.  
**Ziel:** Technische Koordination mehrerer Overlaytypen ohne Messaging-Fachlogik.  
**Scope:** zentraler Alarm, bestehende Hostmeldungen, Ueberwachungsausfall-Platzhalter; Position und Prioritaet als Contracts.  
**Tests:** Prioritaet, Multi-Monitor-Zielmenge, getrenntes Clear.  
**Windows-Smoke:** bestehender Alarm erscheint weiterhin auf allen Monitoren.  
**Green Gate:** Bestandsalarm wird ueber Koordinator angezeigt, ohne Verhaltensverlust.

### A06 – Gemeinsame Desktop-App-Shell

**Status:** `PLANNED`  
**Abhaengigkeit:** A04, A05.  
**Ziel:** genau eine Qt-App, ein Tray und ein Composition Root.  
**Scope:** Shell und Capability-Auswahl; noch kein Messaging.  
**Tests:** Startup, Single Instance, Capability-Kombinationen, Shutdown.  
**Windows-Smoke:** Tray, gespeicherter Modus und Alt-CLI funktionieren.  
**Green Gate:** keine parallelen Qt-Entry-Points ausser dokumentierter Kompatibilitaet.

## 5. Phase S – Serverentscheidungen und Serverfundament

### S01 – ADR: Server, Echtzeittransport und Datenbank

**Status:** `PLANNED`  
**Abhaengigkeit:** B01.  
**Ziel:** Vergleich und Freigabe der produktiven Servertechnologien fuer Windows-Betrieb.  
**Scope:** ADR mit Kandidaten, Betriebsmodell, Migrationen, Transaktionen, Echtzeit, Backup, Testbarkeit und Lizenz; kein Produktcode und keine neue Dependency.  
**Tests:** nicht anwendbar; Plausibilitaets- und Entscheidungscheckliste.  
**Green Gate:** menschlich freigegebener ADR. Ohne Freigabe bleibt S02 blockiert.

### S02 – Server-Paket und Health-Endpunkt

**Status:** `BLOCKED` bis S01 freigegeben.  
**Abhaengigkeit:** S01.  
**Ziel:** minimaler Serverprozess mit genau einem Entry Point und Health-Status.  
**Scope:** Composition Root, Konfiguration, strukturierte Logs, kontrolliertes Shutdown; keine Fachdaten.  
**Tests:** Start/Stop, Health, ungueltige Konfiguration, Portkonflikt.  
**Green Gate:** Server laeuft auf Windows-Testumgebung reproduzierbar.

### S03 – Datenbankbasis und Migrationen

**Status:** `PLANNED`  
**Abhaengigkeit:** S02.  
**Ziel:** transaktionale Persistenz, Migrationsrunner und Testdatenbank.  
**Scope:** Infrastruktur, keine fachlichen Tabellen ausser technischer Migrationstabelle.  
**Tests:** leere DB, Upgrade, Rollback-/Fehlerfall, paralleler Start.  
**Green Gate:** frische und bestehende Testdatenbank erreichen denselben Schema-Stand.

### S04 – Serverseitige Uhr, IDs und Transaktions-Ports

**Status:** `PLANNED`  
**Abhaengigkeit:** S03.  
**Ziel:** zentrale opaque IDs, UTC-Zeit und testbare Transaktionsgrenzen.  
**Tests:** deterministische Fake-Clock, ID-Eindeutigkeit, Rollback.  
**Green Gate:** Fachmodule verwenden keine direkte Systemzeit oder zufaellige IDs ausser ueber Ports.

## 6. Phase D – Geraete, Nutzer und Sitzungen

### D01 – Stabile lokale Geraeteidentitaet

**Status:** `PLANNED`  
**Abhaengigkeit:** A06, S04.  
**Ziel:** interne Geraete-ID plus administrierter Windows-Hostname.  
**Tests:** Erststart, Neustart, Hostname-Aenderung, kopierte Konfiguration.  
**Green Gate:** Geraete-ID bleibt stabil; sichtbarer Name folgt dem Windows-PC-Namen.

### D02 – Geraeteregistrierung am Server

**Status:** `PLANNED`  
**Abhaengigkeit:** D01.  
**Ziel:** Registrierung und Aktualisierung eines Geraets ohne Nutzeranmeldung.  
**Tests:** neu, bekannt, umbenannt, doppelte ID, ungueltiger Hostname.  
**Green Gate:** Server fuehrt eindeutige Geraete ohne Chatfunktion.

### D03 – Heartbeat und Geraete-Presence

**Status:** `PLANNED`  
**Abhaengigkeit:** D02.  
**Ziel:** `ONLINE`, `OFFLINE`, `CONNECTION_UNSTABLE` durch Heartbeat und Ablaufzeit.  
**Tests:** regelmaessig, Timeout, Wiederkehr, geordnetes Logout, Serverneustart.  
**Green Gate:** abrupt beendeter Client wird ohne explizites Logout offline.

### D04 – Systemadministrator-Prinzipal

**Status:** `PLANNED`  
**Abhaengigkeit:** S04.  
**Ziel:** administrative Identitaet ohne automatische Chatmitgliedschaft.  
**Tests:** Admin-Metadatenzugriff erlaubt, Chatinhalt-API verweigert.  
**Green Gate:** Adminrolle erzeugt keine Conversation-Berechtigung.

### D05 – Administrative Nutzerverwaltung

**Status:** `PLANNED`  
**Abhaengigkeit:** D04.  
**Ziel:** Nutzer anlegen, umbenennen, deaktivieren und Passwort zuruecksetzen.  
**Tests:** eindeutige Namen, Deaktivierung, Passwort optional, privilegiertes Konto ohne Passwort verboten.  
**Green Gate:** normale Nutzer koennen keine Konten selbst erstellen.

### D06 – Nutzeranmeldung

**Status:** `PLANNED`  
**Abhaengigkeit:** D05, D02.  
**Ziel:** Anmeldung mit optionalem Passwort und Geraetebindung der Sitzung.  
**Tests:** ohne Passwort, korrekt/falsch, deaktiviert, unbekannt.  
**Green Gate:** Passwort-Hash statt Klartext; Fehler geben keine sensiblen Details preis.

### D07 – Exklusive Nutzersitzung

**Status:** `PLANNED`  
**Abhaengigkeit:** D06.  
**Ziel:** genau eine aktive Sitzung je Nutzer.  
**Tests:** erste Anmeldung, Wechsel auf zweiten PC, Rennen zweier Logins, alter Client erhaelt Logout.  
**Green Gate:** zu keinem Zeitpunkt bleiben zwei gueltige Sitzungen bestehen.

### D08 – Nutzer-Presence

**Status:** `PLANNED`  
**Abhaengigkeit:** D07, D03.  
**Ziel:** `OFFLINE`, `AVAILABLE`, `AWAY`, `DO_NOT_DISTURB`.  
**Tests:** Inaktivitaet, manueller Status, Logout, Geraeteausfall.  
**Green Gate:** dringliche und Alarmwarnungen werden durch DND nicht unterdrueckt.

## 7. Phase M – Messaging-Kern

### M01 – Conversation- und Mitgliedschaftsmodell

**Status:** `PLANNED`  
**Abhaengigkeit:** D07.  
**Ziel:** gemeinsame Grundlage fuer User-, Device- und Group-Conversations.  
**Tests:** Typinvarianten, Mitgliedschaft, Berechtigungsabfragen.  
**Green Gate:** keine Nachrichtentabelle und keine UI in diesem Inkrement.

### M02 – Append-only-Nachrichtenpersistenz

**Status:** `PLANNED`  
**Abhaengigkeit:** M01.  
**Ziel:** unveraenderliche Textnachricht mit Serverzeitpunkt.  
**Tests:** Insert/Read, kein Update-/Delete-Pfad, Transaktionsfehler.  
**Green Gate:** oeffentliche API bietet keine Bearbeitungs- oder Loeschoperation.

### M03 – Senden mit Idempotenz-ID

**Status:** `PLANNED`  
**Abhaengigkeit:** M02.  
**Ziel:** Send-Command mit `client_message_id` und serverseitiger Duplikatvermeidung.  
**Tests:** Wiederholung, konkurrierende Wiederholung, unberechtigter Sender, ungueltiger Empfaenger.  
**Green Gate:** identische Client-ID erzeugt genau eine Nachricht.

### M04 – Echtzeitzustellung

**Status:** `PLANNED`  
**Abhaengigkeit:** M03, S02.  
**Ziel:** neue Nachrichten an aktive berechtigte Clients ausliefern.  
**Tests:** online, offline, Reconnect, mehrere Teilnehmer, keine Fremdzustellung.  
**Green Gate:** Persistenz ist erfolgreich, auch wenn Live-Zustellung scheitert.

### M05 – Zustellungsstatus

**Status:** `PLANNED`  
**Abhaengigkeit:** M04.  
**Ziel:** `SENT` und `DELIVERED` getrennt pro Ziel fuehren.  
**Tests:** offline, mehrfacher Clientversuch, Wiederholung, Gruppenfanout.  
**Green Gate:** Statusaenderungen veraendern die Nachricht nicht.

### M06 – Lesebestaetigung

**Status:** `PLANNED`  
**Abhaengigkeit:** M05.  
**Ziel:** Chat-Oeffnung markiert alle bis dahin vorliegenden Nachrichten gelesen.  
**Tests:** Einzelchat, Gruppe, bereits gelesen, spaeter eintreffende Nachricht, unberechtigter Leser.  
**Green Gate:** Gruppenleserliste enthaelt Nutzer und Zeit, keine Geraete.

### M07 – Dauerhafter Einzelchat

**Status:** `PLANNED`  
**Abhaengigkeit:** M06.  
**Ziel:** genau eine Conversation pro Nutzerpaar.  
**Tests:** Reihenfolge der Nutzer, konkurrierende Erstellung, Wiederverwendung.  
**Green Gate:** parallele Einzelchats desselben Paars sind technisch verhindert.

### M08 – Sieben-Tage-Ladung und Pagination

**Status:** `PLANNED`  
**Abhaengigkeit:** M07.  
**Ziel:** initial letzte sieben Tage, aeltere Seiten stabil nachladen.  
**Tests:** Grenzzeitpunkt, gleiche Zeitstempel, leere Seite, keine Duplikate/Luecken.  
**Green Gate:** sortierte Pagination ist deterministisch.

### M09 – Lokaler Chatcache

**Status:** `PLANNED`  
**Abhaengigkeit:** M08.  
**Ziel:** geladene Unterhaltungen nach Serverausfall lesbar halten.  
**Tests:** Neustart, Cache-Migration, Beschädigung, Berechtigungswechsel.  
**Green Gate:** Cache ist nicht die serverseitige Wahrheitsquelle.

### M10 – Persistente Offline-Ausgangswarteschlange

**Status:** `PLANNED`  
**Abhaengigkeit:** M03, M09.  
**Ziel:** lokale Queue mit Retry und sichtbarem Wartestatus.  
**Tests:** Neustart, Verbindungsabbruch waehrend Sendung, Retry, permanent ungueltig, Reihenfolge.  
**Green Gate:** kein Peer-to-Peer-Ersatzversand; keine Doppelanlage.

### M11 – Geraetechat

**Status:** `PLANNED`  
**Abhaengigkeit:** M06, D02.  
**Ziel:** jeder Nutzer kann jedes registrierte Geraet anschreiben.  
**Tests:** unbesetztes Geraet, spaetere Anmeldung, kompletter Verlauf, Antwort an urspruenglichen Nutzer.  
**Green Gate:** Geraete-ACK und Nutzer-READ bleiben getrennt.

### M12 – Inline-Zitat und threadfaehige Referenz

**Status:** `PLANNED`  
**Abhaengigkeit:** M08.  
**Ziel:** `reply_to_message_id` und `thread_root_message_id` ohne Thread-UI.  
**Tests:** gueltige/fremde/fehlende Ursprungsnachricht, Archivhistorie.  
**Green Gate:** Zitat verweist auf Original statt Textkopie als alleinige Wahrheit.

### M13 – Reaktionen

**Status:** `PLANNED`  
**Abhaengigkeit:** M02.  
**Ziel:** feste Reaktionen setzen, aendern und entfernen.  
**Tests:** eine Reaktion pro Nutzer/Nachricht, Wechsel, Remove, Fremdzugriff.  
**Green Gate:** Reaktion ist eigener Datensatz; Nachricht bleibt unveraendert.

## 8. Phase G – Gruppen

### G01 – Gruppenerstellung und private Sichtbarkeit

**Status:** `PLANNED`  
**Abhaengigkeit:** M01.  
**Ziel:** jeder Nutzer kann eine private Gruppe erstellen und wird Eigentümer.  
**Tests:** Nichtmitglied sieht Gruppe nicht; kein oeffentliches Listing.  
**Green Gate:** Gruppe ist nur fuer Mitglieder auffindbar.

### G02 – Gruppenrollen und Hinzufuegen

**Status:** `PLANNED`  
**Abhaengigkeit:** G01.  
**Ziel:** `GROUP_OWNER`, `GROUP_ADMIN`, `MEMBER` und Hinzufuegen nach Rechteprofil.  
**Tests:** Rechte-Matrix inklusive negativer Faelle.  
**Green Gate:** Hilfsadmin darf hinzufuegen, aber nicht entfernen.

### G03 – Entfernen und Adminverwaltung

**Status:** `PLANNED`  
**Abhaengigkeit:** G02.  
**Ziel:** nur Eigentümer entfernt Mitglieder; Hilfsadmins verwalten innerhalb der freigegebenen Grenzen.  
**Tests:** Eigentümer nicht durch Hilfsadmin entfernbar; Rollenwechsel.  
**Green Gate:** serverseitige Autorisierung unabhaengig von UI.

### G04 – Vollstaendige Historie fuer neue Mitglieder

**Status:** `PLANNED`  
**Abhaengigkeit:** G03, M08.  
**Ziel:** neues Mitglied sieht gesamten bisherigen Verlauf.  
**Tests:** Eintrittszeitpunkt, Pagination, Lesestatus startet korrekt.  
**Green Gate:** historische Nachrichten werden nicht kopiert oder umgeschrieben.

### G05 – Kein Selbstaustritt

**Status:** `PLANNED`  
**Abhaengigkeit:** G03.  
**Ziel:** Selbstentfernung wird fachlich und API-seitig verhindert.  
**Tests:** Member, Admin und Owner versuchen Austritt.  
**Green Gate:** nur Eigentümeroperation oder Systemprozess kann Mitgliedschaft beenden.

### G06 – Eigentuemlichkeit und Nutzerdeaktivierung

**Status:** `PLANNED`  
**Abhaengigkeit:** G03, D05.  
**Ziel:** Eigentümertransfer oder Archivierung vor Deaktivierung.  
**Tests:** aktive Gruppen blockieren Deaktivierung; Transfer; mehrere Gruppen; Rennen.  
**Green Gate:** keine aktive Gruppe ohne aktiven Eigentümer.

### G07 – Gruppenarchivierung

**Status:** `PLANNED`  
**Abhaengigkeit:** G06.  
**Ziel:** read-only Archiv statt Loeschung.  
**Tests:** Schreiben verweigert, Lesen/Suche erlaubt, Reaktivierung mit neuem Eigentümer.  
**Green Gate:** kein physischer Delete-Pfad fuer Gruppe oder Verlauf.

### G08 – Systemadmin-Metadatenansicht

**Status:** `PLANNED`  
**Abhaengigkeit:** G07, D04.  
**Ziel:** verwaiste Gruppen verwalten, ohne Nachrichteninhalt anzuzeigen.  
**Tests:** Metadaten erlaubt; Nachrichten, Screenshots und Suche verweigert.  
**Green Gate:** Admin-API serialisiert keine Content-Felder.

## 9. Phase U – Desktop-Messaging-Oberflaeche

### U01 – App-Shell-Navigation und eigener Status

**Status:** `PLANNED`  
**Abhaengigkeit:** A06, D08.  
**Ziel:** klassische Messenger-Grundstruktur mit eigenem Nutzer- und Rechnerstatus.  
**Tests:** ViewModel/Controller ohne echte GUI; Startupzustand.  
**Windows-Smoke:** Tray und Hauptfenster.  
**Green Gate:** UI enthaelt keine direkte Netzwerk- oder Persistenzlogik.

### U02 – Kontakt- und Geraeteliste

**Status:** `PLANNED`  
**Abhaengigkeit:** U01, D03, D08.  
**Ziel:** Nutzer nach sinnvoller Presence und Geraete nach Status gruppieren.  
**Tests:** Sortierung, Statuswechsel, Offline, unbesetzt.  
**Green Gate:** kein veralteter Status ohne sichtbare Kennzeichnung.

### U03 – Einzelchat-Oberflaeche

**Status:** `PLANNED`  
**Abhaengigkeit:** U02, M08.  
**Ziel:** Chatfenster, sieben Tage, Nachladen, Sendestatus und Lesen.  
**Tests:** Presenter/ViewModel; Scroll-Pagination; Fehlerstatus.  
**Windows-Smoke:** reale Qt-Bedienung.  
**Green Gate:** kein Edit-/Delete-Menue fuer gesendete Nachrichten.

### U04 – Geraetechat-Oberflaeche

**Status:** `PLANNED`  
**Abhaengigkeit:** U03, M11.  
**Ziel:** Rechner als direktes Ziel und sichtbare ACK-/READ-Unterscheidung.  
**Tests:** unbesetzter/belegter Rechner, Antwortziel.  
**Green Gate:** vollstaendiger Geraeteverlauf ist am Geraet sichtbar.

### U05 – Gruppenoberflaeche

**Status:** `PLANNED`  
**Abhaengigkeit:** U03, G07.  
**Ziel:** Gruppe erstellen, Mitglieder/Rollen verwalten, archivierte Gruppe read-only.  
**Tests:** UI-Aktionen nach Rechte-Matrix.  
**Green Gate:** ausgeblendete UI ersetzt nicht serverseitige Autorisierung.

### U06 – Inline-Zitat und Reaktionsoberflaeche

**Status:** `PLANNED`  
**Abhaengigkeit:** U03, M12, M13.  
**Ziel:** Zitatnavigation und feste Reaktionen.  
**Tests:** Originalsprung, nicht geladene Historie, Reaktionsliste.  
**Green Gate:** keine sichtbare Thread-Oberflaeche.

### U07 – Screenshot aus Zwischenablage

**Status:** `PLANNED`  
**Abhaengigkeit:** U03.  
**Ziel:** Windows-Zwischenablagebild mit Vorschau senden.  
**Scope:** kein Dateidialog und kein allgemeiner Upload.  
**Tests:** Bild vorhanden/nicht vorhanden, Abbruch, Groessenlimit nach ADR.  
**Windows-Smoke:** `Win+Shift+S` → Einfuegen → Versand.  
**Green Gate:** nur Bilddaten aus der Zwischenablage werden akzeptiert.

## 10. Phase N – Screenshots, Suche und Dringlichkeit

### N01 – Serverseitiger Screenshot-Speicher

**Status:** `PLANNED`  
**Abhaengigkeit:** U07, S03.  
**Ziel:** transaktionale Metadaten, Pruefsumme und verwalteter Dateispeicher.  
**Tests:** Upload, Abbruch, Duplikat, unberechtigter Abruf, verwaiste Datei.  
**Green Gate:** Binaerdaten liegen nicht als grosse Felder in der Nachrichtentabelle.

### N02 – Berechtigte Suche und Archivindex

**Status:** `PLANNED`  
**Abhaengigkeit:** M08, G07, N01.  
**Ziel:** Text-, Nutzer-, Gruppen-, Geraete-, Datums- und Screenshotfilter.  
**Tests:** eigene/fremde Inhalte, archivierte Gruppe, Sonderzeichen, Pagination.  
**Green Gate:** Systemadmin erhaelt keine inhaltliche Fremdsuche.

### N03 – Dringlichkeitsmodell und drei Vorschaumodi

**Status:** `PLANNED`  
**Abhaengigkeit:** M03.  
**Ziel:** `FULL`, `PREVIEW`, `HIDDEN` als unveraenderliche Nachrichteneigenschaft.  
**Tests:** Validierung, User/Device/Group, Rechte, Serialisierung.  
**Green Gate:** verdeckte Nachricht liefert dem Overlay keinen Inhaltstext.

### N04 – Persistenter Dringlichkeitsstatus

**Status:** `PLANNED`  
**Abhaengigkeit:** N03, M06.  
**Ziel:** offen, geoeffnet, gelesen/bestaetigt getrennt pro Empfaenger.  
**Tests:** Volltext, Vorschau, verdeckt, mehrere Sitzungswechsel, Geraete-ACK.  
**Green Gate:** verdeckte Nachricht kann vor Oeffnen nicht als gelesen bestaetigt werden.

### N05 – Dringliches Multi-Monitor-Overlay

**Status:** `PLANNED`  
**Abhaengigkeit:** A05, N04.  
**Ziel:** persistente Windows-aehnliche Stapel am Bildschirmrand auf allen Monitoren.  
**Tests:** Layoutberechnung, Stapel, Ueberlauf, getrenntes Clear.  
**Windows-Smoke:** mehrere Monitore; Overlay bleibt im Vordergrund und verschwindet nicht automatisch.  
**Green Gate:** Alarmcast-Mitte bleibt unverdeckt.

### N06 – Overlay-Aktionen und Chatnavigation

**Status:** `PLANNED`  
**Abhaengigkeit:** N05, U03, U04, U05.  
**Ziel:** `Oeffnen` und je nach Modus `Gelesen` korrekt ausfuehren.  
**Tests:** Zielchat, archivierter Chat, verdeckt, Gruppenlesestatus.  
**Green Gate:** Aktion ist idempotent und serverseitig autorisiert.

## 11. Phase I – Vollstaendige Alarmcast-Integration

### I01 – Mehrere Alarmquellen und Zuordnungen

**Status:** `PLANNED`  
**Abhaengigkeit:** A04, D02.  
**Ziel:** ein Ueberwacher kann mehreren Quellen zugeordnet sein; Standard eine.  
**Tests:** Zuordnung, Entfernen, zwei gleichzeitige Alarme, reconnect je Quelle.  
**Green Gate:** Alarmereignis enthaelt eindeutige Quelle.

### I02 – Lokale Alarmcast-Berechtigungspruefung

**Status:** `PLANNED`  
**Abhaengigkeit:** I01, D07.  
**Ziel:** Start/Stop/Reset/Configure nach Nutzer- oder Geraetecapability.  
**Tests:** vollstaendige Rechte-Matrix; kein Nutzer; privilegiertes Konto ohne Passwort.  
**Green Gate:** Start/Stop bleibt lokal; keine Fernsteuerungs-API.

### I03 – Zentraler Alarmereignis- und Reset-Log

**Status:** `PLANNED`  
**Abhaengigkeit:** I02, S03.  
**Ziel:** Quelle, Alarm-ID, Zeiten, Reset-Geraet, Reset-Nutzer und Berechtigungsart zentral speichern.  
**Tests:** online, offline gepuffert, Wiederholung, Reihenfolge.  
**Green Gate:** kein Audiostream wird zentral gespeichert.

### I04 – Persistente Ausfallwarnung

**Status:** `PLANNED`  
**Abhaengigkeit:** I01, A05.  
**Ziel:** nicht erreichbare Quelle, Audio-/Outputfehler und gestopptes Modul dauerhaft anzeigen.  
**Tests:** Fehlerarten, Wiederherstellung, DND, mehrere Quellen.  
**Windows-Smoke:** echte Netzwerk- und Audioausfaelle.  
**Green Gate:** Warnung ist visuell vom Analysealarm unterscheidbar.

### I05 – Parallele Alarm- und Dringlichkeitsanzeige

**Status:** `PLANNED`  
**Abhaengigkeit:** I04, N06.  
**Ziel:** zentraler Alarm und Randnachrichten gleichzeitig, getrennte Bestaetigung.  
**Tests:** Prioritaet, Z-Order, Clear eines Typs, mehrere Monitore.  
**Green Gate:** keiner der beiden Typen entfernt oder bestaetigt den anderen.

### I06 – Migration vorhandener Alarmcast-Einstellungen

**Status:** `PLANNED`  
**Abhaengigkeit:** B03, A06, I02.  
**Ziel:** `host.json`, `client.json`, `mode.txt`, Autostart und Audioeinstellungen in gemeinsames Profil uebernehmen.  
**Tests:** Host, Client, beide, unvollstaendig, wiederholte Migration, Rollback.  
**Windows-Smoke:** reale vorhandene Konfiguration.  
**Green Gate:** Quelldateien werden nicht ungefragt geloescht; Migration laeuft nur einmal.

## 12. Phase O – Archiv, Backup und Betrieb

### O01 – Screenshot-Archivierung

**Status:** `PLANNED`  
**Abhaengigkeit:** N01, N02.  
**Ziel:** aeltere Screenshots nach konfigurierbarer Frist in separaten Archivspeicher verschieben.  
**Tests:** Standard 12 Monate, Grenzdatum, Abruf, Ausfall, Wiederholung.  
**Green Gate:** Nachricht und Suchmetadaten bleiben aktiv; keine automatische Loeschung.

### O02 – Konsistenter Backup-Satz

**Status:** `PLANNED`  
**Abhaengigkeit:** O01, I03.  
**Ziel:** Datenbank, Screenshots, Archivindex, Logs und Konfiguration konsistent auf Netzlaufwerk sichern.  
**Tests:** Erfolg, nicht erreichbares Netzlaufwerk, Teilausfall, atomare Gueltigmarkierung.  
**Green Gate:** unvollstaendiges Backup wird nicht als restore-faehig angeboten.

### O03 – Backuprotation

**Status:** `PLANNED`  
**Abhaengigkeit:** O02.  
**Ziel:** anpassbare Standardrotation 7 taeglich, 4 woechentlich, 12 monatlich.  
**Tests:** Zeitgrenzen, Monatswechsel, zu schützende letzte gueltige Sicherung.  
**Green Gate:** Rotation loescht nie den einzigen gueltigen Sicherungssatz.

### O04 – Integritaetspruefung und Restore-Werkzeug

**Status:** `PLANNED`  
**Abhaengigkeit:** O03.  
**Ziel:** automatischer Integritaetscheck und dokumentierter Restore in leere Zielumgebung.  
**Tests:** valides/defektes Backup, Versionsmigration, Dateipruefsummen.  
**Windows-Smoke:** vollstaendiger Restore-Test.  
**Green Gate:** wiederhergestellte Daten bestehen definierte Konsistenzabfragen.

### O05 – Windows-Server-Dienst

**Status:** `PLANNED`  
**Abhaengigkeit:** S02, O04.  
**Ziel:** Server automatisch und kontrolliert unter Windows betreiben.  
**Tests:** Installation, Start, Stop, Neustart, Dienstkonto, Netzlaufwerkszugriff.  
**Green Gate:** keine interaktive Benutzeranmeldung fuer Dauerbetrieb erforderlich.

### O06 – Desktop-Build, Autostart und Installation

**Status:** `PLANNED`  
**Abhaengigkeit:** I06, N06.  
**Ziel:** reproduzierbare Desktop-EXE und dokumentierte Verteilung.  
**Tests:** PyInstaller, Upgrade ueber Bestandsversion, Autostart, Settings-Erhalt.  
**Green Gate:** Neuinstallation und Upgrade sind getrennt getestet.

## 13. Phase R – Systemabnahme

### R01 – Mehrclient-End-to-End-Test

**Status:** `PLANNED`  
**Abhaengigkeit:** O05, O06.  
**Ziel:** Server, zwei Nutzerclients, Geraetechat, Gruppe, Offline-Queue und Alarmcast gemeinsam testen.  
**Tests:** festes E2E-Drehbuch mit beobachtbaren Ergebnissen.  
**Green Gate:** alle Kernablaeufe ohne direkte Datenbankmanipulation erfolgreich.

### R02 – Ausfall- und Wiederanlauftest

**Status:** `PLANNED`  
**Abhaengigkeit:** R01.  
**Ziel:** Serverausfall, Netzunterbrechung, Clientabsturz, Alarmquelle offline, Netzlaufwerk offline.  
**Green Gate:** Alarmcast bleibt direkt funktionsfaehig; Messaging synchronisiert ohne Doppelungen.

### R03 – Abnahme gegen Spezifikation 1.0

**Status:** `PLANNED`  
**Abhaengigkeit:** R02.  
**Ziel:** tracebare Abnahmematrix fuer jeden Spezifikationsabschnitt.  
**Green Gate:** jede Anforderung besitzt Testbeleg oder dokumentierte manuelle Abnahme; keine offene kritische Abweichung.

### R04 – Release Candidate

**Status:** `PLANNED`  
**Abhaengigkeit:** R03.  
**Ziel:** versionierter Release Candidate, Release Notes, Installations- und Restore-Dokumentation.  
**Green Gate:** nur freigegebene Artefakte; kein neues Feature in diesem Inkrement.

## 14. Freigabe des jeweils naechsten Inkrements

Nach Merge eines Inkrements:

1. PR und Green Gate werden extern beziehungsweise durch einen zweiten Agent geprueft.
2. Roadmap-Status wird auf `DONE` gesetzt.
3. Die naechste detaillierte Inkrementdatei wird erstellt oder aktualisiert.
4. Genau dieses Inkrement wird auf `READY` gesetzt.
5. `tasks/ACTIVE_TASK.md` wird angepasst.
6. Erst danach wird ein neuer Codex-Task gestartet.
