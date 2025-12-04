# Lisanslama Sistemi Dokümantasyonu

## Genel Bakış
MyRhythmNexus, kurumsal dağıtımlar için donanım kilidi (Hardware Lock) ve özellik tabanlı (Feature-based) bir lisanslama sistemi kullanır. Bu sistem, yazılımın sadece yetkili makinelerde çalışmasını ve müşterinin satın aldığı modüllerin (örn: QR Giriş, Finans, Raporlama) kontrolünü sağlar.

## Mimari
Sistem üç ana bileşenden oluşur:
1.  **Backend (Lisans Sunucusu):** Lisans anahtarlarını, geçerlilik sürelerini ve donanım kimliklerini yönetir.
2.  **Veritabanı (`licenses` tablosu):** Lisans durumunu tutan tek gerçeklik kaynağıdır.
3.  **Desktop Client (Lisans Yöneticisi):** Uygulama başlangıcında lisansı doğrular ve yerel donanım kimliğini sunucuya iletir.

## Veri Modeli (`License`)
| Alan | Tip | Açıklama |
|---|---|---|
| `license_key` | String | Benzersiz lisans anahtarı (Format: `MRN-XXXX-XXXX-XXXX`) |
| `client_name` | String | Müşteri adı (örn: "FitLife Studio") |
| `is_active` | Boolean | Lisansın manuel olarak iptal edilip edilmediği |
| `expires_at` | DateTime | Lisansın son geçerlilik tarihi |
| `hardware_id` | String | İlk aktivasyonda kilitlenen donanım kimliği (UUID) |
| `features` | JSON | Aktif modüller (örn: `{"qr_checkin": true, "finance": false}`) |
| `last_check_in` | DateTime | Son başarılı doğrulama zamanı |

## API Endpointleri

### Public (Desktop Client için)
*   **POST `/api/v1/license/validate`**
    *   **Girdi:** `{ "license_key": "...", "machine_id": "..." }`
    *   **İşlem:**
        1.  Anahtarı bulur.
        2.  Süresi dolmuş mu kontrol eder.
        3.  `hardware_id` boşsa, gelen `machine_id` ile kilitler.
        4.  `hardware_id` doluysa, gelen `machine_id` ile eşleşiyor mu kontrol eder.
    *   **Çıktı:** `{ "valid": true, "features": {...}, "expires_at": "..." }`

*   **GET `/api/v1/license/check-feature/{feature_name}`**
    *   Belirli bir özelliğin (örn: `finance_module`) açık olup olmadığını döner.

### Admin (Yönetim Paneli için)
*   **POST `/api/v1/admin/licenses`**: Yeni lisans oluşturur.
*   **GET `/api/v1/admin/licenses`**: Tüm lisansları listeler.
*   **PATCH `/api/v1/admin/licenses/{id}`**: Lisans süresini uzatır veya özellikleri değiştirir.
*   **DELETE `/api/v1/admin/licenses/{id}`**: Lisansı siler.

## Desktop Entegrasyonu
Masaüstü uygulaması (`desktop/core/license_manager.py`), `uuid.getnode()` kullanarak kararlı bir makine kimliği üretir.
1.  Uygulama açılışında `config.json`'dan kayıtlı lisans anahtarını okur.
2.  Backend'e `/validate` isteği atar.
3.  Başarılıysa `LoginWindow` açılır.
4.  Başarısızsa veya anahtar yoksa `LicenseWindow` açılır ve kullanıcıdan anahtar ister.

## Güvenlik Notları
*   **Donanım Kilidi:** Lisans bir kez aktive edildiğinde o makineye kilitlenir. Başka bir makinede kullanılamaz.
*   **Sıfırlama:** Müşteri bilgisayar değiştirirse, Admin API üzerinden `hardware_id` alanı `NULL` yapılarak lisans boşa çıkarılabilir.
*   **Offline Mod:** Şu an için sistem her açılışta internet bağlantısı ve backend erişimi gerektirir. (Gelecekte offline cache eklenebilir).
