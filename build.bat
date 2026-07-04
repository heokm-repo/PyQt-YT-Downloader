@echo off
echo ========================================
echo  YTDownloader Build Script
echo ========================================
echo.

echo [1/4] Reading version from constants.py...
for /f "delims=" %%v in ('python get_version.py') do set APP_VER=%%v
if "%APP_VER%"=="" (
    echo ERROR: Failed to read version from constants.py
    pause
    exit /b 1
)
echo       Version: %APP_VER%

echo [2/4] Cleaning previous build...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo [3/4] Building with PyInstaller (one-dir)...
python -m PyInstaller YTDownloader.spec

echo [4/4] Creating installer with Inno Setup...
set "ISCC_EXE=%ISCC_PATH%"
if not defined ISCC_EXE (
    for %%p in ("%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" "%ProgramFiles%\Inno Setup 6\ISCC.exe") do (
        if exist "%%~p" set "ISCC_EXE=%%~p"
    )
)
if not defined ISCC_EXE (
    for /f "delims=" %%p in ('where ISCC 2^>nul') do (
        if not defined ISCC_EXE set "ISCC_EXE=%%p"
    )
)
if defined ISCC_EXE (
    "%ISCC_EXE%" /DMyAppVersion="%APP_VER%" installer.iss
) else (
    echo WARNING: Inno Setup not found. Skipping installer creation.
    echo Set ISCC_PATH or install Inno Setup 6 from https://jrsoftware.org/isinfo.php
)

echo.
echo Build complete!
pause
