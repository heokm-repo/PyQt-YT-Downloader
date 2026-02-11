"""
앱 삭제 기능 모듈
앱 완전 삭제를 위한 배치 파일 및 VBScript 생성/실행
"""

import os
import sys
import subprocess
from utils.logger import log
from constants import UNINSTALL_BATCH_FILENAME, UNINSTALL_VBS_FILENAME, APPDATA_DIR_NAME


def uninstall_app():
    """
    앱 완전 삭제 실행
    
    Returns:
        bool: 성공 여부 (True: 삭제 프로세스 시작, False: 실패)
    """
    try:
        # 개발 환경 체크
        if not getattr(sys, 'frozen', False):
            log.warning("개발 환경에서는 앱 삭제가 시뮬레이션됩니다.")
            return False
        
        # 1. exe 파일 경로 가져오기
        exe_path = sys.executable
        exe_dir = os.path.dirname(exe_path)
        exe_name = os.path.basename(exe_path)
        
        # 2. 배치 파일 경로
        bat_path = os.path.join(exe_dir, UNINSTALL_BATCH_FILENAME)
        
        # 3. 배치 파일 내용 작성
        bat_content = _generate_uninstall_bat(exe_name)
        
        # 4. 배치 파일 작성 (cp949 인코딩)
        with open(bat_path, 'w', encoding='cp949') as f:
            f.write(bat_content)
        
        # 5. VBScript 파일 생성 (배치 파일을 숨김 모드로 실행)
        vbs_path = os.path.join(exe_dir, UNINSTALL_VBS_FILENAME)
        vbs_content = _generate_silent_vbs()
        
        with open(vbs_path, 'w', encoding='utf-8') as f:
            f.write(vbs_content)
        
        log.info(f"uninstall.bat 생성 완료: {bat_path}")
        log.info(f"uninstall_silent.vbs 생성 완료: {vbs_path}")
        
        # 6. VBScript 실행 (배치 파일을 숨김 모드로 실행)
        subprocess.Popen(
            f'wscript.exe "{vbs_path}"',
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        log.info("uninstall_silent.vbs 실행 완료, 앱 종료 예정...")
        return True
        
    except Exception as e:
        log.error(f"앱 삭제 중 오류 발생: {e}", exc_info=True)
        return False


def _generate_uninstall_bat(exe_name):
    """
    uninstall.bat 파일 내용 생성
    
    Args:
        exe_name: 실행 파일명
    
    Returns:
        str: 배치 파일 내용
    """
    return f"""@echo off
echo ========================================
echo YT Downloader Uninstall
echo ========================================
echo.

echo [1/4] Waiting for process to close...
timeout /t 3 /nobreak >nul

echo [2/4] Force closing process...
taskkill /F /IM "{exe_name}" /T >nul 2>&1

echo [3/4] Additional wait...
timeout /t 2 /nobreak >nul

echo [4/4] Removing AppData folder...
set "APPDATA_DIR=%APPDATA%\\{APPDATA_DIR_NAME}"
if exist "%APPDATA_DIR%" (
    attrib -r "%APPDATA_DIR%\\*.*" /s /d >nul 2>&1
    rd /s /q "%APPDATA_DIR%" >nul 2>&1
    if exist "%APPDATA_DIR%" (
        timeout /t 1 /nobreak >nul
        rd /s /q "%APPDATA_DIR%" >nul 2>&1
    )
    if exist "%APPDATA_DIR%" (
        timeout /t 1 /nobreak >nul
        rd /s /q "%APPDATA_DIR%" >nul 2>&1
    )
    echo AppData folder removed.
) else (
    echo AppData folder not found.
)

echo [5/5] Removing executable...
set "EXE_FILE=%~dp0{exe_name}"
if exist "%EXE_FILE%" (
    attrib -r "%EXE_FILE%" >nul 2>&1
    del /f /q "%EXE_FILE%" >nul 2>&1
    if exist "%EXE_FILE%" (
        timeout /t 1 /nobreak >nul
        del /f /q "%EXE_FILE%" >nul 2>&1
    )
    if exist "%EXE_FILE%" (
        timeout /t 1 /nobreak >nul
        del /f /q "%EXE_FILE%" >nul 2>&1
    )
    echo Executable removed.
) else (
    echo Executable not found.
)

echo.
echo Uninstall complete!

REM VBScript 파일 삭제
if exist "%~dp0{UNINSTALL_VBS_FILENAME}" (
    del /f /q "%~dp0{UNINSTALL_VBS_FILENAME}" >nul 2>&1
)

REM 배치 파일 자체 삭제 후 종료
(goto) 2>nul & del "%~f0"
"""


def _generate_silent_vbs():
    """
    VBScript 파일 내용 생성 (배치 파일을 숨김 모드로 실행)
    
    Returns:
        str: VBScript 파일 내용
    """
    return f'''Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objShell = CreateObject("WScript.Shell")

' VBScript 파일의 디렉토리 가져오기
strScriptPath = WScript.ScriptFullName
strScriptDir = objFSO.GetParentFolderName(strScriptPath)

' 배치 파일 경로 생성
strBatFile = strScriptDir & "\\" & "{UNINSTALL_BATCH_FILENAME}"

' 배치 파일 존재 확인 후 실행 (숨김 모드)
If objFSO.FileExists(strBatFile) Then
    objShell.Run """" & strBatFile & """", 0, False
End If

Set objShell = Nothing
Set objFSO = Nothing
'''
