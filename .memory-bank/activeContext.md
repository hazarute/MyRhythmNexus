# Aktif Bağlam

## 🎯 Şu Anki Odak
**ULUSLARARASILAŞTIRMA (i18n) - MASAÜSTÜ UYGULAMASINA ÇOKLU DİL DESTEĞİ EKLEME**

## ✅ Önceki Tamamlanan Özellikler
**SATIŞ FORMUNDA MANUEL FİYAT OVERRIDE ÖZELLİĞİ TAMAMLANDI - ADMİNLER İNDİRİM UYGULAYABİLİR**

### Teknik Bileşenler (Faz 19)
| Bileşen | Dosya | Durum |
|---------|-------|-------|
| Backend Schema | backend/schemas/sales.py | ✅ purchase_price_override alanı eklendi |
| API Endpoint | backend/api/v1/sales.py | ✅ Validation logic (pozitif fiyat, max 2x limit) |
| Desktop UI | desktop/ui/views/tabs/sales_pos_tab.py | ✅ Checkbox + input field + toggle logic |
| Submission Handler | desktop/ui/components/salespostab/submission_handler.py | ✅ Payload'a override ekleme |
| Test Suite | tests/test_subscription_lifecycle.py | ✅ 5 test senaryosu - tümü başarılı |

## 🔄 Yeni Odak: Uluslararasılaştırma (i18n)

### Problem (Çözülecek ✅)
- Masaüstü uygulama şu anda sadece Türkçe destekliyor
- Global erişim için İngilizce desteği gerekli
- Kullanıcı deneyimi iyileştirmesi olarak çoklu dil desteği

### Çözüm: Gettext Tabanlı i18n Sistemi
- **Pattern:** Python gettext modülü + _() wrapper fonksiyonu
- **Teknik:** locale/{lang}/LC_MESSAGES/ yapısı + .po/.mo dosyaları
- **UI/UX:** Uygulama başlangıcında dil seçimi + ayarlar menüsünde dil değiştirme

### Teknik Bileşenler (Faz 20)
| Bileşen | Görev | Durum |
|---------|-------|-------|
| Gettext Altyapısı | locale klasörü ve temel yapılar | ⏳ Planlandı |
| Çeviri Wrapper | _() fonksiyonu oluşturma | ⏳ Planlandı |
| UI Metinleri | Tüm desktop metinlerini _() ile sarmak | ⏳ Planlandı |
| .po Dosyaları | tr.po ve en.po oluşturma | ⏳ Planlandı |
| Türkçe Çeviriler | Mevcut metinlerin .po'ya aktarılması | ⏳ Planlandı |
| İngilizce Çeviriler | Tüm metinlerin İngilizce çevirisi | ⏳ Planlandı |
| .mo Derleme | Çeviri dosyalarının derlenmesi | ⏳ Planlandı |
| Locale Yönetimi | Config ve uygulama başlatma | ⏳ Planlandı |
| Dil Seçimi UI | Ayarlar menüsüne dil seçici | ⏳ Planlandı |
| Testler | Dil değiştirme ve doğrulama | ⏳ Planlandı |
| Dokümantasyon | i18n kullanım kılavuzu | ⏳ Planlandı |

### Yapılacak Düzeltmeler
- Desktop uygulamasının tüm metinlerini uluslararasılaştırma fonksiyonları ile sarmak
- Türkçe ve İngilizce çeviri dosyaları oluşturmak
- Kullanıcı dil tercihini konfigüre etme ve uygulama başlatmada yükleme
- Dil değiştirme seçeneği ekleme
- Test senaryoları ile doğrulama

## 📊 Proje Durum
- **Backend:** FastAPI, Auth, CRM, Satış, QR sistemi, Otomatik Aktivite Yönetimi, Üye Filtreleme, Async Relationship Loading, Hard Delete tamamlandı.
- **Desktop UI:** Login, Dashboard, Üye Yönetimi, Satış POS, Scheduler, Check-in, Otomatik Güncelleme Sistemi tamamlandı.
- **Deployment:** Docker containerized deployment, production-ready yapılandırma, CI/CD pipeline tamamlandı.
- **Sistem Özellikleri:** Kart Sistemi, Access Type, ClassEvent, Booking, CheckIn, Otomatik Pasif Üye Yönetimi, Aktif Üye Filtreleme, Async API Stability, Hard Delete, Otomatik Masaüstü Güncellemeleri, Containerized Production Deployment entegre.
- **Yeni Özellik:** Çoklu dil desteği (Türkçe/İngilizce) - geliştirme aşamasında.

## 🚀 Sıradaki Adım
**FAZ 20: ULUSLARARASILAŞTIRMA (i18n)** - Masaüstü uygulamasına gettext tabanlı çoklu dil desteği ekleme süreci başlayacak.

## 📝 Teknik Referans
- **Özellik:** Masaüstü uygulama uluslararasılaştırma sistemi
- **Çözüm:** Python gettext + locale yapısı + _() wrapper fonksiyonu
- **Pattern:** Uygulama başlatma sırasında locale ayarı + kullanıcı dil seçimi
- **Değiştirilecek Dosyalar:** Tüm desktop/ui/ dosyaları + yeni locale/ klasörü + config güncellemeleri



