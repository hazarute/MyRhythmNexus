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
    if ! python -c "import PyInstaller" &> /dev/null; then
        print_error "PyInstaller not found. Install with: pip install pyinstaller"
        exit 1
    fi
}

# Clean previous builds
clean_build() {
    print_status "Cleaning previous builds..."
    rm -rf build dist *.spec
}

# Build desktop app
build_desktop() {
    print_status "Building desktop application..."

    # Create executable with all dependencies
    pyinstaller --clean --onefile \
        --name MyRhythmNexus-Desktop \
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
    OUT_NAME="dist/MyRhythmNexus-Desktop"
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
    if [ -f "dist/MyRhythmNexus-Desktop.exe" ]; then
        print_warning "Note: Executable test requires GUI environment"
        print_status "Manual testing recommended:"
        print_status "1. Run: ./dist/MyRhythmNexus-Desktop.exe"
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
    print_status "📦 Ready for distribution: dist/MyRhythmNexus-Desktop.exe"
    print_status ""
    print_warning "Remember to test the executable thoroughly before distribution!"
}

# Run main function
main