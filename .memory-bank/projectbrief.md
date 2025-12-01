# Proje Özeti: MyRhythmNexus

## Vizyon
Spor ve dans stüdyoları için geliştirilen, "Kart (ServicePackage)" mantığına dayalı, ölçeklenebilir ve modüler bir yönetim ekosistemi. Monolitik yapı yerine, sorumlulukları ayrılmış 3 ana katmandan oluşur. Şu anki odak noktamız **Proje 1: Çekirdek** katmanıdır.

## Temel Hedef (Proje 1: Çekirdek)
Stüdyonun arka ofis işlemlerini, üye yönetimini, satışları, ders programlamayı ve fiziksel giriş kontrolünü (QR) yöneten merkezi sistemi kurmak.

## Temel Bileşenler
1.  **Backend API:** Sisteme beyinlik yapan merkezi sunucu.
2.  **Admin Paneli:** İşletme sahibi ve personel için masaüstü uygulaması.
3.  **Üye Vitrini:** Üyeler için QR kod görüntüleme arayüzü.
4.  **Otomatik Sistemler:** Background scheduler ile pasif üye yönetimi.
5.  **Otomatik Güncelleme:** Masaüstü uygulamasının GitHub Releases ile otomatik güncellenmesi.
6.  **Containerized Deployment:** Docker ile production-ready deployment altyapısı.
7.  **Uluslararasılaştırma (i18n):** Çoklu dil desteği (Türkçe/İngilizce) ile global erişim.

## Otomatik Özellikler
*   **Pasif Üye Yönetimi:** 60+ gün paket satın almamış üyeler otomatik olarak `is_active = false` yapılır.
*   **Zaman Takibi:** Tüm zaman işlemleri Türkiye saati (Europe/Istanbul) kullanır.
*   **Background Jobs:** APScheduler ile günlük otomatik görevler çalışır.
*   **Otomatik Güncellemeler:** Masaüstü uygulaması GitHub Releases üzerinden otomatik güncellenir.
*   **Containerized Scaling:** Docker Compose ile production deployment ve scaling.
*   **Dil Yönetimi:** Kullanıcı tercihine göre otomatik dil yükleme ve çeviri desteği.
