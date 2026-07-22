# Build Alarmcast single EXE (requires Python 3.12)
$ErrorActionPreference = "Stop"

$py312 = & py -3.12 -c "import sys; print(sys.executable)" 2>$null
if (-not $py312) {
    Write-Error "Python 3.12 nicht gefunden. Installiere Python 3.12 und fuehre erneut aus: py -3.12 -m pip install -e '.[dev]'"
}

Set-Location $PSScriptRoot\..
& $py312 -m pip install -e ".[dev]"
& $py312 -m PyInstaller alarmcast.spec
& $py312 -m PyInstaller alarmcast-debug.spec
$exe = Get-Item "dist\alarmcast.exe" -ErrorAction SilentlyContinue
if ($exe) {
    $mb = [math]::Round($exe.Length / 1MB, 1)
    Write-Host "Fertig: dist\alarmcast.exe ($mb MB)"
}
Write-Host "Debug: dist\alarmcast-debug.exe"
