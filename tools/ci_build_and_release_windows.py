#!/usr/bin/env python3
"""Windows-oriented build-and-release helper.

This is a platform-split variant of `tools/ci_build_and_release.py` focused on
Windows builds. It keeps the same behavior for version discovery and GitHub
release upload, but removes Docker/Linux-specific code paths and the
CRLF->LF normalization which is only applied for Linux artifacts.
"""
from __future__ import annotations

import argparse
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
    requests = None


def read_version_from_config() -> Optional[str]:
    cfg = Path('desktop') / 'core' / 'config.py'
    if not cfg.exists():
        return None
    text = cfg.read_text(encoding='utf-8')
    m = re.search(r"DesktopConfig\.VERSION\s*=\s*['\"]([^'\"]+)['\"]", text)
    if m:
        return m.group(1).strip()
    try:
        repo_root = Path.cwd()
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        from desktop.core.config import DesktopConfig  # type: ignore

        v = getattr(DesktopConfig, 'VERSION', None)
        if v:
            return str(v)
    except Exception:
        pass
    ver_file = Path('desktop') / 'version.txt'
    if ver_file.exists():
        try:
            return ver_file.read_text(encoding='utf-8').strip()
        except Exception:
            pass
    return None


def run_build_script() -> bool:
    """Run the appropriate build script for the current platform.

    On Windows this runs `build-desktop.bat`. If running on Unix and a
    `build-desktop.sh` exists, it will run that instead.
    """
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


def find_built_exe(version: Optional[str] = None, prefer_linux: bool = False) -> Optional[Path]:
    d = Path('dist')
    if d.exists():
        files = [f for f in d.iterdir() if f.is_file()]
        if not files:
            return None
        if version:
            ver_name = f'MyRhythmNexus_v{version}'
            for candidate in files:
                if candidate.name == ver_name or candidate.stem == ver_name:
                    return candidate
        for candidate in files:
            if candidate.name == 'MyRhythmNexus-Desktop' or candidate.name.startswith('MyRhythmNexus'):
                return candidate
        return files[0]
    r = Path('release')
    if r.exists():
        exes = list(r.glob('*.exe'))
        if exes:
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
    payload = {'tag_name': tag, 'name': tag, 'body': f'Release {tag} (automated)', 'prerelease': False}
    resp = requests.post(f'{api_base}/repos/{repo}/releases', headers=headers, json=payload, timeout=30)
    if resp.status_code == 201:
        release = resp.json()
    elif resp.status_code == 422:
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
    parser.add_argument('--clean-dist', action='store_true', help='Remove contents of dist/ before building')
    parser.add_argument('--version', default=None)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--interactive', action='store_true', help='Ask interactively for any missing inputs')
    args = parser.parse_args(argv)
    if len(sys.argv) == 1 and sys.stdin.isatty():
        args.interactive = True
    def prompt(prompt_text: str, default: Optional[str] = None, secret: bool = False) -> str:
        if default:
            resp = input(f"{prompt_text} [{default}]: ").strip()
            return resp or default
        else:
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
    repo = args.repo
    token = args.token or os.environ.get('GITHUB_TOKEN')
    version = args.version or read_version_from_config()
    no_build = args.no_build
    dry_run = args.dry_run
    if args.interactive:
        print('Interactive mode — provide values (leave blank to accept defaults)')
        if not token:
            try:
                import getpass
                tok = getpass.getpass('GITHUB token (press Enter to skip): ').strip()
                token = tok or None
            except Exception:
                token = None
        if not version:
            print('Version is required (provide in desktop/core/config.py or --version).', file=sys.stderr)
            return 2
        no_build = not prompt_yesno('Run build script before packaging?', default=not no_build)
        if token:
            dry_run = prompt_yesno('Dry-run (do not call GitHub)?', default=dry_run)
    else:
        if not version:
            print('Unable to determine version. Provide --version or ensure DesktopConfig.VERSION in desktop/core/config.py, or use --interactive', file=sys.stderr)
            return 2
    if not args.interactive and not token:
        try:
            import getpass
            if sys.stdin.isatty():
                tok = getpass.getpass('GitHub token (leave blank to skip release upload): ').strip()
                token = tok or None
            else:
                token = None
        except Exception:
            token = None
    print('Repo:', repo)
    print('Version:', version)
    print('No-build:', no_build)
    print('Dry-run:', dry_run)
    if not no_build:
        if version:
            os.environ['VERSION'] = str(version)
            print('Exported VERSION for build script:', os.environ['VERSION'])
        if getattr(args, 'clean_dist', False) or getattr(args, 'clean-dist', False):
            d = Path('dist')
            if d.exists():
                print('Cleaning dist/ directory (preserving MyRhythmNexus artifacts)...')
                for f in d.iterdir():
                    try:
                        if f.is_file() or f.is_symlink():
                            if f.name.startswith('MyRhythmNexus'):
                                print('  Preserving', f.name)
                                continue
                            f.unlink()
                        elif f.is_dir():
                            if f.name.startswith('MyRhythmNexus'):
                                print('  Preserving dir', f.name)
                                continue
                            shutil.rmtree(f)
                    except Exception as e:
                        print('Failed to remove', f, e)
        ok = run_build_script()
        if not ok:
            return 3
    exe = find_built_exe(version, prefer_linux=False)
    if not exe:
        print('Built exe not found in dist/ or release/.', file=sys.stderr)
        return 4
    print('Found exe:', exe)
    if not token:
        print('No GITHUB token provided; skipping writing to release/. Built artifact at:', exe)
        return 0
    release_dir = Path('release')
    release_dir.mkdir(parents=True, exist_ok=True)
    real_ext = exe.suffix.lower()
    suffix = real_ext if real_ext == '.exe' else ''
    dst_name = f'MyRhythmNexus_v{version}{suffix}'
    dst = release_dir / dst_name
    try:
        try:
            if exe.resolve() == dst.resolve():
                print('Built artifact already at destination, skipping copy:', dst)
            else:
                if os.name == 'nt' and str(exe).lower() == str(dst).lower():
                    print('Built artifact already at destination (case-insensitive match), skipping copy:', dst)
                else:
                    # Copy to a temporary file first and then atomically replace the
                    # destination. This ensures we always overwrite existing files
                    # and minimizes race conditions.
                    tmp = dst.with_suffix(dst.suffix + '.tmp')
                    try:
                        shutil.copy2(exe, tmp)
                        os.replace(tmp, dst)
                        print('Copied to', dst)
                    finally:
                        try:
                            if tmp.exists():
                                tmp.unlink()
                        except Exception:
                            pass
        except FileNotFoundError:
            tmp = dst.with_suffix(dst.suffix + '.tmp')
            try:
                shutil.copy2(exe, tmp)
                os.replace(tmp, dst)
                print('Copied to', dst)
            finally:
                try:
                    if tmp.exists():
                        tmp.unlink()
                except Exception:
                    pass
    except PermissionError as e:
        print('Warning: could not copy built artifact due to file lock:', e, file=sys.stderr)
        print('The built artifact is located at:', exe)
        print('If you want the file copied to the release directory, close any process that may be using the file and re-run the script, or copy manually.', file=sys.stderr)
        return 0
    except Exception as e:
        print('Failed to copy built artifact:', e, file=sys.stderr)
        return 5
    if not token:
        print('GITHUB_TOKEN not provided via --token or GITHUB_TOKEN env var; skipping GitHub upload.', file=sys.stderr)
        return 0
    success = create_release_and_upload(repo, token, version, dst, dry_run=dry_run)
    return 0 if success else 6


if __name__ == '__main__':
    raise SystemExit(main())
