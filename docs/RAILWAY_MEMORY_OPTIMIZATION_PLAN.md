# 🚀 MyRhythmNexus - Railway Bellek (Memory) Optimizasyon Planı

Bu belge, Tuğba Dans ve Spor Stüdyosu canlı ortamında (Railway) çalışan MyRhythmNexus projesinin aylık 5$ Hobby Plan kotasını aşmasına neden olan bellek (RAM) tüketimini optimize etme yol haritasını içermektedir.

---

## 1. 📊 Mevcut Durum ve Maliyet Analizi

* **Railway Fiyatlandırması:** 1 GB RAM / Ay = 10.00$ (saniye bazlı faturalandırılır).
* **Hobby Plan Kredisi:** 5.00$ / Ay (Kesintisiz **500 MB RAM** kullanımına denk gelir).
* **Mevcut Harcama:** 5$ kredi + 2$ - 5$ ek fatura = **7$ - 10$ / Ay**.
* **Mevcut Toplam RAM Tüketimi:** Proje 7/24 ortalama **700 MB - 1000 MB (0.7 - 1.0 GB) RAM** tüketmektedir.
* **Hedef:** Toplam 7/24 RAM kullanımını **250 MB - 350 MB** seviyesine düşürerek ek maliyeti sıfırlamak ve 5$ planının içinde kalmak.

---

## 2. 🔍 Bellek Tüketiminin Kök Nedenleri

### A. Çoklu Servis (Multi-Service) Mimari Yükü
Railway üzerinde tek bir servis yerine üç farklı bileşen 7/24 aralıksız çalışmaktadır:
1. **PostgreSQL Veritabanı:** ~180 MB - 280 MB RAM (Varsayılan postgres ayarları).
2. **Backend API (`tugbadansvespor-production`):** ~220 MB - 350 MB RAM (FastAPI + Uvicorn + Python 3.13 + Glibc heap parçalanması).
3. **Lisans Sunucusu (`licenseserver-production-0ceb`):** ~100 MB - 140 MB RAM (Yalnızca nadiren lisans doğrulaması yapan bağımsız Python konteyneri).

### B. Kod ve Çalışma Zamanı (Runtime) Darboğazları
1. **SQLAlchemy Connection Pool Sınırsızlığı:**
   * Dosya: `backend/core/database.py`
   * `pool_size` ve `max_overflow` belirtilmediği için 15 bağlantıya kadar açık kalabilmekte, `pool_recycle` olmadığı için bağlantılar asla kapatılmamaktadır. PostgreSQL tarafında her açık bağlantı 5-10 MB RAM tutar.
2. **Glibc Bellek Parçalanması (Memory Fragmentation):**
   * Dockerfile `python:3.13-slim` (Debian glibc tabanlı) kullanmaktadır. Glibc, çok çekirdekli Railway ortamında serbest bırakılan bellek sayfalarını işletim sistemine geri iade etmez (`ptmalloc` arena sorunu).
3. **Desktop Polling Döngüsü:**
   * Masaüstü açıkken her 60 saniyede bir `GET /api/v1/stats/dashboard` çağrılmaktadır.
   * `backend/api/v1/stats.py` içerisindeki borç/abonelik sorgusu stüdyo tarihindeki tüm aktif, beklemede ve süresi bitmiş abonelikleri her dakikada bir belleğe çekip işlemektedir.
4. **`selectinload` Eager Loading ve Yüksek Limitler:**
   * `backend/api/v1/sales.py` içindeki `list_subscriptions` uç noktası `limit: 100` ile 5 katmanlı alt ilişkiyi tek seferde belleğe yüklemektedir.
5. **Mükerrer `Jinja2Templates` Tanımları:**
   * `backend/web/routes/` altındaki 10 farklı route dosyasında ayrı ayrı Jinja2Templates oluşturulmuştur; ortak bir instance yerine bellekte 10 ayrı şablon ortamı tutulmaktadır.

---

## 3. 🛠️ Adım Adım Optimizasyon Eylem Planı

### Aşama 1: Lisans Sunucusunu Ana Backend'e Entegre Etme (Kazanç: ~120 MB RAM / ~1.20$ Tasarruf)
* `license_server/` altındaki `/api/v1/license/validate` endpoint'ini ana backend'e router olarak ekleyin.
* Desktop uygulamasının lisans URL'sini ana backend adresine yönlendirin.
* Railway üzerindeki `licenseserver` servisini silin (Böylece 7/24 çalışan 1 adet Python konteyneri tamamen kaldırılmış olur).

### Aşama 2: Veritabanı Havuzunu Kısma (Kazanç: ~50-70 MB RAM)
* `backend/core/database.py` içerisinde `create_async_engine` ayarlarını güncelleyin:
  ```python
  engine = create_async_engine(
      settings.DATABASE_URL,
      pool_size=2,
      max_overflow=2,
      pool_recycle=300,
      pool_pre_ping=True,
      connect_args=connect_args
  )
  ```

### Aşama 3: Dockerfile İçinde Glibc Optimizasyonu (Kazanç: ~50-80 MB RAM)
* `Dockerfile.backend` içerisine arena sınırlandırması ekleyin:
  ```dockerfile
  ENV MALLOC_ARENA_MAX=2
  ```

### Aşama 4: PostgreSQL Parametrelerini Hafifletme (Kazanç: ~80-100 MB RAM)
* Railway PostgreSQL servis değişkenlerine veya custom konfigürasyona şunları ekleyin:
  * `shared_buffers = 32MB`
  * `max_connections = 25`
  * `work_mem = 2MB`

### Aşama 5: Masaüstü Polling ve Sorgu İyileştirmeleri
* `desktop/ui/views/dashboard.py` içindeki 60 saniyelik `auto_refresh` süresini 180 veya 300 saniyeye çıkarın.
* `backend/api/v1/stats.py` içindeki borç hesaplama sorgusunu SQL tarafında aggregate edin; tüm abonelik satırlarını Python belleğine çekmek yerine sadece aggregate toplamını alın.
* `backend/web/` altındaki 10 farklı `Jinja2Templates` tanımını `backend/core/templates.py` içinde tek bir singleton haline getirin.
