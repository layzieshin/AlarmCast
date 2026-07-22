# Manueller Smoke-Test — Alarmcast EXE

Voraussetzungen:

- Python **3.12** Build-Umgebung (Projekt: `requires-python >=3.12,<3.13`)
- EXE gebaut: `dist/alarmcast.exe` (siehe `alarmcast.spec`)
- Zwei Windows-PCs im selben LAN (oder ein PC mit zwei Instanzen zum Schnelltest)
- Host-PC: Firewall-Regel fuer eingehend TCP **50050**
- mDNS/Multicast im LAN erlaubt (sonst manuelle Host-IP am Client)

## 1) Build

```powershell
cd i:\Projekte\Alarmcast
py -3.12 -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
pyinstaller alarmcast.spec
```

Ergebnis: `dist\alarmcast.exe` (Zielgroesse nach Slim-Build: deutlich unter 280 MB)

Debug-Build (Fehler in Konsole sichtbar): `dist\alarmcast-debug.exe`

### Wichtig: Start ohne Argument

- **Doppelklick** auf `alarmcast.exe` oeffnet einen Modus-Dialog (Host / Client).
- Die gewaehlte Rolle wird in `%APPDATA%\AlarmCast\mode.txt` gespeichert.
- Fuer feste Rollen besser **Verknuepfungen** mit `--host` bzw. `--client` nutzen.

## 2) Host starten

1. Auf Host-PC: `dist\alarmcast.exe --host` (oder Doppelklick → „Host“)
2. Fenster oeffnen, **PSK** notieren (Label im Host-Fenster)
3. **Start** klicken
4. Erwartung: Status `aktiv auf Port 50050`, Clientliste leer

Konfig liegt unter: `%APPDATA%\AlarmCast\host.json`

## 3) Client starten

1. Auf Client-PC: `dist\alarmcast.exe --client`
2. **PSK** vom Host eintragen
3. Host-Adresse leer lassen (mDNS) **oder** Host-IP manuell setzen
4. **Verbinden** klicken
5. Erwartung: Status `Verbunden mit <host>:50050`
6. Host-Fenster zeigt Client in der Liste

Konfig liegt unter: `%APPDATA%\AlarmCast\client.json`

## 4) Audio-Streaming

1. Am Host-PC einen hoerbaren Systemton abspielen (z. B. kurzer Windows-Sound)
2. Erwartung: Client spielt Ton ab (wenn nicht gemutet)

## 5) Optischer Alarm

1. Am Host innerhalb von 3 s **zwei** kurze Toene ausloesen
2. Erwartung: gelbes Warndreieck oben rechts auf **jedem** Client-Monitor (blinkend)

## 6) UI Convenience (Client)

1. Tab **Uebersicht**: Status, Verbinden/Stop, Reset nur bei Alarm, Host-Nachricht
2. Tab **Einstellungen**: Rolle, PSK, Host-IP, Lautstaerke, Mute, Testton, Autostart, Auto-Connect, Nachrichten-Overlay
3. Fenstergroesse fest **460×560**; Einstellungen ohne Scrollleiste, Button **Speichern**

## 7) UI Convenience (Host)

1. Tab **Uebersicht**: Status, Clientliste, Nachricht senden (Modus-Combo), Start/Stop, Reset nur bei Alarm
2. Tab **Einstellungen**: Rolle, Autostart, Auto-Start Server, Schwelle, Signale, Fenster, PSK, Port, **Speichern**
3. Tab **Logs**: Ereignistabelle (Connect, Alarm, Reset)
4. Fenstergroesse fest **480×520**
5. Client: Warndreieck = Windows-Standardicon, transparenter Hintergrund, 15% groesser, smoother Pulse 0-100% Opacity
6. Tab **Logs**: Buttons zum Oeffnen von Ereignislog und technischem Log in Notepad

Ereignisdatei: `%APPDATA%\AlarmCast\events.jsonl`

## 8) Reset

1. Am Client **Alarm zuruecksetzen** klicken
2. Erwartung: Overlay verschwindet sofort
3. Host-Alarmzustand ist zurueckgesetzt (erneute 2 Toene loesen Alarm wieder aus)

## 9) Reconnect

1. Host-EXE beenden
2. Erwartung: Client zeigt Reconnect-Status
3. Host neu starten + **Start**
4. Erwartung: Client verbindet wieder automatisch (nach wenigen Sekunden)

## 10) Single-Instance und Tray

1. Alarmcast starten (Host oder Client)
2. EXE ein zweites Mal starten → bestehendes Fenster kommt in den Vordergrund, **kein** zweiter Prozess im Task-Manager
3. Fenster mit **X** schliessen → App laeuft weiter, Tray-Icon im Infobereich bleibt
4. Doppelklick auf Tray-Icon → Fenster wieder sichtbar
5. Tray → **Beenden** → Prozess endet (ggf. Bestaetigungsdialog)

## 11) Nachrichten-Modi (Host → Client)

1. Client: Einstellungen → **Nachrichten-Overlay aktiv**
2. Host: Modus **Nur Status** senden → nur Statuszeile am Client
3. Host: Modus **Info (10s)** → graublaues Top-Overlay ~10 s + Statuszeile
4. Host: Modus **Bestaetigung** → Overlay mit Button bis Klick
5. Client: Overlay deaktivieren → alle Modi nur Statuszeile

## 12) Negative Tests

| Test | Erwartung |
|---|---|
| Falsche PSK am Client | Kein stabiler Stream, Host loggt WARN (ungueltige PSK) |
| Client Mute aktiv | Kein hoerbarer Stream, Overlay bei Alarm trotzdem sichtbar, Testton bleibt moeglich |
| mDNS blockiert | Manuelle Host-IP im Client funktioniert |

## Build-Groesse (Vorher/Nachher)

| Build | Groesse (ca.) | Anmerkung |
|---|---|---|
| Alt (`collect_all(PySide6)`) | ~280 MB | QML/WebEngine/Addons mit eingepackt |
| Neu (slim spec) | siehe Ergebnisprotokoll | ohne `collect_all(PySide6)`, Qt-Module excluded |

Offiziell vorgesehen: **Python 3.12** (`requires-python >=3.12,<3.13`). Fuer produktive Builds: `scripts\build_exe.ps1`.

## Ergebnisprotokoll

| Schritt | OK / FAIL | Notiz |
|---|---|---|
| Build EXE (slim) | OK | ~62 MB (vorher ~280 MB mit collect_all PySide6) |
| Doppelklick Modus-Dialog | | |
| Host Start | | |
| Client Verbindung | | |
| Audio Stream | | |
| Overlay Alarm | | |
| Reset | | |
| Volume Slider + Testton | | |
| Host Protokoll + MSG | | |
| Reconnect | | |
| Falsche PSK | | |
