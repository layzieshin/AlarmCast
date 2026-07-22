# Alarmcast — Projekt-Brief

## Wer

Praxis-/Labor-Umgebung. Auf einem PC laeuft die Steuersoftware fuer ein Analysengeraet, das bei Fehlern oder Auffaelligkeiten lokal einen Warnton ausgibt. Aerzte arbeiten an separaten PCs im selben LAN.

## Was

Eine Windows-App in zwei Rollen:

- **Host** (auf dem Geraete-PC): erfasst den Systemton per WASAPI-Loopback und streamt ihn ueber TCP an alle Client-PCs. Erkennt anhand des Audiopegels ein definiertes Signalmuster und sendet bei Treffer ein Alarm-Flag.
- **Client** (auf jedem Arzt-PC): spielt den Stream ab (mute-/lautstaerkebar) und zeigt bei Alarm zusaetzlich ein gelbes Warndreieck oben rechts auf **jedem** Monitor.

Eine Binary, Modus per CLI-Schalter (`--host` / `--client`).

## Warum

Der lokale Warnton am Geraete-PC wird in der Praxis ueberhoert, wenn niemand vor Ort ist. Reines Lauterstellen ist keine Option (Patientenkontakt, professioneller Eindruck). Daher ein duales Warnsystem: dezent akustisch + deutlich optisch.

## MVP

1. Host streamt Audio (48 kHz, Mono, int16, 20 ms Frames) an verbundene Clients.
2. Client gibt Audio wieder, individuell stumm-/regelbar.
3. Host erkennt 2 Signale innerhalb 3 s (parametrisierbar) und sendet Alarm.
4. Client zeigt bei Alarm ein gelbes Warndreieck pro Monitor oben rechts (blinkend, mit Fade).
5. Client findet Host per mDNS, Fallback auf manuelle Adresse.
6. Verbindung ist mit Pre-Shared Token authentifiziert.
7. Konfiguration in `%APPDATA%\AlarmCast\`. Client startet optional mit Windows.
8. Beide Modi als Single-EXE auslieferbar.

## Nicht-Ziele (vorerst)

- Mehrere Hosts gleichzeitig.
- Sprachuebermittlung in beide Richtungen.
- Plattformen ausser Windows.
- Verschluesselung (TLS) — internes vertrauenswuerdiges LAN, PSK reicht.
- Cloud-Backend, Mobile-App, Web-Dashboard.
- Zentrales Compliance-Audit / Cloud-Reporting (lokales Host-Ereignisprotokoll siehe ADR 0002).

## Erfolgsmessung

- Ein Praxistest mit 1 Host + ≥2 Clients laeuft 60 Minuten stabil ohne Reconnect-Stoerung.
- Ein Alarm-Pattern wird in 10/10 Tests korrekt erkannt; alle Clients zeigen das Warndreieck binnen 1 Sekunde.
- Reset am Client blendet alle Overlays sofort aus.
- Kein AV-/EDR-System der Praxis-PCs schlaegt beim Discovery oder Verbindungsaufbau Alarm.
