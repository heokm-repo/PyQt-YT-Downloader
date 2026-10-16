@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 exit /b 1
echo Starting YTDownloader build...
python -B -m build_scripts.build_release %*
set "BUILD_EXIT=%ERRORLEVEL%"
popd
exit /b %BUILD_EXIT%
