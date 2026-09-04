; A proper Windows installer.
; Needs Inno Setup 6: https://jrsoftware.org/isdl.php
; Build the app first (build.bat), then open this file in Inno Setup
; and press Build, or run:  iscc installer.iss

#define AppName    "Murmur"
#define AppVersion "0.1.0"
#define AppExe     "Murmur.exe"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Murmur
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
OutputDir=dist
OutputBaseFilename=Murmur-Setup-{#AppVersion}
SetupIconFile=assets\murmur.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; Per user, so no admin prompt.
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "dist\Murmur\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";        Filename: "{app}\{#AppExe}"
Name: "{userstartup}\{#AppName}";  Filename: "{app}\{#AppExe}"; Tasks: startupicon

[Tasks]
Name: "startupicon"; Description: "Start {#AppName} when Windows starts"; GroupDescription: "Extras:"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Start {#AppName} now"; Flags: nowait postinstall skipifsilent
