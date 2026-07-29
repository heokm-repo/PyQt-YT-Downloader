; Inno Setup Script for YT Downloader
; https://jrsoftware.org/isinfo.php

#ifndef MyAppName
  #define MyAppName "YT Downloader"
#endif
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#ifndef MyAppPublisher
  #define MyAppPublisher "Heo KyungMin"
#endif
#ifndef MyAppURL
  #define MyAppURL "https://github.com/heokm-repo/PyQt-YT-Downloader"
#endif
#ifndef MyAppExeName
  #define MyAppExeName "YTDownloader.exe"
#endif
#ifndef MyAppInstallDirName
  #define MyAppInstallDirName "YTDownloader"
#endif
#ifndef MyOutputDir
  #define MyOutputDir "output"
#endif
#ifndef MySetupIconFile
  #define MySetupIconFile "app_icon.ico"
#endif
#ifndef MyDistDir
  #define MyDistDir "dist\YTDownloader"
#endif
[Setup]
AppId={{B8F3D1A2-5C4E-4F7A-9B1D-2E3F4A5B6C7D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppInstallDirName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#MyOutputDir}
OutputBaseFilename=Setup_{#MyAppInstallDirName}_v{#MyAppVersion}
SetupIconFile={#MySetupIconFile}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
; Reuse the existing install directory during updates
UsePreviousAppDir=yes
; Automatically close the running app
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy the full PyInstaller one-dir build output
Source: "{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; Remove the previous PyInstaller runtime before copying the new one.
; This prevents obsolete Python packages from surviving an in-place update.
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent runasoriginaluser
Filename: "{app}\{#MyAppExeName}"; Flags: nowait runasoriginaluser; Check: ShouldRunAfterSilentUpdate

[Code]
function HasRunAfterInstallParam: Boolean;
var
  I: Integer;
  Value: String;
begin
  Result := False;
  for I := 1 to ParamCount do
  begin
    Value := ParamStr(I);
    if (CompareText(Value, '/RUNAFTERINSTALL') = 0) or
       (CompareText(Value, '-RUNAFTERINSTALL') = 0) then
    begin
      Result := True;
      Exit;
    end;
  end;
end;

function ShouldRunAfterSilentUpdate: Boolean;
begin
  Result := WizardSilent and HasRunAfterInstallParam;
end;
