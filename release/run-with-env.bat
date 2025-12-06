@echo off
REM Run the release EXE with environment overrides (no file copy)
setlocal
set "RHYTHM_NEXUS_LICENSE_SERVER_URL=http://localhost:8001/api/v1"
set "RHYTHM_NEXUS_BACKEND_URL=http://localhost:8000/api/v1"

REM Run the release executable from this folder
"%~dp0MyRhythmNexus_v1.0.0.exe"
endlocal
