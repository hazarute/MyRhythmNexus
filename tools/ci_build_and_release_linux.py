#!/usr/bin/env python3
"""Thin CLI wrapper for Linux builder workflows.

This file delegates implementation to `tools.LinuxBuilder` modules to keep the
CLI small and the logic testable.
"""
from __future__ import annotations

import argparse
import os
import sys
import shutil
from pathlib import Path
from typing import Optional

import importlib.util


def _load_module_from_path(name: str, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f'Cannot load module {name} from {path}')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base = Path(__file__).resolve().parent / 'LinuxBuilder'
ci_io = _load_module_from_path('linuxbuilder.ci_io', base / 'ci_io.py')
build_runner = _load_module_from_path('linuxbuilder.build_runner', base / 'build_runner.py')
artifact = _load_module_from_path('linuxbuilder.artifact', base / 'artifact.py')
packaging = _load_module_from_path('linuxbuilder.packaging', base / 'packaging.py')
github_release = _load_module_from_path('linuxbuilder.github_release', base / 'github_release.py')


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
    # packaging options (Linux-only customer packaging)
    parser.add_argument('--package-customer', action='store_true', help='Create a per-customer zip tailored for Linux (install.sh only)')
    parser.add_argument('--exe-path', default=None, help='Path to built exe to include in package (overrides auto-detect)')
    parser.add_argument('--backend-url', default=None, help='Backend URL to write into config.json when packaging')
    parser.add_argument('--customer', default=None, help='Customer short name used in package filename')
    parser.add_argument('--output-dir', default='release', help='Output directory for customer zip')
    parser.add_argument('--license-server-url', default=None, help='License server URL for config (optional)')
    args = parser.parse_args(argv)

    if len(sys.argv) == 1 and sys.stdin.isatty():
        args.interactive = True

    def prompt(prompt_text: str, default: Optional[str] = None) -> str:
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
    version = args.version or artifact.read_version_from_config()
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

        if sys.stdin.isatty():
            while True:
                print('\nSelect build target:')
                print('  1) Local Linux (build-desktop.sh)')
                print('  2) Docker builder')
                choice = input('Choose 1 or 2 [2]: ').strip() or '2'
                if choice in ('1', '2'):
                    break
                print('Please choose 1 or 2.')
            args.docker = (choice == '2')
        else:
            args.docker = getattr(args, 'docker', False)
        
        if token:
            dry_run = prompt_yesno('Dry-run (do not call GitHub)?', default=dry_run)

        # Note: GitHub upload/token prompt removed per configuration.
        if not version:
            print('Version is required (provide in desktop/core/config.py or --version).', file=sys.stderr)
            return 2
        no_build = not prompt_yesno('Run build script before packaging?', default=not no_build)
        pkg_choice = prompt_yesno('Create per-customer package after build?', default=False)
        if pkg_choice:
            args.package_customer = True
            if not args.backend_url:
                args.backend_url = prompt('Backend URL (e.g. https://acme.example.com/api/v1)')
            if not args.customer:
                args.customer = prompt('Customer short name (used in package filename)')
            out_dir = input(f"Output directory [{getattr(args, 'output_dir', 'release')}]: ").strip()
            if out_dir:
                args.output_dir = out_dir
            exe_override = input('Path to EXE to include (leave blank to auto-detect from dist/): ').strip()
            if exe_override:
                args.exe_path = exe_override
            if not args.license_server_url:
                ls = input('License server URL (optional): ').strip()
                if ls:
                    args.license_server_url = ls
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

    # Non-interactive token prompting removed — upload disabled.

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
        if getattr(args, 'docker', False):
            ok = build_runner.run_docker_builder(version, Path.cwd())
        else:
            ok = build_runner.run_local_build(Path('build-desktop.sh'))
        if not ok:
            return 3

    # Normalize CRLF->LF for Linux artifacts (best-effort)
    try:
        ci_io.normalize_crlf_in_dir(Path('dist'))
    except Exception:
        pass

    exe = artifact.find_built_exe(version, prefer_linux=getattr(args, 'docker', True))
    if not exe:
        if getattr(args, 'docker', False):
            print('Built artifact for Linux not found in dist/. If the builder produced a Windows .exe (dist/*.exe) this script will not accept it for a Docker/Linux build.', file=sys.stderr)
            print('Check Docker build logs — you may see "shopt: not found" if /bin/sh was used instead of bash inside the container. Ensure the builder runs with bash or that build-desktop.sh is POSIX-compatible.', file=sys.stderr)
        else:
            print('Built exe not found in dist/ or release/.', file=sys.stderr)
        return 4
    print('Found exe:', exe)

    if args.package_customer:
        exe_for_package = Path(args.exe_path) if args.exe_path else exe
        if not exe_for_package or not exe_for_package.exists():
            print('Package requested but EXE not found:', exe_for_package, file=sys.stderr)
            return 4
        backend_url = args.backend_url
        customer = args.customer
        out_dir = Path(args.output_dir or 'release')
        license_server = args.license_server_url
        if args.interactive and (not backend_url or not customer):
            if not backend_url:
                backend_url = input('Backend URL (e.g. https://acme.example.com/api/v1): ').strip()
            if not customer:
                customer = input('Customer short name (used in package filename): ').strip()
        if not backend_url or not customer:
            print('When using --package-customer you must provide --backend-url and --customer (or use --interactive).', file=sys.stderr)
            return 2

        zip_path, digest = packaging.create_customer_package(exe_for_package, backend_url, customer, out_dir, license_server)
        print('Created package:', zip_path)
        # Continue to GitHub release if token is present
        # return 0

    if not token:
        print('No GITHUB token provided; skipping writing to release/. Built artifact at:', exe)
        return 0

    release_dir = Path('release')
    release_dir.mkdir(parents=True, exist_ok=True)
    real_ext = exe.suffix.lower()
    # Fix: pathlib treats .0 in v1.1.0 as an extension. Ignore numeric suffixes.
    if real_ext and real_ext[1:].isdigit():
        real_ext = ''
    dst_name = f'MyRhythmNexus_v{version}{real_ext}'
    dst = release_dir / dst_name

    try:
        try:
            if exe.resolve() == dst.resolve():
                print('Built artifact already at destination, skipping copy:', dst)
            else:
                shutil.copy2(exe, dst)
                print('Copied to', dst)
        except FileNotFoundError:
            shutil.copy2(exe, dst)
            print('Copied to', dst)
    except Exception as e:
        print('Failed to copy built artifact:', e, file=sys.stderr)
        return 5

    success = github_release.create_release_and_upload(repo, token, version, dst, dry_run=dry_run)
    return 0 if success else 6


if __name__ == '__main__':
    raise SystemExit(main())
