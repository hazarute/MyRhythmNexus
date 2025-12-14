import os
import json
import requests
import tempfile
import zipfile
import sys
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any
import platform
from desktop.core.config import get_app_config_dir
import re

try:
    from packaging.version import Version, InvalidVersion
    _HAS_PACKAGING = True
except Exception:
    _HAS_PACKAGING = False

class UpdateManager:
    """Handles update logic: checking, downloading, and installing."""

    GITHUB_REPO = "hazarute/MyRhythmNexus"
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    CURRENT_VERSION_FILE = "version.json"

    def __init__(self, current_version: str = "1.0.0"):
        self.current_version = current_version
        self.app_data_dir = get_app_config_dir()
        self.app_data_dir.mkdir(parents=True, exist_ok=True)

    def get_current_version_info(self) -> Dict[str, Any]:
        """Get current version information from local file or detection."""
        version_file = self.app_data_dir / self.CURRENT_VERSION_FILE
        detected_version = self._detect_version_from_files()

        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'version' not in data:
                        data['version'] = self.current_version
                    if 'installed' not in data:
                        data['installed'] = False

                    # When running from source (not frozen), prefer runtime/current_version
                    # to avoid using a stale saved `version.json` that may belong to
                    # a packaged installer. For packaged/frozen executables, keep
                    # the saved value but allow the runtime `current_version` to
                    # override if it is newer.
                    try:
                        if not getattr(sys, 'frozen', False):
                            data['version'] = self.current_version or detected_version
                        else:
                            if self.current_version and self._is_newer_version(self.current_version, data.get('version', '0.0.0')):
                                data['version'] = self.current_version
                    except Exception:
                        pass

                    return data
            except Exception:
                pass

        # Fallback detection
        return {"version": detected_version, "installed": False}

    def _detect_version_from_files(self) -> str:
        """Try to detect version from local files or executable name."""
        detected_version = self.current_version
        try:
            if getattr(sys, 'frozen', False):
                exe_path = Path(sys.executable)
                possible = exe_path.parent / 'version.txt'
                if possible.exists():
                    try:
                        with open(possible, 'r', encoding='utf-8') as vf:
                            first = vf.readline().strip()
                            if first:
                                detected_version = first.split()[-1].lstrip('v')
                    except Exception:
                        pass
                else:
                    # try to infer from executable name
                    import re
                    m = re.search(r"v?(\d+\.\d+(?:\.\d+)*)", exe_path.name)
                    if m:
                        detected_version = m.group(1)
            else:
                # Source mode
                repo_version = Path(__file__).resolve().parents[2] / 'version.txt' # Adjusted path
                if not repo_version.exists():
                     repo_version = Path(__file__).resolve().parents[2] / 'desktop' / 'version.txt'
                
                if repo_version.exists():
                    try:
                        with open(repo_version, 'r', encoding='utf-8') as vf:
                            first = vf.readline().strip()
                            if first:
                                detected_version = first.split()[-1].lstrip('v')
                    except Exception:
                        pass
        except Exception:
            pass
        return detected_version

    def save_version_info(self, version_info: Dict[str, Any]):
        """Save version information to disk."""
        version_file = self.app_data_dir / self.CURRENT_VERSION_FILE
        try:
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_info, f, indent=2)
        except Exception:
            pass

    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """Check GitHub for latest release."""
        try:
            response = requests.get(self.GITHUB_API_URL, timeout=10)
            response.raise_for_status()
            release_data = response.json()

            latest_version = release_data.get('tag_name', '').lstrip('v')
            current_info = self.get_current_version_info()

            if self._is_newer_version(latest_version, current_info.get('version', '0.0.0')):
                download_url = self._get_download_url(release_data)
                if download_url:
                    return {
                        'version': latest_version,
                        'download_url': download_url,
                        'changelog': release_data.get('body', ''),
                        'release_url': release_data.get('html_url', '')
                    }
        except Exception as e:
            print(f"Update check failed: {e}")

        return None

    def _is_newer_version(self, new_version: str, current_version: str) -> bool:
        """Compare version strings."""
        # Normalize inputs to strings
        if new_version is None:
            return False
        if current_version is None:
            current_version = '0.0.0'

        new_v = str(new_version).strip()
        cur_v = str(current_version).strip()

        # Prefer using packaging.version when available
        if _HAS_PACKAGING:
            try:
                return Version(new_v) > Version(cur_v)
            except InvalidVersion:
                # fall back to simple parse below
                pass

        # Fallback: numeric segment comparison ignoring non-digit suffixes
        def to_int_parts(v: str):
            # remove any leading non-digit characters like 'v' or 'version '
            v = re.sub(r'^[^0-9]+', '', v)
            parts = []
            for seg in v.split('.'):
                # extract first run of digits from the segment
                m = re.search(r"(\d+)", seg)
                if m:
                    parts.append(int(m.group(1)))
                else:
                    parts.append(0)
            return parts

        try:
            new_parts = to_int_parts(new_v)
            current_parts = to_int_parts(cur_v)
            max_len = max(len(new_parts), len(current_parts))
            new_parts.extend([0] * (max_len - len(new_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            return new_parts > current_parts
        except Exception:
            return False

    def _get_download_url(self, release_data: Dict) -> Optional[str]:
        """Extract download URL from release data, respecting platform."""
        assets = release_data.get('assets', [])
        system = platform.system().lower()
        
        preferred = []
        excluded = []

        if system.startswith('win'):
            preferred = ['.exe']
            excluded = ['.appimage', '.deb', '.rpm', '.dmg']
        elif system.startswith('linux'):
            preferred = ['.AppImage', '.tar.gz', '.zip', '']
            excluded = ['.exe', '.msi', '.dmg', '.pkg']
        elif system.startswith('darwin') or system.startswith('mac'):
            preferred = ['.dmg', '.tar.gz', '.zip', '']
            excluded = ['.exe', '.msi', '.appimage', '.deb', '.rpm']
        else:
            preferred = ['']

        def score_asset(a: Dict) -> int:
            name = a.get('name', '').lower()
            score = 0
            if 'myrhythmnexus' in name:
                score += 10
            for idx, suf in enumerate(preferred):
                if suf and name.endswith(suf.lower()):
                    score += 100 - idx
                    break
            if system.startswith('linux') and ('linux' in name or 'x86_64' in name or 'amd64' in name):
                score += 5
            return score

        best = None
        best_score = -1
        for asset in assets:
            s = score_asset(asset)
            if s > best_score:
                best_score = s
                best = asset

        if best:
            best_name = best.get('name', '').lower()
            for ext in excluded:
                if best_name.endswith(ext):
                    return None
            return best.get('browser_download_url')
        return None

    def download_and_install_update(self, update_info: Dict[str, Any], progress_callback=None) -> bool:
        """Download and install update."""
        try:
            download_url = update_info.get('download_url')
            if not download_url:
                return False

            import urllib.parse
            parsed = urllib.parse.urlparse(download_url)
            base_name = Path(parsed.path).name
            
            suffix = ''
            if base_name.endswith('.exe'): suffix = '.exe'
            elif base_name.endswith('.zip'): suffix = '.zip'
            elif base_name.endswith('.tar.gz') or base_name.endswith('.tgz'): suffix = '.tar.gz'
            elif base_name.endswith('.AppImage'): suffix = '.AppImage'

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or '') as temp_file:
                temp_path = temp_file.name

            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            progress_callback(progress)

            current_exe = self._get_current_executable_path()
            if not current_exe:
                # Manual install fallback
                fallback_dir = self.app_data_dir
                dest = fallback_dir / base_name
                try:
                    shutil.move(temp_path, str(dest))
                    return True
                except Exception:
                    return False

            return self._install_file(temp_path, current_exe, suffix)

        except Exception as e:
            print(f"Update installation failed: {e}")
            return False
        finally:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

    def _install_file(self, temp_path: str, current_exe: Path, suffix: str) -> bool:
        """Handle the actual file replacement logic."""
        backup_path = str(current_exe) + '.backup'
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)

            if suffix in ('.zip', '.tar.gz'):
                return self._install_archive(temp_path, current_exe, backup_path, suffix)
            else:
                # Single binary
                shutil.move(str(current_exe), backup_path)
                try:
                    os.chmod(temp_path, 0o755)
                except Exception:
                    pass
                shutil.move(temp_path, str(current_exe))
                
            self._update_version_record()
            return True
        except Exception:
            # Fallback
            try:
                fallback_path = str(current_exe) + '.new'
                if os.path.exists(fallback_path):
                    os.remove(fallback_path)
                shutil.move(temp_path, fallback_path)
            except Exception:
                pass
            return False

    def _install_archive(self, temp_path: str, current_exe: Path, backup_path: str, suffix: str) -> bool:
        tmpdir = tempfile.mkdtemp()
        try:
            if suffix == '.zip':
                with zipfile.ZipFile(temp_path, 'r') as zf:
                    zf.extractall(tmpdir)
            else:
                import tarfile
                with tarfile.open(temp_path, 'r:gz') as tf:
                    tf.extractall(tmpdir)
            
            candidate = None
            for p in Path(tmpdir).rglob('*'):
                if p.is_file() and p.name.startswith('MyRhythmNexus'):
                    candidate = p
                    break
            
            if not candidate:
                raise Exception('No suitable binary found inside archive')
            
            shutil.move(str(current_exe), backup_path)
            shutil.move(str(candidate), str(current_exe))
            try:
                os.chmod(str(current_exe), 0o755)
            except Exception:
                pass
            return True
        finally:
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                pass

    def _update_version_record(self):
        """Update the installed version record."""
        # Note: We don't have the exact version string here easily unless passed down, 
        # but we can update the timestamp or mark as installed.
        # For simplicity, we might need to pass version info to this method or rely on next startup check.
        pass

    def _get_current_executable_path(self) -> Optional[Path]:
        if getattr(sys, 'frozen', False):
            return Path(sys.executable)
        return None

    def restart_application(self):
        current_exe = self._get_current_executable_path()
        if current_exe:
            import subprocess
            subprocess.Popen([str(current_exe)])
            sys.exit(0)
