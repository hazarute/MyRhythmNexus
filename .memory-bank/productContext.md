# Ürün Bağlamı

## Problem
Stüdyo yönetiminde karmaşık üyelik yapıları, ders takibi ve fiziksel giriş kontrolünün entegrasyon zorlukları.
Kurumsal müşteriler için lisanslama, modül bazlı erişim izinleri ve donanım kilidi eksikliği mevcut.

## Çözüm
"ServicePackage" (Kart) mimarisi ile esnek üyelik modelleri sunan, QR tabanlı kesin giriş kontrolü sağlayan entegre bir sistem. Kurumsal lisanslama ise `licenses` tablosu, `features` bayrakları ve donanım kimliğine kilitlenen doğrulama akışıyla sağlanacak.

## Kullanıcı Deneyimi Hedefleri
*   **Personel/Admin:** CustomTkinter ile geliştirilmiş, hızlı ve güçlü bir masaüstü uygulaması. Üye kaydı, satış, finansal takip ve ders yönetimi tek merkezden.
*   **Üyeler:** Karmaşık olmayan, sadece QR kodlarına ve abonelik durumlarına erişebildikleri "Lite" bir web arayüzü. Giriş yaptıktan sonra sahip oldukları aktif "Kartları" (ServicePackage) listeleyip, ilgili kartın QR kodunu görüntüleyebilirler.
*   **Giriş Kontrolü:** USB QR okuyucu entegrasyonu ile hızlı ve hatasız "Check-In" süreci.
*   **Uluslararası Erişim:** Türkçe ve İngilizce dil desteği ile global kullanıcı deneyimi.
*   **Kurumsal Müşteriler:** Lisans anahtarı, donanım ID ve modül izinleriyle sadece yetkili makinelerde çalışan, özellik bazlı lisans yönetimi.
