#!/usr/bin/env python3
"""Create a Studio installation ZIP containing:
 - the built Linux binary (single-file from PyInstaller)
 - a `config.json` (provided)
 - an `install.sh` that copies files to user locations and creates a .desktop launcher

Usage:
  python tools/create_studio_package.py --exe dist/MyRhythmNexus-Desktop --config release/config.json --customer studio --output release

The produced file is `release/MyRhythmNexus-studio.zip` and a `.sha256` checksum next to it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def make_install_sh(workdir: Path, exe_name: str, customer: str, icon_name: str | None = None) -> None:
    sh = []
    sh.append("#!/bin/sh")
    sh.append("set -e")
    sh.append("")
    sh.append("# installer for MyRhythmNexus (user-local, no sudo)")
    sh.append('APPDIR=${XDG_CONFIG_HOME:-$HOME/.config}/MyRhythmNexus')
    sh.append('mkdir -p "$APPDIR"')
    sh.append('THISDIR="$(cd "$(dirname "$0")" && pwd)"')
    sh.append('')
    sh.append(f'echo "Installing MyRhythmNexus ({customer})..."')
    sh.append(f'cp "$THISDIR/{exe_name}" "$APPDIR/{exe_name}"')
    sh.append(f'cp "$THISDIR/config.json" "$APPDIR/config.json"')
    if icon_name:
        sh.append(f'cp "$THISDIR/{icon_name}" "$APPDIR/{icon_name}"')
    sh.append(f'chmod +x "$APPDIR/{exe_name}"')
    sh.append('')
    sh.append('# Make a local bin and copy the executable for easy PATH usage')
    sh.append('mkdir -p "$HOME/.local/bin"')
    sh.append(f'cp "$APPDIR/{exe_name}" "$HOME/.local/bin/{exe_name}"')
    sh.append(f'chmod +x "$HOME/.local/bin/{exe_name}"')
    sh.append('')
    desktop_filename = f"myrhythm-{customer}.desktop"
    sh.append('# Create desktop entry')
    sh.append('mkdir -p "$HOME/.local/share/applications"')
    sh.append('DESKTOP_PATH="$HOME/.local/share/applications/' + desktop_filename + '"')
    sh.append('cat > "$DESKTOP_PATH" <<EOF')
    sh.append('[Desktop Entry]')
    sh.append('Type=Application')
    sh.append('Name=MyRhythmNexus')
    sh.append(f'Exec=$HOME/.local/bin/{exe_name}')
    if icon_name:
        sh.append(f'Icon=$HOME/.config/MyRhythmNexus/{icon_name}')
    else:
        sh.append('Icon=utilities-terminal')
    sh.append('Terminal=false')
    sh.append('Categories=Utility;')
    sh.append('EOF')
    sh.append('')
    sh.append('# Try to copy the .desktop file to common Desktop locations for convenience')
    sh.append('if [ -d "$HOME/Desktop" ]; then')
    sh.append('  cp "$DESKTOP_PATH" "$HOME/Desktop/" || true')
    sh.append('fi')
    sh.append('if [ -d "$HOME/Masaüstü" ]; then')
    sh.append('  cp "$DESKTOP_PATH" "$HOME/Masaüstü/" || true')
    sh.append('fi')
    sh.append('')
    sh.append('echo "Installation complete. You can launch MyRhythmNexus from the Applications menu or Desktop."')

    path = workdir / 'install.sh'
    path.write_text('\n'.join(sh), encoding='utf-8')
    try:
        path.chmod(0o755)
    except Exception:
        pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def package(exe_path: Path, config_path: Path, customer: str, output_dir: Path, icon_path: Path | None = None) -> Path:
    if not exe_path.exists():
        raise FileNotFoundError(f"Exe not found: {exe_path}")
    if not config_path.exists():
        raise FileNotFoundError(f"config.json not found: {config_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    product = 'MyRhythmNexus'
    zip_name = f"{product}-{customer}.zip"
    zip_path = output_dir / zip_name

    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        exe_name = exe_path.name
        shutil.copy2(exe_path, workdir / exe_name)
        shutil.copy2(config_path, workdir / 'config.json')
        icon_name = None
        if icon_path:
            icon_name = icon_path.name
            shutil.copy2(icon_path, workdir / icon_name)

        make_install_sh(workdir, exe_name, customer, icon_name)

        # Create zip
        with ZipFile(zip_path, 'w', ZIP_DEFLATED) as z:
            for p in sorted(workdir.rglob('*')):
                arcname = p.relative_to(workdir)
                z.write(p, arcname)

    # checksum
    digest = sha256_file(zip_path)
    (zip_path.with_suffix(zip_path.suffix + '.sha256')).write_text(digest, encoding='ascii')
    return zip_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--exe', required=True, help='Path to built linux binary (single-file)')
    parser.add_argument('--config', required=True, help='Path to config.json to include')
    parser.add_argument('--customer', required=True, help='Customer short name used in package filename')
    parser.add_argument('--output', default='release', help='Output directory for zip')
    parser.add_argument('--icon', default=None, help='Optional icon file to include (png)')
    args = parser.parse_args(argv)

    exe = Path(args.exe)
    cfg = Path(args.config)
    icon = Path(args.icon) if args.icon else None
    out = Path(args.output)

    try:
        zip_path = package(exe, cfg, args.customer, out, icon)
        print('Created:', zip_path)
        return 0
    except Exception as e:
        print('Error:', e, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
