**Release Automation & CI (per-customer packaging)**

Bu doküman, otomatik paketleme ve GitHub Actions örneğini açıklar.

1) Repo içindeki araçlar
  - `tools/package_customer.py` — Python ile per-customer ZIP üretir.
  - `tools/package_customer.ps1` — PowerShell muadili (Windows ortamında kullanılabilir).
  - `.github/workflows/package_release.yml` — Örnek workflow. `workflow_dispatch` ile manuel tetiklenir.

2) Örnek GitHub Actions akışı
  - Manual tetikleyin (`Actions` → `Package per-customer release`).
  - Input olarak `exe_path` (ör. `dist/MyRhythmNexus.exe`) ve `customers` (JSON array) verin.
  - Workflow Windows runner üzerinde PowerShell script çağırır ve `release/` içindeki artifact'leri upload eder.

3) Python tabanlı CI önerisi (opsiyonel değişiklik)
  - Eğer CI ortamınız Linux/Windows karışık ise, workflow'u Python packager kullanacak şekilde değiştirmek daha taşınabilir olur.
  - Örnek adımlar:
    - Checkout
    - Setup Python
    - Run `python -m pip install -r requirements.txt` (eğer paketleyicide ek paket varsa)
    - Run `python tools/package_customer.py --exe-path $EXE --backend-url $URL --customer $NAME --output-dir release`
    - Upload `release/` artifacts

4) Güvenlik ve otomasyon notları
  - CI ortamında *sensitive* secret'lar (e.g. code signing certificate password) GitHub Secrets olarak saklanmalıdır.
  - Eğer paketlere parola koyacaksanız parola yönetimini ayrı bir secret ile yapın.

5) Örnek `customers.json` (CI'da kullanılmak üzere)
```json
[{"name":"acme","backend":"https://acme.example.com/api/v1"}, {"name":"beta","backend":"https://beta.example.com/api/v1"}]
```

6) Sonraki adımlar
  - İsterseniz workflow'u Python packager ile güncelleyeceğim.
  - Ayrıca bir Inno Setup `.iss` şablonu ekleyip daha iyi UX (kısayol, uninstall) sağlayabilirim.
