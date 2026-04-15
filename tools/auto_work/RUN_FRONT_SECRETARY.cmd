@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
if exist "%LocalAppData%\Programs\Python\Python314\python.exe" (
  "%LocalAppData%\Programs\Python\Python314\python.exe" "%SCRIPT_DIR%front_secretary.py" %*
  exit /b %ERRORLEVEL%
)
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%SCRIPT_DIR%front_secretary.py" %*
  exit /b %ERRORLEVEL%
)
python "%SCRIPT_DIR%front_secretary.py" %*
exit /b %ERRORLEVEL%
