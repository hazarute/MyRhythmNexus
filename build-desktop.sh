#!/bin/bash

# MyRhythmNexus Desktop App Builder
# Desktop uygulamasında değişiklik yapıldığında bu script'i çalıştırın

set -e

echo "🖥️  MyRhythmNexus Desktop App Builder"
echo "===================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if PyInstaller is installed
check_pyinstaller() {
    # Diagnostic info to help CI environments where pip/python mismatch may occur
    print_status "Checking python executable and PyInstaller availability..."
    echo "Python: $(which python 2>/dev/null || echo 'which python not found')"
    python --version || true
    echo "pip-installed PyInstaller info:";
    python -m pip show pyinstaller || true

    # Prefer invoking PyInstaller via the python -m PyInstaller entrypoint.
    # Try a couple of methods to detect the installed module/version because
    # different PyInstaller releases and environments expose the entrypoint
    # slightly differently.
    if python -m PyInstaller --version &> /dev/null; then
        : # found
    else
        # fallback: try importing the module and printing attribute
        if python -c "import PyInstaller as m; print(getattr(m, '__version__', ''))" &> /dev/null; then
            :
        else
            print_error "PyInstaller not found. Install with: python -m pip install pyinstaller"
            exit 1
        fi
    fi
}

# Clean previous builds
clean_build() {
    print_status "Cleaning previous builds..."
    # Avoid removing the dist directory itself when running inside containers
    # where dist may be a mounted volume. Remove build and spec files and
    # try to empty dist contents if possible.
    rm -rf build *.spec || true
    if [ -d "dist" ]; then
        # Preserve any existing MyRhythmNexus* artifacts in dist/ (do not remove
        # customer or previous build artifacts). Remove other files to keep the
        # directory tidy while avoiding deleting versioned outputs.
        # Attempt to enable nullglob when running under bash; when running under
        # a POSIX shell (dash/sh) `shopt` is not available so fall back to a
        # safe loop that checks file existence.
        NULLGLOB_SET=0
        if [ -n "$BASH_VERSION" ]; then
            shopt -s nullglob
            NULLGLOB_SET=1
        fi
        for item in dist/*; do
            # If no matches and glob was not expanded (e.g. literal 'dist/*'),
            # ensure we don't try to remove that literal string.
            [ ! -e "$item" ] && break
            base=$(basename "$item")
            case "$base" in
                MyRhythmNexus*)
                        echo "[INFO] Preserving $item" ;;
                *)
                        rm -rf "$item" || echo "[WARNING] Failed to remove $item" ;;
            esac
        done
        if [ "$NULLGLOB_SET" = "1" ]; then
            shopt -u nullglob
        fi
    fi
}

# Build desktop app
build_desktop() {
    print_status "Building desktop application..."

    # Create executable with all dependencies
    # Name the produced binary using the VERSION env if present so dist contains
    # a versioned filename (e.g. MyRhythmNexus_v1.0.3). This avoids ambiguous
    # generic names and makes CI/packaging deterministic.
    OUT_BASENAME="MyRhythmNexus_v${VERSION:-1.0.0}"
    # Use the module invocation to avoid relying on the console script name
    python -m PyInstaller --clean --onefile \
        --name "$OUT_BASENAME" \
        --hidden-import customtkinter \
        --hidden-import PIL \
        --hidden-import PIL.Image \
        --hidden-import PIL.ImageTk \
        --hidden-import httpx \
        --hidden-import pydantic \
        --hidden-import pydantic_settings \
        --hidden-import sqlalchemy \
        --hidden-import fastapi \
        --hidden-import uvicorn \
        --hidden-import pydantic_core \
        --hidden-import cv2 \
        --add-data "backend:backend" \
        --add-data "desktop:desktop" \
        desktop/main.py

    # Determine expected output name (PyInstaller on Linux produces a binary without .exe)
    OUT_NAME="dist/${OUT_BASENAME}"
    if [ -f "$OUT_NAME" ]; then
        FILE_SIZE=$(stat -c%s "$OUT_NAME" 2>/dev/null || stat -f%z "$OUT_NAME" 2>/dev/null || echo 0)
        print_status "✅ Desktop app built successfully!"
        print_status "📁 Executable: $OUT_NAME"
        print_status "📏 Size: $((FILE_SIZE/1024/1024)) MB"
        print_status "📅 Built: $(date)"
    else
        print_error "❌ Build failed!"
        exit 1
    fi
}

# Test the built executable
test_executable() {
    print_status "Testing executable..."
    # If a Windows .exe exists, offer instructions; otherwise for Linux the
    # binary will be named using the version (handled above).
    if [ -f "dist/MyRhythmNexus-Desktop.exe" ] || ls dist/*.exe &> /dev/null; then
        print_warning "Note: Executable test requires GUI environment"
        print_status "Manual testing recommended:"
        print_status "1. Run: ./dist/<executable>"
        print_status "2. Check if app starts and connects to backend"
        print_status "3. Test login and basic functionality"
    fi
}

# Create version info
create_version_info() {
    VERSION_FILE="desktop/version.txt"
    # Use VERSION env var if provided, otherwise default to 1.0.0
    if [ -n "$VERSION" ]; then
        echo "MyRhythmNexus Desktop v$VERSION" > "$VERSION_FILE"
    else
        echo "MyRhythmNexus Desktop v1.0.0" > "$VERSION_FILE"
    fi
    echo "Built: $(date)" >> "$VERSION_FILE"
    echo "Git: $(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')" >> "$VERSION_FILE"
    print_status "Version info created: $VERSION_FILE"
}

# Main build process
main() {
    print_status "Starting desktop app build process..."

    # Install Python dependencies from requirements.txt to ensure PyJWT and others are available
    if [ -f "requirements.txt" ]; then
        print_status "Installing Python requirements from requirements.txt..."
        python -m pip install -r requirements.txt
    fi

    check_pyinstaller
    clean_build
    create_version_info
    build_desktop
    test_executable

    print_status ""
    print_status "🎉 Build complete!"
    print_status "📦 Ready for distribution: $OUT_NAME"
    print_status ""
    print_warning "Remember to test the executable thoroughly before distribution!"
}

# Run main function
main