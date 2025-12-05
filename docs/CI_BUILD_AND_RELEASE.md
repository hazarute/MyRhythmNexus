**CI Build & Release**

Bu doküman `tools/ci_build_and_release.py` script'inin nasıl kullanılacağını, hangi ortam değişkenlerinin gerektiğini, interaktif mod ve hata ayıklama ipuçlarını açıklar. Aşağıdaki adımlar lokal (Windows) build ve GitHub Release otomasyonu içindir.

**Amaç**
- Masaüstü uygulamasını build etmek (isteğe bağlı), üretilen `.exe` dosyasını `release/` klasörüne koymak ve GitHub Releases içine yüklemek.

**Önkoşullar**
- Python 3.8+
- `requests` paketi (GitHub upload için): `pip install requests`
- PyInstaller ve build bağımlılıkları (Windows build için)
- Depo kökünde `build-desktop.bat` (Windows) veya `build-desktop.sh` (Unix) bulunmalı
- GitHub üzerinde release oluşturma yetkisi olan token (`GITHUB_TOKEN`)

**Nasıl çalışır**
- Script sürümü `desktop/core/config.py` içindeki `DesktopConfig.VERSION` satırından otomatik alır (veya `--version` ile verirsiniz).
- `--no-build` verilmezse önce build script çalıştırılır.
- `dist/` içindeki üretilen `.exe` bulunur ve `release/MyRhythmNexus_v{version}.exe` olarak kopyalanır.
- Eğer `GITHUB_TOKEN` sağlanmışsa (`--token` veya `GITHUB_TOKEN` env), tag olarak `v{version}` ile release oluşturulur ve exe upload edilir.

**Kullanım Örnekleri**
- Tam otomatik (Windows lokal, önce build çalıştırır):
```powershell
$env:VERSION = "1.2.3"
$env:GITHUB_TOKEN = "ghp_..."
python tools\ci_build_and_release.py
```

- Sadece paketle (mevcut exe'yi kullan, build etme):
```powershell
python tools\ci_build_and_release.py --no-build --version 1.2.3
```

- İnteraktif (adım adım sorar):
```powershell
python tools\ci_build_and_release.py --interactive
```

**Parametreler**
- `--repo`: GitHub repo (varsayılan `hazarute/MyRhythmNexus`)
- `--token`: GitHub token (veya `GITHUB_TOKEN` env)
- `--no-build`: Build adımını atlar
- `--version`: Yayınlanacak sürüm numarası
- `--dry-run`: GitHub çağrısı yapmaz (test)
- `--interactive`: Eksik parametreleri sorar

**Gerekli token izinleri**
- Token `repo` (veya release yazma yetkisi) içermeli. GitHub Actions ortamında `GITHUB_TOKEN` otomatik sağlanır.

**Railway / Linux notu**
- Windows `.exe` üretimi için genelde Windows runner (veya yerel Windows makine) daha güvenilirdir. Railway gibi Linux konteynerlarında Windows exe üretimi karmaşık olabilir. Bu yüzden:
  - Windows'ta build edip exe'yi artifact/paket olarak CI'ye koymak en sağlam yoldur.
  - Alternatif: GitHub Actions `runs-on: windows-latest` ile tam otomasyon kurmak daha pratiktir.

**Hata ayıklama & sık sorunlar**
- `build-desktop.bat`/`.sh` çalışmazsa: PyInstaller'ın ve bağımlılıkların kurulu olduğundan emin olun.
- `GITHUB_TOKEN` yoksa upload atlanır — script bunu uyarır.
- `dist/*.exe` bulunamazsa build başarısız oldu demektir; build çıktısını kontrol edin.
- Windows üzerinde updater/exe üzerine yazma kilitlenmesi olabilir; release sırasında kullanıcıya doğru installer/updater akışı sağlamanızı öneririz.

**İyi uygulamalar**
- `desktop/version.txt` veya `DesktopConfig.VERSION` ile sürümü eşleştirin.
- Release tag'ını `v{version}` formatında kullanın (ör. `v1.2.3`).
- CI otomasyonunda `VERSION` env var set ederek deterministic release sağlayın.

**Örnek GitHub Actions (özet)**
- İşin özü: `windows-latest` runner'a build adımını koyun, sonra `tools/ci_build_and_release.py --no-build --token ${{ secrets.GITHUB_TOKEN }} --version 1.2.3` çalıştırın (veya doğrudan upload adımını kullanın).

**GitHub Actions workflow & Secrets**
- Repo içine bir workflow (örneğin `.github/workflows/build_release_windows.yml`) ekleyerek otomasyonu tetikleyebilirsiniz. Bu repository içinde `workflow_dispatch` (elle tetikleme) veya `push` ile tag itme gibi tetikleyiciler tanımlanabilir. Bu repo'ya eklediğimiz örnek workflow Windows runner (`windows-latest`) üzerinde çalışır ve `secrets.GITHUB_TOKEN` kullanır.

-- Güvenlik önemli: GitHub tarafından rezerve edilmiş prefix'lerle başlayan secret isimleri (`GITHUB_...`) repo secrets olarak kullanılamaz veya çakışma yaratabilir. Bu yüzden kişisel erişim token'ınızı repo secret olarak eklerken `RELEASE_TOKEN` veya `PERSONAL_TOKEN` gibi bir isim kullanın. Eğer yanlışlıkla bir token paylaştıysanız hemen GitHub -> Settings -> Developer settings -> Personal access tokens alanından o token'ı iptal edin ve yeni token oluşturun; sonra GitHub repo ayarlarından `Settings -> Secrets and variables -> Actions -> New repository secret` bölümüne yeni secret'ı ekleyin.

- Workflow örneğimiz `secrets.RELEASE_TOKEN` kullanacak şekilde yapılandırıldı. (GitHub Actions ortamı ayrıca otomatik olarak `GITHUB_TOKEN` sağlar, ama kendi PAT'inizi yüklemek istiyorsanız `RELEASE_TOKEN` gibi farklı bir isim kullanın.)

**Kısa adımlar: token ekleme**
1. GitHub repository sayfanıza gidin
2. `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`
3. `Name`: `RELEASE_TOKEN`, `Value`: (PAT'nizi yapıştırın) -> `Add secret`

Not: Eğer token'ı yanlışlıkla paylaştıysanız (ör. sohbet), onu derhal iptal edin; bu iletişimde paylaştığınız token'ı kullanmayın ve bir yenisini oluşturun.
