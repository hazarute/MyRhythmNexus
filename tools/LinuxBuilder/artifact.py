from pathlib import Path
from typing import Optional
import re
import sys


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


def find_built_exe(version: Optional[str] = None, prefer_linux: bool = True) -> Optional[Path]:
    d = Path('dist')
    if d.exists():
        files = [f for f in d.iterdir() if f.is_file()]
        if not files:
            return None
        if prefer_linux:
            linux_candidates = [c for c in files if c.suffix.lower() != '.exe']
            if version:
                ver_name = f'MyRhythmNexus_v{version}'
                for candidate in linux_candidates:
                    if candidate.name == ver_name or candidate.stem == ver_name:
                        return candidate
            for candidate in linux_candidates:
                if candidate.name.startswith('MyRhythmNexus'):
                    return candidate
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
