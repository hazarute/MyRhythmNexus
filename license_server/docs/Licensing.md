# MyRhythmNexus - Merkezi Lisanslama Sistemi (SaaS)

Bu döküman, MyRhythmNexus projesinin merkezi lisanslama sisteminin (License Server) mimarisini, kurulumunu ve çalışma mantığını detaylandırır.

## 1. Proje Özeti

**License Server**, MyRhythmNexus masaüstü uygulamalarının lisans durumunu yöneten, doğrulayan ve kontrol eden merkezi bir mikroservistir. Bu sistem, uygulamanın yerel veritabanında lisans tutması yerine, merkezi bir otoriteden yetki almasını sağlar.

### Temel Özellikler
*   **SaaS Mimarisi:** Tüm lisanslar tek bir merkezden yönetilir.
*   **Offline-First:** İnternet kesintilerinde çalışmaya devam eder (RSA İmzalı JWT).
*   **Donanım Kilidi (Hardware Locking):** Lisans sadece ilk aktive edildiği bilgisayarda çalışır.
*   **Güvenlik:** RSA-2048 asimetrik şifreleme ve Rate Limiting (Brute-force koruması).
*   **Modüler Yapı:** Özellik bazlı kısıtlama (örn. "qr_checkin": true/false).

---

## 2. Mimari

Sistem iki ana bileşenden oluşur: **Authority (Sunucu)** ve **Client (Masaüstü Uygulaması)**.

### 2.1. License Server (Authority)
*   **Teknoloji:** FastAPI, SQLAlchemy, SQLite (Dev) / PostgreSQL (Prod).
*   **Görevi:** Lisansları saklar, doğrular ve imzalı JWT token üretir.
*   **Anahtar Yönetimi:** `private.pem` (Gizli Anahtar) ile tokenları imzalar.

### 2.2. Desktop Client (MyRhythmNexus)
*   **Görevi:** Uygulama açılışında lisansı doğrular.
*   **Anahtar Yönetimi:** `public.pem` (Açık Anahtar) ile sunucudan gelen token'ın imzasını doğrular.
*   **Offline Mod:** Geçerli bir token'ı yerel diskte saklar ve internet yoksa bu token'ı kullanır (Varsayılan: 7 gün geçerlilik).

---

## 3. Güvenlik Protokolleri

### 3.1. RSA-2048 & JWT
Sistem, simetrik olmayan şifreleme kullanır.
1.  Sunucu, `private.pem` kullanarak payload'ı (Lisans Key, Hardware ID, Features, Expiration) imzalar.
2.  Oluşan JWT token istemciye gönderilir.
3.  İstemci, içine gömülü `public.pem` ile bu imzanın sunucuya ait olduğunu ve verinin değiştirilmediğini doğrular.

### 3.2. Hardware Locking (Donanım Kilidi)
*   İstemci, MAC adresi ve benzersiz sistem özelliklerinden bir `machine_id` (UUIDv5) üretir.
*   İlk doğrulama isteğinde sunucu bu ID'yi lisansa kaydeder.
*   Sonraki isteklerde, gelen ID ile kayıtlı ID eşleşmezse lisans reddedilir.

### 3.3. Rate Limiting
*   `/api/v1/license/validate` endpoint'i dakikada maksimum **5 istek** kabul eder.
*   Bu, brute-force denemelerini engeller.

---

## 4. Veritabanı Şeması

### Customers (Müşteriler)
| Alan | Tip | Açıklama |
|---|---|---|
| id | Integer | PK |
| name | String | Müşteri/Salon Adı |
| email | String | İletişim E-postası |
| is_active | Boolean | Müşteri aktif mi? |

### Licenses (Lisanslar)
| Alan | Tip | Açıklama |
|---|---|---|
| id | Integer | PK |
| license_key | String | Format: `MRN-XXXX-XXXX-XXXX` |
| customer_id | Integer | FK -> Customers |
| hardware_id | String | Kilitlenen Cihaz ID'si (İlk kullanımda dolar) |
| expires_at | DateTime | Lisans bitiş tarihi |
| is_active | Boolean | Manuel iptal için |
| features | JSON | `{"qr": true, "limit": 100}` |
| last_checkin | DateTime | Son görülme zamanı |

---

## 5. API Referansı

### Admin Endpoints
*   `POST /api/v1/customers/`: Yeni müşteri oluştur.
*   `POST /api/v1/licenses/`: Yeni lisans oluştur.
*   `GET /api/v1/licenses/`: Tüm lisansları listele.

### Client Endpoints
*   `POST /api/v1/license/validate`
    *   **Request:** `{ "license_key": "...", "hardware_id": "..." }`
    *   **Response:**
        ```json
        {
            "valid": true,
            "token": "eyJhbGciOiJSUzI1NiIs...", // İmzalı JWT
            "message": "License valid"
        }
        ```

---

## 6. Kurulum ve Geliştirme

### Gereksinimler
*   Python 3.10+
*   Docker (Opsiyonel)

### Yerel Kurulum
1.  Bağımlılıkları yükleyin:
    ```bash
    pip install -r license_server/requirements.txt
    ```
2.  RSA Anahtarlarını oluşturun:
    ```bash
    python license_server/generate_keys.py
    ```
    *(Bu işlem `private.pem` ve `public.pem` dosyalarını oluşturur)*
3.  Sunucuyu başlatın:
    ```bash
    uvicorn license_server.main:app --reload --port 8001
    ```

### Docker ile Çalıştırma
```bash
docker build -t license-server ./license_server
docker run -p 8001:8000 license-server
```

### İstemci Entegrasyonu (Önemli)
Sunucuda oluşturulan `public.pem` dosyasını, masaüstü uygulamasının `desktop/assets/` klasörüne kopyalamanız gerekir. İstemci, imzayı doğrulamak için bu anahtara ihtiyaç duyar.

---

## 7. Deployment (Railway)

Proje Railway üzerinde çalışmaya hazırdır.
1.  `Dockerfile` kök dizinde mevcuttur.
2.  Environment Variable olarak `DATABASE_URL` verilmelidir (PostgreSQL).
3.  `private.pem` içeriği güvenli bir şekilde environment variable veya secret file olarak sunucuya verilmelidir (Şu anki yapıda dosya olarak bekler, production için env var dönüşümü yapılabilir).
