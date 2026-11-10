@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "APP_DIR=dist\Neo AI Terminal"
set "OUT_ZIP=dist\NeoAI-Terminal-Portable-Windows.zip"

echo.
echo  Neo AI Terminal - Lightweight Portable Windows Builder
 echo -----------------------------------------------
echo  The EXE stays small; Python files are in _internal.
echo  Node.js + jsdom + Vazir are stored beside the EXE.
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3.10+ was not found on this build computer.
  echo         Install 64-bit Python from https://www.python.org/downloads/
  pause
  exit /b 1
)
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 goto failed

where node >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js LTS is required on the build computer.
  echo         Install from https://nodejs.org and run this script again.
  pause
  exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 goto failed

 echo [1/5] Installing lean Python dependencies...
python -m pip install --upgrade -r requirements-windows-exe.txt
if errorlevel 1 goto failed

 echo [2/5] Installing production npm dependencies...
call npm install --omit=dev --no-audit --no-fund
if errorlevel 1 goto failed
node -e "require('jsdom')" >nul 2>&1
if errorlevel 1 goto failed
if not exist "node_modules\vazir-font\dist\font-face.css" goto failed

 echo [3/5] Building small onedir EXE...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
python -m PyInstaller --noconfirm --clean NeoAITerminal.spec
if errorlevel 1 goto failed

if not exist "%APP_DIR%\Neo AI Terminal.exe" (
  echo [ERROR] PyInstaller did not create the EXE.
  goto failed
)

 echo [4/5] Adding external Node.js, jsdom and Vazir beside the EXE...
if not exist "%APP_DIR%\node" mkdir "%APP_DIR%\node"
for /f "delims=" %%N in ('where node') do if not defined NODE_SOURCE set "NODE_SOURCE=%%N"
if not defined NODE_SOURCE goto failed
copy /y "%NODE_SOURCE%" "%APP_DIR%\node\node.exe" >nul
if errorlevel 1 goto failed
robocopy "node_modules" "%APP_DIR%\node_modules" /E /NFL /NDL /NJH /NJS /NC /NS /XD .cache
if errorlevel 8 goto failed
> "%APP_DIR%\portable.flag" echo Neo AI Terminal portable mode
if not exist "%APP_DIR%\data" mkdir "%APP_DIR%\data"
copy /y "README_FA.md" "%APP_DIR%\README_FA.md" >nul
copy /y "LICENSE" "%APP_DIR%\LICENSE" >nul
copy /y "THIRD_PARTY_NOTICES.md" "%APP_DIR%\THIRD_PARTY_NOTICES.md" >nul

 echo [5/5] Creating portable ZIP...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%APP_DIR%\*' -DestinationPath '%OUT_ZIP%' -Force"
if errorlevel 1 goto failed

for %%F in ("%APP_DIR%\Neo AI Terminal.exe") do set "EXE_SIZE=%%~zF"
for %%F in ("%OUT_ZIP%") do set "ZIP_SIZE=%%~zF"

echo.
echo [DONE] Lightweight portable build completed.
echo EXE : %APP_DIR%\Neo AI Terminal.exe
 echo ZIP : %OUT_ZIP%
echo.
echo Main EXE size: %EXE_SIZE% bytes
 echo Portable ZIP size: %ZIP_SIZE% bytes
echo.
echo IMPORTANT: Do not move the EXE alone. Keep _internal, node, node_modules, data and portable.flag beside it.
start "" "%APP_DIR%\Neo AI Terminal.exe"
pause
exit /b 0

:failed
echo.
echo [ERROR] Build failed. Review the messages above.
pause
exit /b 1
