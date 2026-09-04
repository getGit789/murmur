# Murmur one-line installer.
#
#   powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/getGit789/murmur/main/install.ps1 | iex"
#
# Downloads the latest release, puts it in %LOCALAPPDATA%\Programs\Murmur,
# adds a Start Menu entry, and starts it. No admin rights needed.
# Everything Murmur hears stays on your machine when the engine is "local".

$ErrorActionPreference = "Stop"
$repo   = "getGit789/murmur"
$target = "$env:LOCALAPPDATA\Programs\Murmur"

Write-Host "Finding the latest Murmur release..."
$api     = "https://api.github.com/repos/$repo/releases/latest"
$release = Invoke-RestMethod -Uri $api -Headers @{ "User-Agent" = "murmur-installer" }
$asset   = $release.assets | Where-Object { $_.name -like "Murmur-*.zip" } | Select-Object -First 1
if (-not $asset) { throw "The latest release has no Murmur zip. Try again later." }

$zip = Join-Path $env:TEMP "murmur-install.zip"
Write-Host ("Downloading {0} ({1} MB)..." -f $asset.name, [math]::Round($asset.size / 1MB))
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip -UseBasicParsing

# A running copy locks its own files.
Get-Process Murmur -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

if (Test-Path $target) { Remove-Item $target -Recurse -Force }
Write-Host "Unpacking..."
Expand-Archive -Path $zip -DestinationPath (Split-Path $target) -Force
Remove-Item $zip -Force
if (-not (Test-Path "$target\Murmur.exe")) { throw "Unpack failed - Murmur.exe is missing." }

$lnk = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Murmur.lnk"
$s = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk)
$s.TargetPath       = "$target\Murmur.exe"
$s.WorkingDirectory = $target
$s.IconLocation     = "$target\_internal\assets\murmur.ico"
$s.Description      = "Murmur - Speak. It types."
$s.Save()

# Tell Windows the app exists, so it shows up in "Apps & features"
# (and in uninstall tools) with a working Uninstall button.
$reg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\Murmur"
$un  = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$target\_internal\uninstall.ps1`""
New-Item -Path $reg -Force | Out-Null
New-ItemProperty -Path $reg -Name DisplayName     -Value "Murmur" -PropertyType String -Force | Out-Null
New-ItemProperty -Path $reg -Name DisplayVersion  -Value $release.tag_name.TrimStart("v") -PropertyType String -Force | Out-Null
New-ItemProperty -Path $reg -Name Publisher       -Value "Damir Kranjcevic" -PropertyType String -Force | Out-Null
New-ItemProperty -Path $reg -Name InstallLocation -Value $target -PropertyType String -Force | Out-Null
New-ItemProperty -Path $reg -Name DisplayIcon     -Value "$target\Murmur.exe" -PropertyType String -Force | Out-Null
New-ItemProperty -Path $reg -Name UninstallString -Value $un -PropertyType String -Force | Out-Null
New-ItemProperty -Path $reg -Name QuietUninstallString -Value $un -PropertyType String -Force | Out-Null
New-ItemProperty -Path $reg -Name HelpLink        -Value "https://github.com/getGit789/murmur" -PropertyType String -Force | Out-Null
New-ItemProperty -Path $reg -Name NoModify        -Value 1 -PropertyType DWord -Force | Out-Null
New-ItemProperty -Path $reg -Name NoRepair        -Value 1 -PropertyType DWord -Force | Out-Null
$kb = [math]::Round((Get-ChildItem $target -Recurse | Measure-Object Length -Sum).Sum / 1KB)
New-ItemProperty -Path $reg -Name EstimatedSize   -Value $kb -PropertyType DWord -Force | Out-Null

Write-Host ""
Write-Host "Installed. Hold Right Ctrl in any app, talk, let go - it types."
Write-Host "Settings live under Ctrl+comma."
Write-Host "Uninstall any time from Windows Settings > Apps > Murmur."
Start-Process "$target\Murmur.exe"
