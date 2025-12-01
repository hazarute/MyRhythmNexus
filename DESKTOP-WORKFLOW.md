# MyRhythmNexus Development Workflow

## 🖥️ Desktop App Development & Deployment

### Development Aşaması

#### 1. Kod Değişiklikleri
```bash
# Desktop kodunda değişiklik yapın
# Örnek: desktop/ui/views/members.py
```

#### 2. Development Test
```bash
# Python script'ini çalıştırarak test edin
python desktop/main.py

# Backend bağlantısını test edin
# (localhost:8000 çalışıyor olmalı)
```

#### 3. Build Production Executable
```bash
# Windows için:
build-desktop.bat

# Linux/Mac için:
./build-desktop.sh
```

#### 4. Test Executable
```bash
# Oluşan executable'ı test edin
dist/MyRhythmNexus-Desktop.exe

# Backend bağlantısını kontrol edin
# Login, CRUD operations test edin
```

#### 5. Distribute
```bash
# Executable'ı kullanıcılara dağıtın
# Email, download link, network share, etc.
```

## 🔄 Update Süreci

### Küçük Güncellemeler
1. **Kod değiştir** → `build-desktop.bat` → **Dağıt**
2. **Version numarasını güncelle**
3. **Changelog yaz**

### Büyük Güncellemeler
1. **Database migration varsa backend'i güncelle**
2. **API değişiklikleri varsa backend deploy et**
3. **Desktop app'i build et**
4. **Tüm kullanıcılara duyuru yap**

## 📋 Version Management

### Version Dosyası
```txt
# desktop/version.txt (otomatik oluşturulur)
MyRhythmNexus Desktop v1.0.0
Built: 2025-12-01 15:30:00
Git: abc1234
```

### Semantic Versioning
- **MAJOR**: Breaking changes (API değişti)
- **MINOR**: New features (yeni buton, bölüm)
- **PATCH**: Bug fixes (hata düzeltmeleri)

## 🚀 Deployment Strategies

### 1. Manual Distribution
```bash
# Her güncelleme sonrası:
1. build-desktop.bat çalıştır
2. dist/MyRhythmNexus-Desktop.exe dosyasını paylaş
3. Kullanıcılara "yeni versiyon indirin" de
```

### 2. Network Share (Şirket İçi)
```bash
# Şirket ağında paylaşılan klasör
\\company-server\apps\MyRhythmNexus\latest\MyRhythmNexus-Desktop.exe
```

### 3. Web Download (İleri Seviye)
```bash
# Web sunucunuzda download sayfası
https://yourdomain.com/download/desktop-app
```

### 4. Auto-Update (Gelecek Özellik)
```python
# Gelecekte eklenebilir
def check_for_updates():
    # Version kontrolü
    # Otomatik download
    # Silent update
```

## ⚙️ Build Optimization

### Build Süresi Azaltma
```bash
# --onedir ile klasör olarak build et (daha hızlı)
pyinstaller --onedir desktop/main.py

# Sadece değişen dosyaları yeniden build et
# (PyInstaller incremental build desteklemez)
```

### Executable Boyutu Azaltma
```bash
# Gereksiz modülleri exclude et
--exclude-module matplotlib
--exclude-module numpy  # eğer kullanılmıyorsa

# UPX compression
pyinstaller --upx-dir /path/to/upx desktop/main.py
```

## 🐛 Troubleshooting

### Build Hataları
```bash
# Hidden import eksik
--hidden-import eksik_modul

# Module not found
pip install eksik_paket
```

### Runtime Hataları
```bash
# Executable çalışmıyor
# Console mode ile debug et
pyinstaller --console desktop/main.py

# Log dosyası kontrol et
type ~/.rhythm-nexus/app.log
```

### Backend Bağlantı Problemi
```bash
# Config kontrol et
type ~/.rhythm-nexus/config.json

# Environment variable kontrol et
echo %RHYTHM_NEXUS_BACKEND_URL%
```

## 📊 Build Metrics

### Tipik Build Süreleri
- **İlk build**: 2-3 dakika
- **Incremental**: 1-2 dakika
- **Clean build**: 2-3 dakika

### Executable Boyutları
- **Minimum**: ~30MB (sadece temel bağımlılıklar)
- **Full**: ~50MB (tüm özellikler)
- **Compressed**: ~35MB (UPX ile)

## 🎯 Best Practices

1. **Her değişiklik sonrası test edin**
2. **Version numarasını güncelleyin**
3. **Changelog tutun**
4. **Backup alın**
5. **Kullanıcılara önceden haber verin**
6. **Rollback planı hazırlayın**