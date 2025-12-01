# Masaüstü Uygulama Otomatik Güncelleme Sistemi

Bu dokümantasyon, MyRhythmNexus masaüstü uygulamasının otomatik güncelleme sisteminin kurulum ve kullanımını açıklamaktadır.

## 🚀 Özellikler

- **Otomatik Güncelleme Kontrolü**: Uygulama başlatılırken otomatik olarak yeni sürümler kontrol edilir
- **GitHub Releases Entegrasyonu**: Güncellemeler GitHub Releases üzerinden dağıtılır
- **Kullanıcı Dostu Arayüz**: Güncelleme dialog'u ile kullanıcı deneyimi
- **Güvenli Güncelleme**: Yedekleme ve geri dönüş mekanizması
- **Otomatik Dağıtım**: CI/CD pipeline ile otomatik release oluşturma

## 📋 Gereksinimler

### Geliştirme Ortamı
- Python 3.8+
- PyInstaller
- GitHub CLI (gh)
- requests kütüphanesi

### GitHub Repository
- Public veya private GitHub repository
- GitHub CLI ile authentication
- Releases oluşturma yetkisi

## ⚙️ Kurulum

### 1. GitHub Repository Ayarları

```bash
# GitHub CLI ile giriş yapın
gh auth login

# Repository'yi ayarlayın (varsayılan branch main)
gh repo set-default your-username/MyRhythmNexus
```

### 2. Updater Modülünü Yapılandırma

`desktop/core/updater.py` dosyasındaki `GITHUB_REPO` değişkenini güncelleyin:

```python
GITHUB_REPO = "your-username/MyRhythmNexus"  # Gerçek repo adınız
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

## 🔄 Kullanım

### Manuel Build ve Release

```bash
# Sadece masaüstü uygulamasını build et
./deploy.sh desktop

# Build et ve GitHub release oluştur (otomatik versiyon)
./deploy.sh release

# Belirli versiyon ile release oluştur
VERSION=v1.2.3 ./deploy.sh release
```

### Otomatik Güncelleme Akışı

1. **Uygulama Başlatma**: Kullanıcı uygulamayı başlattığında `check_and_update_on_startup()` çağrılır
2. **Versiyon Kontrolü**: GitHub API üzerinden en son release kontrol edilir
3. **Güncelleme Dialog'u**: Yeni sürüm varsa kullanıcıya gösterilir
4. **İndirme ve Yükleme**: Kullanıcı onaylarsa otomatik indirme ve yükleme yapılır
5. **Yeniden Başlatma**: Güncelleme sonrası uygulama yeniden başlatılır

### CI/CD Entegrasyonu (GitHub Actions)

`.github/workflows/release.yml` dosyası oluşturun:

```yaml
name: Release Desktop App

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: windows-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Build and release
      run: ./deploy.sh release
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## 🔧 Yapılandırma

### Updater Ayarları

`desktop/core/updater.py` dosyasında aşağıdaki ayarları yapabilirsiniz:

```python
# Kontrol sıklığı (saniye) - varsayılan 24 saat
CHECK_INTERVAL = 86400

# GitHub API timeout (saniye)
API_TIMEOUT = 10

# Geçici dosya uzantısı
TEMP_SUFFIX = '.exe'
```

### Sürüm Dosyası

Uygulama, sürüm bilgilerini `~/.rhythm-nexus/version.json` dosyasında saklar:

```json
{
  "version": "1.2.3",
  "installed": true,
  "last_check": 1703123456.789,
  "updated_at": "1703123456.789"
}
```

## 🛠️ Sorun Giderme

### Yaygın Problemler

1. **GitHub CLI Authentication Hatası**
   ```bash
   gh auth login
   gh auth status
   ```

2. **Release Oluşturma Hatası**
   - Repository yetkilerini kontrol edin
   - GitHub CLI'nin güncel olduğundan emin olun

3. **Güncelleme Kontrolü Çalışmıyor**
   - İnternet bağlantısını kontrol edin
   - GitHub API limitlerini kontrol edin
   - Firewall ayarlarını kontrol edin

4. **İndirme Hatası**
   - Release assets'inin doğru adlandırıldığından emin olun
   - Dosya izinlerini kontrol edin

### Log Dosyaları

Uygulama logları `~/.rhythm-nexus/app.log` dosyasında bulunur.

### Manuel Güncelleme

Otomatik sistem çalışmıyorsa:

1. GitHub Releases sayfasından en son `.exe` dosyasını indirin
2. Mevcut uygulamayı kapatın
3. Yeni dosyayı eski dosyanın üzerine kopyalayın
4. Uygulamayı yeniden başlatın

## 📊 İzleme ve Bakım

### Güncelleme İstatistikleri

GitHub Releases sayfasından:
- İndirme sayıları
- Kullanıcı geri bildirimleri
- Hata raporları

### Düzenli Bakım

- Haftalık olarak yeni sürümler kontrolü
- Aylık olarak bağımlılık güncellemeleri
- Çeyrek dönemlerde major version güncellemeleri

## 🔒 Güvenlik

- Tüm güncellemeler GitHub Releases üzerinden dağıtılır
- Otomatik güncellemeler için kullanıcı onayı gerekir
- Eski sürümler yedeklenir (`.backup` uzantısı)
- İndirilen dosyalar doğrulanır

## 📝 Sürüm Notları

### v1.0.0
- İlk otomatik güncelleme sistemi
- GitHub Releases entegrasyonu
- Kullanıcı dostu güncelleme dialog'u
- Güvenli güncelleme mekanizması