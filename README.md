# MyRhythmNexus

[![Lisans: BSL 1.1](https://img.shields.io/badge/Lisans-BSL_1.1-blue.svg?style=flat-square)](./LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg?style=flat-square)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121-green.svg?style=flat-square)](https://fastapi.tiangolo.com/)
[![Masaüstü Sürüm](https://img.shields.io/badge/Masa%C3%BCst%C3%BC-v1.1.0-6f42c1.svg?style=flat-square)](./desktop/version.txt)

Pilates, dans ve fitness işletmeleri için modern operasyon platformu: **masaüstü admin + backend API + üye web portalı + merkezi lisanslama**.

---

## 🚀 Hızlı Başlangıç

### Seçenek A — Docker ile backend/web çalıştırma

```bash
git clone https://github.com/hazarute/MyRhythmNexus.git
cd MyRhythmNexus
cp .env.example .env
# .env içeriğini düzenleyin (en az SECRET_KEY)
./deploy.sh server
```

Erişim noktaları:
- Web: `http://localhost`
- API: `http://localhost:8000`
- API Dokümantasyonu (geliştirme ortamında): `http://localhost:8000/docs`

### Seçenek B — Yerel backend çalıştırma

```bash
git clone https://github.com/hazarute/MyRhythmNexus.git
cd MyRhythmNexus
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn backend.main:app --reload
```

---

## 📋 İçindekiler

- [Proje Özeti (Ne / Neden / Nasıl)](#-proje-özeti-ne--neden--nasıl)
- [Özellikler](#-özellikler)
- [Mimari](#-mimari)
- [Teknoloji Yığını](#-teknoloji-yığını)
- [Kurulum](#-kurulum)
- [Yapılandırma](#-yapılandırma)
- [Kullanım](#-kullanım)
- [Test](#-test)
- [Dokümantasyon](#-dokümantasyon)
- [Katkıda Bulunma](#-katkıda-bulunma)
- [Lisans](#-lisans)
- [İletişim](#-iletişim)

---

## 📚 Proje Özeti (Ne / Neden / Nasıl)

### Ne?
MyRhythmNexus; üye yönetimi, satış, paket/abonelik takibi, ders operasyonları ve QR check-in süreçlerini tek platformda birleştiren stüdyo yönetim sistemidir.

### Neden?
Stüdyo operasyonları çoğu zaman birden fazla araçta dağınık yürütülür. Bu durum veri tutarsızlığı, operasyonel gecikme ve raporlama zorluğu üretir. MyRhythmNexus bu parçalı yapıyı tek bir doğruluk kaynağında toplar.

### Nasıl?
- **Backend (`backend/`)**: FastAPI tabanlı API + üye web portalı + zamanlanmış görevler
- **Masaüstü (`desktop/`)**: CustomTkinter tabanlı admin paneli
- **Lisans Sunucusu (`license_server/`)**: Ayrı FastAPI servisiyle merkezi lisans doğrulama

---

## ✨ Özellikler

### Operasyonel Çekirdek
- Üye CRM (kayıt, güncelleme, aktivasyon/pasivasyon)
- ServicePackage/Subscription yaşam döngüsü
- Satış ve ödeme kayıtları
- Ölçüm takibi ve profil yönetimi

### Giriş Kontrolü
- QR token tabanlı check-in
- Abonelik ve plan türüne göre doğrulama (`SESSION_BASED` / `TIME_BASED`)
- Etkinlik kapasite ve uygunluk kontrolleri

### Otomasyon
- Günlük inaktif üye pasifleştirme
- Süresi/hakkı dolan abonelikleri `expired` işaretleme
- Süresi dolan aboneliklerde QR pasifleştirme/yenileme

### Lisanslama
- Ayrı lisans servisi üzerinden doğrulama
- Donanım kilitleme yaklaşımı
- RSA imzalı JWT ile offline-first doğrulama akışı

### Uluslararasılaştırma (i18n)
- Türkçe/İngilizce dil altyapısı
- `gettext` tabanlı çeviri araçları (`i18n_manager.py`, `fill_translations.py`, `scan_ui_strings.py`, `wrap_ui_strings.py`)

---

## 🏛️ Mimari

```text
Masaüstü Admin (CustomTkinter) ─┐
                                ├── FastAPI Backend (API + Web)
Üye Web (Jinja2 / /web/*) ──────┘             │
                                              └── PostgreSQL

Masaüstü Lisans Yöneticisi ───────────────▶ Lisans Sunucusu (FastAPI, RSA JWT)
```

Ana route yüzeyleri:
- API: `/api/v1/*`
- Web Portalı: `/web/*`

Önemli dosyalar:
- `backend/main.py`
- `backend/api/api.py`
- `backend/web/router.py`
- `backend/core/scheduler.py`
- `desktop/main.py`
- `desktop/core/license_manager.py`
- `license_server/main.py`

---

## 🧰 Teknoloji Yığını

- **Dil:** Python 3.9+
- **Backend:** FastAPI
- **ORM:** SQLAlchemy 2.x (async)
- **Veritabanı:** PostgreSQL (ana), SQLite (bazı yerel/geliştirme senaryoları)
- **Migrasyon:** Alembic
- **Masaüstü Arayüz:** CustomTkinter
- **Web Arayüz:** Jinja2 (SSR)
- **Kimlik Doğrulama:** JWT
- **Zamanlanmış Görevler:** APScheduler
- **Konteynerleşme:** Docker + Docker Compose
- **Paketleme:** PyInstaller

---

## ⚙️ Kurulum

### Önkoşullar
- Python 3.9+
- Docker + Docker Compose (Docker senaryosu için)
- Git

### 1) Depoyu klonlayın

```bash
git clone https://github.com/hazarute/MyRhythmNexus.git
cd MyRhythmNexus
```

### 2) Ortam dosyasını oluşturun

```bash
cp .env.example .env
```

### 3A) Docker ile çalıştırın

```bash
./deploy.sh server
```

### 3B) Yerel Python ile çalıştırın

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn backend.main:app --reload
```

### Masaüstü derleme (Windows)

```bat
build-desktop.bat
```

### Masaüstü derleme (Linux/macOS)

```bash
./build-desktop.sh
```

---

## 🛠️ Yapılandırma

`.env.example` dosyasını temel alın; gerçek değerleri `.env` içine yazın.

Önemli değişkenler:
- `DATABASE_URL`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `HOST`, `PORT`
- `CORS_ORIGINS`
- `FIRST_SUPERUSER`, `FIRST_SUPERUSER_PASSWORD`
- `RHYTHM_NEXUS_LICENSE_SERVER_URL`

Örnek:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/myrhythmnexus
SECRET_KEY=REPLACE_ME_WITH_STRONG_SECRET
HOST=0.0.0.0
PORT=8000
RHYTHM_NEXUS_LICENSE_SERVER_URL=http://localhost:8001/api/v1
```

> Güvenlik: Gerçek `.env` dosyasını asla repoya commit etmeyin.

---

## 💡 Kullanım

### Backend / Web
- Root URL `/`, uygun kullanıcı ajanı koşullarında `/web/qr-bridge` veya `/web/auth/login` yönlendirmesi yapar.
- Üye web portalı `/web/*` altında çalışır (login, dashboard, subscriptions, measurements, finance, profile).

### API
Örnek çağrı:

```python
import httpx

resp = httpx.get("http://localhost:8000/api/v1/members")
print(resp.status_code)
```

### Lisans Sunucusu
`license_server/` bağımsız çalışır ve masaüstü lisans doğrulaması için kullanılır.

---

## ✅ Test

```bash
pytest
```

Belirli bir test dosyası:

```bash
pytest tests/test_desktop_integration.py -q
```

---

## 📚 Dokümantasyon

- Dağıtım: `docs/DEPLOYMENT.md`
- Paketleme: `docs/PACKAGING.md`
- Masaüstü Güncellemeleri: `docs/DESKTOP_UPDATES.md`
- Masaüstü İş Akışı: `docs/DESKTOP-WORKFLOW.md`
- I18N Kılavuzu: `docs/I18N-GUIDE.md`
- Sürüm Otomasyonu: `docs/RELEASE_AUTOMATION.md`
- Lisans Sunucusu README: `license_server/README.md`
- Lisans Sunucusu Dokümanı: `license_server/docs/Licensing.md`

---

## 🤝 Katkıda Bulunma

Katkılar memnuniyetle karşılanır.

Önerilen akış:
1. Issue açın (hata/özellik açıklamasıyla)
2. Branch oluşturun
3. Değişiklik + test
4. Pull Request açın (problem, çözüm, test özeti ile)

Not: Bu repoda ayrı bir `CONTRIBUTING.md` henüz bulunmuyor; katkı süreçleri için PR açıklamasında ayrıntı vermeniz önerilir.

---

## ⚖️ Lisans

Bu proje **Business Source License 1.1 (BSL 1.1)** ile yayınlanır.

- Detay: `LICENSE`
- Ticari kullanım bilgisi: `COMMERCIAL_LICENSE.md`

Özet:
- Üretim dışı kullanım BSL kapsamında mümkündür.
- Üretim/ticari kullanım için ayrı ticari lisans gerekir.

---

## 📞 İletişim

- Ticari lisans: `kayraspaceinc@gmail.com`
- Proje sahibi: Hazar Üte

---

MyRhythmNexus — Stüdyo operasyonları için birleşik yönetim platformu.