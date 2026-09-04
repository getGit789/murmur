# Murmur one-line installer.
#
#   powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/getGit789/murmur/main/install.ps1 | iex"
#
# Downloads the latest release, puts it in %LOCALAPPDATA%\Programs\Murmur,
# adds Start Menu and (if you want) Desktop shortcuts, registers the app
# with Windows, sets it to start quietly with the computer, and starts it.
# No admin rights needed. With the local engine your voice never leaves
# your machine.

$ErrorActionPreference = "Stop"
$repo   = "getGit789/murmur"
$target = "$env:LOCALAPPDATA\Programs\Murmur"

function New-MurmurShortcut([string]$Path, [string]$Arguments = "") {
    $s = (New-Object -ComObject WScript.Shell).CreateShortcut($Path)
    $s.TargetPath       = "$target\Murmur.exe"
    if ($Arguments) { $s.Arguments = $Arguments }
    $s.WorkingDirectory = $target
    $s.IconLocation     = "$target\_internal\assets\murmur.ico"
    $s.Description      = "Murmur - Speak. It types."
    $s.Save()
}

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

# Start Menu entry, always.
$programs = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
New-MurmurShortcut "$programs\Murmur.lnk"

# Desktop shortcut, if wanted. From the Desktop (or the Start Menu) you
# can right-click Murmur and choose "Pin to taskbar".
$answer = "y"
try { $answer = Read-Host "Add a Desktop shortcut? (Y/n)" } catch { $answer = "y" }
if ($answer -notmatch "^\s*n") {
    New-MurmurShortcut "$env:USERPROFILE\Desktop\Murmur.lnk"
    Write-Host "Desktop shortcut added. Right-click it to Pin to taskbar."
}

# Start with Windows, quietly: tray only, no window. The talk key
# works the moment you log in.
New-MurmurShortcut "$programs\Startup\Murmur.lnk" "--hidden"

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
Write-Host "Murmur starts quietly with Windows from now on."
Write-Host "Settings live under Ctrl+comma (a free Groq key there makes it faster)."
Write-Host "Uninstall any time from Windows Settings > Apps > Murmur."
Start-Process "$target\Murmur.exe"
