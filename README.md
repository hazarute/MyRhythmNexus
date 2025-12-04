# MyRhythmNexus - Studio Management Core System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

> **Modern, scalable studio management system for Pilates, dance, and fitness studios with integrated QR check-in and automated member management.**

---

## 🚀 Quick Start

Get the system running in minutes with Docker:

```bash
# Clone the repository
git clone https://github.com/hazarute/MyRhythmNexus.git
cd MyRhythmNexus

# Start the complete system
./deploy.sh server

# Build desktop app (optional)
./deploy.sh desktop
```

**Access Points:**
- 🌐 **Web UI:** http://localhost
- 📡 **API:** http://localhost:8000
- 📚 **API Docs:** http://localhost:8000/docs

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Architecture](#-architecture)
- [Internationalization (i18n)](#-internationalization-i18n)
- [Contributing](#-contributing)
- [License](#-license)

---

## 📖 Overview

MyRhythmNexus is a comprehensive, modular management ecosystem designed specifically for Pilates, dance, and fitness studios. Built on a "Service Package" (card) logic, it provides complete back-office operations, member management, sales tracking, class scheduling, and physical access control via QR codes.

### 🎯 Current Focus: Core Management System (Project 1)
The foundation layer that handles all back-office operations and physical access control for studios.

### 🔮 Future Phases
- **Project 2:** Member Portal - Mobile-friendly interface for class reservations and profile management
- **Project 3:** Gamification - Wearable tech integration with competitive motivation modules

### 💡 Key Innovation
Unlike monolithic systems, MyRhythmNexus follows a **modular architecture** where each layer has clear responsibilities and can scale independently.

---

## ✨ Features

### 🏢 Core Management
- **Member CRM:** Complete member lifecycle management with automated status tracking
- **Service Packages:** Flexible "card" system for different service combinations
- **Sales POS:** Integrated point-of-sale with payment tracking
- **Class Scheduling:** Template-based class management with calendar integration

### 🔐 Access Control
- **QR Check-in:** Physical access control with USB QR readers
- **Real-time Validation:** Instant verification against active subscriptions
- **Session Tracking:** Automatic attendance counting and quota management

### 🤖 Automation
- **Auto Member Deactivation:** 60+ day inactive members automatically deactivated
- **Background Jobs:** Scheduled tasks for member status updates
- **Timezone Management:** All operations in Turkey timezone (Europe/Istanbul)

### 🌍 Internationalization (i18n)
- **Multi-language Support:** English and Turkish translations available.
- **Dynamic Locale Management:** Language selection via settings menu.
- **Translation Tools:** Includes `i18n_manager.py`, `fill_translations.py`, `scan_ui_strings.py`, and `wrap_ui_strings.py` for managing translations.
- **Gettext Integration:** `.po` and `.mo` files for efficient translation handling.

### 🐳 Deployment
- **Containerized:** Docker & Docker Compose for production deployment
- **Auto Updates:** Desktop app automatic updates via GitHub Releases
- **Multi-environment:** Development and production configurations

---

## 🏗️ Tech Stack

### Backend & API
- **Framework:** FastAPI (async Python web framework)
- **Database:** PostgreSQL 15 with async SQLAlchemy 2.0+
- **Migrations:** Alembic
- **Authentication:** OAuth2 with JWT tokens
- **Background Jobs:** APScheduler

### Frontend & UI
- **Desktop App:** CustomTkinter (Python native GUI)
- **Web Interface:** Jinja2 templates with HTMX
- **Mobile Ready:** PWA-compatible for future mobile app

### DevOps & Deployment
- **Containerization:** Docker & Docker Compose
- **Web Server:** Nginx reverse proxy
- **Packaging:** PyInstaller for desktop executables
- **CI/CD:** GitHub Actions ready

### Development Tools
- **Schema Definition:** Prisma (single source of truth)
- **Type Safety:** Python type hints mandatory
- **Environment:** python-dotenv for configuration
- **Testing:** pytest with comprehensive test coverage

---

## ⚙️ Installation

### Prerequisites
- **Python:** 3.9 or higher
- **Docker & Docker Compose:** For containerized deployment
- **Git:** For version control

### Option 1: Docker Deployment (Recommended)

```bash
# Clone repository
git clone https://github.com/your-username/MyRhythmNexus.git
cd MyRhythmNexus

# Start complete system
./deploy.sh server

# Build desktop app (optional)
./deploy.sh desktop
```

### Option 2: Manual Installation

```bash
# Clone and setup
git clone https://github.com/your-username/MyRhythmNexus.git
cd MyRhythmNexus

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
alembic upgrade head

# Start backend
uvicorn backend.main:app --reload

# Build desktop app
pyinstaller desktop.spec
```

---

## 🛠️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres123@db:5432/myrhythmnexus

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-production-secret-key-change-this-very-long-random-string

# CORS Origins (Add your production domain)
CORS_ORIGINS=["https://yourdomain.com", "http://localhost:3000"]

# Environment
ENVIRONMENT=production

# Admin User
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin123
```

### Desktop App Configuration

The desktop app automatically reads backend URL from config:

```python
# Override backend URL if needed
BACKEND_URL="https://api.yourdomain.com"
```

---

## 💡 Usage

### Starting the System

```bash
# Complete deployment (backend + web + database)
./deploy.sh all

# Only backend services
./deploy.sh server

# Only desktop app
./deploy.sh desktop
```

### API Usage Example

```python
import httpx

# Check member status
response = httpx.get("http://localhost:8000/api/v1/members/123")
member_data = response.json()

# Process QR check-in
checkin_response = httpx.post("http://localhost:8000/api/v1/checkin", json={
    "qr_code": "ABC123",
    "class_event_id": 456
})
```

### Desktop App Usage

1. **Launch:** Run `MyRhythmNexus-Desktop.exe`
2. **Login:** Use admin credentials
3. **Member Management:** Add/edit members, manage subscriptions
4. **Sales:** Process service package sales
5. **Scheduling:** Create class templates and events
6. **Check-in:** Connect QR reader for physical access control

---

## 🏛️ Architecture

### System Layers

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Desktop App   │    │     Mobile      │
│   (Members)     │    │   (Staff)       │    │   (Future)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────────────┐
                    │   Backend API      │
                    │   (FastAPI)        │
                    └────────────────────┘
                             │
                    ┌────────────────────┐
                    │   PostgreSQL DB    │
                    └────────────────────┘
```

### Core Business Logic

1. **Service Package System:** Products are "cards" combining Category + Service + Plan
2. **Subscription Management:** Each sale creates a subscription with fixed QR code
3. **Class Management:** Templates → Calendar events with booking permissions
4. **Access Control:** QR validation → Session check-in → Quota deduction

### Database Schema
- **Single Source of Truth:** `prisma/schema.prisma`
- **Async Operations:** SQLAlchemy 2.0+ with asyncpg
- **Migrations:** Alembic for schema evolution

---

## 🌍 Internationalization (i18n)

### Overview
MyRhythmNexus supports multiple languages, including English and Turkish, to provide a seamless user experience for global users.

### Key Features
- **Dynamic Locale Management:** Users can switch languages via the settings menu.
- **Translation Tools:** Includes `i18n_manager.py` for managing `.po` and `.mo` files.
- **Multi-language Support:** All UI elements are wrapped with `_()` for translation.
- **Helper Scripts:**
  - `fill_translations.py`: Auto-fill translations.
  - `scan_ui_strings.py`: Detect untranslated strings.
  - `wrap_ui_strings.py`: Automatically wrap strings with `_()`.

### Workflow
1. Extract translatable strings using `i18n_manager.py`.
2. Update `.po` files with translations.
3. Compile `.mo` files for runtime use.
4. Load the appropriate locale at application startup.

---

## 🛡️ Licensing System

- **Purpose:** Corporate deployments need hardware-bound licenses, feature flags, and renewal tracking before enterprise-grade modules unlock.
- **Backend Stack:** FastAPI exposes `/api/v1/license/validate` (runtime) and `/api/v1/admin/licenses` (superuser CRUD). The heavy lifting occurs in `backend/services/license.py`, which enforces expiry, hardware locking (`hardwareId`), active flags, and `features` JSON-based module checks.
- **Hardware Stability:** The desktop’s `get_machine_id()` hashes motherboard serial, CPU ID, and disk serial so the license survives WiFi or adapter changes but invalidates when the physical machine is replaced.
- **Database Schema:** Prisma `licenses` table now stores `licenseKey`, `clientName`, `contactEmail`, `isActive`, `expiresAt`, `hardwareId`, `features`, `createdAt`, `updatedAt`.
- **Desktop Enforcement:** Desktop startup caches `license_status`, encrypts/signs that cache before writing to disk, and prevents module usage if cached time goes backwards (clock tampering) or hardware hash mismatches. Online sessions revalidate against `/validate` and update the encrypted cache with server time.
- **Documentation Note:** Inspired by "Readme Nasıl Olusturulur.txt", this section states the why/what/next pattern and points to `.memory-bank` docs for deeper rationale.

---

## 🤝 Contributing

We welcome contributions! This project follows a structured development process.

### Development Setup

```bash
# Fork and clone
git clone https://github.com/hazarute/MyRhythmNexus.git
cd MyRhythmNexus

# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest

# Start development server
uvicorn backend.main:app --reload
```

### Guidelines

- **Code Style:** Follow PEP 8 with type hints mandatory
- **Database:** Models must align with `prisma/schema.prisma`
- **Testing:** Write tests for new features
- **Documentation:** Update relevant docs for changes

### AI-Driven Development Protocol

This project uses a unique AI-human collaboration model:
- **Human (Architect):** Defines goals and requirements
- **AI (Technical Lead):** Creates technical plans and schemas
- **GitHub Copilot (Developer):** Implements code following `.memory-bank` guidelines

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern async web framework
- **SQLAlchemy** - Powerful ORM for Python
- **CustomTkinter** - Beautiful desktop UI framework
- **Prisma** - Next-generation ORM for database management
- **Shields.io** - Badge generation service

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/hazarute/MyRhythmNexus/issues)
- **Discussions:** [GitHub Discussions](https://github.com/hazarute/MyRhythmNexus/discussions)
- **Documentation:** See `DEPLOYMENT.md` and `DESKTOP_UPDATES.md` for detailed guides
- **Contact:** Hazar Üte <hazarute@gmail.com>

---

**MyRhythmNexus** - Transforming studio management with modern technology and thoughtful design.