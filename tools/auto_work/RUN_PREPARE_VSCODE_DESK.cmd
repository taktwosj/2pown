@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0prepare_vscode_desk.ps1" %*
exit /b %ERRORLEVEL%
