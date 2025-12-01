# Teknoloji Bağlamı

## Teknoloji Yığını
*   **Dil:** Python 3.x
*   **Web Framework:** FastAPI
*   **Veritabanı:** PostgreSQL
*   **ORM:** SQLAlchemy 2.0+ (Async)
*   **Şema Yönetimi:** Prisma (Schema definition only), Alembic (Migrations)
*   **GUI Framework:** CustomTkinter (Python)
*   **Frontend (Lite Web):** Jinja2 Templates + HTMX
*   **Auth:** OAuth2 / JWT
*   **Background Jobs:** APScheduler (Otomatik görevler için)
*   **Timezone Management:** zoneinfo (Python 3.9+, Türkiye saati desteği)
*   **Packaging & Distribution:** PyInstaller (Masaüstü executable)
*   **Auto Updates:** GitHub Releases API + Custom Updater
*   **HTTP Client:** requests (Güncelleme sistemi için)
*   **CI/CD Tools:** GitHub CLI, GitHub Actions
*   **Containerization:** Docker & Docker Compose (Production deployment)
*   **Web Server:** Nginx (Reverse proxy + static files)
*   **Database Container:** PostgreSQL 15 (Production database)
*   **Uluslararasılaştırma:** Python gettext (Çoklu dil desteği)

## Geliştirme Standartları
*   **Tip Güvenliği:** Python Type Hinting zorunlu.
*   **Veritabanı:** `prisma/schema.prisma` dosyasına sadık kalınacak.
*   **Konfigürasyon:** Hassas veriler `.env` dosyasından okunacak.
*   **Zaman Yönetimi:** Tüm zaman işlemleri Türkiye saati (Europe/Istanbul) kullanacak.
*   **Kod Organizasyonu:**
    *   **Modülerleştirme:** Büyük dosyalar (>500 satır) küçük, sorumluluğu net modüllere bölünmeli
    *   **Separation of Concerns:** Her modül tek bir sorumluluğa sahip olmalı
    *   **Coordinator Pattern:** Büyük view'lar tab/component koordinatörü olarak çalışmalı, detaylar alt modüllere delege edilmeli
    *   **Reusable Methods:** Her modül `setup()` ve `refresh()` gibi standart metodlara sahip olmalı
    *   **Dosya Yapısı:** İlgili modüller alt klasörlerde organize edilmeli (örn: `views/tabs/`)
    *   **Satır Limiti:** İdeal dosya boyutu 40-350 satır arası, 800+ satır refaktör sinyalidir
