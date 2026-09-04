; A proper Windows installer.
; Needs Inno Setup 6: https://jrsoftware.org/isdl.php
; Build the app first (build.bat), then open this file in Inno Setup
; and press Build, or run:  iscc installer.iss

#define AppName    "Murmur"
#define AppVersion "1.3.0"
#define AppExe     "Murmur.exe"

[Setup]
; A fixed id so upgrades replace cleanly and uninstall is tracked.
AppId={{7E9C2F1A-3B4D-4E5F-9A6B-1C2D3E4F5A6B}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Murmur
AppPublisherURL=https://github.com/getGit789/murmur
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
OutputDir=dist
OutputBaseFilename=Murmur-Setup-{#AppVersion}
SetupIconFile=assets\murmur.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
VersionInfoVersion={#AppVersion}
VersionInfoProductName={#AppName}
; Per user, so no admin prompt.
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "startupicon"; Description: "Start {#AppName} automatically when Windows starts (runs quietly in the background)"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "dist\Murmur\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";            Filename: "{app}\{#AppExe}"
Name: "{group}\Uninstall {#AppName}";  Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}";      Filename: "{app}\{#AppExe}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}";      Filename: "{app}\{#AppExe}"; Parameters: "--hidden"; Tasks: startupicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Start {#AppName} now"; Flags: nowait postinstall skipifsilent
