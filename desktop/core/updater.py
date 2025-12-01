import os
import json
import requests
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any
import customtkinter as ctk
from tkinter import messagebox

class AutoUpdater:
    """Automatic updater for MyRhythmNexus Desktop application"""

    GITHUB_REPO = "your-username/MyRhythmNexus"  # Replace with your actual GitHub username/repo
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    CURRENT_VERSION_FILE = "version.json"

    def __init__(self, current_version: str = "1.0.0"):
        self.current_version = current_version
        self.app_data_dir = Path.home() / ".rhythm-nexus"
        self.app_data_dir.mkdir(exist_ok=True)

    def get_current_version_info(self) -> Dict[str, Any]:
        """Get current version information"""
        version_file = self.app_data_dir / self.CURRENT_VERSION_FILE
        if version_file.exists():
            try:
                with open(version_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"version": self.current_version, "installed": False}

    def save_version_info(self, version_info: Dict[str, Any]):
        """Save version information"""
        version_file = self.app_data_dir / self.CURRENT_VERSION_FILE
        with open(version_file, 'w') as f:
            json.dump(version_info, f)

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

            # Create backup
            backup_path = str(current_exe) + '.backup'
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename(current_exe, backup_path)

            # Replace executable
            os.rename(temp_path, current_exe)

            # Update version info
            self.save_version_info({
                'version': update_info['version'],
                'installed': True,
                'updated_at': str(Path(__file__).stat().st_mtime)
            })

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

    # Only check once per day
    current_info = updater.get_current_version_info()
    last_check = current_info.get('last_check')

    import time
    current_time = time.time()

    if last_check and (current_time - last_check) < 86400:  # 24 hours
        return

    # Update last check time
    current_info['last_check'] = current_time
    updater.save_version_info(current_info)

    # Check for updates
    update_info = updater.check_for_updates()
    if update_info:
        updater.show_update_dialog(update_info)