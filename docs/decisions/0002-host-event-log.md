# ADR 0002: Lokales Host-Ereignisprotokoll

## Status

Angenommen (2026-05-22)

## Kontext

Die Praxis moechte nachvollziehen, welche Clients wann verbunden waren und wer einen Alarm zurueckgesetzt hat. Das Projekt-Brief listete „Audit-Logs / Compliance-Reporting“ als Nicht-Ziel — gemeint war ein zentrales Compliance-System, nicht ein lokales Betriebsprotokoll.

## Entscheidung

- Append-only JSONL unter `%APPDATA%\AlarmCast\events.jsonl` (nur Host)
- Ereignistypen: Verbindung, Trennung, Alarm an/aus, Reset lokal/remote, Nachricht gesendet, Server start/stop
- UI-Tab „Protokoll“ am Host; kein separates Client-Protokoll in v1
- Zusaetzlich rotierende Datei `alarmcast.log` fuer technische Logs

## Konsequenzen

- Kein TLS, keine Cloud-Synchronisation
- Kein PII-Schutz ueber LAN hinaus — Datei liegt lokal auf dem Host-PC
- Erweiterbar um Export (CSV) ohne Protokoll-Aenderung
