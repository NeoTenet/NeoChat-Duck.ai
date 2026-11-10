@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "APP_NAME=Neo AI Terminal"
set "APP_DIR=dist\%APP_NAME%"
set "OUT_ZIP=dist\NeoAI-Terminal-Lightweight-Portable-Windows.zip"
set "CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe"

if not exist "%CSC%" set "CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe"
if not exist "%CSC%" (
  echo [ERROR] .NET Framework C# compiler was not found.
  echo         Use a Windows 10/11 computer with .NET Framework 4.8 enabled.
  pause
  exit /b 1
)

if exist "dist" rmdir /s /q "dist"
mkdir "%APP_DIR%" || goto failed

 echo.
 echo  Neo AI Terminal - Lightweight Portable Builder
 echo  ------------------------------------------------
 echo  The EXE is a tiny bootstrapper. Python, Node.js and libraries
 echo  are downloaded into the local runtime folder on first launch.
 echo.

 echo [1/4] Compiling the lightweight Windows launcher...
"%CSC%" /nologo /optimize+ /target:winexe /platform:x64 /out:"%APP_DIR%\Neo AI Terminal.exe" ^
  /reference:System.dll ^
  /reference:System.Core.dll ^
  /reference:System.Drawing.dll ^
  /reference:System.Windows.Forms.dll ^
  /reference:System.Web.Extensions.dll ^
  /reference:System.IO.Compression.dll ^
  /reference:System.IO.Compression.FileSystem.dll ^
  neo_portable_launcher.cs
if errorlevel 1 goto failed

 echo [2/4] Copying the application source and web interface...
for %%F in (neo_launcher.py web_app.py duck_cli.py duckai_catalog.py duck_i18n.py duck_voice.py api_providers.py secure_store.py jsa_jsdom.js lang_fa.json package.json requirements-portable.txt README_FA.md README_EN.md BUILD-WINDOWS-EXE.md LICENSE THIRD_PARTY_NOTICES.md) do (
  if not exist "%%F" (
    echo [ERROR] Required project file is missing: %%F
    goto failed
  )
  copy /y "%%F" "%APP_DIR%\%%F" >nul || goto failed
)
robocopy "web" "%APP_DIR%\web" /E /NFL /NDL /NJH /NJS /NC /NS
if errorlevel 8 goto failed
mkdir "%APP_DIR%\generated" 2>nul
> "%APP_DIR%\generated\README.txt" echo Generated images are stored in this folder after the first run.
> "%APP_DIR%\portable.flag" echo Neo AI Terminal lightweight portable mode

 echo [3/4] Preparing first-run setup metadata...
mkdir "%APP_DIR%\runtime" 2>nul
> "%APP_DIR%\runtime\README.txt" echo Python 3.13.17, Node.js LTS and app dependencies are installed here automatically on first launch.

 echo [4/4] Creating the portable ZIP...
if not exist "dist" mkdir "dist"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path '%APP_DIR%\*' -DestinationPath '%OUT_ZIP%' -Force"
if errorlevel 1 goto failed

for %%F in ("%APP_DIR%\Neo AI Terminal.exe") do set "EXE_SIZE=%%~zF"
for %%F in ("%OUT_ZIP%") do set "ZIP_SIZE=%%~zF"

echo.
echo [DONE] Lightweight portable package created.
echo Launcher : %APP_DIR%\Neo AI Terminal.exe
echo ZIP      : %OUT_ZIP%
echo EXE size : %EXE_SIZE% bytes
echo ZIP size : %ZIP_SIZE% bytes
echo.
echo On the target computer, extract the ENTIRE ZIP and double-click the EXE.
echo First launch requires internet access. Python, Node.js and dependencies
 echo are downloaded once into the adjacent runtime folder.
echo.
if not defined GITHUB_ACTIONS pause
exit /b 0

:failed
echo.
echo [ERROR] Build failed. Review the messages above.
if not defined GITHUB_ACTIONS pause
exit /b 1
