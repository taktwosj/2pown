@echo off
setlocal

set "TELEGRAM_START=C:\2POW\03_telegram_py\START_TELEGRAM_BOT_NOW.bat"
set "MENU34_SHADOW_BASE=%~1"

if not defined MENU34_SHADOW_BASE (
  if exist "C:\2POW\ivwith\daily_sync.py" (
    set "MENU34_SHADOW_BASE=C:\2POW"
  )
)

if not exist "%TELEGRAM_START%" (
  echo [ERROR] 03_telegram_py start script not found: %TELEGRAM_START%
  exit /b 1
)

if defined MENU34_SHADOW_BASE (
  call "%TELEGRAM_START%" "%MENU34_SHADOW_BASE%"
) else (
  call "%TELEGRAM_START%"
)
exit /b %errorlevel%
