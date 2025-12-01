#!/bin/bash

# MyRhythmNexus Deployment Script

set -e

echo "🚀 MyRhythmNexus Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Create .env file if it doesn't exist
create_env_file() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating template..."

        cat > .env << EOF
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres123@db:5432/myrhythmnexus

# Security - CHANGE THIS IN PRODUCTION!
SECRET_KEY=your-production-secret-key-change-this-very-long-random-string

# CORS Origins - Add your production domain
CORS_ORIGINS=["https://yourdomain.com", "http://localhost:3000"]

# Environment
ENVIRONMENT=production

# Admin User
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin123
EOF

        print_warning "Please edit .env file with your production settings before running again!"
        exit 1
    fi
}

# Deploy backend and web
deploy_server() {
    print_status "Starting server deployment..."

    # Stop existing containers
    docker-compose down || true

    # Build and start services
    docker-compose up -d --build

    print_status "Waiting for services to be ready..."
    sleep 30

    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        print_status "✅ Server deployment successful!"
        print_status "🌐 Web UI: http://localhost"
        print_status "📡 API: http://localhost:8000"
        print_status "📚 API Docs: http://localhost:8000/docs"
    else
        print_error "❌ Server deployment failed!"
        docker-compose logs
        exit 1
    fi
}

# Build desktop app
build_desktop() {
    print_status "Building desktop application..."

    # Check if PyInstaller is installed
    if ! python -c "import PyInstaller" &> /dev/null; then
        print_error "PyInstaller is not installed. Install with: pip install pyinstaller"
        exit 1
    fi

    # Create dist directory
    mkdir -p dist

    # Build executable
    pyinstaller --clean desktop.spec

    if [ -f "dist/MyRhythmNexus-Desktop.exe" ]; then
        print_status "✅ Desktop app built successfully!"
        print_status "📁 Executable: dist/MyRhythmNexus-Desktop.exe"
    else
        print_error "❌ Desktop app build failed!"
        exit 1
    fi
}

# Create GitHub release and upload desktop app
create_release() {
    print_status "Creating GitHub release..."

    # Check if GitHub CLI is installed
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is not installed. Install from: https://cli.github.com/"
        print_error "Or manually create release and upload the desktop app."
        exit 1
    fi

    # Check if user is authenticated
    if ! gh auth status &> /dev/null; then
        print_error "GitHub CLI is not authenticated. Run: gh auth login"
        exit 1
    fi

    # Get version from user or use current date
    if [ -z "$VERSION" ]; then
        VERSION="v$(date +%Y.%m.%d)"
        print_warning "No VERSION specified, using: $VERSION"
        print_warning "Set VERSION environment variable to specify version (e.g., VERSION=v1.2.3)"
    fi

    # Build desktop app first
    build_desktop

    # Create release
    if gh release create "$VERSION" \
        --title "MyRhythmNexus Desktop $VERSION" \
        --notes "Automated desktop application release" \
        "dist/MyRhythmNexus-Desktop.exe#MyRhythmNexus-Desktop-$VERSION.exe"; then

        print_status "✅ Release created successfully!"
        print_status "🔗 Release URL: https://github.com/$(gh repo view --json owner,name -q '.owner.login + \"/\" + .name')/releases/tag/$VERSION"
    else
        print_error "❌ Failed to create release!"
        exit 1
    fi
}

# Show usage
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  server      - Deploy backend and web UI to server"
    echo "  desktop     - Build desktop application executable"
    echo "  release     - Build desktop app and create GitHub release"
    echo "  all         - Deploy server and build desktop app"
    echo "  stop        - Stop all server services"
    echo "  logs        - Show server logs"
    echo ""
    echo "Environment Variables:"
    echo "  VERSION     - Release version (e.g., v1.2.3) - defaults to date-based"
    echo ""
    echo "Examples:"
    echo "  $0 server              # Deploy to server"
    echo "  $0 desktop             # Build desktop app"
    echo "  $0 release             # Create GitHub release"
    echo "  $0 release VERSION=v1.2.3  # Create specific version release"
    echo "  $0 all                 # Full deployment"
}

# Main script
case "${1:-all}" in
    "server")
        check_docker
        create_env_file
        deploy_server
        ;;
    "desktop")
        build_desktop
        ;;
    "release")
        create_release
        ;;
    "all")
        check_docker
        create_env_file
        deploy_server
        build_desktop
        ;;
    "stop")
        check_docker
        print_status "Stopping server services..."
        docker-compose down
        print_status "✅ Services stopped"
        ;;
    "logs")
        check_docker
        docker-compose logs -f
        ;;
    *)
        usage
        exit 1
        ;;
esac