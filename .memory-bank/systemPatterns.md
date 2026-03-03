# Sistem Mimarisi

Son güncelleme: 2026-03-03

## Yüksek Seviye Topoloji

1. **Ana Uygulama Sunucusu (`backend/`)**
   - FastAPI uygulaması (`backend/main.py`)
   - İki yüzey sunar:
     - REST API: `/api/v1/*`
     - Web portal: `/web/*` (Jinja2 template rendering)
   - `UserActivityScheduler` ile günlük otomasyon görevleri

2. **Desktop İstemci (`desktop/`)**
   - CustomTkinter GUI
   - `desktop/core/api_client.py` ile backend API tüketimi
   - `desktop/core/license_manager.py` ile lisans kontrolü (license server ile)

3. **Lisans Otoritesi (`license_server/`)**
   - Ayrı FastAPI uygulaması
   - `/api/v1/license/validate` endpoint’i
   - RSA private key ile JWT üretimi, client tarafında public key ile doğrulama

4. **Veritabanı ve Şema Disiplini**
   - Uygulama katmanında SQLAlchemy
   - Şema referansı: `prisma/schema.prisma`
   - Migrasyon: Alembic

## Önemli Uygulama Kalıpları

### API + Web Ayrımı
- Aynı backend içinde API ve web route’ları ayrı modüllerde tutulur.
- Web route’larında cookie tabanlı auth akışı (`access_token`) kullanılır.

### Eager Loading Kuralı
- Template render veya response serializasyonunda lazy-load kaynaklı async hataları önlemek için `selectinload()` tercih edilir.

### Check-in Alan Modeli
- QR token → `SubscriptionQrCode` doğrulama
- Abonelik + plan türü (`SESSION_BASED` / `TIME_BASED`) kontrolü
- Event uygunluk ve kapasite kontrolleri

### Scheduler Görevleri
- İnaktif üyeleri pasifleştirme
- Süresi/hakkı biten abonelikleri `expired` işaretleme
- Expired abonelikler için QR token deactivation/rotation

## Dağıtım Deseni
- Docker Compose ile `db`, `backend`, `web` servisleri
- Desktop için PyInstaller tabanlı exe üretimi
- Release/packaging akışı `tools/` altında müşteri bazlı scriptlerle desteklenir
