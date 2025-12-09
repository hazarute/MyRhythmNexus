@echo off
setlocal
set APPDIR=%APPDATA%\MyRhythmNexus
if not exist "%APPDIR%" mkdir "%APPDIR%"
copy "%~dp0\MyRhythmNexus_v1.0.3.exe" "%APPDIR%\MyRhythmNexus_v1.0.3.exe" /Y
copy "%~dp0\config.json" "%APPDIR%\config.json" /Y
echo Kurulum tamamlandi. Uygulamayi baslatmak icin exe'yi calistirin.
pause
endlocal
