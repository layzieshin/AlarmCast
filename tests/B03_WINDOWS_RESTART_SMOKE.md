# B03 Windows-Neustart-Smoke

Dieser Test prueft die Persistenz in zwei getrennten Python-Prozessen. Er verwendet ein neu
erzeugtes temporaeres `APPDATA`. Die Anwendungsprozesse lesen und schreiben ausschliesslich
dort; Pruefsummen vor und nach dem Lauf belegen, dass die echte Benutzerkonfiguration unter
`%APPDATA%\AlarmCast` unveraendert bleibt.

## Schritte

In PowerShell aus dem Repository-Root:

```powershell
$b03TestedCommit = git rev-parse HEAD
$b03RealAppData = $env:APPDATA
$b03RealConfig = Join-Path $b03RealAppData 'AlarmCast'
$b03Names = @('host.json','client.json','host.json.bak','client.json.bak')
$b03Before = @{}
foreach ($b03Name in $b03Names) {
  $b03Path = Join-Path $b03RealConfig $b03Name
  if (Test-Path -LiteralPath $b03Path) {
    $b03Before[$b03Name] = (Get-FileHash -LiteralPath $b03Path -Algorithm SHA256).Hash
  }
}
$b03TempBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$b03SmokeRoot = Join-Path $b03TempBase ('alarmcast-b03-' + [guid]::NewGuid())
$b03SmokeRoot = [System.IO.Path]::GetFullPath($b03SmokeRoot)
if (-not $b03SmokeRoot.StartsWith($b03TempBase, [System.StringComparison]::OrdinalIgnoreCase) `
    -or -not ([System.IO.Path]::GetFileName($b03SmokeRoot)).StartsWith('alarmcast-b03-')) {
  throw 'Unsafe smoke path'
}
New-Item -ItemType Directory -Path $b03SmokeRoot | Out-Null
try {
  $env:APPDATA = $b03SmokeRoot
  @'
from alarmcast.core.config import ClientConfig, HostConfig, save_client_config, save_host_config
save_host_config(HostConfig(psk="B03-SMOKE", signal_target=5, window_seconds=7.5))
save_client_config(ClientConfig(host_addr="192.0.2.25", psk="B03-SMOKE", volume=0.4))
'@ | & '.\.venv\Scripts\python.exe' -
  if ($LASTEXITCODE -ne 0) { throw 'Smoke process A failed' }
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
'@ | & '.\.venv\Scripts\python.exe' -
  if ($LASTEXITCODE -ne 0) { throw 'Smoke process B failed' }
}
finally {
  $env:APPDATA = $b03RealAppData
  if (Test-Path -LiteralPath $b03SmokeRoot) {
    Remove-Item -LiteralPath $b03SmokeRoot -Recurse -Force
  }
}
foreach ($b03Name in $b03Names) {
  $b03Path = Join-Path $b03RealConfig $b03Name
  $b03ExistsAfter = Test-Path -LiteralPath $b03Path
  if ($b03Before.ContainsKey($b03Name)) {
    if (-not $b03ExistsAfter -or `
        (Get-FileHash -LiteralPath $b03Path -Algorithm SHA256).Hash -ne $b03Before[$b03Name]) {
      throw "Real config changed: $b03Name"
    }
  } elseif ($b03ExistsAfter) {
    throw "Real config created: $b03Name"
  }
}
Write-Output "Real APPDATA configuration unchanged; tested commit $b03TestedCommit"
```

Erwartet werden die Meldungen `B03 restart smoke OK: <temporaerer Pfad>` und
`Real APPDATA configuration unchanged; tested commit <SHA>`. Beide Python-Prozesse muessen
ohne Assertion oder Traceback mit Exitcode 0 enden. Die vier temporaeren JSON-Dateien muessen
vollstaendige Objekte mit `schema_version` 1 sein.

## Ausfuehrungsprotokoll

- Datum: 2026-07-22
- Getesteter Commit: `37d6292329ee78462fee7db20c821c5a2c48cf82`
- Tester: Codex auf Windows, Python 3.12.10
- Ergebnis: `OK`; Host- und Clientwerte blieben im zweiten Prozess erhalten, Haupt- und
  Sicherungsdateien waren gueltige Schema-1-Objekte, die echte APPDATA-Konfiguration blieb
  laut SHA-256-Vergleich unveraendert und das temporaere Verzeichnis wurde entfernt.
