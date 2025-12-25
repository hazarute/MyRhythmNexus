#!/usr/bin/env python3
"""
Windows-only packager for per-customer distribution.

Usage:
    python tools/package_customer_windows.py --exe-path dist/MyRhythmNexus.exe --backend-url https://acme.example.com/api/v1 --customer acme --output-dir release

Produces: release/MyRhythmNexus-acme.zip and .sha256
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import subprocess
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def write_config(path: Path, backend_url: str, license_server_url: str | None = None) -> None:
    cfg = {"backend_urls": [backend_url], "settings": {"theme": "dark"}}
    if license_server_url:
        cfg["license_server_url"] = license_server_url
        cfg["LICENSE_SERVER_URL"] = license_server_url
    path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def write_install_files(workdir: Path, exe_name: str) -> None:
    # Windows install.bat
    bat = (
        "@echo off\n"
        "setlocal\n"
        "set APPDIR=%APPDATA%\\MyRhythmNexus\n"
        "if not exist \"%APPDIR%\" mkdir \"%APPDIR%\"\n"
        f"copy \"%~dp0\\{exe_name}\" \"%APPDIR%\\{exe_name}\" /Y\n"
        "copy \"%~dp0\\config.json\" \"%APPDIR%\\config.json\" /Y\n"
        "echo Kurulum tamamlandi. Uygulamayi baslatmak icin exe'yi calistirin.\n"
        "pause\n"
        "endlocal\n"
    )
    (workdir / "install.bat").write_text(bat, encoding="ascii")


def make_zip(workdir: Path, zip_path: Path) -> None:
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as z:
        for p in sorted(workdir.rglob("*")):
            arcname = p.relative_to(workdir)
            z.write(p, arcname)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def remove_zone_identifier(path: Path) -> None:
    """
    Remove the Windows Zone.Identifier alternate data stream if present; no-op on non-Windows.
    """
    if os.name != "nt":
        return
    try:
        ads = str(path) + ":Zone.Identifier"
        if Path(ads).exists():
            os.remove(ads)
    except Exception:
        pass


def set_file_attributes(path: Path) -> None:
    """
    Set sane file permissions for Windows: clear read-only bit.
    """
    try:
        if os.name == "nt":
            os.chmod(path, 0o644)
    except Exception:
        pass


def add_unblock_script(workdir: Path) -> None:
    """
    Add helper scripts to unblock files on Windows (PowerShell and batch).
    """
    bat = (
        "@echo off\n"
        "REM Recursively unblock files using PowerShell\n"
        "powershell -NoProfile -Command \"Get-ChildItem -Path '%~dp0' -Recurse -Force | Unblock-File -ErrorAction SilentlyContinue\"\n"
        "echo Unblock complete.\n"
    )
    (workdir / "Unblock-Files.bat").write_text(bat, encoding="ascii")

    ps1 = (
        "# Unblock files in this folder and subfolders\n"
        "Get-ChildItem -Path $PSScriptRoot -Recurse -Force | Unblock-File -ErrorAction SilentlyContinue\n"
        "Write-Host 'Unblock complete.'\n"
    )
    (workdir / "Unblock-Files.ps1").write_text(ps1, encoding="utf-8")

    for fname in ("Unblock-Files.bat", "Unblock-Files.ps1"):
        try:
            set_file_attributes(workdir / fname)
        except Exception:
            pass


def package_windows(exe_path: Path, backend_url: str, customer: str, output_dir: Path, license_server_url: str | None = None) -> Path:
    if not exe_path.exists():
        raise FileNotFoundError(f"Exe not found: {exe_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    product = "MyRhythmNexus"
    zip_name = f"{product}-{customer}-windows.zip"
    zip_path = output_dir / zip_name

    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        exe_name = exe_path.name

        # Copy EXE and clean ADS
        shutil.copy2(exe_path, workdir / exe_name)
        remove_zone_identifier(workdir / exe_name)
        set_file_attributes(workdir / exe_name)

        # Config
        write_config(workdir / "config.json", backend_url, license_server_url)

        # Install files
        write_install_files(workdir, exe_name)
        remove_zone_identifier(workdir / "install.bat")
        set_file_attributes(workdir / "install.bat")

        # Unblock scripts
        add_unblock_script(workdir)

        # README for Windows users (Turkish instructions)
        readme = """# MyRhythmNexus Kurulum Talimatları (Türkçe)

    ## ADIM 1: ZIP Dosyasını Ayıkla
    1. ZIP dosyasını sağ tıklayın
    2. "Tümünü ayıkla" seçeneğini tıklayın
    3. Bir klasöre ayıklayın

    ## ADIM 2: Güvenlik Engelini Kaldır (ÖNEMLİ!)
    1. Ayıklanan klasöre gidin
    2. Unblock-Files.bat dosyasını **sağ tıklayın**
    3. "Yönetici olarak çalıştır" seçeneğini tıklayın
    4. Çıkan siyah pencerede herhangi bir tuşa basın

    ## ADIM 3: Kurulumu Tamamla
    1. install.bat dosyasını çalıştırın
    2. Kurulum tamamlandığında program otomatik başlayacaktır

    ## SIK SORULAN SORULAR:
    ❓ **"Windows bu uygulamanın çalıştırılmasını engelledi" hatası alıyorum**
    → Lütfen ADIM 2'yi tekrar uygulayın

    ❓ **Yönetici izni istiyor**
    → Windows'ta herhangi bir program kurarken yönetici izni normaldir
    """
        (workdir / "README.txt").write_text(readme, encoding="utf-8")

        # Create ZIP
        make_zip(workdir, zip_path)

    # Checksum
    digest = sha256_file(zip_path)
    (zip_path.with_suffix(zip_path.suffix + ".sha256")).write_text(digest, encoding="ascii")

    # Remove ADS on ZIP file
    if os.name == 'nt':
        remove_zone_identifier(zip_path)

    return zip_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe-path")
    parser.add_argument("--backend-url")
    parser.add_argument("--customer")
    parser.add_argument("--output-dir", default="release")
    parser.add_argument("--license-server-url", default=None,
                        help="License server URL; can also be provided via LICENSE_SERVER_URL env var")
    parser.add_argument("--interactive", action="store_true",
                        help="Force interactive prompts even if flags are provided")
    parser.add_argument("--build", action="store_true",
                        help="Run build-desktop.bat (Windows) before packaging and use produced EXE if --exe-path not given")
    args = parser.parse_args(argv)

    license_server = args.license_server_url or os.environ.get("LICENSE_SERVER_URL")

    def prompt_nonempty(prompt_text: str, default: str | None = None) -> str:
        while True:
            if default:
                resp = input(f"{prompt_text} [{default}]: ").strip()
                if not resp:
                    resp = default
            else:
                resp = input(f"{prompt_text}: ").strip()
            if resp:
                return resp

    def prompt_exe_path(initial: str | None = None) -> Path:
        while True:
            prompt = f"Path to EXE{(' ['+initial+']' if initial else '')}: "
            p = input(prompt).strip()
            if not p and initial:
                p = initial
            if not p:
                print("Please specify the path to the EXE.")
                continue
            p = p.strip('"')
            ppath = Path(p)
            if not ppath.exists():
                print(f"File not found: {ppath}")
                cont = input("Try again? [Y/n]: ").strip().lower()
                if cont in ("n", "no"):
                    raise SystemExit(2)
                continue
            return ppath

    if args.build:
        try:
            if os.name == "nt" and Path("build-desktop.bat").exists():
                print("Running build-desktop.bat...")
                subprocess.run(["cmd", "/c", "build-desktop.bat"], check=True)
            else:
                print("No Windows build script found (build-desktop.bat). Skipping build.")
        except subprocess.CalledProcessError as e:
            print(f"Build script failed: {e}", file=sys.stderr)
            return 2

    if args.interactive or not (args.exe_path and args.backend_url and args.customer):
        print("Interactive packaging mode — provide details below.")
        exe_initial = args.exe_path
        if args.build and not exe_initial:
            candidates = []
            d = Path("dist")
            if d.exists():
                for p in sorted(d.iterdir()):
                    if p.is_file() and p.name.startswith("MyRhythmNexus"):
                        candidates.append(p)
                if not candidates:
                    candidates = [p for p in sorted(d.iterdir()) if p.is_file()]
            if candidates:
                exe_initial = str(candidates[0])
                print(f"Auto-detected built artifact: {exe_initial}")

        exe = prompt_exe_path(exe_initial)
        backend = prompt_nonempty("Backend URL (e.g. https://acme.example.com/api/v1)", args.backend_url)
        customer = prompt_nonempty("Customer short name (used in package filename)", args.customer)
        out_dir = input(f"Output directory [{args.output_dir}]: ").strip() or args.output_dir
        out = Path(out_dir)
        ls_default = license_server or None
        ls = input(f"License server URL (optional){(' ['+ls_default+']' if ls_default else '')}: ").strip()
        if not ls and ls_default:
            ls = ls_default
        print("\nSummary:")
        print(f"  EXE: {exe}")
        print(f"  Backend URL: {backend}")
        print(f"  Customer: {customer}")
        print(f"  Output dir: {out}")
        print(f"  License server: {ls or '<none>'}")
        ok = input("Proceed? [Y/n]: ").strip().lower()
        if ok in ("n", "no"):
            print("Aborted by user.")
            return 2
        try:
            zip_path = package_windows(exe, backend, customer, out, ls or None)
            print(f"Created: {zip_path}")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
    else:
        exe_path_arg = args.exe_path
        if args.build and not exe_path_arg:
            candidates = []
            d = Path("dist")
            if d.exists():
                for p in sorted(d.iterdir()):
                    if p.is_file() and p.name.startswith("MyRhythmNexus"):
                        candidates.append(p)
                if not candidates:
                    candidates = [p for p in sorted(d.iterdir()) if p.is_file()]
            if candidates:
                exe_path_arg = str(candidates[0])
                print(f"Auto-detected built artifact: {exe_path_arg}")

        exe = Path(exe_path_arg)
        out = Path(args.output_dir)
        try:
            zip_path = package_windows(exe, args.backend_url, args.customer, out, license_server)
            print(f"Created: {zip_path}")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2


if __name__ == "__main__":
    raise SystemExit(main())
