@echo off
REM Install release config to user's AppData and run the release EXE
setlocal
set "APP_CONFIG=%APPDATA%\MyRhythmNexus"
if not exist "%APP_CONFIG%" mkdir "%APP_CONFIG%"
copy /Y "%~dp0config.json" "%APP_CONFIG%\config.json" >nul
if %errorlevel% equ 0 (
  echo Copied config.json to %APP_CONFIG%\config.json
) else (
  echo Failed to copy config.json to %APP_CONFIG%\config.json
)

REM Run the release executable from the release folder
"%~dp0MyRhythmNexus_v1.0.0.exe"
endlocal
