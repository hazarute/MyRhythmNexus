# Kodlama Standartları

Son güncelleme: 2026-03-03

## 1) Temel İlkeler
- Basit, okunabilir ve bakım dostu çözüm tercih edilir.
- İş kuralları route içinde büyütülmez; uygun servis/modül katmanına taşınır.
- Güvenlik anahtarları ve hassas bilgiler repoya yazılmaz; `.env`/config üzerinden okunur.

## 2) Python ve FastAPI
- İsimlendirme: `snake_case` (fonksiyon/değişken), `PascalCase` (sınıf)
- Yeni kodlarda type hint zorunlu.
- `except: pass` yasak.
- Async route’larda blocking I/O yapılmaz.
- DB işlemleri `AsyncSession` ile yönetilir; commit hatalarında rollback zorunlu.

## 3) SQLAlchemy Kullanımı
- Template veya response öncesi gerekli ilişkiler `selectinload()` ile eager-load edilir.
- Lazy-load kaynaklı runtime hatalarına (özellikle async context) izin verilmez.

## 4) Web (Jinja2) ve Desktop (CustomTkinter)
- Web context’te standard key’ler korunur (`request`, `user`, `current_user`, `page_title`, `error`).
- Desktop config erişimi `desktop/core/config.py` üzerinden merkezi yürütülür.
- Lisans akışı `desktop/core/license_manager.py` ve `license_server/` ile uyumlu tutulur.

## 5) Test ve Doğrulama
- Testler davranış odaklı yazılır, implementation detayına kilitlenmez.
- Değişiklik sonrası önce dar kapsamlı test, sonra daha geniş regression çalıştırılır.
- Legacy/stale testler açıkça işaretlenir; sessizce kırık bırakılmaz.

## 6) Dokümantasyon Disiplini
- Mimari/süreç değişikliklerinde `.memory-bank/` dosyaları aynı oturumda güncellenir.
- README, release scriptleri ve gerçek dosya adları birbirleriyle tutarlı tutulur.