import os
import json
import requests
import subprocess
import tempfile
import zipfile
import sys
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any
import customtkinter as ctk
from tkinter import messagebox
from desktop.core.config import DesktopConfig

class AutoUpdater:
    """Automatic updater for MyRhythmNexus Desktop application"""

    # Use the project's GitHub repository so the updater checks your releases
    GITHUB_REPO = "hazarute/MyRhythmNexus"
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    CURRENT_VERSION_FILE = "version.json"
    CONFIG_FILE = "config.json"

    def __init__(self, current_version: str = "1.0.0"):
        self.current_version = current_version
        self.app_data_dir = Path.home() / ".rhythm-nexus"
        self.app_data_dir.mkdir(exist_ok=True)

        # Ensure a persistent config file exists in the application data directory.
        # This file is where we store per-installation settings such as backend DB URLs.
        cfg_path = self.app_data_dir / self.CONFIG_FILE
        if not cfg_path.exists():
            default_cfg = {"backend_urls": [], "settings": {}}
            try:
                with open(cfg_path, 'w', encoding='utf-8') as f:
                    json.dump(default_cfg, f, indent=2)
            except Exception:
                # ignore write errors here; callers can handle later
                pass

    def get_current_version_info(self) -> Dict[str, Any]:
        """Get current version information"""
        version_file = self.app_data_dir / self.CURRENT_VERSION_FILE
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # ensure structure contains expected keys
                    if 'version' not in data:
                        data['version'] = self.current_version
                    if 'installed' not in data:
                        data['installed'] = False
                    # keep last_check if present
                    return data
            except:
                pass
        # No persisted version info found — try to detect from local files
        detected_version = self.current_version
        # If running as frozen executable, try to read version.txt next to executable
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
                    # try to infer from executable name: MyRhythmNexus_v1.0.exe
                    name = exe_path.name
                    import re
                    m = re.search(r"v?(\d+\.\d+(?:\.\d+)*)", name)
                    if m:
                        detected_version = m.group(1)
            else:
                # When running from source, try to read desktop/version.txt in repo
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
            detected_version = self.current_version

        return {"version": detected_version, "installed": False}

    def save_version_info(self, version_info: Dict[str, Any]):
        """Save version information"""
        version_file = self.app_data_dir / self.CURRENT_VERSION_FILE
        try:
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_info, f, indent=2)
        except Exception:
            pass

    # --- Config helpers ---
    def get_config(self) -> Dict[str, Any]:
        cfg_path = self.app_data_dir / self.CONFIG_FILE
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"backend_urls": [], "settings": {}}

    def save_config(self, cfg: Dict[str, Any]):
        cfg_path = self.app_data_dir / self.CONFIG_FILE
        try:
            with open(cfg_path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    def add_backend_url(self, url: str):
        cfg = self.get_config()
        urls = cfg.get('backend_urls', [])
        if url not in urls:
            urls.append(url)
            cfg['backend_urls'] = urls
            self.save_config(cfg)

    def get_backend_urls(self):
        cfg = self.get_config()
        return cfg.get('backend_urls', [])

    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """Check GitHub for latest release"""
        try:
            response = requests.get(self.GITHUB_API_URL, timeout=10)
            response.raise_for_status()
            release_data = response.json()

            latest_version = release_data.get('tag_name', '').lstrip('v')
            current_info = self.get_current_version_info()

            if self._is_newer_version(latest_version, current_info.get('version', '0.0.0')):
                return {
                    'version': latest_version,
                    'download_url': self._get_download_url(release_data),
                    'changelog': release_data.get('body', ''),
                    'release_url': release_data.get('html_url', '')
                }
        except Exception as e:
            print(f"Update check failed: {e}")

        return None

    def _is_newer_version(self, new_version: str, current_version: str) -> bool:
        """Compare version strings"""
        try:
            new_parts = [int(x) for x in new_version.split('.')]
            current_parts = [int(x) for x in current_version.split('.')]

            # Pad shorter version with zeros
            max_len = max(len(new_parts), len(current_parts))
            new_parts.extend([0] * (max_len - len(new_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))

            return new_parts > current_parts
        except:
            return False

    def _get_download_url(self, release_data: Dict) -> Optional[str]:
        """Extract download URL from release data"""
        assets = release_data.get('assets', [])
        for asset in assets:
            if asset.get('name', '').endswith('.exe'):
                return asset.get('browser_download_url')
        return None

    def download_and_install_update(self, update_info: Dict[str, Any], progress_callback=None) -> bool:
        """Download and install update"""
        try:
            download_url = update_info.get('download_url')
            if not download_url:
                return False

            # Download to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.exe') as temp_file:
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

            # Get current executable path
            current_exe = self._get_current_executable_path()
            if not current_exe:
                return False

            # NOTE: Replacing a running executable on Windows can fail because the file is locked.
            # Here we attempt a backup/replace, but for robust behavior consider using a
            # separate updater helper process or installer (Squirrel/WinSparkle/winget) that
            # runs after the app exits. This implementation will try a rename, and if it fails
            # will leave the downloaded file next to the executable for manual replacement.

            backup_path = str(current_exe) + '.backup'
            try:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                # Try to move the running exe to backup and put new exe in place
                shutil.move(str(current_exe), backup_path)
                shutil.move(temp_path, str(current_exe))
            except Exception as move_err:
                # If moving failed (likely on Windows while running), keep the downloaded
                # file in the app directory and inform caller. Do not delete app_data_dir.
                try:
                    fallback_path = str(current_exe) + '.new'
                    if os.path.exists(fallback_path):
                        os.remove(fallback_path)
                    shutil.move(temp_path, fallback_path)
                except Exception:
                    pass
                return False

            # Update version info
            vi = {
                'version': update_info['version'],
                'installed': True,
                'updated_at': str(Path(__file__).stat().st_mtime)
            }
            # Preserve/ensure last_check if present
            prev = self.get_current_version_info()
            if 'last_check' in prev:
                vi['last_check'] = prev['last_check']
            self.save_version_info(vi)

            return True

        except Exception as e:
            print(f"Update installation failed: {e}")
            return False
        finally:
            # Cleanup temp file if it still exists
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

    def _get_current_executable_path(self) -> Optional[Path]:
        """Get path of current executable"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return Path(sys.executable)
        return None

    def show_update_dialog(self, update_info: Dict[str, Any]) -> bool:
        """Show update dialog to user"""
        dialog = ctk.CTkToplevel()
        dialog.title("Güncelleme Mevcut")
        dialog.geometry("500x400")
        dialog.resizable(False, False)

        # Center the dialog
        dialog.transient()
        dialog.grab_set()

        # Title
        title_label = ctk.CTkLabel(
            dialog,
            text=f"Yeni Sürüm Mevcut: v{update_info['version']}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(20, 10))

        # Changelog
        changelog_frame = ctk.CTkScrollableFrame(dialog, width=450, height=200)
        changelog_frame.pack(pady=(0, 20), padx=20)

        changelog_text = ctk.CTkLabel(
            changelog_frame,
            text=update_info.get('changelog', 'Değişiklik günlüğü bulunamadı'),
            wraplength=400,
            justify="left"
        )
        changelog_text.pack(pady=10, padx=10)

        # Progress bar (initially hidden)
        progress_bar = ctk.CTkProgressBar(dialog, width=400)
        progress_bar.pack(pady=(0, 20))
        progress_bar.pack_forget()

        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=(0, 20))

        update_now = False

        def on_update():
            nonlocal update_now
            update_now = True
            update_button.configure(state="disabled", text="İndiriliyor...")
            skip_button.configure(state="disabled")
            progress_bar.pack(pady=(0, 20))

            def progress_callback(progress):
                progress_bar.set(progress / 100)

            success = self.download_and_install_update(update_info, progress_callback)

            if success:
                messagebox.showinfo("Başarılı", "Güncelleme tamamlandı! Uygulama yeniden başlatılacak.")
                dialog.destroy()
                self.restart_application()
            else:
                messagebox.showerror("Hata", "Güncelleme başarısız oldu.")
                update_button.configure(state="normal", text="Şimdi Güncelle")
                skip_button.configure(state="normal")
                progress_bar.pack_forget()

        def on_skip():
            dialog.destroy()

        update_button = ctk.CTkButton(
            button_frame,
            text="Şimdi Güncelle",
            command=on_update
        )
        update_button.pack(side="left", padx=(0, 10))

        skip_button = ctk.CTkButton(
            button_frame,
            text="Daha Sonra",
            command=on_skip,
            fg_color="transparent",
            border_width=2
        )
        skip_button.pack(side="left")

        dialog.wait_window()
        return update_now

    def restart_application(self):
        """Restart the application"""
        current_exe = self._get_current_executable_path()
        if current_exe:
            subprocess.Popen([str(current_exe)])
            sys.exit(0)

def check_and_update_on_startup():
    """Check for updates on application startup"""
    updater = AutoUpdater()
    # Perform update check on every startup (user requested behavior).
    # Note: this will call GitHub API on every start; keep rate limits in mind.
    try:
        # Respect configured check interval (minutes) to avoid hitting rate limits.
        interval_minutes = getattr(DesktopConfig, 'CHECK_UPDATE_INTERVAL_MINUTES', 60)
        interval_seconds = int(interval_minutes) * 60

        current_info = updater.get_current_version_info()
        last_check = current_info.get('last_check')
        current_time = time.time()

        if last_check and (current_time - last_check) < interval_seconds:
            # Skip checking — within configured interval
            return

        # Update last check time for record-keeping
        current_info['last_check'] = current_time
        updater.save_version_info(current_info)

        # Perform the update check
        update_info = updater.check_for_updates()
        if update_info:
            updater.show_update_dialog(update_info)
    except Exception as e:
        # Do not propagate errors on startup; log to stdout for debugging
        print(f"Update check failed on startup: {e}")