# A01 – Alarmcast-Vertragsmodell

**Status:** `READY`  
**Abhaengigkeit:** B03 ist gemergt.  
**Art:** Reines Vertrags- und Testinkrement; keine Laufzeit- oder UI-Aenderung.

## 1. Ziel

A01 fuehrt die erste stabile oeffentliche Grenze fuer die schrittweise Kapselung des bestehenden Alarmcast-Host-/Client-Kerns ein.

Unter `src/alarmcast/alarmcast_runtime/contracts.py` entstehen kleine, unveraenderliche und von Low-Level-Technik freie Verträge fuer:

- Laufzustand von Quelle und Ueberwacher,
- Alarmzustand,
- Verbindungszustand,
- Netzwerkendpunkt als reines Datenobjekt,
- verbundene Ueberwacher aus Sicht der Quelle,
- Source- und Monitor-Snapshots,
- fachliche Reset-Anforderungen.

Die Contracts bilden ausschliesslich bereits vorhandene Alarmcast-Zustaende ab. A01 fuehrt keine Fassade, keinen Adapter, kein Event-Bus-Verhalten und keine neue Produktfunktion ein.

## 2. Vor Beginn

Lies die in `AGENTS.md` festgelegte Reihenfolge und fuehre die Baseline mit der gesperrten B01-Umgebung aus:

```text
git status --short
uv lock --check
uv sync --locked --extra dev
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy src
uv run --frozen pytest -q
```

Untersuche vor dem ersten Edit mindestens:

- `docs/target-architecture.md`, insbesondere Abschnitte 4, 6 und 7,
- `docs/implementation-roadmap.md`, A01 bis A04,
- `src/alarmcast/core/alarm_logic.py`,
- `src/alarmcast/core/protocol.py`,
- `src/alarmcast/host/detector.py`,
- `src/alarmcast/host/server.py`,
- die bestehende Host-Runtime in `src/alarmcast/host/ui/main_window.py`,
- `src/alarmcast/client/net.py`,
- die bestehende Client-Runtime und Alarmanzeige,
- die B02-Architekturguards.

Bestehende Host-, Client-, Core-, UI-, Entry-Point- und Konfigurationsdateien werden nicht eigenmaechtig umgebaut.

## 3. Verbindlicher Ablageort

Fuehre ausschliesslich die benoetigte neue Modulgrenze ein:

```text
src/alarmcast/alarmcast_runtime/
  __init__.py
  contracts.py
```

`__init__.py` bleibt minimal und enthaelt keine Composition, keine konkreten Implementierungen und keine spekulativen Re-Exports.

Es wird in A01 noch keine `api.py`, `source_adapter.py`, `monitor_adapter.py`, `composition.py` oder GUI-Struktur angelegt.

## 4. Verbindliches Vertragsmodell

Verwende Python-3.12-Standardmittel, vorzugsweise `enum.StrEnum` sowie `@dataclass(frozen=True, slots=True)`.

Die folgenden oeffentlichen Typen und Bedeutungen sind verbindlich. Exakte Stringwerte der Enums werden als kleingeschriebene stabile Werte gespeichert.

### 4.1 Enums

```text
RuntimeState
- STOPPED = "stopped"
- RUNNING = "running"

AlarmState
- INACTIVE = "inactive"
- ACTIVE = "active"

ConnectionState
- DISCONNECTED = "disconnected"
- DISCOVERING = "discovering"
- CONNECTING = "connecting"
- CONNECTED = "connected"
- RECONNECTING = "reconnecting"

ResetOrigin
- LOCAL_SOURCE = "local_source"
- LOCAL_MONITOR = "local_monitor"
- REMOTE_MONITOR = "remote_monitor"
```

A01 fuehrt bewusst keine spekulativen `STARTING`, `STOPPING`, `FAILED` oder Server-/Messaging-Zustaende ein, weil der aktuelle Alarmcast-Kern diese nicht als stabile fachliche Zustaende bereitstellt.

### 4.2 Datenobjekte

```text
NetworkEndpoint
- host: str
- port: int

ConnectedMonitor
- name: str
- endpoint: NetworkEndpoint

SourceSnapshot
- runtime_state: RuntimeState
- alarm_state: AlarmState
- connected_monitors: tuple[ConnectedMonitor, ...] = ()

MonitorSnapshot
- runtime_state: RuntimeState
- connection_state: ConnectionState
- alarm_state: AlarmState
- source_endpoint: NetworkEndpoint | None = None

AlarmResetRequest
- origin: ResetOrigin
- requester: str | None = None
```

