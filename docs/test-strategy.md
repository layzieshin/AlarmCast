# Teststrategie

## 1. Grundsatz

Tests sind Teil jedes Inkrements und keine Abschlussphase. Ein Task ist nur fertig, wenn sein Verhalten beobachtbar geprueft wurde und relevante Bestandsfunktionen weiterhin funktionieren.

Kein Agent darf einen Test loeschen, abschwaechen, ueberspringen oder auf Implementierungsdetails umschreiben, nur um das Green Gate zu erreichen.

## 2. Testpyramide

### 2.1 Domain-Unit-Tests

Schnelle, deterministische Tests ohne Qt, Netzwerk, Dateisystem, echte Uhr oder Datenbank.

Beispiele:

- Rollen- und Berechtigungsregeln,
- exklusive Nutzersitzung,
- Gruppenrechte,
- unveraenderliche Nachrichten,
- Dringlichkeitsmodi,
- Pagination-Cursor,
- Idempotenzentscheidungen,
- Backuprotation.

### 2.2 Adapter- und Komponenten-Tests

Ein Modul mit austauschbaren Fakes fuer seine Ports.

Beispiele:

- Alarmcast-Fassade mit Fake-Capture und Fake-Netzwerk,
- Overlay-Koordinator mit simulierten Monitorgeometrien,
- lokale Queue mit temporaerem Dateisystem,
- Settings-Migrationen,
- Screenshot-Speicher.

### 2.3 Persistenz-Integrationstests

Echte Testdatenbank beziehungsweise echte Migrationsengine, aber keine Produktivdaten.

Zu pruefen:

- frische Datenbank,
- Upgrade ueber alle Migrationen,
- Transaktionsrollback,
- Eindeutigkeitsbedingungen,
- konkurrierende Operationen,
- append-only-Eigenschaften,
- Archiv- und Backupkonsistenz.

### 2.4 API- und Realtime-Integrationstests

Serverprozess oder In-Process-Testserver mit realer Serialisierung.

Zu pruefen:

- Authentifizierung und Autorisierung,
- Geraeteregistrierung und Heartbeat,
- exklusive Sitzung,
- Nachrichtensendung und Idempotenz,
- Live-Zustellung,
- Reconnect,
- Lesebestaetigung,
- Gruppenfanout,
- verweigerter Fremdzugriff.

### 2.5 Architekturtests

Architekturregeln muessen automatisiert fehlschlagen, wenn ein Agent sie verletzt.

Mindestens:

- `core` importiert nicht aus `host` oder `client`,
- `host` und `client` importieren nicht direkt voneinander,
- spaetere Fachmodule werden nur ueber oeffentliche Grenzen verwendet,
- GUI importiert keine Server-ORM- oder Low-Level-Datenbankmodule,
- Messaging importiert keine Alarmcast-Sockets,
- Admin-API serialisiert keine Chatcontent-Felder,
- keine unerlaubten Entry Points,
- keine lokalen Secrets oder Configdateien im Repository.

### 2.6 Windows-Smoke-Tests

Erforderlich fuer Betriebssystem- und Hardwareverhalten, das CI nicht zuverlaessig simuliert:

- WASAPI-Loopback,
- Audioausgabe und Devicewechsel,
- Mute und Lautstaerke,
- Tray und Single-Instance,
- Windows-Autostart,
- Windows-Zwischenablage mit `Win+Shift+S`,
- Multi-Monitor-Overlays,
- Always-on-top-Verhalten,
- Windows-Dienst,
- Netzlaufwerk und Dienstkonto,
- PyInstaller-Build und Upgrade.

Jede manuelle Pruefung besitzt feste Schritte, erwartetes Ergebnis, Datum, getestete Version und Tester.

### 2.7 Mehrclient-End-to-End-Tests

Spaetestens ab dem Messaging-Kern wird ein reproduzierbares Mehrclient-Drehbuch gepflegt. Es umfasst mindestens:

- zentralen Server,
- zwei Nutzer an getrennten PCs,
- einen unbesetzten Geraeteclient,
- Einzelchat,
- Gruppenchat,
- Lesestatus,
- Offline-Queue,
- dringliche Nachricht,
- eine Alarmcast-Quelle und mindestens einen Ueberwacher.

## 3. Standardbefehle

Nach Einrichtung der Entwicklungsumgebung:

```powershell
python --version
ruff check .
ruff format --check .
mypy src
pytest -q
```

Taskbezogene Tests werden vor dem Gesamtlauf gezielt ausgefuehrt, zum Beispiel:

```powershell
pytest -q tests/test_config.py
pytest -q tests/integration/test_sessions.py
```

Ein Befehl darf nur als bestanden dokumentiert werden, wenn seine Ausgabe im aktuellen Arbeitsstand gesehen wurde.

## 4. Baseline-Regel

Vor jeder Aenderung wird die Baseline ausgefuehrt. Falls ein Test bereits vor dem Task fehlschlaegt:

1. Fehlerausgabe sichern,
2. Ursache nicht automatisch reparieren,
3. pruefen, ob der aktive Task die Ursache beruehrt,
4. bei unklarem Zusammenhang stoppen,
5. im PR Vorher-/Nachher-Zustand getrennt dokumentieren.

## 5. Testdaten und Zeit

- Keine echten Patientendaten, Nutzernamen, PSKs oder internen Adressen.
- Testdaten sind offensichtlich fiktiv.
- Zeitabhaengige Regeln verwenden eine injizierbare Uhr.
- Zufalls-IDs werden in Tests ueber deterministische Provider kontrolliert.
- Netzwerkfehler werden ueber Fakes oder kontrollierte lokale Testserver simuliert.

## 6. Sicherheits- und Berechtigungstests

Jede erlaubte Operation benoetigt mindestens einen negativen Gegenfall.

Besonders wichtig:

- Systemadmin ohne Chatinhalte,
- Nichtmitglied ohne Gruppensicht,
- Hilfsadmin ohne Remove-/Archivrecht,
- unberechtigter Nutzer ohne Alarmcast-Start/Stop/Reset,
- fremder Screenshot nicht abrufbar,
- fremde Suche liefert keine Treffer,
- verdeckte dringliche Nachricht liefert keinen Vorschautext,
- deaktivierter Nutzer kann sich nicht anmelden.

## 7. Migrations-Tests

Jede Schema- oder Konfigurationsmigration prueft:

- gueltigen Altstand,
- teilweise oder fehlende Felder,
- wiederholten Lauf,
- Abbruch beziehungsweise Fehler,
- Erhalt der letzten gueltigen Daten,
- Upgrade ueber mehrere Versionen.

Produktive Altdateien werden niemals als Testfixture mit echten Geheimnissen committed.

## 8. Abnahmetraceability

`docs/specification-1.0.md` ist die Anforderungsquelle. Spaetestens in R03 entsteht eine Matrix:

```text
Anforderung → Inkrement → automatisierter Test → manueller Test → Ergebnis
```

Bereits vorher muss jeder PR in seinem Abschlussbericht die betroffenen Spezifikationsabschnitte nennen.

## 9. CI-Stufen

Nach B01 soll CI mindestens enthalten:

1. Format und Lint,
2. Typpruefung,
3. Unit- und plattformneutrale Integrationstests,
4. Architekturtests,
5. Windows-spezifischen Testjob,
6. spaeter Build-Smoke fuer Desktop und Server.

Audiohardware und echte Multi-Monitor-Szenarien bleiben dokumentierte manuelle Gates.
