# Proje Özeti: MyRhythmNexus

## Vizyon
Pilates/dans/fitness stüdyoları için; üyelik, satış, ders, check-in ve operasyon yönetimini tek ekosistemde birleştiren modüler bir platform.

## Güncel Ürün Kapsamı (2026-03-03)
MyRhythmNexus şu anda üç bağlı parçadan oluşur:

1. **Backend Platform (`backend/`)**
   - FastAPI tabanlı REST API (`/api/v1/*`)
   - Üye portalı için server-rendered web rotaları (`/web/*`)
   - Scheduler ile otomatik üye pasifleştirme + abonelik expiration süreçleri

2. **Desktop Admin Uygulaması (`desktop/`)**
   - CustomTkinter tabanlı operasyon paneli
   - Backend’e API client ile bağlanır
   - Açılışta lisans doğrulama akışı içerir

3. **Merkezi Lisans Sunucusu (`license_server/`)**
   - Ayrı FastAPI servisidir
   - Lisans key + hardware ID doğrular
   - RSA imzalı JWT ile offline-first lisans modelini destekler

## Temel İş Değeri
- Personel için hızlı admin operasyonları (desktop)
- Üyeler için erişilebilir web self-service alanı
- Fiziksel giriş kontrolü için QR bazlı check-in
- Kurumsal dağıtımlar için merkezi lisanslama

## Çekirdek Fonksiyonlar
- Üye CRM ve rol yönetimi
- Kart/paket (ServicePackage) ve abonelik yaşam döngüsü
- Satış ve ödeme kayıtları
- Ders/etkinlik bazlı giriş doğrulama
- Ölçüm takibi ve profil işlemleri
- TR/EN i18n altyapısı

## Sürümleme Bağlamı
- Mevcut dağıtım artefaktları ve masaüstü konfigürasyonu **v1.1.0** hattını işaret ediyor.
