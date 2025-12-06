#!/usr/bin/env python3
"""Build desktop executable and create GitHub release with the produced EXE.

Usage:
  python tools/ci_build_and_release.py [--repo owner/repo] [--token GHTOKEN] [--no-build] [--version X.Y.Z] [--dry-run]

Behavior:
 - Reads version from `desktop/core/config.py` (DesktopConfig.VERSION) unless `--version` provided.
 - Runs `build-desktop.sh` on Unix or `build-desktop.bat` on Windows unless `--no-build`.
 - Looks for produced EXE in `dist/` and copies it to `release/MyRhythmNexus_v{version}.exe`.
 - Creates a GitHub release (tag `v{version}`) and uploads the exe as an asset.

Note: Provide `GITHUB_TOKEN` via env or `--token`. The token needs `repo` scope to create releases and upload assets.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

try:
    import requests
except Exception:
    requests = None  # user must install requests for GitHub API actions


def read_version_from_config() -> Optional[str]:
    cfg = Path('desktop') / 'core' / 'config.py'
    if not cfg.exists():
        return None
    text = cfg.read_text(encoding='utf-8')
    # look for DesktopConfig.VERSION = "1.0.0"
    m = re.search(r"DesktopConfig\.VERSION\s*=\s*['\"]([^'\"]+)['\"]", text)
    if m:
        return m.group(1).strip()
    # Try importing the module to read DesktopConfig.VERSION if regex didn't find it
    try:
        # Ensure repo root is on sys.path
        repo_root = Path.cwd()
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from desktop.core.config import DesktopConfig  # type: ignore
        v = getattr(DesktopConfig, 'VERSION', None)
        if v:
            return str(v)
    except Exception:
        pass

    # Fallback: check for a desktop/version.txt file written by build scripts
    ver_file = Path('desktop') / 'version.txt'
    if ver_file.exists():
        try:
            return ver_file.read_text(encoding='utf-8').strip()
        except Exception:
            pass

    return None


def run_build_script() -> bool:
    """Run build-desktop.sh or build-desktop.bat depending on platform."""
    # prefer .bat on Windows
    if os.name == 'nt':
        script = Path('build-desktop.bat')
        if not script.exists():
            print('build-desktop.bat not found', file=sys.stderr)
            return False
        cmd = ['cmd', '/c', str(script)]
    else:
        script = Path('build-desktop.sh')
        if not script.exists():
            print('build-desktop.sh not found', file=sys.stderr)
            return False
        cmd = ['sh', str(script)]

    print('Running build script:', ' '.join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print('Build failed:', e, file=sys.stderr)
        return False
    return True


def find_built_exe() -> Optional[Path]:
    # First prefer looking in dist/ (typical PyInstaller output)
    d = Path('dist')
    if d.exists():
        exes = list(d.glob('*.exe'))
        if exes:
            # prefer files that contain MyRhythmNexus in name
            for e in exes:
                if 'MyRhythmNexus' in e.name:
                    return e
            return exes[0]

    # Fallback: maybe an already packaged release exists in release/
    r = Path('release')
    if r.exists():
        exes = list(r.glob('*.exe'))
        if exes:
            # prefer versioned file pattern
            for e in exes:
                if 'MyRhythmNexus' in e.name:
                    return e
            return exes[0]

    return None


def create_release_and_upload(repo: str, token: str, version: str, asset_path: Path, dry_run: bool = False) -> bool:
    if requests is None:
        print('requests module not available; install with: pip install requests', file=sys.stderr)
        return False

    api_base = 'https://api.github.com'
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}

    tag = f'v{version}'
    print(f'Creating release {tag} in {repo}...')
    if dry_run:
        print('DRY-RUN: would create release and upload asset', asset_path)
        return True

    # Create release
    payload = {'tag_name': tag, 'name': tag, 'body': f'Release {tag} (automated)', 'prerelease': False}
    resp = requests.post(f'{api_base}/repos/{repo}/releases', headers=headers, json=payload, timeout=30)
    if resp.status_code == 201:
        release = resp.json()
    elif resp.status_code == 422:
        # release exists — get it
        print('Release already exists, finding existing release...')
        r = requests.get(f'{api_base}/repos/{repo}/releases/tags/{tag}', headers=headers, timeout=30)
        if r.status_code != 200:
            print('Failed to fetch existing release:', r.status_code, r.text, file=sys.stderr)
            return False
        release = r.json()
    else:
        print('Failed to create release:', resp.status_code, resp.text, file=sys.stderr)
        return False

    upload_url = release.get('upload_url', '')
    if '{' in upload_url:
        upload_url = upload_url.split('{')[0]

    # Upload asset
    headers_upload = {'Authorization': f'token {token}', 'Content-Type': 'application/octet-stream'}
    params = {'name': asset_path.name}
    with open(asset_path, 'rb') as f:
        up = requests.post(upload_url, headers=headers_upload, params=params, data=f, timeout=60)
    if up.status_code in (201, 200):
        print('Asset uploaded successfully.')
        return True
    else:
        print('Asset upload failed:', up.status_code, up.text, file=sys.stderr)
        return False


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', default=os.environ.get('GITHUB_REPO', 'hazarute/MyRhythmNexus'))
    parser.add_argument('--token', default=os.environ.get('GITHUB_TOKEN'))
    parser.add_argument('--no-build', action='store_true')
    parser.add_argument('--version', default=None)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--interactive', action='store_true', help='Ask interactively for any missing inputs')
    args = parser.parse_args(argv)

    # Interactive prompts helpers
    def prompt(prompt_text: str, default: Optional[str] = None, secret: bool = False) -> str:
        if default:
            resp = input(f"{prompt_text} [{default}]: ").strip()
            return resp or default
        else:
            # no default
            while True:
                resp = input(f"{prompt_text}: ").strip()
                if resp:
                    return resp

    def prompt_yesno(prompt_text: str, default: bool = True) -> bool:
        d = 'Y/n' if default else 'y/N'
        resp = input(f"{prompt_text} [{d}]: ").strip().lower()
        if resp == '':
            return default
        return resp in ('y', 'yes')

    # gather inputs (allow interactive override)
    repo = args.repo
    token = args.token or os.environ.get('GITHUB_TOKEN')
    version = args.version or read_version_from_config()
    no_build = args.no_build
    dry_run = args.dry_run

    if args.interactive:
        print('Interactive mode — provide values (leave blank to accept defaults)')
        repo = prompt('GitHub repo (owner/repo)', repo)
        if not token:
            token = prompt('GITHUB token (or set GITHUB_TOKEN env var)')
        version = prompt('Version to release', version or '')
        if not version:
            print('Version is required.', file=sys.stderr)
            return 2
        no_build = not prompt_yesno('Run build script before packaging?', default=not no_build)
        dry_run = prompt_yesno('Dry-run (do not call GitHub)?', default=dry_run)
    else:
        # non-interactive path: require version
        if not version:
            print('Unable to determine version. Provide --version or ensure DesktopConfig.VERSION in desktop/core/config.py, or use --interactive', file=sys.stderr)
            return 2

    # If token not provided, prompt the user (hidden input). If left blank, we will skip GitHub upload.
    if not token:
        try:
            import getpass
            # Only prompt if running in a TTY; otherwise remain None and skip upload
            if sys.stdin.isatty():
                tok = getpass.getpass('GitHub token (leave blank to skip release upload): ').strip()
                if tok:
                    token = tok
                else:
                    token = None
            else:
                token = None
        except Exception:
            token = None

    print('Repo:', repo)
    print('Version:', version)
    print('No-build:', no_build)
    print('Dry-run:', dry_run)

    # run build unless requested not to
    if not no_build:
        ok = run_build_script()
        if not ok:
            return 3

    # find exe
    exe = find_built_exe()
    if not exe:
        print('Built exe not found in dist/ or release/.', file=sys.stderr)
        return 4
    print('Found exe:', exe)

    release_dir = Path('release')
    release_dir.mkdir(parents=True, exist_ok=True)
    dst_name = f'MyRhythmNexus_v{version}.exe'
    dst = release_dir / dst_name
    shutil.copy2(exe, dst)
    print('Copied to', dst)

    # create release and upload
    if not token:
        print('GITHUB_TOKEN not provided via --token or GITHUB_TOKEN env var; skipping GitHub upload.', file=sys.stderr)
        return 0 if dry_run else 5

    success = create_release_and_upload(repo, token, version, dst, dry_run=dry_run)
    return 0 if success else 6


if __name__ == '__main__':
    raise SystemExit(main())
