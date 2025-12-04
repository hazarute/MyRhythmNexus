# Aktif Bağlam

## Yeni Odak
- **Merkezi Lisanslama Sistemi (SaaS Dönüşümü)** – Yerel lisanslama yapısından vazgeçildi. Merkezi bir "License Server" ve RSA imzalı JWT token yapısına geçiş yapılıyor.
- **Temizlik ve Stabilizasyon:** Eski yerel lisanslama kodları (backend/models/license.py vb.) tamamen temizlendi ve veritabanı migrasyonu yapıldı.

## Teknik Bağlam
- **Mevcut Durum:** Proje, yerel lisanslama kodlarından arındırıldı. `license_server` ayrı bir mikroservis olarak çalışıyor.
- **Yeni Hedef:** `license_server`'ı Railway'e deploy etmek ve Desktop uygulamasını production ortamına hazırlamak.
- **Teknoloji:** FastAPI, SQLite (License Server Dev), RSA-2048, PyJWT.
- **İletişim:** MyRhythmNexus (Client) <-> License Server (Authority).
- **Güvenlik:** Offline-first doğrulama için Public Key dağıtımı.

## Tamamlanan Özellikler
- FAZ 21: Merkezi Lisanslama Sistemi (SaaS) - Temel Kurulum.
    - License Server (FastAPI + RSA + JWT) hazır.
    - Desktop Client Entegrasyonu (Online + Offline doğrulama) hazır.
    - Rate Limiting (SlowAPI) eklendi.
    - **Temizlik:** Eski `License` tablosu ve backend kodları silindi. Alembic migrasyonu (`remove_license_table`) uygulandı.

## Problemler
- Railway üzerinde kalıcı veri (Persistent Storage) için SQLite yerine PostgreSQL'e geçiş yapılması gerekecek (Production aşamasında).

## Çözüm
- Lisanslama sistemi MVP olarak yayına hazır.
- Proje GitHub'a pushlanıp Railway'e bağlanabilir.

## Proje Durum
- **Backend:** FastAPI, Auth, CRM, Satış, QR/Check-in, otomatik pasif üyelik scheduler’ı, async relationship loading, hard delete hazır; lisanslama yükü üzerinden alındı.
- **Desktop UI:** Login, Dashboard, Üye Yönetimi, Satış POS, Scheduler, Check-in ve otomatik güncelleme gibi modüller çalışıyor; çoklu dil altyapısı entegre.
- **Deployment:** Docker container’lar, production-ready konfigürasyon ve CI/CD pipeline tamamlandı.
- **Yeni Özellik:** Çoklu dil desteği aktif; licensing sistemi SaaS modeline evrildi.



