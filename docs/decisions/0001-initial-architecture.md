# 0001 — Initiale Architektur

## Status

accepted (2026-05-22)

## Kontext

Bestehender Python-Prototyp (Tkinter, soundcard, sounddevice, custom TCP) liefert das fachliche Konzept und hat folgende Erfahrungen gesammelt:

- **Tkinter-Overlay** unter Windows ist fragil (Transparenz, ColorKey, graue Kaesten).
- **TCP-Send-Konkurrenz**: paralleles `sendall()` aus Audio- und Control-Thread auf demselben Socket zerschiesst Frames. Loesung war ein Send-Lock pro Verbindung.
- **`sounddevice.WasapiSettings(loopback=True)`** funktioniert nicht — Workaround: `soundcard` fuer Capture, `sounddevice` fuer Output.
- **numpy 2.x** brach `frombuffer`-Pfade in aelteren Audio-Libs → Pin auf `1.26.4`.
- **TCP-Subnet-Scan** zur Host-Discovery wirkt fuer AV-/EDR-Systeme wie Portscanning.
- **Konfiguration neben EXE** verursacht Konflikte, wenn die EXE von einer NAS-Freigabe startet und mehrere Clients dieselbe Datei beschreiben.

Zielumgebung: Windows, Praxis-LAN, ein Host (PC am Analysengeraet) und mehrere Clients (Arzt-PCs).

## Entscheidung

1. **Stack**: Python 3.12 + PySide6 (Qt). Audio via `soundcard` (Loopback) und `sounddevice` (Output), Numerik `numpy==1.26.4`, Discovery `zeroconf`, Build `pyinstaller`.
2. **Single Binary** mit Modus-Schalter `--host` / `--client` statt zwei Programmen. Gemeinsame Logik in `core/`.
3. **Protokoll**: TCP auf Port 50050 mit eigenem Framing `[type:1][len:u32 LE][payload]` und Frame-Typen `A` (Audio), `C` (Control), `H` (Hello). **Send-Lock pro Verbindung** verpflichtend.
4. **Authentifizierung**: Pre-Shared Token im HELLO-Frame, konstanzeitiger Vergleich via `hmac.compare_digest` am Host. PSK wird beim Erststart des Hosts generiert und im Host-GUI sichtbar gemacht.
5. **Discovery**: mDNS/Zeroconf, Service `_alarmcast._tcp.local.`, TXT-Record `version=1`. **Kein** Subnet-Scan. Fallback: manuelle Host-Adresse in `client.json`.
6. **Konfiguration**: ausschliesslich `%APPDATA%\AlarmCast\{host,client}.json`. Kein Fallback "neben EXE".
7. **Autostart Client**: Registry-Eintrag unter `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, Toggle im Settings-Fenster, **Default: an**.
8. **Overlay**: Qt-Frameless-Topmost-Fenster pro Monitor, `WA_TranslucentBackground`, Fade ueber `QGraphicsOpacityEffect`.

## Konsequenzen

**Positiv**

- Eine Build-Pipeline, ein Repo, ein Dependency-Manifest.
- Audio-Erfahrungen aus dem Prototyp uebertragbar.
- Qt loest die zwei groessten Schmerzen des Prototyps (Overlay-Transparenz, Threading-Modell).
- mDNS ist AV-/EDR-freundlich (Standard-Service-Discovery, gleiches Protokoll wie Drucker, AirPlay, Chromecast).
- PSK schuetzt vor versehentlichen Fehlverbindungen ohne TLS-Overhead.
- Konfig zentral in `%APPDATA%` → NAS-Deployment funktioniert problemlos.

**Negativ**

- Single-EXE Groesse ~50–80 MB (PySide6).
- mDNS kann in restriktiven Netzen blockiert sein → manuelle Adresse muss als Fallback gepflegt bleiben.
- PSK-Verteilung out-of-band (Admin traegt einmalig ein) — Komfort-Verbesserung (z. B. QR-Code im Host-GUI) bleibt Future-Work.
- Single-Binary mit zwei Modi heisst: jede Dependency wird in beiden Modi mitgeliefert, auch wenn nur einer sie braucht.

## Alternativen (geprueft und verworfen)

- **.NET 8 + WPF (NAudio)**: technisch sehr sauber, aber kompletter Neuanfang ohne klaren Mehrwert fuer diesen Anwendungsfall.
- **Rust + egui / Tauri**: kleinste EXE, hoechste Lernkurve, Audio-Stack (cpal/wasapi-rs) aufwendiger.
- **TCP-Subnet-Scan zur Discovery**: triggert moderne EDR-Loesungen, abgelehnt.
- **TLS auf der TCP-Verbindung**: Overkill im internen Praxis-LAN.
- **Zwei getrennte Repos** fuer Host und Client: doppelte Pflege von Protokoll und Konfig, abgelehnt zugunsten Single-Binary.
- **Konfig neben EXE mit Fallback**: erzeugt im NAS-Szenario stille Konflikte, abgelehnt.
