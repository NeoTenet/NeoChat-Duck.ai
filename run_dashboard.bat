@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo  Neo AI Terminal - Duck.ai Free models inside the panel
echo  ------------------------------------------------------

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3.10+ was not found. Install it from https://www.python.org/downloads/
  pause
  exit /b 1
)
python -c "import fastapi, uvicorn, multipart, requests, PIL, keyring" >nul 2>&1
if errorlevel 1 (
  echo [SETUP] Installing Python dependencies...
  python -m pip install -r requirements.txt
  if errorlevel 1 goto failed
)
where node >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js LTS is required by Duck.ai's in-panel challenge client.
  echo         Install Node.js from https://nodejs.org and run this file again.
  pause
  exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
  echo [ERROR] npm not found. Reinstall Node.js LTS with npm included.
  pause
  exit /b 1
)
set "NEED_NPM=0"
node -e "require('jsdom')" >nul 2>&1
if errorlevel 1 set "NEED_NPM=1"
if not exist "node_modules\vazir-font\dist\font-face.css" set "NEED_NPM=1"
if "%NEED_NPM%"=="1" (
  echo [SETUP] Installing jsdom and the local Vazir font automatically...
  call npm install --omit=dev
  if errorlevel 1 goto failed
)
node -e "require('jsdom')" >nul 2>&1
if errorlevel 1 goto failed
if not exist "node_modules\vazir-font\dist\font-face.css" goto failed

echo [OK] Dependencies ready.
echo [START] http://127.0.0.1:8765
python neo_launcher.py
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo [ERROR] Setup or startup failed. See the message above.
pause
exit /b 1
