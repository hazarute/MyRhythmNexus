**Paketleme & Dağıtım (Müşteri-özel config)**

- **Amaç:** Masaüstü uygulamasını tek bir `.exe` olarak derliyorsunuz; müşteriye özel `config.json` dosyası ile birlikte dağıtım amacıyla ZIP/installer paketleri oluşturmak.
- **Not:** `config.json` içine SADECE non-sensitive ayarlar koyun (ör. `backend_url`, `license_server_url`, UI tercihi). DB parolası, private keys veya `SECRET_KEY` kesinlikle konmamalıdır.

1) Seçenekler
  - Per-customer EXE (gömülü config): her müşteri için ayrı build. Yönetmesi zor ve yeniden paketleme gerektirir.
  - EXE + ayrı `config.json` (bu repo'da desteklenen yöntem): tek `.exe` + müşteri-özel `config.json` ve `install` yardımcıları. Bu yöntemi kullanıyoruz.
  - First-run provisioning: tek `.exe`, ilk açılışta provisioning endpoint'ten config alır (merkezi yönetim). Daha ileri bir opsiyon.

2) Dosya yerleşimi (müşteri PC)
  - Windows (önerilen): `%APPDATA%\MyRhythmNexus\config.json`
  - Linux/macOS: `$XDG_CONFIG_HOME/MyRhythmNexus/config.json` veya `~/.config/MyRhythmNexus/config.json`

3) Araçlar (repo içinde)
  - `tools/package_customer.py` — Cross-platform, Python tabanlı paketleyici. Girdi: `--exe-path`, `--backend-url`, `--customer`, `--output-dir`.
  - `tools/package_customer.ps1` — PowerShell versiyonu (Windows CI veya yerel Windows kullanımı için).
  - `.github/workflows/package_release.yml` — Örnek workflow (Windows runner + PowerShell). İsterseniz workflow'u Python packager ile değiştirebilirim.

4) Hızlı kullanım örnekleri

  - Python paketi ile (lokal makine):
    ```powershell
    python tools\package_customer.py --exe-path dist\MyRhythmNexus.exe \
      --backend-url "https://acme.example.com/api/v1" --customer acme --output-dir release \
      --license-server-url "https://license.mycompany.com/api/v1"
    ```

  - PowerShell paketi ile (Windows):
    ```powershell
    .\tools\package_customer.ps1 -ExePath "dist\MyRhythmNexus.exe" -BackendUrl "https://acme.example.com/api/v1" -CustomerName "acme" -OutputDir "release"
    ```

5) Çıktılar
  - `release/MyRhythmNexus-<customer>.zip`
  - `release/MyRhythmNexus-<customer>.zip.sha256`
  - ZIP içinde: `MyRhythmNexus.exe`, `config.json`, `install.bat`, `install.sh` (opsiyonel)

6) Güvenlik önerileri
  - `config.json` içindeki hassas bilgileri önlemek: sadece `backend_url` vb. koyun.
  - Paketleri transfer ederken güvenli kanallar (SFTP, secure portal) kullanın. Eğer e-posta kullanılacaksa arşivi parola ile şifreleyin ve parolayı ayrı kanaldan gönderin.
  - EXE/installer için code-signing yapın (Windows SmartScreen uyarılarını azaltır).
  - Paketlerin SHA256 checksum'unu verin; alıcı checksum'u kontrol etsin.

7) Öneriler
  - Küçük/orta ölçekte: bu `EXE + config.json` yöntemi iyi çalışır.
  - Daha ölçekli / merkezi kontrol istiyorsanız: `first-run provisioning` (benim önerim) ile tek bir EXE dağıtıp sunucu üzerinden config sağlayın.
