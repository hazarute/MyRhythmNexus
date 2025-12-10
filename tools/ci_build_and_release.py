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


def find_built_exe(version: Optional[str] = None, prefer_linux: bool = False) -> Optional[Path]:
    # First prefer looking in dist/ (typical PyInstaller output)
    d = Path('dist')
    if d.exists():
        # Look for platform-specific output: on Windows PyInstaller makes *.exe,
        # on Linux it typically produces an executable file without extension.
        # Prefer any file that contains 'MyRhythmNexus' in the name.
        files = [f for f in d.iterdir() if f.is_file()]
        if not files:
            return None
        # When building for Linux (Docker builder) prefer artifacts without the
        # Windows .exe suffix. If prefer_linux is True, ignore .exe files so a
        # stray Windows build won't be picked up accidentally.
        if prefer_linux:
            linux_candidates = [c for c in files if c.suffix.lower() != '.exe']
            if version:
                ver_name = f'MyRhythmNexus_v{version}'
                for candidate in linux_candidates:
                    if candidate.name == ver_name or candidate.stem == ver_name:
                        return candidate
            # prefer any linux candidate that starts with MyRhythmNexus
            for candidate in linux_candidates:
                if candidate.name.startswith('MyRhythmNexus'):
                    return candidate
            # no linux-style artifact found
            return None
        # Prefer exact versioned name if provided (MyRhythmNexus_v{version})
        if version:
            ver_name = f'MyRhythmNexus_v{version}'
            for candidate in files:
                # match either full filename or stem (so MyRhythmNexus_v1.0.3 and
                # MyRhythmNexus_v1.0.3.exe both match)
                if candidate.name == ver_name or candidate.stem == ver_name:
                    return candidate
        # Prefer exact name match for legacy builds, then anything starting with MyRhythmNexus
        for candidate in files:
            if candidate.name == 'MyRhythmNexus-Desktop' or candidate.name.startswith('MyRhythmNexus'):
                return candidate
        # Fallback: return first file in dist
        return files[0]

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
    parser.add_argument('--docker', action='store_true', help='Run the Linux build inside the Docker builder image')
    parser.add_argument('--clean-dist', action='store_true', help='Remove contents of dist/ before building')
    parser.add_argument('--version', default=None)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--interactive', action='store_true', help='Ask interactively for any missing inputs')
    args = parser.parse_args(argv)

    # If the script is launched without any CLI args in an interactive terminal,
    # enable interactive mode so the user can choose step-by-step options.
    if len(sys.argv) == 1 and sys.stdin.isatty():
        args.interactive = True

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
        # Ask which platform to build for first so subsequent prompts can adapt.
        if sys.stdin.isatty():
            while True:
                print('\nSelect build target:')
                print('  1) Windows (.exe)')
                print('  2) Linux (Docker builder)')
                choice = input('Choose 1 or 2 [1]: ').strip() or '1'
                if choice in ('1', '2'):
                    break
                print('Please choose 1 or 2.')
            args.docker = (choice == '2')
            if args.docker:
                print('Selected: Docker/Linux build')
            else:
                print('Selected: Windows/.exe build')
        else:
            # Non-interactive stdin — default to existing flags or Windows
            args.docker = getattr(args, 'docker', False)
        # Do not prompt for repo (default is fine) and do not prompt for version
        # because version is automatically read from `desktop/core/config.py`.
        if not token:
            # Allow empty token in interactive mode (user may skip upload)
            try:
                import getpass
                tok = getpass.getpass('GITHUB token (press Enter to skip): ').strip()
                token = tok or None
            except Exception:
                token = None
        # Do not ask for version interactively; require it to be present already
        if not version:
            print('Version is required (provide in desktop/core/config.py or --version).', file=sys.stderr)
            return 2
        no_build = not prompt_yesno('Run build script before packaging?', default=not no_build)
        # Only ask about dry-run if a token was provided (otherwise upload is skipped anyway)
        if token:
            dry_run = prompt_yesno('Dry-run (do not call GitHub)?', default=dry_run)
    else:
        # non-interactive path: require version
        if not version:
            print('Unable to determine version. Provide --version or ensure DesktopConfig.VERSION in desktop/core/config.py, or use --interactive', file=sys.stderr)
            return 2

    # If not in interactive mode and token not provided, prompt the user once (hidden).
    if not args.interactive and not token:
        try:
            import getpass
            # Only prompt if running in a TTY; otherwise remain None and skip upload
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

    # run build unless requested not to
    if not no_build:
        # Export VERSION so build script can name the exe accordingly
        if version:
            os.environ['VERSION'] = str(version)
            print('Exported VERSION for build script:', os.environ['VERSION'])
        # Optionally clean dist to avoid stale .exe / non-exe collisions
        if getattr(args, 'clean_dist', False) or getattr(args, 'clean-dist', False):
            d = Path('dist')
            if d.exists():
                print('Cleaning dist/ directory (preserving MyRhythmNexus artifacts)...')
                for f in d.iterdir():
                    try:
                        # Preserve any existing MyRhythmNexus build artifact (do not delete
                        # old builds). If the build is the same version, the builder will
                        # overwrite the file in place. If it's a different version, we keep
                        # the old artifact and produce a new versioned file alongside it.
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

        if getattr(args, 'docker', False):
            def run_docker_builder() -> bool:
                image = 'myrhythm-desktop-builder:latest'
                cwd = Path.cwd()
                # Build image
                print('Building Docker image for builder...')
                cmd_build = ['docker', 'build', '-t', image, '-f', 'tools/desktop-builder/Dockerfile', '.']
                try:
                    subprocess.run(cmd_build, check=True)
                except subprocess.CalledProcessError as e:
                    print('Docker build failed:', e, file=sys.stderr)
                    return False

                # Run container and mount repo. Mount `dist` always so artifacts are saved.
                # Mount `release` only when a GitHub token is provided so we don't
                # accidentally write built artifacts into `release/` when uploads are
                # intentionally skipped.
                dist_host = str(cwd / 'dist')
                release_host = str(cwd / 'release')
                os.makedirs(dist_host, exist_ok=True)
                os.makedirs(release_host, exist_ok=True)
                # Pass VERSION into the container so created files and version.txt
                # are stamped correctly.
                # Run the builder script under bash inside the container to ensure
                # bash-only features (like shopt) are available. If bash is not
                # present in the image this will fail — the builder image should
                # include bash (the provided Dockerfile does). We mount the repo
                # and pass VERSION into the container.
                base_mounts = ['-e', f'VERSION={version}', '-v', f'{dist_host}:/src/dist', '-v', f'{str(cwd)}:/src']
                # Only mount release when token is available (we will copy to release later when token is present)
                if token:
                    mounts = base_mounts + ['-v', f'{release_host}:/src/release']
                else:
                    mounts = base_mounts
                # Command: run bash and execute the bundled build script
                cmd_run = ['docker', 'run', '--rm'] + mounts + [image, '/bin/bash', '-lc', './build-desktop.sh']
                print('Running Docker builder...')
                try:
                    subprocess.run(cmd_run, check=True)
                except subprocess.CalledProcessError as e:
                    print('Docker run failed:', e, file=sys.stderr)
                    return False
                return True

            ok = run_docker_builder()
        else:
            ok = run_build_script()
        if not ok:
            return 3

    # When building for Linux (Docker builder) ensure any text artifacts in
    # `dist/` use LF line endings. A common cross-platform issue is that
    # Windows machines produce files with CRLF which break shebang lines on
    # Linux ("bad interpreter: No such file or directory"). Convert CRLF -> LF
    # for non-binary files in dist/ to avoid requiring `dos2unix` on the target.
    try:
        if getattr(args, 'docker', False):
            d = Path('dist')
            if d.exists():
                def _is_binary(p: Path, blocksize: int = 1024) -> bool:
                    try:
                        with p.open('rb') as fh:
                            chunk = fh.read(blocksize)
                        return b'\x00' in chunk
                    except Exception:
                        return True

                def _normalize_crlf(p: Path) -> None:
                    try:
                        data = p.read_bytes()
                        # quick check: only touch files that contain CRLF and
                        # are not binary
                        if b'\r\n' in data and b'\x00' not in data:
                            data = data.replace(b'\r\n', b'\n')
                            p.write_bytes(data)
                            print('Normalized line endings to LF for', p)
                    except Exception as e:
                        print('Warning: failed to normalize', p, e)

                for f in d.iterdir():
                    if f.is_file():
                        if not _is_binary(f):
                            _normalize_crlf(f)
    except Exception:
        # Best-effort: if normalization fails do not abort the build flow.
        pass

    # find exe
    exe = find_built_exe(version, prefer_linux=getattr(args, 'docker', False))
    if not exe:
        if getattr(args, 'docker', False):
            print('Built artifact for Linux not found in dist/. If the builder produced a Windows .exe (dist/*.exe) this script will not accept it for a Docker/Linux build.', file=sys.stderr)
            print('Check Docker build logs — you may see "shopt: not found" if /bin/sh was used instead of bash inside the container. Ensure the builder runs with bash or that build-desktop.sh is POSIX-compatible.', file=sys.stderr)
        else:
            print('Built exe not found in dist/ or release/.', file=sys.stderr)
        return 4
    print('Found exe:', exe)

    # If no GitHub token was provided, do not write into `release/` — the user
    # requested that release uploads be explicitly enabled. Just report where
    # the built artifact is and exit successfully.
    if not token:
        print('No GITHUB token provided; skipping writing to release/. Built artifact at:', exe)
        return 0

    release_dir = Path('release')
    release_dir.mkdir(parents=True, exist_ok=True)
    # Preserve the built file's suffix only when it is a real extension (e.g. .exe).
    # Filenames like MyRhythmNexus_v1.0.3 contain dots in the version and
    # would produce an incorrect suffix ('.3') — ignore those.
    real_ext = exe.suffix.lower()
    suffix = real_ext if real_ext == '.exe' else ''
    dst_name = f'MyRhythmNexus_v{version}{suffix}'
    dst = release_dir / dst_name
    try:
        # If the built artifact is already the same file as the destination (for
        # example the builder wrote directly into `release/` because we mounted it), skip copying.
        try:
            if exe.resolve() == dst.resolve():
                print('Built artifact already at destination, skipping copy:', dst)
            else:
                # If source and destination are identical paths (case-insensitive
                # on Windows) treat them as equal as well.
                if os.name == 'nt' and str(exe).lower() == str(dst).lower():
                    print('Built artifact already at destination (case-insensitive match), skipping copy:', dst)
                else:
                    shutil.copy2(exe, dst)
                    print('Copied to', dst)
        except FileNotFoundError:
            # exe or dst parent missing — attempt copy anyway
            shutil.copy2(exe, dst)
    except PermissionError as e:
        # Common on Windows when the file is locked by another process. Don't
        # crash the whole script — report and exit successfully because build
        # itself already completed. User can manually resolve the lock.
        print('Warning: could not copy built artifact due to file lock:', e, file=sys.stderr)
        print('The built artifact is located at:', exe)
        print('If you want the file copied to the release directory, close any process that may be using the file and re-run the script, or copy manually.', file=sys.stderr)
        return 0
    except Exception as e:
        print('Failed to copy built artifact:', e, file=sys.stderr)
        return 5

    # create release and upload
    if not token:
        # If no token provided, we intentionally skip GitHub upload but consider
        # the build/package operation successful. Return 0 to indicate success.
        print('GITHUB_TOKEN not provided via --token or GITHUB_TOKEN env var; skipping GitHub upload.', file=sys.stderr)
        return 0

    success = create_release_and_upload(repo, token, version, dst, dry_run=dry_run)
    return 0 if success else 6


if __name__ == '__main__':
    raise SystemExit(main())
