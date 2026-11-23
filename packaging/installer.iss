; Inno Setup script: Windows installer with Start-menu and optional desktop shortcut.
#define AppVersion GetEnv("APP_VERSION")
[Setup]
AppName=Recording to Word
AppVersion={#AppVersion}
DefaultDirName={autopf}\Recording to Word
DefaultGroupName=Recording to Word
OutputDir=..\dist
OutputBaseFilename=RecordingToWord-Windows-Setup
SetupIconFile=icon.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern

[Files]
Source: "..\dist\RecordingToWord\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\Recording to Word"; Filename: "{app}\RecordingToWord.exe"
Name: "{autodesktop}\Recording to Word"; Filename: "{app}\RecordingToWord.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"

[Run]
Filename: "{app}\RecordingToWord.exe"; Description: "Open Recording to Word now"; Flags: postinstall nowait skipifsilent
