# Teknoloji Bağlamı

Son güncelleme: 2026-03-03

## Ana Teknoloji Yığını
- **Dil:** Python 3.x
- **Backend Framework:** FastAPI
- **ORM:** SQLAlchemy 2.x (async)
- **Veritabanı:** PostgreSQL (ana), SQLite (bazı local/dev senaryoları)
- **Migrasyon:** Alembic
- **Desktop UI:** CustomTkinter
- **Web UI:** Jinja2 templates (backend içi SSR)
- **Auth:** JWT (API + web cookie akışları)
- **Scheduler:** APScheduler
- **Lisans Servisi:** FastAPI + PyJWT + RSA key pair
- **Paketleme:** PyInstaller
- **Container:** Docker + Docker Compose
- **Ters Proxy / Web:** Nginx (Docker web image)

## Önemli Modül Konumları
- API router hub: `backend/api/api.py`
- Web router hub: `backend/web/router.py`
- Scheduler: `backend/core/scheduler.py`
- Desktop config: `desktop/core/config.py`
- Desktop lisans yönetimi: `desktop/core/license_manager.py`
- License server entrypoint: `license_server/main.py`

## i18n Araçları
- `i18n_manager.py`
- `fill_translations.py`
- `scan_ui_strings.py`
- `wrap_ui_strings.py`

## Teknik Gerçeklik Notları
- Backend içinde ayrı bir `/api/v1/license/*` modülü yok; lisans doğrulama `license_server/` servisinde.
- Desktop sürüm hattı şu an `1.1.0` olarak geçiyor.
- Build/deploy script adları ve spec dosya adları arasında farklılık olabildiği için release adımında dosya adı doğrulaması şart.
