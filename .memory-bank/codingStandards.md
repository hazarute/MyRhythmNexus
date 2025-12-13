
# Kodlama Standartları ve Mimari Kurallar (MyRhythmNexus)

Bu doküman, MyRhythmNexus kod tabanına katkı veren **tüm ekip üyeleri (insan + yapay zeka)** için bağlayıcıdır. Amaç: sürdürülebilirlik, güvenilirlik, üretim kalitesi ve hız.

Kapsam: Python (FastAPI, SQLAlchemy async, Alembic, APScheduler), Jinja2/HTMX tabanlı web arayüzü, CustomTkinter masaüstü uygulaması, testler (pytest).

---

## 1) Genel Kodlama Felsefesi

**1.1. Sadelik ve doğruluk**
- En basit çalışan çözümü tercih edin. “Clever” kod yerine okunabilir kod.
- Kısa vadeli hız için uzun vadeli bakım maliyetini artırmayın.

**1.2. SOLID + DRY + KISS**
- **DRY:** Aynı iş mantığını kopyalamayın. Ortak davranışları tek bir fonksiyona/servise çıkarın.
- **SRP (Single Responsibility):** Dosya/sınıf/fonksiyon tek sorumluluk taşımalı.
- **KISS:** Gereksiz soyutlama (abstraction) eklemeyin.

**1.3. Modülerlik ve katmanlar**
- Web ve API katmanları birbirine “UI odaklı” bağımlılıklar eklememeli.
- İş kuralları route fonksiyonlarının içine gömülmez; `services/` veya uygun modüle taşınır.

**1.4. Async-first disiplin (FastAPI + SQLAlchemy Async)**
- Async route’larda blocking I/O yasaktır (dosya okuma, ağır CPU işi, requests vb.).
- DB erişimi **sadece** AsyncSession üzerinden yapılır.

**1.5. Veri kaynağı tekliği (SSOT)**
- Şema doğruluğu için `prisma/schema.prisma` ana referanstır; migrasyonlar Alembic ile sürdürülür.

**1.6. Güvenlik ve gizli bilgi**
- Secret/Key/Token **asla** repoya yazılmaz. Sadece `.env` ve `settings` üzerinden okunur.
- Auth/permission kontrolleri route seviyesinde “unutulamaz”: her korumalı endpoint açıkça kontrol eder.

---

## 2) İsimlendirme Kuralları (Naming Conventions)

**2.1. Python (genel)**
- Modül/dosya: `snake_case.py`
- Paket klasörü: `snake_case/`
- Fonksiyon/metot: `snake_case()`
- Değişken: `snake_case`
- Sınıf: `PascalCase`
- Sabit: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`
- “Dunder” (`__x__`) yalnızca Python standardı ile uyumlu durumlarda.

**2.2. FastAPI**
- Router değişkeni: `router`
- Dependency fonksiyonları: `get_*` (örn. `get_db`, `get_current_user`)
- Endpoint fonksiyonları: eylem + nesne (örn. `create_member`, `list_subscriptions`, `update_profile`).

**2.3. SQLAlchemy / Model alanları**
- DB alan isimleri: `snake_case`.
- Relationship adları: çoğul/tekil anlamına dikkat (örn. `payments` liste, `package` tek).

**2.4. Template (Jinja2)**
- Template dosyaları: `snake_case.html`.
- Context anahtarları: mümkün olduğunca standart: `request`, `user`, `current_user`, `page_title`, `error`, `errors`.

**2.5. Testler**
- Dosya: `test_*.py`
- Test fonksiyonu: `test_<davranis>_<beklenti>()` (örn. `test_logout_clears_cookie`).

---

## 3) Yorum ve Dokümantasyon (Docstrings)

**3.1. Zorunlu format**
- Docstring standardı: **Google style**.

**3.2. Nerede zorunlu?**
- Public fonksiyonlar, servis sınıfları, kritik iş kuralları, FastAPI route’ları: docstring zorunlu.
- “Ne yaptığını” söyleyen docstring değil; **niyet + yan etkiler + hata davranışı** açıklanır.

**3.3. Kod içi yorumlar**
- Yorum, “kodun söylediğini” tekrar etmeyecek; **neden** o çözümün seçildiğini açıklayacak.
- Geçici yorumlar (TODO/FIXME) tarih ve kısa bağlam içermeli.

**3.4. Örnek (Google docstring)**
```python
def create_access_token(data: dict[str, str], expires_delta: timedelta) -> str:
		"""Create a signed JWT access token.

		Args:
				data: Claims to embed in the token.
				expires_delta: Expiration delta.

		Returns:
				Signed JWT string.

		Raises:
				ValueError: If claims are invalid.
		"""
