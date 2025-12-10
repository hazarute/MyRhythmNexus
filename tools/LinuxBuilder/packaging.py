from pathlib import Path
import shutil
import tempfile
import re
import importlib.util

# Load sibling ci_io module without relying on package imports
ci_io_path = Path(__file__).resolve().parent / 'ci_io.py'
spec = importlib.util.spec_from_file_location('linuxbuilder.ci_io', str(ci_io_path))
ci_io = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci_io)
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
from typing import Optional, Tuple


def _make_zip(workdir: Path, zip_path: Path) -> None:
    with ZipFile(zip_path, 'w', ZIP_DEFLATED) as z:
        for p in sorted(workdir.rglob('*')):
            arcname = p.relative_to(workdir)
            z.write(p, arcname)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def write_customer_config(path: Path, backend_url: str, license_server_url: Optional[str] = None) -> None:
    cfg = {"backend_urls": [backend_url], "settings": {"theme": "dark"}}
    if license_server_url:
        cfg["license_server_url"] = license_server_url
        cfg["LICENSE_SERVER_URL"] = license_server_url
    txt = (import_json := __import__('json')).dumps(cfg, indent=2) + "\n"
    ci_io.write_text_lf(path, txt)


def write_install_sh_only(workdir: Path, exe_name: str, version: Optional[str] = None) -> None:
    desktop_name = f"MyRhythmNexus{('_v' + version) if version else ''}"
    desktop_file = desktop_name + ".desktop"
    sh = (
        "#!/bin/sh\n"
        "APPDIR=${XDG_CONFIG_HOME:-$HOME/.config}/MyRhythmNexus\n"
        "mkdir -p \"$APPDIR\"\n"
        f"cp \"$(dirname \"$0\")/{exe_name}\" \"$APPDIR/{exe_name}\"\n"
        "cp \"$(dirname \"$0\")/config.json\" \"$APPDIR/config.json\"\n"
        "echo 'Kurulum tamamlandi.'\n"
        "DESKTOP_DIR=$(xdg-user-dir DESKTOP 2>/dev/null || echo \"$HOME/Desktop\")\n"
        "mkdir -p \"$DESKTOP_DIR\"\n"
        f"cat > \"$DESKTOP_DIR/{desktop_file}\" <<'EOF'\n"
        f"[Desktop Entry]\n"
        f"Name={desktop_name}\n"
        f"Exec=$APPDIR/{exe_name}\n"
        f"Type=Application\n"
        f"Terminal=false\n"
        f"Icon=\n"
        "EOF\n"
        f"chmod +x \"$DESKTOP_DIR/{desktop_file}\"\n"
        f"echo 'Masaustu kisayolu olusturuldu:' \"$DESKTOP_DIR/{desktop_file}\"\n"
    )
    path = workdir / 'install.sh'
    ci_io.write_text_lf(path, sh, mode=0o755)


def create_customer_package(exe_for_package: Path, backend_url: str, customer: str, out_dir: Path, license_server: Optional[str] = None, product: str = 'MyRhythmNexus') -> Tuple[Path, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_name = f"{product}-{customer}.zip"
    zip_path = out_dir / zip_name
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        exe_name = exe_for_package.name
        shutil.copy2(exe_for_package, workdir / exe_name)
        ver = None
        m = re.search(r'_v([0-9]+(?:\.[0-9]+)*)', exe_name)
        if m:
            ver = m.group(1)
        write_customer_config(workdir / 'config.json', backend_url, license_server)
        write_install_sh_only(workdir, exe_name, version=ver)

        # normalize
        ci_io.normalize_crlf_in_dir(workdir)

        _make_zip(workdir, zip_path)

    digest = _sha256_file(zip_path)
    (zip_path.with_suffix(zip_path.suffix + '.sha256')).write_text(digest, encoding='ascii')
    return zip_path, digest
