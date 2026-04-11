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
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DMyAppVersion="%APP_VER%" installer.iss
) else (
    echo WARNING: Inno Setup not found. Skipping installer creation.
    echo Install Inno Setup 6 from https://jrsoftware.org/isinfo.php
)

echo.
echo Build complete!
pause