```

---

## 4) Hata Yönetimi (Error Handling)

**4.1. Genel ilkeler**
- “Sessiz” hata bastırma yasaktır: `except: pass` **yasak**.
- Geniş yakalama (`except Exception`) sadece **sınır katmanlarında** (route / worker / CLI entry) ve mutlaka loglayarak yapılabilir.
- `finally` yalnızca gerçekten gerekli cleanup için.

**4.2. FastAPI’de hata yönetimi**
- Kullanıcı hataları için `HTTPException` kullanın.
- Beklenen doğrulama hataları: 400/422; yetki/auth: 401/403.
- DB transaction hatalarında: rollback + log + uygun HTTP yanıtı.

**4.3. SQLAlchemy AsyncSession**
- Bir işlem akışında commit başarısızsa: `await session.rollback()` zorunlu.
- Template render sırasında lazy-loading tetiklenmesine izin vermeyin.
	- İlişkiler gerekiyorsa query’de **eager loading** uygulayın (`selectinload()` vb.).

**4.4. Hata mesajları**
- Kullanıcıya dönen mesajlar: sade, güvenli, PII içermeyen.
- Log mesajları: teşhis edilebilir (request id, user id gibi güvenli bağlam).

---

## 5) Modüler Yapı ve İçe Aktarma (Imports)

**5.1. Import sırası (PEP 8 uyumlu)**
1) Standart kütüphane
2) Üçüncü parti
3) Proje içi

Örnek:
```python
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import select

from backend.core.database import get_db
```

**5.2. Mutlak import (absolute import) tercih edilir**
- Proje içinde `from backend...` şeklinde absolute import kullanın.
- Relatif import sadece aynı paket içinde ve netlik sağlıyorsa kullanılabilir.

**5.3. Döngüsel bağımlılık yasağı**
- `models` → `services` → `routes` yönünde akış tercih edilir.
- `routes` içinde iş mantığı büyüyorsa servis katmanına çıkarın.
- Template’ler Python modüllerini import etmez; veri sadece context üzerinden gelir.

**5.4. Side-effect import yasaktır**
- Import sırasında DB bağlantısı başlatma, scheduler start etme, dosya yazma gibi yan etkiler yasaktır.

---

## 6) Tip Belirleme (Type Hinting)

**6.1. Zorunluluk**
- Yeni yazılan tüm Python kodlarında type hint **zorunludur**.
- Mevcut koda dokunurken (refactor/feature) ilgili fonksiyonların tiplerini iyileştirin.

**6.2. Kurallar**
- `Any` son çaredir. Kullanımı gerekçelendirilmelidir.
- Koleksiyonlar parametrik olmalı: `list[str]`, `dict[str, int]`.
- `Optional[T]` sadece gerçekten `None` olabilen değerlerde.
- Async fonksiyonlar: `async def ... -> T` (T dönüş tipi açık olmalı).

**6.3. Pydantic / Şema katmanı**
- API input/output için Pydantic şemaları kullanın; route’larda ham dict döndürmeyin.
- Şemalar “DB modelini aynen kopyalamak” için değil; **API kontratı** için tasarlanır.

---

## 7) Loglama

**7.1. Print yasağı**
- Üretim kodunda `print()` **yasaktır**.
- Sadece kısa süreli lokal debug için kullanılabilir; PR/merge öncesi kaldırılmalı.

**7.2. logging standardı**
- Her modül başında:
```python
import logging
logger = logging.getLogger(__name__)
```
- Seviyeler:
	- `logger.debug`: detay (default kapalı olmalı)
	- `logger.info`: normal iş akışı (login, create, update)
	- `logger.warning`: beklenmeyen ama recoverable durum
	- `logger.error`: hata oluştu (exception yok veya ayrı log)
	- `logger.exception`: exception yakaladığınız bloklarda stack trace ile

**7.3. Log içeriği**
- PII (telefon, email, adres) loglamak yasaktır.
- Token/secret kesinlikle loglanmaz.

---

## 8) Test Kuralları

**8.1. Genel test yaklaşımı**
- Test framework: pytest.
- Testler deterministic olmalı (rasgelelik/timezone etkileri kontrol altında).
- Testler “implementation detail” değil “davranış” test eder.

**8.2. Yapı ve isimlendirme**
- Dosya: `tests/test_*.py`
- Fixture’lar: `tests/conftest.py` veya ilgili modül içinde.
- Test isimleri: `test_<olay>_<beklenti>`.

**8.3. Web / API testleri**
- Route testlerinde en az:
	- 200/302 başarılı akış
	- 401/403 yetkisiz akış
	- Hatalı input (422/400)
- Auth testlerinde cookie davranışı açıkça doğrulanır (login set-cookie, logout delete-cookie).

**8.4. DB testleri**
- Her test izolasyonlu olmalı: transaction rollback veya test DB stratejisi.
- “Gerçek production DB” üzerinde test koşmak yasaktır.

**8.5. Performans / uzun testler**
- Uzun süren testleri işaretleyin (örn. `@pytest.mark.slow`) ve CI’da ayrı çalıştırın.

