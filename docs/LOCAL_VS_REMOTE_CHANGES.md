# 📋 GitHub Reposu vs Local PC Gerçek Değişiklik Raporu

**Tarih:** 19 Eylül 2026  
**Proje:** MyRhythmNexus (Tuğba Dans ve Spor Stüdyosu)  
**Mevcut Dal:** `main` (Remote `origin/main` ile senkron)  

---

## 1. 🛠️ Windows — Linux Satır Sonu (CRLF vs LF) Uyuşmazlığının Çözümü

### Sorunun Kök Nedeni:
Proje daha önce Windows ortamında kodlandığı için çalışma dizinindeki (working tree) dosyalar **CRLF (`\r\n`)** satır sonlarına sahipti. Linux (CachyOS KDE) ortamına geçildiğinde Git'in satır sonu denetimi (`core.autocrlf`) yapılandırılmadığı için, Git dosyadaki her satır sonunu (`\r`) bir karakter değişikliği olarak yorumlayarak projedeki **yüzlerce dosyayı sahte olarak "değiştirildi (modified)"** gösteriyordu.

### Yapılan Müdahale:
1. **Yerel Git Ayarı:** `git config core.autocrlf true` yapılandırması yerel repoya tanımlandı.
2. **Kalıcı Repo Standardı:** Proje köküne [`.gitattributes`](file:///run/media/hazars/Depo/Projects/MyRhythmNexus/.gitattributes) dosyası eklendi. Bu dosya metin tabanlı kaynak kodları (`.py`, `.sh`, `.json`, `.md` vb.) için LF, Windows scriptleri (`.bat`, `.ps1`) için CRLF kuralını repo genelinde kalıcı hale getirdi.
3. **Sonuç:** Sahte modifiye görünen yüzlerce dosya listeden düştü; geriye yalnızca **gerçekten içeriği değişen 2 dosya** ve yerelde oluşturulmuş yeni dosyalar kaldı.

---

## 2. ✏️ Gerçek Değişiklik İçeren Takip Edilen Dosyalar (Modified Files)

GitHub `origin/main` ile yerel dosya içeriği arasında **gerçek kod farkı** bulunan yalnızca 2 dosya vardır:

| Dosya Yolu | Durum | Değişiklik Özeti |
| :--- | :--- | :--- |
| [`.gitignore`](file:///run/media/hazars/Depo/Projects/MyRhythmNexus/.gitignore) | `Modified` | `.codegraph/` dizini yerel indeks klasörü olarak ignore listesine eklendi (+3 satır). |
| [`prisma/schema.prisma`](file:///run/media/hazars/Depo/Projects/MyRhythmNexus/prisma/schema.prisma) | `Modified` | `subscriptions` tablosundaki `auto_created_class_events boolean [default: false]` satırı kaldırıldı (-3 satır). |

---

## 3. 📄 Yeni Eklenen / İzlenmeyen Dosyalar (Untracked Files)

Yerel bilgisayarda bulunan ancak henüz GitHub reposunda yer almayan dosyalar ve işlevleri:

### A. Konfigürasyon ve Dokümantasyon Dosyaları
* [`.gitattributes`](file:///run/media/hazars/Depo/Projects/MyRhythmNexus/.gitattributes): Windows ve Linux arasındaki satır sonu karmaşasını sonsuza dek önleyen evrensel kural dosyası.
* [`CLAUDE.md`](file:///run/media/hazars/Depo/Projects/MyRhythmNexus/CLAUDE.md): Proje geliştirme prensipleri ve yapay zeka çalışma yönergeleri.
* [`docs/RAILWAY_MEMORY_OPTIMIZATION_PLAN.md`](file:///run/media/hazars/Depo/Projects/MyRhythmNexus/docs/RAILWAY_MEMORY_OPTIMIZATION_PLAN.md): Railway 5$ Hobby Plan kotasını aşan bellek kullanımını düşürme eylem planı.
* [`docs/superpowers/plans/2026-09-14-dead-code-cleanup.md`](file:///run/media/hazars/Depo/Projects/MyRhythmNexus/docs/superpowers/plans/2026-09-14-dead-code-cleanup.md): 14 Eylül tarihli ölü kod temizleme uygulama planı.

### B. Yerel Bakım ve Yardımcı Scriptler
* [`scripts/cleanup_incorrect_plans.py`](file:///run/media/hazars/Depo/Projects/MyRhythmNexus/scripts/cleanup_incorrect_plans.py): "4 Seans K-Pop" ve "4 Seans Hip - Hop" hatalı paket tanımlarını ve bunlara bağlı sahte abonelik kayıtlarını veritabanından güvenle temizleyen bakım scripti.
* [`scripts/export_users_csv.py`](file:///run/media/hazars/Depo/Projects/MyRhythmNexus/scripts/export_users_csv.py): Veritabanındaki kullanıcıları telefon ve ad-soyad bilgisiyle CSV formatında dışa aktaran araç.
* [`scripts/find_plan_subscribers.py`](file:///run/media/hazars/Depo/Projects/MyRhythmNexus/scripts/find_plan_subscribers.py): Belirli planlara kayıtlı aboneleri sorgulayan yardımcı script.
* [`scripts/send_whatsapp.py`](file:///run/media/hazars/Depo/Projects/MyRhythmNexus/scripts/send_whatsapp.py): Stüdyo üyelerine özel kampanya ("Arkadaşını Getir %50", "Uzun Dönem", "HotHour") mesajlarını WhatsApp üzerinden web tarayıcı aracılığıyla otomatik gönderen script.

### C. 🚨 DİKKAT: Gizlilik İçeren Müşteri Verileri (Kesinlikle GitHub'a Yüklenmemeli!)
Aşağıdaki dosyalar stüdyo müşterilerinin **gerçek kişisel verilerini (KVKK)** içermektedir ve asla GitHub reposuna commit edilmemelidir:
* `scripts/users_export.csv`: 1.879 satırlık stüdyo üyesi isim ve telefon listesi.
* `scripts/whatsapp_ilerleme.json`: WhatsApp mesaj gönderiminin hangi müşteride kaldığını tutan ilerleme verisi.
* `scripts/whatsapp_log.csv`: Hangi telefon numarasına ne zaman mesaj gönderildiğini tutan log dosyası.

> [!CAUTION]
> `scripts/*.csv` ve `scripts/*.json` dosyalarının yanlışlıkla `git add .` yapılarak canlıya gitmesini önlemek için derhal [`.gitignore`](file:///run/media/hazars/Depo/Projects/MyRhythmNexus/.gitignore) dosyasına eklenmesi şiddetle tavsiye edilir.

---

## 4. 🚀 Railway Canlı Dağıtım Güvenlik Notu

Railway, GitHub reposunun `main` dalına bağlıdır ve buraya yapılacak bir `git push` işlemi:
1. Docker imajlarını derlemeye başlayacaktır.
2. Alembic migrasyonlarını canlı veritabanında tetikleyecektir.
3. Uygulamayı yeniden başlatacaktır.

Bu nedenle:
* Şu an hiçbir commit veya push işlemi yapılmamıştır.
* Repoda sadece yerel yapılandırma (`core.autocrlf`) ve takip edilmeyen rapor dosyaları bulunmaktadır.
