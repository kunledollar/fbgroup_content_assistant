#define MyAppName "Community Pulse AI"
#define MyAppExeName "CommunityPulseAI.exe"
[Setup]
AppId={{4BEF1FF2-2BE8-42E3-9E59-B67197662CE1}
AppName={#MyAppName}
AppVersion=0.1.0
DefaultDirName={autopf}\Community Pulse AI
DefaultGroupName={#MyAppName}
OutputDir=..\dist
OutputBaseFilename=CommunityPulseAI-Setup
Compression=lzma
SolidCompression=yes
[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"
[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
