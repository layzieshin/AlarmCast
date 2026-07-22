# B03 Windows-Neustart-Smoke

Dieser Test prueft die Persistenz in zwei getrennten Python-Prozessen. Er verwendet ein neu
erzeugtes temporaeres `APPDATA`; die echte Benutzerkonfiguration unter
`%APPDATA%\AlarmCast` wird weder gelesen noch geschrieben.

## Schritte

In PowerShell aus dem Repository-Root:

```powershell
$realAppData = $env:APPDATA
$smokeRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("alarmcast-b03-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $smokeRoot | Out-Null
$env:APPDATA = $smokeRoot

@'
from alarmcast.core.config import ClientConfig, HostConfig, save_client_config, save_host_config

save_host_config(HostConfig(psk="B03-SMOKE", signal_target=5, window_seconds=7.5))
save_client_config(ClientConfig(host_addr="192.0.2.25", psk="B03-SMOKE", volume=0.4))
'@ | .\.venv\Scripts\python.exe -

@'
import json
from alarmcast.core.config import get_config_dir, load_client_config, load_host_config

host = load_host_config()
client = load_client_config()
assert (host.psk, host.signal_target, host.window_seconds) == ("B03-SMOKE", 5, 7.5)
assert (client.host_addr, client.psk, client.volume) == ("192.0.2.25", "B03-SMOKE", 0.4)
root = get_config_dir()
for name in ("host.json", "client.json", "host.json.bak", "client.json.bak"):
    data = json.loads((root / name).read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
print(f"B03 restart smoke OK: {root}")
'@ | .\.venv\Scripts\python.exe -

$env:APPDATA = $realAppData
Remove-Item -LiteralPath $smokeRoot -Recurse -Force
```

Erwartet wird genau eine Erfolgsmeldung `B03 restart smoke OK: <temporaerer Pfad>`. Beide
Prozesse muessen ohne Assertion oder Traceback mit Exitcode 0 enden. Die vier JSON-Dateien
muessen vollstaendige Objekte mit `schema_version` 1 sein.

## Ausfuehrungsprotokoll

- Datum: wird nach dem Green Gate eingetragen
- Getesteter Commit: wird nach dem Implementierungscommit eingetragen
- Tester: Codex auf Windows, Python 3.12.10
- Ergebnis: wird nach dem Green Gate eingetragen
