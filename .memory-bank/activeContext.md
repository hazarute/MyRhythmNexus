# Aktif Bağlam

## Şu Anki Odak
**Faz 23: Web Arayüzü (Member Portal) Revizyonu — %100 TAMAMLANDI (production-ready)**

FastAPI backend, SQLAlchemy async queries, JWT authentication ve responsive tasarım başarılı şekilde çalışıyor. Şu an öncelik frontend'in genişletilmiş versiyonunun stabilizasyonu ve sayfa/route revizyonlarıdır.

> Not: **Web tabanlı Admin Panel (Faz 24) artık yürürlüğe konmayacak.** Yönetim/işletme arayüzü `desktop/` klasöründeki masaüstü uygulaması üzerinden yürütülmeye devam edecektir.

## Teknik Bağlam (Kısa)
- **Kaynak:** `backend/web/ReferansTemplate/` altı referans şablonları.
- **Hedef:** `backend/web/templates/` ve `backend/web/routes/` yapısının stabil hale getirilmesi (FastAPI + Jinja2).
- **Mimari:** Jinja2 template inheritance (`base.html`), modular `APIRouter` routing, async SQLAlchemy, JWT (cookie) auth.

## Teknik Kararlar (Özet)
1. **FastAPI AsyncSession** ile veritabanı işlemleri (async/await) — devam ediyor ✅
2. **JWT Token (cookie)** mekanizması kullanılıyor (secure, httponly) ✅
3. **selectinload()** ile eager-loading kullanılarak `greenlet_spawn` sorunları çözüldü ✅
4. Tüm template context'lerine `"user": current_user` standardı eklendi ✅

## Yapılan Değişiklikler (Faz 23 sonucu)
- Jinja2 porting ve `base.html` ile 9 template oluşturuldu
- Modüler `backend/web/routes/` yapısı kuruldu ve route'lar FastAPI'ye bağlandı
- Auth flow (JWT cookie) ve temel route testleri tamamlandı

## Güncel Durum ve Öncelikler
- **Frontend genişletmesi:** Lite sürümün ötesine geçen, daha kapsamlı kullanıcı deneyimi (daha fazla sayfa ve detay) üzerine revizyonlar devam ediyor. Bu revizyonlar route bağlantıları, template context'leri ve mobil/desktop uyumluluğunu kapsıyor. (in-progress)
- **Testler:** Route-level ve entegrasyon testleri devam ediyor — template rendering, auth flows, eager-loading kontrolleri öncelikli.
- **Eksik / Revize edilecek sayfalar:** Abonelik detay + QR, ödemeler detay görünümü, ölçüm geçmişinin detaylandırılması, profil ayarları (güncelleme akışı) — üzerinde çalışılıyor.
- **QR Kod:** Hâlâ placeholder kullanımı devam ediyor; gerçek QR üretimi backend tarafında `cryptography` veya uygun kütüphane ile planlandı.

## Sonraki Adımlar
1. Frontend sayfa revizyonlarını tamamlayıp tüm route bağlantılarını doğrulama
2. Eksik sayfaların (abone detay/QR, finance detail, measurements history vb.) implementasyonu ve testleri
3. Entegrasyon testleri ile tam regression geçirme

## Beklemede Olan Görevler
- QR üretimi (backend) — planlandı
- Masaüstü Admin — `desktop/` üzerinden yönetilmeye devam edecek (web-admin iptal edildi)