# MyRhythmNexus - Deployment Guide

Bu kılavuz, MyRhythmNexus uygulamasının production ortamına dağıtımını açıklar.

## 🏗️ Sistem Mimarisi

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Desktop App   │    │     Mobile      │
│   (Members)     │    │   (Staff)       │    │   (Future)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────────────┐
                    │   Backend API      │
                    │   (FastAPI)        │
                    └────────────────────┘
                             │
                    ┌────────────────────┐
                    │   PostgreSQL DB    │
                    └────────────────────┘
```

## 🚀 Hızlı Başlangıç

### 1. Sunucu Kurulumu (Backend + Web UI)

```bash
# .env dosyasını düzenleyin
cp .env.example .env
nano .env  # Production ayarlarını girin

# Deploy edin
./deploy.sh server
```

### 2. Desktop App Kurulumu

```bash
# Executable oluşturun
./deploy.sh desktop

# Oluşan executable'ı kullanıcılara dağıtın
# dist/MyRhythmNexus-Desktop.exe
```

## 📋 Gereksinimler

### Sunucu Gereksinimleri
- Docker & Docker Compose
- Linux/Windows/macOS
- 2GB RAM minimum
- 10GB disk space

### Desktop Gereksinimleri
- Python 3.13+
- PyInstaller
- Windows/macOS/Linux

## ⚙️ Yapılandırma

### Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Security
SECRET_KEY=your-very-long-random-secret-key

# CORS - Desktop app için gerekli
CORS_ORIGINS=["https://yourdomain.com", "http://localhost:3000"]

# Environment
ENVIRONMENT=production

# Admin
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=secure-password
```

### Desktop App Yapılandırması

Desktop app, backend URL'sini otomatik olarak config'den okur:

```python
# desktop/core/config.py
BACKEND_URL = os.getenv("RHYTHM_NEXUS_BACKEND_URL", "http://localhost:8000")
```

Production'da değiştirmek için:
```bash
# Environment variable
export RHYTHM_NEXUS_BACKEND_URL="https://api.yourdomain.com"

# Veya config dosyası
echo '{"backend_url": "https://api.yourdomain.com"}' > ~/.rhythm-nexus/config.json
```

## 🐳 Docker Deployment

### Services

1. **db** - PostgreSQL 15
2. **backend** - FastAPI application
3. **web** - Nginx (static files + reverse proxy)

### Komutlar

```bash
# Başlat
docker-compose up -d

# Log'ları gör
docker-compose logs -f

# Durdur
docker-compose down

# Yeniden build
docker-compose up -d --build
```

## 🖥️ Desktop App Distribution

### PyInstaller ile Build

```bash
# Gereksinimler
pip install pyinstaller

# Build et
pyinstaller desktop.spec

# Çıktı: dist/MyRhythmNexus-Desktop.exe
```

### Dağıtım Seçenekleri

1. **Direct Download**: Executable'ı web sunucunuzdan indirilebilir yapın
2. **Installer**: NSIS/Inno Setup ile installer oluşturun
3. **Auto-Update**: Electron-builder benzeri auto-update sistemi ekleyin

## 🔒 Güvenlik

### Production Checklist

- [ ] SECRET_KEY değiştirildi
- [ ] Database credentials değiştirildi
- [ ] CORS_ORIGINS production domain ile güncellendi
- [ ] HTTPS enabled
- [ ] Firewall yapılandırıldı
- [ ] Database backups ayarlandı
- [ ] Monitoring/logging aktif

### HTTPS Kurulumu

```nginx
# nginx.conf için SSL yapılandırması
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # ... diğer ayarlar
}
```

## 📊 Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/

# Web health
curl http://localhost/health

# Database health
docker-compose exec db pg_isready -U postgres
```

### Logs

```bash
# Tüm servis logları
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

## 🆘 Troubleshooting

### Common Issues

1. **Port Conflict**: 8000/80 portları kullanımda
   ```bash
   # Port değiştirin docker-compose.yml'de
   ports: ["8080:8000"]
   ```

2. **Database Connection**: Bağlantı hatası
   ```bash
   # .env dosyasını kontrol edin
   # Docker network'ü kontrol edin
   docker-compose exec backend python -c "import backend.core.database; print('OK')"
   ```

3. **CORS Issues**: Desktop app bağlanamıyor
   ```bash
   # CORS_ORIGINS'a desktop app'in origin'ini ekleyin
   CORS_ORIGINS=["https://yourdomain.com", "app://rhythm-nexus"]
   ```

## 📞 Support

Sorularınız için issue açın veya dokümantasyonu kontrol edin.