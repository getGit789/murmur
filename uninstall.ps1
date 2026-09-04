# Murmur uninstaller. Runs from "Apps & features", Revo, or by hand:
#
#   powershell -ExecutionPolicy Bypass -File "%LOCALAPPDATA%\Programs\Murmur\_internal\uninstall.ps1"
#
# Settings, dictionary and history are kept. Add -All to remove those too.

param([switch]$All)

$ErrorActionPreference = "SilentlyContinue"
$target = "$env:LOCALAPPDATA\Programs\Murmur"

# This script ships inside the install folder. Deleting the folder you
# are running from is unreliable, so hop to a copy in TEMP first.
if ($PSCommandPath -and $PSCommandPath -like "$target*") {
    $hop = Join-Path $env:TEMP "murmur-uninstall.ps1"
    Copy-Item -LiteralPath $PSCommandPath -Destination $hop -Force
    $hopArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $hop)
    if ($All) { $hopArgs += "-All" }
    Start-Process powershell.exe -ArgumentList $hopArgs
    exit 0
}

Write-Host "Removing Murmur..."
Get-Process Murmur -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

$programs = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
Remove-Item -LiteralPath "$programs\Murmur.lnk" -Force              # Start Menu
Remove-Item -LiteralPath "$programs\Startup\Murmur.lnk" -Force      # start with Windows
Remove-Item -LiteralPath "$env:USERPROFILE\Desktop\Murmur.lnk" -Force  # Desktop
Remove-Item -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\Murmur" -Recurse -Force
Remove-Item -LiteralPath $target -Recurse -Force

if ($All) {
    Remove-Item -LiteralPath "$env:APPDATA\Murmur" -Recurse -Force
    Write-Host "Murmur is gone, settings and history included."
} else {
    Write-Host "Murmur is uninstalled."
    Write-Host "Your settings and history were kept at $env:APPDATA\Murmur"
    Write-Host "(run the uninstaller with -All to remove those as well)."
}
Start-Sleep -Seconds 3