Alle Contracts sind unveraenderlich. Es werden keine Listen, Dictionaries, Qt-Objekte, Sockets, Threads, Audioobjekte oder Callbacktypen als oeffentliche Felder verwendet.

## 5. Verbindliche Invarianten

### 5.1 `NetworkEndpoint`

- `host` ist ein nicht leerer, bereits getrimmter String.
- `port` liegt zwischen 1 und 65535.
- Es findet keine DNS-Aufloesung, IP-Pruefung oder Socketerzeugung statt.

### 5.2 `ConnectedMonitor`

- `name` ist ein nicht leerer, bereits getrimmter String.
- `endpoint` ist ein `NetworkEndpoint`.

### 5.3 `SourceSnapshot`

- `connected_monitors` ist immer ein Tuple.
- Bei `RuntimeState.STOPPED` muss der Alarm `INACTIVE` sein und die Monitorliste leer sein.
- A01 erfindet keine stabile Monitor-ID. Name und Endpunkt bilden nur den aktuell beobachtbaren Verbindungs-Snapshot ab.

### 5.4 `MonitorSnapshot`

- Bei `RuntimeState.STOPPED` gilt zwingend:
  - `ConnectionState.DISCONNECTED`,
  - `AlarmState.INACTIVE`,
  - kein `source_endpoint`.
- `CONNECTING`, `CONNECTED` und `RECONNECTING` benoetigen einen `source_endpoint`.
- `DISCONNECTED` und `DISCOVERING` duerfen keinen `source_endpoint` tragen.
- Ein aktiver Alarm darf waehrend eines Verbindungsverlustes im laufenden Monitor-Snapshot bestehen bleiben; A01 darf ihn nicht automatisch aus dem Connection-State ableiten.

### 5.5 `AlarmResetRequest`

- `REMOTE_MONITOR` benoetigt einen nicht leeren, bereits getrimmten `requester`, entsprechend dem heute vom Host empfangenen Clientnamen.
- `LOCAL_SOURCE` und `LOCAL_MONITOR` tragen keinen `requester`.
- Es wird noch keine Alarm-ID erfunden. Der aktuelle Bestand besitzt genau einen lokalen Alarmzustand je Quelle und kein stabiles Alarm-ID-Protokoll.

Verletzte Invarianten schlagen unmittelbar mit `ValueError` oder `TypeError` fehl. Fehler werden nicht still normalisiert.

## 6. Reinheit der Vertragsgrenze

`contracts.py` darf nur Python-Standardbibliothek und Typen aus demselben Contract-Modul verwenden.

Insbesondere verboten sind direkte oder indirekte oeffentliche Abhaengigkeiten auf:

- PySide6 oder andere Qt-Typen,
- `socket`, `threading`, `asyncio`,
- `numpy`, `soundcard`, `sounddevice`,
- `zeroconf`,
- bestehende Module unter `alarmcast.core`, `alarmcast.host` oder `alarmcast.client`,
- Protokollframes, Byte-Payloads, Callbacks oder konkrete Implementierungen.

Die Tests muessen diese Reinheit automatisiert pruefen. Ein spaeterer Adapter darf die bestehenden Low-Level-Zustaende in diese Contracts uebersetzen; A01 implementiert diesen Adapter noch nicht.

## 7. In Scope

1. `src/alarmcast/alarmcast_runtime/__init__.py` minimal anlegen.
2. `src/alarmcast/alarmcast_runtime/contracts.py` mit dem verbindlichen Modell anlegen.
3. Kleine, gezielte Validierung der Invarianten implementieren.
4. Vollstaendige positive und negative Tests fuer Enums, Immutability, Slots, Werte, Defaults und Invarianten erstellen.
5. Einen Architekturtest gegen verbotene Imports und Low-Level-Typen in `contracts.py` ergaenzen.
6. Unter `docs/` die Bedeutung und Grenzen der Alarmcast-Contracts dokumentieren.
7. `docs/implementation-roadmap.md` aktualisieren:
   - B03 auf `DONE`,
   - A01 waehrend der Umsetzung auf `IN_PROGRESS`,
   - im Abschlussstand auf `REVIEW`.
8. Bestehende Tests und Architekturguards vollstaendig gruen halten.

## 8. Nicht in Scope

