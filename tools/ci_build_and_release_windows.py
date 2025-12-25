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
import sys
import shutil
from pathlib import Path
from typing import Optional

import importlib.util


base = Path(__file__).resolve().parent / 'WindowsBuilder'

# Dynamic loaders for WindowsBuilder modules; if loading fails we fall back
# to the inline implementation still present in this file.
def _load_module_from_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f'Cannot load module {name} from {path}')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

try:
    build_runner = _load_module_from_path('windowsbuilder.build_runner', base / 'build_runner.py')
except Exception:
    build_runner = None

try:
    artifact = _load_module_from_path('windowsbuilder.artifact', base / 'artifact.py')
except Exception:
    artifact = None

try:
    github_release = _load_module_from_path('windowsbuilder.github_release', base / 'github_release.py')
except Exception:
    github_release = None


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
    # Prefer WindowsBuilder's artifact reader if available
    if artifact is not None:
        version = args.version or artifact.read_version_from_config()
    else:
        version = args.version
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
        if build_runner is None:
            print('WindowsBuilder.build_runner not available; cannot run build.', file=sys.stderr)
            return 1
        ok = build_runner.run_build_script()
        if not ok:
            return 3
    if artifact is None:
        print('WindowsBuilder.artifact not available; cannot locate built exe.', file=sys.stderr)
        return 4
    exe = artifact.find_built_exe(version, prefer_linux=False)
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
    if github_release is None:
        print('GitHub release helper not available; skipping upload. Built artifact at:', dst)
        return 0
    success = github_release.create_release_and_upload(repo, token, version, dst, dry_run=dry_run)
    return 0 if success else 6


if __name__ == '__main__':
    raise SystemExit(main())
