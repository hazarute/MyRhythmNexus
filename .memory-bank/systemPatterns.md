# Sistem Mimarisi

## Mimari Yapı

1.  **Veritabanı Katmanı (PostgreSQL):**
    *   Tek Gerçek Kaynak (SSOT): `prisma/schema.prisma`.
    *   ORM: SQLAlchemy 2.0+ (Async).
    *   Migrasyon: Alembic.

2.  **Backend API Katmanı (FastAPI):**
    *   Merkezi sunucu.
    *   REST API (Admin ve Web için).
    *   Jinja2 Templates (Üye Vitrini için).
    *   Auth: OAuth2 (JWT).

3.  **İstemci Katmanları:**
    *   **Admin Paneli:** Python CustomTkinter Masaüstü Uygulaması.
    *   **Üye Vitrini:** HTML/HTMX (Server-side rendering via FastAPI).
    *   **Dağıtım & Güncelleme:** PyInstaller executable + GitHub Releases otomatik güncelleme sistemi.

4.  **Containerized Deployment (Production):**
    *   **Backend Container:** FastAPI uygulaması (Docker)
    *   **Database Container:** PostgreSQL 15 (Persistent volumes)
    *   **Web Container:** Nginx reverse proxy + static files
    *   **Orchestration:** Docker Compose (Multi-service management)

5.  **Uluslararasılaştırma (i18n) Sistemi:**
    *   **Framework:** Python gettext modülü
    *   **Dil Dosyaları:** `locale/{lang}/LC_MESSAGES/messages.po` ve `messages.mo`
    *   **Çeviri Fonksiyonu:** `_()` wrapper fonksiyonu tüm UI metinlerinde kullanılır
    *   **Dil Yönetimi:** Uygulama başlangıcında locale ayarı + kullanıcı tercih konfigürasyonu
    *   **Desteklenen Diller:** Türkçe (tr) ve İngilizce (en) - genişletilebilir yapı
    *   **i18n Yardımcı Araçlar:** `i18n_manager.py` (extract/update/compile), `fill_translations.py`, `scan_ui_strings.py`, `wrap_ui_strings.py` — geliştirme sürecini kolaylaştırmak için eklendi

    6.  **Lisanslama Sistemi:**
        *   **Veritabanı:** `licenses` tablosu `prisma/schema.prisma` içinde tanımlı (`features` JSON, `hardwareId`, `expiresAt`).
        *   **Servis Katmanı:** `backend/services/license.py` ile tüm lisans doğrulamaları ve feature check adımları burada olmalı.
        *   **API:** `/api/v1/license/validate`, `/api/v1/admin/licenses` endpoint’leri FastAPI ile superuser erişimleri kontrol edecek.
        *   **Desktop Entegrasyonu:** `desktop/core/license_manager.py` ile machine_id hesaplama, cache ve doğrulama isteklerini yönet.

