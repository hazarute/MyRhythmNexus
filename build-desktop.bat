@echo off
REM MyRhythmNexus Desktop App Builder (Windows)
REM Desktop uygulamasında değişiklik yapıldığında bu script'i çalıştırın

echo 🖥️  MyRhythmNexus Desktop App Builder
echo ====================================

REM Colors (Windows CMD doesn't support ANSI colors well, so we'll use plain text)
set "GREEN=[INFO]"
set "YELLOW=[WARNING]"
set "RED=[ERROR]"

echo %GREEN% Starting desktop app build process...

REM Check if PyInstaller is installed
REM Ensure required Python packages are installed (reads requirements.txt)
echo %GREEN% Installing Python requirements (this may take a while)...
python -m pip install -r requirements.txt

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo %RED% PyInstaller not found even after installing requirements. Install with: pip install pyinstaller
    exit /b 1
)

REM Clean previous builds
echo %GREEN% Cleaning previous builds...
if exist build rmdir /s /q build
REM Clean dist/, but preserve any MyRhythmNexus* artifacts (do not delete customer builds)
if exist dist (
    echo %GREEN% Preserving MyRhythmNexus artifacts in dist/ and removing others...
    for /f "delims=" %%F in ('dir /b "dist"') do (
        call :maybe_remove "%%F"
    )
) 
if exist *.spec del *.spec

REM Create version info (use VERSION env if provided)
if defined VERSION (
    echo MyRhythmNexus Desktop v%VERSION%> desktop\version.txt
) else (
    echo MyRhythmNexus Desktop v1.0.0> desktop\version.txt
)
REM Prepare executable name to include version when available
set "EXE_NAME=MyRhythmNexus-Desktop"
REM Try to read VERSION from Python DesktopConfig first
set "PY_VER="
for /f "usebackq delims=" %%V in (`python -c "import sys; sys.path.insert(0, r'%CD%'); from desktop.core.config import DesktopConfig; print(getattr(DesktopConfig,'VERSION',''))"`) do set "PY_VER=%%V"

if defined PY_VER (
    if not "%PY_VER%"=="" (
        set "EXE_NAME=MyRhythmNexus_v%PY_VER%"
    )
)

REM Fallback to env var VERSION if Python read failed
if "%EXE_NAME%"=="MyRhythmNexus-Desktop" (
    if defined VERSION (
        set "EXE_NAME=MyRhythmNexus_v%VERSION%"
    ) else (
        set "EXE_NAME=MyRhythmNexus_v1.0.0"
    )
)
echo Built: %date% %time%>> desktop\version.txt
echo Git: N/A>> desktop\version.txt
echo %GREEN% Version info created: desktop\version.txt

REM Build desktop app
echo %GREEN% Building desktop application...
pyinstaller --clean --onefile ^
    --name %EXE_NAME% ^
        --hidden-import jwt ^
    --hidden-import customtkinter ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageTk ^
    --hidden-import httpx ^
    --hidden-import pydantic ^
    --hidden-import pydantic_settings ^
    --hidden-import sqlalchemy ^
    --hidden-import fastapi ^
    --hidden-import uvicorn ^
    --hidden-import pydantic_core ^
    --add-data "backend;backend" ^
    --add-data "desktop;desktop" ^
    desktop/main.py

if exist "dist\%EXE_NAME%.exe" (
    for %%A in ("dist\%EXE_NAME%.exe") do set FILE_SIZE=%%~zA
    set /a FILE_SIZE_MB=%FILE_SIZE%/1024/1024
    echo %GREEN% ✅ Desktop app built successfully!
    echo %GREEN% 📁 Executable: dist\%EXE_NAME%.exe
    echo %GREEN% 📏 Size: %FILE_SIZE_MB% MB
    echo %GREEN% 📅 Built: %date% %time%
) else (
    echo %RED% ❌ Build failed!
    exit /b 1
)

REM Test note
echo.
echo %GREEN% 🎉 Build complete!
echo %GREEN% 📦 Ready for distribution: dist\%EXE_NAME%.exe
echo.
echo %YELLOW% Remember to test the executable thoroughly before distribution!
echo %YELLOW% Run: dist/MyRhythmNexus-Desktop.exe

REM If CI environment variable is set, skip pause so automated runners won't hang
if defined CI goto :EOF
pause

goto :EOF

:maybe_remove
REM %~1 is the name of the item inside dist
set "_item=%~1"
echo %_item% | findstr /b /i "MyRhythmNexus" >nul
if errorlevel 1 (
    REM not a MyRhythmNexus* file/dir -> remove
    if exist "dist\%_item%\*" (
        rmdir /s /q "dist\%_item%"
    ) else (
        del /q "dist\%_item%"
    )
)
set "_item="
goto :eof