# Lisans Sunucusu — Yönetici Scriptleri

Bu belge, `license_server/scripts/` altında bulunan yardımcı scriptleri (betikleri) açıklar. Bunlar, lisans sunucusu veritabanındaki müşterileri ve lisansları yönetmek için geliştirme ve idari kullanım amaçlı küçük CLI (Komut Satırı Arayüzü) araçlarıdır.

Önemli notlar
- Bu scriptler doğrudan `license_server/database.py` aracılığıyla yapılandırılan Lisans Sunucusu veritabanı ve uygulamanızın kullandığı ortam değişkenleri (geliştirme için genellikle bir SQLite dosyası) üzerinde çalışır. Üretim ortamında (production), güvenli yönetici araçlarını yalnızca uygun şekilde güvenliği sağlanmış ve yedeklenmiş bir veritabanına karşı çalıştırmalısınız.
- Windows PowerShell üzerinde depo kök dizininden (repo root) çalıştırırken, `license_server` paketinin içe aktarılabilmesi için `PYTHONPATH` değişkenini depo kök dizinine ayarlayın. Örnek:

```powershell
$env:PYTHONPATH = "E:\NewWork\MyRhythmNexus"
python license_server/scripts/list_customer_licenses.py --all
````

  - Birçok script etkileşimlidir ve değişiklik yapmadan önce onayınızı isteyecektir. İstemleri (prompts) dikkatlice okuyun.
  - `private.pem` şu anda geliştirme kolaylığı için depoda bulunmaktadır. Üretim (production) özel anahtarlarını ASLA git'e commit etmeyin; üretimde gizli bilgi yöneticinizi (secrets manager) kullanın.

## Scriptler

1)  `create_license_cli.py`

<!-- end list -->

  - Amaç: Bir `Customer` (Müşteri) ve o müşteri için bir `License` (Lisans) oluşturur. Test ve demo lisanslarını önyüklemek (bootstrap) için kullanışlıdır.
  - Davranış:
      - Bir `Customer` satırı oluşturur (isim, e-posta, isteğe bağlı meta veriler).
      - Otomatik oluşturulmuş bir `license_key`, son kullanma tarihi, özellikler JSON'ı ve isteğe bağlı `hardware_id` (HWID) ile müşteriye bağlı bir `License` satırı oluşturur.
      - Oluşturulan `license_key` ve son kullanma tarihini ekrana yazdırır.
  - Kullanım örnekleri:

<!-- end list -->

```powershell
$env:PYTHONPATH = "E:\NewWork\MyRhythmNexus"
python license_server/scripts/create_license_cli.py --name "FitLife Studio" --email contact@fitlife.com --days 365
# etkileşimli: argümanları atlayın ve istemleri takip edin
```

2)  `reset_hwid_cli.py`

<!-- end list -->

  - Amaç: Genellikle bir cihaz değiştirildiğinde, bir müşteri için mevcut lisans veya lisanslarla ilişkili `hardware_id`'yi (HWID) sıfırlar.
  - Davranış:
      - Bir müşteri seçmenizi ister (veya `--email` kabul eder).
      - Eşleşen lisansları gösterir ve bir veya daha fazlasını seçmenize izin verir.
      - Seçilen lisanslar için `hardware_id`'yi yeni bir değere ayarlar (veya temizler).
      - Güncellemeden önce onay gerektirir.
  - Kullanım örneği:

<!-- end list -->

```powershell
$env:PYTHONPATH = "E:\NewWork\MyRhythmNexus"
python license_server/scripts/reset_hwid_cli.py --email contact@fitlife.com
```

3)  `add_license_for_customer.py`

<!-- end list -->

  - Amaç: Mevcut bir müşteri için ek bir lisans ekler (çoklu cihaz veya çoklu koltuk satın alımları için kullanışlıdır).
  - Davranış:
      - `--email` kabul eder veya müşteri e-postasını sorar.
      - Verilen müşteri için, geçerlilik günleri ve özellikler seçenekleriyle yeni bir `License` satırı oluşturur.
      - Yeni `license_key` değerini yazdırır.
  - Kullanım örneği:

<!-- end list -->

```powershell
$env:PYTHONPATH = "E:\NewWork\MyRhythmNexus"
python license_server/scripts/add_license_for_customer.py --email contact@fitlife.com --days 365
```

4)  `delete_license_cli.py`

<!-- end list -->

  - Amaç: Lisans satırlarını soft-delete (yazılımsal silme, `is_active=False` yapma) veya hard-delete (tamamen silme) işlemi yapar.
  - Davranış:
      - Müşteriyi `--email` ile (veya etkileşimli istemle) bulur.
      - Lisansları listeler ve belirli lisans(lar)ı dizin, `all` (tümü) veya lisans anahtarı ile seçmenize izin verir.
      - Varsayılan olarak soft-delete gerçekleştirir (`is_active=False` ayarlar). Veritabanı satırını tamamen kaldırmak için `--hard` kullanın.
      - Yıkıcı değişiklikleri onaylamak için `yes` yazılmasını gerektirir.
  - Kullanım örnekleri:

<!-- end list -->

```powershell
$env:PYTHONPATH = "E:\NewWork\MyRhythmNexus"
python license_server/scripts/delete_license_cli.py --email contact@fitlife.com --license-key MRN-XXXX --hard
python license_server/scripts/delete_license_cli.py --email contact@fitlife.com    # etkileşimli seçim
```

5)  `list_customer_licenses.py`

<!-- end list -->

  - Amaç: Müşterileri ve lisanslarını listelemek için salt okunur yardımcı araç.
  - Davranış:
      - `--all`: tüm müşterileri ve lisanslarını listeler.
      - `--email <adres>`: tek bir müşterinin lisanslarını gösterir.
      - `--active-only`: sadece aktif lisansları gösterir.
      - `license_key`, `active` durumu, `expires` zaman damgası, `hwid` ve `features` JSON'ını yazdırır.
  - Kullanım örnekleri:

<!-- end list -->

```powershell
$env:PYTHONPATH = "E:\NewWork\MyRhythmNexus"
python license_server/scripts/list_customer_licenses.py --all
python license_server/scripts/list_customer_licenses.py --email contact@fitlife.com --active-only
```

## Diğer araçlar

  - `license_server/generate_keys.py`: Geliştirme için yeni bir RSA özel/genel anahtar çifti oluşturmaya yarayan kolaylık scripti. Üretimde, anahtarları güvenli bir şekilde oluşturmalı ve saklamalı, özel anahtarları asla kaynak kontrolüne (source control) göndermemelisiniz.

## Operasyonel öneriler

  - Güvenlik için, yıkıcı scriptleri (`delete_license_cli.py`, `reset_hwid_cli.py`) önce bir veritabanı yedeğine karşı veya bir "staging" ortamında çalıştırın.
  - Otomasyonda (CI / yönetici araçları), doğrudan veritabanına bağlanmak yerine kimlik doğrulamalı bir yönetici API'si kullanmayı tercih edin. Şu anda otomasyona ihtiyacınız varsa, bu scriptleri `--yes` / `--dry-run` bayraklarıyla sarmalayabilirsiniz (istek üzerine bunları ekleyebiliriz).
  - Masaüstü istemcisi tarafından kullanılan `public.pem` ile imzalama için lisans sunucusu tarafından kullanılan `private.pem`in eşleştiğinden emin olun. Üretime geçerken anahtarları döndürün (rotate keys) ve istemcileri buna göre güncelleyin.

## Sorun Giderme

  - Scriptleri çalıştırırken modül içe aktarma hataları mı alıyorsunuz? `PYTHONPATH`in yukarıda gösterildiği gibi depo kök dizinine ayarlandığından emin olun.
  - Veritabanı bağlantı hataları mı var? `license_server/database.py` dosyasını ve lisans sunucusu tarafından kullanılan `LICENSE_DATABASE_URL` ortam değişkenini kontrol edin.

## Sonraki iyileştirmeler (isteğe bağlı)

  - Daha iyi otomasyon desteği için scriptlere `--dry-run` ve `--json` çıktı modları ekle.
  - Kritik davranışlar (oluşturma, silme, sıfırlama) için geçici bir test veritabanı kullanan küçük bir birim test seti ekle.
  - Scriptlerin doğrudan DB erişimine ihtiyaç duymaması için tüm işlemler için kimlik doğrulamalı bir yönetici HTTP API'si sağla.

İsterseniz, bir sonraki adımda anahtar scriptlere `--dry-run` ve `--json` özelliklerini ekleyebilirim — ilk olarak hangisini istersiniz?

```

**Sizin için yapabileceğim bir sonraki adım:** Dosyanın son kısmında bahsedilen, scriptlere `--dry-run` veya `--json` özelliği ekleme konusunda yardımcı olmamı ister misiniz?
```