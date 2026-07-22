# Alarmcast-Runtime-Contracts

## Zweck und Grenze

`alarmcast.alarmcast_runtime.contracts` beschreibt die heute beobachtbaren Zustände von
Alarmcast-Quelle und -Überwacher als unveränderliche Daten. Das Modul enthält keine Laufzeitlogik
und hängt weder von Qt noch von Sockets, Threads, Audioimplementierungen, Discovery oder den
Bestandsmodulen `alarmcast.core`, `alarmcast.host` und `alarmcast.client` ab.

A01 führt keine Fassade, API-Protocols, Adapter, Composition, Events oder neue Produktzustände ein.
Insbesondere existieren weiterhin keine stabile Alarm-ID, Monitor-ID oder Geräte-ID.

## Öffentliche Typen

| Typ | Bedeutung |
| --- | --- |
| `RuntimeState` | `stopped`, `running` |
| `AlarmState` | `inactive`, `active` |
| `ConnectionState` | `disconnected`, `discovering`, `connecting`, `connected`, `reconnecting` |
| `ResetOrigin` | `local_source`, `local_monitor`, `remote_monitor` |
| `NetworkEndpoint` | Bereits getrimmter Host-String und Port von 1 bis 65535 |
| `ConnectedMonitor` | Aktuell beobachtbarer Clientname und Netzwerkendpunkt |
| `SourceSnapshot` | Lauf-, Alarm- und verbundener Überwacherzustand einer Quelle |
| `MonitorSnapshot` | Lauf-, Verbindungs- und Alarmzustand eines Überwachers |
| `AlarmResetRequest` | Lokaler Reset oder vom Host beobachteter Reset eines benannten Überwachers |

Alle Datenobjekte sind `frozen=True` und verwenden Slots. Collections werden ausschließlich als
Tuple veröffentlicht. Eingaben werden nicht getrimmt, aufgelöst oder anderweitig normalisiert;
ungültige Werte schlagen unmittelbar mit `TypeError` oder `ValueError` fehl.

## Invarianten

- Eine gestoppte Quelle ist alarmfrei und hat keine verbundenen Überwacher.
- Ein gestoppter Überwacher ist getrennt, alarmfrei und besitzt keinen Quellenendpunkt.
- `connecting`, `connected` und `reconnecting` benötigen einen Quellenendpunkt.
- `disconnected` und `discovering` dürfen keinen Quellenendpunkt tragen.
- Ein laufender, getrennter Überwacher darf einen bereits aktiven Alarm weiter anzeigen.
- Ein Remote-Reset benötigt den nicht leeren, bereits getrimmten Clientnamen als `requester`.
- Lokale Resets tragen keinen `requester`.

`NetworkEndpoint` validiert nur Form und Portbereich. DNS-Auflösung, IP-Prüfung und
Socketerzeugung sind ausdrücklich nicht Bestandteil des Vertrags.