- keine Source- oder Monitor-Fassade,
- keine `Protocol`-API und kein Event-Bus,
- keine Adapter fuer Host, Client, Capture, Detector, Netzwerk oder Audio,
- keine Aenderung an `core`, `host` oder `client`,
- keine Aenderung an UI, Tray, Overlay oder Qt-Signalen,
- keine Aenderung am TCP-Protokoll, Reset-Frame oder PSK-Verhalten,
- keine neue Konfiguration oder Persistenz,
- keine neue Runtime- oder Dev-Abhaengigkeit,
- keine neue Entry-Point-, Composition- oder Buildlogik,
- kein Windows-/Hardware-Smoke-Test,
- kein Beginn von A02, A03, A04, S01 oder spaeteren Inkrementen.

## 9. Pflicht-Tests

Mindestens folgende Faelle sind abzudecken:

1. Alle Enum-Namen und exakten Stringwerte.
2. Alle Dataclasses sind `frozen=True` und verwenden Slots.
3. Mutationsversuche auf jedem Contract schlagen fehl.
4. `NetworkEndpoint` akzeptiert gueltige Hostnamen/IP-Strings und Ports.
5. Leerer oder nicht getrimmter Host wird abgelehnt.
6. Ports 0, negative Werte und Werte groesser als 65535 werden abgelehnt.
7. `ConnectedMonitor` akzeptiert gueltige Daten und lehnt leere/nicht getrimmte Namen ab.
8. Ein laufender Source-Snapshot kann keinen oder mehrere verbundene Ueberwacher enthalten.
9. Ein gestoppter Source-Snapshot mit aktivem Alarm wird abgelehnt.
10. Ein gestoppter Source-Snapshot mit Monitoren wird abgelehnt.
11. Ein laufender Monitor kann `DISCOVERING` ohne Endpunkt sein.
12. `CONNECTING`, `CONNECTED` und `RECONNECTING` ohne Endpunkt werden abgelehnt.
13. `DISCONNECTED` oder `DISCOVERING` mit Endpunkt werden abgelehnt.
14. Ein gestoppter Monitor mit Verbindung, Endpunkt oder aktivem Alarm wird abgelehnt.
15. Ein laufender, getrennter Monitor darf einen weiterhin aktiven Alarm-Snapshot tragen.
16. Remote-Reset mit gueltigem Requester wird akzeptiert.
17. Remote-Reset ohne Requester sowie lokale Resets mit Requester werden abgelehnt.
18. Tuple-Felder koennen nicht durch mutable Listen ersetzt werden.
19. `contracts.py` importiert keine verbotene Low-Level-Technik und keine Bestandsmodule.
20. Oeffentliche Typannotationen enthalten keine Qt-, Socket-, Thread-, Audio- oder Protokolltypen.
21. Der echte B02-Repository-Integrationsguard bleibt gruen.
22. Das vollstaendige bestehende Testset bleibt gruen.

## 10. Verifikation

Gezielt:

```text
uv run --frozen pytest -q tests/test_alarmcast_contracts.py
uv run --frozen pytest -q tests/architecture
```

Vollstaendiges Green Gate:

```text
uv lock --check
uv sync --locked --extra dev
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy src
uv run --frozen pytest -q
git diff --check
```

## 11. Dokumentation und PR

Der Draft-PR traegt den Titel:

```text
A01 Add immutable Alarmcast contracts
```

Der PR beschreibt mindestens:

- eingefuehrte Contracttypen und exakte Enumwerte,
- abgebildete Bestandszustaende,
- durchgesetzte Invarianten,
- Reinheit von Qt, Socket, Thread, Audio und Bestandsimplementierungen,
- Testergebnisse,
- unveraenderte Produktbereiche,
- bewusste Nicht-Einfuehrung von Fassade, API, Adaptern und Alarm-ID,
- verbleibende Restrisiken.

## 12. Stop-Bedingungen

Stoppe und melde einen Blocker, wenn:

- die vorhandenen Host-/Client-Zustaende dem verbindlichen Modell nachweislich widersprechen,
- eine Invariante nur durch eine Laufzeit-, UI- oder Protokollaenderung erfuellbar waere,
- eine neue Abhaengigkeit erforderlich erscheint,
- ein bestehender Test vor dem Task fehlschlaegt und der Zusammenhang mit A01 unklar ist,
- ein spaeteres Inkrement vorgezogen werden muesste.

A01 endet nach gruenem Draft-PR. A02 wird nicht begonnen.
