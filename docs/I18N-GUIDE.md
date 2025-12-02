# i18n (Uluslararasılaştırma) Rehberi

## Genel Bakış

MyRhythmNexus Desktop uygulaması gettext tabanlı çoklu dil desteği (Turkish/English) ile birlikte gelmektedir.

## Dosya Yapısı

```
desktop/
├── core/
│   └── locale.py           # Çeviri wrapper fonksiyonu ve dil yönetimi
├── locale/
│   ├── messages.pot        # Çeviri şablonu (tüm ayıklanan mesajlar)
│   ├── tr/
│   │   └── LC_MESSAGES/
│   │       ├── messages.po  # Türkçe çeviriler
│   │       └── messages.mo  # Derlenmiş Türkçe çeviriler (binary)
│   └── en/
│       └── LC_MESSAGES/
│           ├── messages.po  # İngilizce çeviriler
│           └── messages.mo  # Derlenmiş İngilizce çeviriler (binary)
└── ...
```

## Yeni Çeviriye Tabi String Ekleme

### 1. Kaynak Kodda Strings'i İşaretleme

```python
from desktop.core.locale import _

# Çevrilecek stringi _() ile sarla
label = ctk.CTkLabel(self, text=_("Merhaba Dünya"))
button = ctk.CTkButton(self, text=_("Kaydet"))
```

### 2. Strings Ayıklama

```bash
python i18n_manager.py extract
```

Bu komut:
- Tüm `_()` işaretli stringleri bulur
- `desktop/locale/messages.pot` dosyasını günceller
- `.po` dosyalarında yeni stringler otomatik eklenir

### 3. Çevirileri Düzenleme

**Türkçe çeviriler:**
- `desktop/locale/tr/LC_MESSAGES/messages.po` dosyasını açın
- İngilizce string'i bulun (msgid satırı)
- Türkçe karşılığını msgstr satırına yazın

**İngilizce çeviriler:**
- `desktop/locale/en/LC_MESSAGES/messages.po` dosyasını açın
- Aynı işlemi yapın

### 4. Çevirileri Derlemek

```bash
python i18n_manager.py compile
```

Bu komut `.po` dosyalarını `.mo` dosyalarına derler (çalışan formata).

## Tüm Workflow

```bash
# 1. Yeni strings ekle ve _() ile işaretle
# 2. Ayıkla
python i18n_manager.py extract

# 3. Çevirileri güncelle (manual olarak .po dosyalarını düzenle)

# 4. Derle
python i18n_manager.py compile

# 5. Test et
python desktop/main.py
```

## i18n_manager.py Komutları

```bash
# Strings ayıkla
python i18n_manager.py extract

# İlk kurulumda .po dosyaları oluştur
python i18n_manager.py init

# Var olan .po dosyalarını güncelle
python i18n_manager.py update

# .po dosyalarını .mo dosyalarına derle
python i18n_manager.py compile

# Tüm workflow'u çalıştır (extract -> update -> compile)
python i18n_manager.py workflow
```

## Dil Değiştirme (Kullanıcı Tarafından)

1. Uygulamada "⚙️ Dil Seçimi" butonuna tıkla
2. İstediğin dili seç (Türkçe / English)
3. Uygulama otomatik olarak yeniden başlar

## Dil Değiştirme (Programlı)

```python
from desktop.core.locale import set_language, initialize_locale
from desktop.core.config import DesktopConfig

# Dil değiştir
set_language("en")  # English
initialize_locale("en")

# Dil tercihini kaydet
DesktopConfig.set_language("en")
```

## .po Dosyası Formatı

```po
# Açıklamalar
#: desktop/ui/windows/main_window.py:25
msgid "Kaydet"
msgstr "Save"

#: desktop/ui/views/dashboard.py:42
msgid "Başarılı"
msgstr "Successful"
```

## İngilizce Çeviriler Güncelleme

Eğer uygulamaya yeni türkçe strings eklediysen ve İngilizce çevirilerini otomatik yapıştırmak istiyorsan:

```bash
python fill_translations.py
```

Bu script:
- Türkçe stringleri msgstr'ye kopyalar (Türkçe .po'ya)
- İngilizce stringleri dictionary'den çeviriye dönüştürür

Sonra manuel olarak dictionary'de bulunmayan stringleri düzenle.

## Best Practices

1. **Formatlama**: f-strings (f"...{var}") veya .format() kullanırken:
   ```python
   # ❌ YANLIŞ
   text = _("Üye: {name}").format(name=member_name)
   
   # ✅ DOĞRU
   message = f"Üye: {member_name}"
   # Veya dinamik çeviri için:
   from desktop.core.locale import _
   text = _("Üye") + f": {member_name}"
   ```

2. **Plural Forms**: Çoğul formlar için:
   ```python
   from desktop.core.locale import ngettext
   
   count = 5
   message = ngettext("1 mesaj", "{n} mesajlar", count).format(n=count)
   ```

3. **Yorum Ekleme**: .po dosyasında translator için yorum:
   ```python
   # Translator: This is a button label
   button = ctk.CTkButton(self, text=_("Kaydet"))
   ```

## Sorun Giderme

### Çeviriler görünmüyor

1. `.mo` dosyalarının derlendiğini kontrol et:
   ```bash
   python i18n_manager.py compile
   ```

2. Doğru dil yüklü mü:
   ```python
   from desktop.core.locale import get_current_language
   print(get_current_language())  # "tr" veya "en" olmalı
   ```

### Yeni strings görünmüyor

1. Strings'i `_()` ile sardığını kontrol et
2. Extract yap:
   ```bash
   python i18n_manager.py extract
   ```
3. Derle:
   ```bash
   python i18n_manager.py compile
   ```

### .po dosyası düzenleme

- Editör önerisi: **Poedit** (ücretli ama ücretsiz lite versiyonu var)
- VSCode'de: "gettext" extension yükle
- Notepad: Düz text editör olarak açabilirsin (UTF-8 olduğundan emin ol)

## Referanslar

- [Python gettext documentation](https://docs.python.org/3/library/gettext.html)
- [Babel documentation](https://babel.pocoo.org/)
- [.po file format](https://www.gnu.org/software/gettext/manual/html_node/PO-Files.html)
