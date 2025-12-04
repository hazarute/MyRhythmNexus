# Aktif Bağlam

## Yeni Odak
- **Licensing System (Lisanslama Sistemi)** – RBAC tamamlandı. Sıradaki adım: Diğer güvenlik kontrolleri (Rate limiting, Logging).

## Teknik Bağlam
- Backend'de `License` modeli ve API'leri (`/api/v1/license`, `/api/v1/admin/licenses`) hazır.
- Admin endpointleri artık `get_current_active_admin` dependency ile korunuyor.
- Desktop tarafında `LicenseManager` ve `LicenseWindow` entegre edildi.
- `tests/test_licensing.py` ile tüm lisans senaryoları test edildi.
- `docs/LICENSING.md` oluşturuldu.
- Gettext/i18n araçları (`wrap_ui_strings`, `i18n_manager`, `locale` dizini) devreye girdi; fakat kullanıcı doğrulama senaryoları ve i18n hataları üzerinde testler hâlâ sürüyor, tespit edilen sorunlar kapatılana kadar bu katman tam stabil sayılmamalı.
- `prisma/schema.prisma`’nın “BÖLÜM 7: LİSANSLAMA ALTYAPISI” kısmına `License` modeli eklendi; FastAPI tarafında `features`, `hardwareId`, `expiresAt`, `lastCheckIn` alanlarını kullanarak lisans/aktiflik kontrolleri kurulacak.
- Lisans durağını audit ve cache akışlarıyla izlemek ve API client’larda (`desktop`, `web`) `license_status` denetimi sağlamak için yeni servisler tasarlanması gerekiyor.

## Tamamlanan Özellikler
- FAZ 21: Licensing System (Backend, Desktop, Tests, Docs, RBAC).
- FAZ 20: Gettext tabanlı çoklu dil altyapısı (UI metin wrapping, locale yapılandırmaları, `.po/.mo` üretimi, config entegrasyonu).
- FAZ 20A: Finance tab modülerleştirmesi (component refactor, formatters/styles, testler, DESKTOP-WORKFLOW dokümantasyonu).
- Satış formunda manuel fiyat override ve ilgili backend validasyonları.

## Problemler
- i18n çeviri sarmalaması tamamlandı ama kullanıcı kontrolleri halen açık; hatalar ve eksik çeviriler raporlandığında hızlı müdahale akışı yoksa kullanıcı deneyimi zarar görebilir.
- Kurumsal lisans geçerliliği, donanım kilidi ve modül bazlı özellik bayrakları hâlâ manuel takip ediliyor; otomatik lisanslama sistemi kurulmadan modüllerin güvenli çalıştığını garanti edemiyoruz.

## Çözüm
- Prisma `License` modeli ile `licenses` tablosunu oluşturduk; FastAPI servislerinde CRUD, donanım kimliği eşleştirmesi, `features`/modül izinleri ve `expiresAt` kontrolleri uygulanacak.
- i18n yardımcı araçlarını (`i18n_manager`, `wrap_ui_strings`, `fill_translations`) canlı tutarak çeviri stokunu güncel tutuyoruz; kullanıcı doğrulama testleri doğrultusunda haraket edilecek.
- Lisans statüsünü cache’leyen servisler ve frontend client’larda `license_status` doğrulaması, modüller arası erişim kontrolleri ile desteklenecek.

## Proje Durum
- **Backend:** FastAPI, Auth, CRM, Satış, QR/Check-in, otomatik pasif üyelik scheduler’ı, async relationship loading, hard delete hazır; lisanslama için ön hazırlık tamamlandı.
- **Desktop UI:** Login, Dashboard, Üye Yönetimi, Satış POS, Scheduler, Check-in ve otomatik güncelleme gibi modüller çalışıyor; çoklu dil altyapısı entegre, i18n doğrulama testleri sürüyor.
- **Deployment:** Docker container’lar, production-ready konfigürasyon ve CI/CD pipeline tamamlandı.
- **Yeni Özellik:** Çoklu dil desteği aktif; licensing sistemi bir sonraki büyük faz olarak ilerletiliyor.