4.  **Modüler Klasör Yapısı:**
MyRhythmNexus/
├── .memory-bank/          # Proje hafızası (Mevcut)
├── .env                   # Hassas bilgiler (DB URL, Secret Key)
├── .gitignore
├── README.md              # Proje Anayasası
├── requirements.txt       # Python bağımlılıkları
├── tests/                 # Proje Test dosyaları
├── prisma/                # Referans şema dosyası
│   └── schema.prisma
│
├── alembic/               # Veritabanı migrasyonları
│   └── versions/
├── alembic.ini            # Alembic konfigürasyonu
│
├── backend/               # --- PROJE 1: BACKEND & WEB API ---
│   ├── main.py            # FastAPI giriş noktası (Entry Point)
│   ├── core/              # Çekirdek ayarlar
│   │   ├── config.py      # Env değişkenleri ve ayarlar
│   │   ├── database.py    # SQLAlchemy bağlantısı
│   │   └── security.py    # JWT ve Hash işlemleri
│   ├── models/            # SQLAlchemy Veritabanı Modelleri (Tables)
│   │   ├── user.py
│   │   ├── service.py     # ServicePackage, Offering vb.
│   │   └── operation.py   # Booking, Schedule, CheckIn
│   ├── schemas/           # Pydantic Modelleri (Veri Doğrulama / DTOs)
│   ├── api/               # API Rotaları (Endpoints)
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── members.py
│   │   │   └── operations.py
│   └── web/               # "Lite Web" arayüzü için
│       ├── router.py      # Web sayfası rotaları
│       ├── templates/     # Jinja2 HTML dosyaları
│       └── static/        # CSS/JS/Images
│
└── desktop/               # --- PROJE 1: MASAÜSTÜ ADMIN PANELİ ---
    ├── main.py            # Uygulama başlatıcı
    ├── assets/            # İkonlar, resimler
    ├── core/              # Masaüstü ayarları
    │   └── api_client.py  # Backend ile konuşan HTTP istemcisi
    ├── services/          # İş mantığı ve Donanım
    │   └── qr_reader.py   # USB QR okuyucu dinleyicisi
    └── ui/                # Kullanıcı Arayüzü (CustomTkinter)
        ├── windows/       # Ana pencereler (Login, Dashboard)
        │   ├── login_window.py
        │   └── main_window.py
        ├── views/         # İçerik sayfaları (Modüler yapı)
        │   ├── dashboard.py      # Ana dashboard
        │   ├── members.py        # Üye listesi (koordinatör)
        │   ├── member_detail.py  # Üye detay (tab koordinatörü - 155 satır)
        │   ├── dialogs/          # Dialog modülleri
        │   │   ├── __init__.py   # Export hub (18 satır)
        │   │   ├── add_member_dialog.py       # Üye ekleme (140 satır)
        │   │   ├── update_member_dialog.py    # Üye güncelleme (135 satır)
        │   │   ├── update_password_dialog.py  # Şifre değiştirme (90 satır)
        │   │   ├── add_measurement_dialog.py  # Ölçüm ekleme (165 satır)
        │   │   └── debt_payment_dialog.py     # Borç ödeme (240 satır)
        │   ├── tabs/             # Üye detay tab modülleri
        │   │   ├── __init__.py
        │   │   ├── profile_tab.py    # Profil & dashboard (180 satır)
        │   │   ├── packages_tab.py   # Paket yönetimi (160 satır)
        │   │   ├── payments_tab.py   # Ödemeler (75 satır)
        │   │   ├── attendance_tab.py # Katılım (40 satır)
        │   │   └── measurements_tab.py # Vücut ölçümleri (320 satır)
        │   ├── staff.py          # Personel yönetimi
        │   ├── definitions.py    # Hizmet tanımları
        │   ├── sales.py          # Satış modülü
        │   ├── scheduler.py      # Ders programı
        │   ├── finance.py        # Finansal raporlar
        │   └── checkin_dialog.py # QR giriş pop-up
        └── components/    # Tekrar kullanılabilir bileşenler (Kart, Tablo)

## Temel İş Akışları
*   **Kart Sistemi:** Kategori + Hizmet + Plan = ServicePackage.
*   **Ders Yönetimi:** ClassTemplate (Şablon) -> ClassEvent (Takvim).
*   **Giriş Kontrolü:** Subscription -> QR Kod -> SessionCheckIn (Seans düşümü burada gerçekleşir).
*   **Finansal Takip:** Subscription -> Payment -> FinanceView (Raporlama).
*   **Otomatik Aktivite Yönetimi:** User.updated_at (paket satın alma) -> Background Scheduler -> is_active = false (60+ gün inaktif).
*   **Containerized Deployment:** Development (volume mounts) vs Production (built images) stratejisi.
*   **Auto Updates:** Desktop app -> GitHub API -> Version check -> Download & replace executable.

## Background Job Patterns
*   **Scheduler Framework:** APScheduler (AsyncIOScheduler).
*   **Job Türü:** Cron-based (Günlük 02:00 Türkiye saati).
*   **İş Mantığı:** MEMBER rolü + is_active = true + updated_at < 60 gün öncesi → is_active = false.
*   **Error Handling:** Transaction rollback, log kayıtları.
*   **Monitoring:** Console log'lar, production'da log dosyası.
