# Aktif Bağlam

## Yeni Odak
- **Desktop Updater İyileştirmeleri:** Linux ortamında yanlış güncelleme algılama sorunu çözüldü. Kod modüler hale getirildi (UpdateManager, UpdateDialog). ConfigManager silinerek ana config.py yapısına entegre edildi.
- **i18n Temizliği:** Çeviri dosyaları (messages.po) normalize edildi ve tutarsızlıklar giderildi.
- **CI/CD:** Linux build scripti (ci_build_and_release_linux.py) GitHub token hatası için düzeltildi.

## Teknik Bağlam
- **Mevcut Durum:** Desktop uygulaması stabilizasyon aşamasında. Updater mantığı platforma özgü hale getirildi ve SRP'ye uygun olarak yeniden yazıldı. Konfigürasyon yönetimi tek merkezde (desktop/core/config.py) toplandı.
- **Yeni Hedef:** Production ortamına hazırlık ve son testler.
- **Teknoloji:** Python, CustomTkinter, GitHub Releases API.

## Tamamlanan Özellikler
- **Updater Refactoring:** updater.py parçalandı.
    - desktop/services/update_manager.py: Güncelleme mantığı (Linux fix dahil).
    - desktop/ui/views/dialogs/update_dialog.py: Güncelleme arayüzü.
    - desktop/core/updater.py: Facade olarak korundu, config.py kullanıyor.
    - **Silinen:** desktop/core/config_manager.py (Gereksiz tekrar önlendi).
- **i18n Cleanup:** 	ools/fix_po_equal.py ile tüm çeviri tutarsızlıkları giderildi.
- **CI Fix:** Linux release scripti token yönetimi iyileştirildi.

## Problemler
- updater.py dosyası SRP (Single Responsibility Principle) ihlali yapıyordu; çözüldü.

## Çözüm
- updater.py refactoring tamamlandı.

## Proje Durum
- **Backend:** FastAPI, Auth, CRM, Satış, QR/Check-in hazır.
- **Desktop UI:** Login, Dashboard, Üye Yönetimi, Satış POS, Scheduler, Check-in ve otomatik güncelleme modülleri aktif.
- **Deployment:** Docker containerlar, production-ready konfigürasyon ve CI/CD pipeline tamamlandı.
