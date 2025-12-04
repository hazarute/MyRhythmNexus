# MyRhythmNexus License Server

![License](https://img.shields.io/badge/license-Proprietary-red.svg?style=flat-square)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?style=flat-square)
![Status](https://img.shields.io/badge/status-Active-success.svg?style=flat-square)

> **MyRhythmNexus** ekosistemi için merkezi, güvenli ve çevrimdışı öncelikli (offline-first) lisans yönetim otoritesi.

--------------------------------------------------------------------------------

## 🚀 Hızlı Başlangıç (Quickstart)

Projeyi yerel ortamda hemen ayağa kaldırmak için:

```bash
# 1. Bağımlılıkları yükle
pip install -r requirements.txt

# 2. RSA Anahtarlarını Üret
python generate_keys.py

# 3. Sunucuyu Başlat
uvicorn main:app --reload
```

---

## 📝 İçindekiler Tablosu

- [Proje Özeti ve Motivasyon](#-proje-özeti-ve-motivasyon)
- [Özellikler](#-özellikler-features)
- [Teknolojik Yığın](#-teknolojik-yığın-tech-stack)
- [Kurulum](#-kurulum-installation)
- [Yapılandırma](#-yapılandırma-configuration)
- [Kullanım](#-kullanım-usage)
- [Lisans](#-lisans-license)

---

## 📚 Proje Özeti ve Motivasyon

**MyRhythmNexus License Server**, spor ve dans stüdyoları için geliştirilen yönetim yazılımının (MyRhythmNexus) lisanslama omurgasıdır.

**Motivasyon:** Dağıtık (on-premise) çalışan müşteri sistemlerinin lisans kontrolünü tek bir merkezden yönetmek, ancak internet kesintilerinde bile müşterinin işinin aksamamasını sağlamak.

**Çözüm:** RSA-2048 asimetrik şifreleme ile imzalanmış JWT token'lar kullanır. Müşteri sistemi, sunucudan aldığı imzalı token'ı saklar ve internet olmasa bile Public Key ile doğrulayarak çalışmaya devam eder.

## ✨ Özellikler (Features)

*   **Merkezi Yönetim:** Tüm müşteri lisansları tek bir veritabanında.
*   **RSA İmzalama:** Lisanslar, sunucunun Private Key'i ile kriptografik olarak imzalanır.
*   **Offline-First:** İmzalı JWT token sayesinde istemciler internet olmadan da lisans doğrulayabilir.
*   **Donanım Kilidi:** Lisanslar, istemcinin benzersiz donanım kimliğine (Machine ID) kilitlenir.
*   **Modüler Yetkilendirme:** Özellikler (Features) JSON yapısı ile dinamik olarak yönetilir.

## 🏗️ Teknolojik Yığın (Tech Stack)

*   **Framework:** FastAPI (Python)
*   **Veritabanı:** SQLite (Başlangıç) / PostgreSQL (Production)
*   **Kriptografi:** `cryptography` (RSA-2048), `PyJWT`
*   **Deployment:** Docker, Railway

## ⚙️ Kurulum (Installation)

### Önkoşullar
*   Python 3.10 veya üzeri
*   pip

### Adımlar

1.  Depoyu klonlayın veya `license_server` klasörüne gidin.
2.  Sanal ortam oluşturun ve aktif edin:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
3.  Bağımlılıkları yükleyin:
    ```bash
    pip install -r requirements.txt
    ```

## 🛠️ Yapılandırma (Configuration)

Proje kök dizininde `.env` dosyası oluşturun. Örnek `.env` içeriği:

```ini
# Uygulama Ayarları
APP_ENV=development
DEBUG=True

# Güvenlik (RSA Anahtarları generate_keys.py ile üretilir)
PRIVATE_KEY_PATH=private.pem
PUBLIC_KEY_PATH=public.pem
```

## 💡 Kullanım (Usage)

### RSA Anahtarlarını Üretme
Sunucu ilk kez kurulduğunda şifreleme anahtarlarını üretmeniz gerekir:
```bash
python generate_keys.py
```
*Bu işlem `private.pem` ve `public.pem` dosyalarını oluşturur.*

### Sunucuyu Başlatma
```bash
uvicorn main:app --reload --port 8000
```

### API Endpoints
*   `POST /api/v1/license/create`: Yeni lisans oluştur (Admin).
*   `POST /api/v1/license/validate`: Lisans kontrolü ve Token üretimi (Client).

## ⚖️ Lisans (License)

Bu proje **Proprietary (Özel Mülkiyet)** lisansı altındadır. İzinsiz kopyalanması, dağıtılması veya kullanılması yasaktır.
