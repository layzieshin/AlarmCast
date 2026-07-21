# ADR 0010 – Verbindlicher Technologie-Stack fuer Messaging-Erweiterung

**Status:** Accepted  
**Datum:** 2026-07-21

## Kontext

Alarmcast ist eine bestehende Windows-Python-Anwendung. Die Messaging-Erweiterung benoetigt einen zentralen Server, persistente Nachrichten, Echtzeitereignisse, lokalen Offlinebetrieb und weiterhin direkte Alarmcast-Kommunikation.

Ein autonomer Coding-Agent darf den Stack nicht inkrementweise neu entscheiden, da dadurch parallele Netzwerkstacks, Datenbanken, Entry Points und Betriebsmodelle entstehen koennten.

## Entscheidung

### Desktop

- Python 3.12
- PySide6
- QtNetwork/QNetworkAccessManager fuer HTTPS REST
- QtWebSockets/QWebSocket fuer WSS
- stdlib `sqlite3` fuer genau eine lokale Cache-/Queue-Datei
- bestehende Alarmcast-Abhaengigkeiten und TCP/mDNS-Protokoll
- PyInstaller
- Inno Setup fuer Installer

### Server

- Python 3.12
- FastAPI
- Uvicorn, Version 1 genau ein Worker
- PostgreSQL
- SQLAlchemy 2
- Alembic
- psycopg 3
- Argon2id via argon2-cffi
- opaque serverseitige Session-Tokens, kein JWT
- PostgreSQL-Volltextsuche
- Windows-Dienst via pywin32

### Bewusst nicht verwendet

- Redis, RabbitMQ, Kafka, Celery oder Broker
- Elasticsearch/OpenSearch
- Docker als Produktionsvoraussetzung
- Electron/Webclient
- zweiter Desktop-HTTP-/WebSocket-Stack
- Poetry, PDM, Hatch oder uv als alternatives Buildsystem
- Ende-zu-Ende-Verschluesselung
- Messaging-Mesh

## Begruendung

- Ein Python-Monorepo reduziert Kontextwechsel und doppelte Fachmodelle.
- QtNetwork/QWebSocket vermeidet einen zweiten asynchronen Desktop-Netzwerkstack neben Qt.
- PostgreSQL bietet Transaktionen, Constraints, Volltextsuche und langfristige Persistenz.
- Ein Worker und ein In-Process-WebSocket-Hub sind fuer den einzelnen internen Server ausreichend und vermeiden einen Broker.
- REST-Reconciliation nach Reconnect macht WebSocket-Events nicht zur dauerhaften Wahrheit.
- Alarmcast bleibt auch bei Messaging-Serverausfall direkt funktionsfaehig.

## Folgen

- Mehrworker-/HA-Betrieb benoetigt eine spaetere Architekturentscheidung.
- Produktionsbetrieb benoetigt PostgreSQL und TLS-Zertifikatskonfiguration.
- Windows-Hardwarefunktionen benoetigen weiterhin manuelle Smoke-Tests.
- Neue Top-Level-Abhaengigkeiten ausserhalb dieser Entscheidung oder eines expliziten Inkrements sind verboten.
