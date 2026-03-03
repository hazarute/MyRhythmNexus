# Aktif Bağlam

Son güncelleme: 2026-03-03

## Şu Anki Odak
**Bellek Bankası yeniden senkronizasyonu tamamlandı.**

Proje artık yalnızca “Faz 23 web revizyonu” odağında değil; kod tabanı **v1.1.0** seviyesinde ve üç ana çalışma ekseni birlikte sürüyor:

1. `backend/` FastAPI API + scheduler + web member portal
2. `desktop/` CustomTkinter admin uygulaması (lisans doğrulama dahil)
3. `license_server/` ayrı FastAPI mikroservisi (RSA imzalı JWT lisans doğrulama)

## Anlık Gerçek Durum
- `backend/web/routes/` altında auth, dashboard, subscriptions, finance, profile, measurements, legal ve `qr-bridge` rotaları aktif.
- API katmanı `backend/api/v1/` altında üyeler, satış, servisler, check-in, ölçümler, istatistik ve personel rotalarıyla çalışıyor.
- Scheduler günlük olarak hem inaktif üyeleri pasife alma hem de abonelik expiration/QR deactivation işlemleri yürütüyor.
- Desktop uygulaması açılışta lisans kontrolü yapıyor, ardından login ve admin pencerelerine geçiyor.
- Lisans doğrulama backend içinde değil; `license_server/` servisinde `/api/v1/license/validate` endpoint’iyle yürütülüyor.

## Öncelikli Riskler / Dikkat Noktaları
- README içindeki bazı ifadeler (ör. “Project 2 gelecekte”) mevcut kod gerçekliğiyle tam örtüşmüyor.
- Dağıtım scriptleri ve build isimleri arasında farklılıklar var (`desktop.spec` vs `MyRhythmNexus_v1.1.0.spec`).
- Test klasöründe eski varsayımlara dayanan testler bulunabilir; güncel davranışla tutarlılık düzenli kontrol edilmeli.

## Sonraki Operasyonel Adım
1. README’nin gerçek mimari ve sürüm akışıyla senkron revizyonu ✅ tamamlandı
2. Test setinde stale senaryoların ayrıştırılması (özellikle desktop config/UI beklentileri)
3. Lisanslama dokümantasyonunun (`docs/` + `license_server/docs/`) tek bir referans akışta birleştirilmesi
