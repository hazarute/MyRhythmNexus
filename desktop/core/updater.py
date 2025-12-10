import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from desktop.core.config import DesktopConfig, load_config, save_config, add_backend_url
from desktop.services.update_manager import UpdateManager
from desktop.ui.views.dialogs.update_dialog import UpdateDialog

class AutoUpdater:
    """
    Facade for update and configuration management.
    Delegates to UpdateManager and uses core config functions.
    """

    def __init__(self, current_version: str = "1.0.0"):
        self.update_manager = UpdateManager(current_version)

    # --- Version / Update Methods ---

    def get_current_version_info(self) -> Dict[str, Any]:
        return self.update_manager.get_current_version_info()

    def save_version_info(self, version_info: Dict[str, Any]):
        self.update_manager.save_version_info(version_info)

    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        return self.update_manager.check_for_updates()

    def download_and_install_update(self, update_info: Dict[str, Any], progress_callback=None) -> bool:
        success = self.update_manager.download_and_install_update(update_info, progress_callback)
        if success:
            # Update version info locally to mark as installed
            vi = {
                'version': update_info['version'],
                'installed': True,
                'updated_at': str(time.time())
            }
            # Preserve last_check
            prev = self.get_current_version_info()
            if 'last_check' in prev:
                vi['last_check'] = prev['last_check']
            self.save_version_info(vi)
        return success

    def show_update_dialog(self, update_info: Dict[str, Any]) -> bool:
        dialog = UpdateDialog(update_info, self.download_and_install_update)
        result = dialog.show()
        if result:
            self.restart_application()
        return result

    def restart_application(self):
        self.update_manager.restart_application()

    # --- Config Methods (Delegated to desktop.core.config) ---

    def get_config(self) -> Dict[str, Any]:
        return load_config()

    def save_config(self, cfg: Dict[str, Any]):
        save_config(cfg)

    def add_backend_url(self, url: str):
        add_backend_url(url)

    def get_backend_urls(self) -> List[str]:
        cfg = load_config()
        return cfg.get('backend_urls', [])


def check_and_update_on_startup():
    """Check for updates on application startup"""
    updater = AutoUpdater()
    try:
        interval_minutes = getattr(DesktopConfig, 'CHECK_UPDATE_INTERVAL_MINUTES', 60)
        interval_seconds = int(interval_minutes) * 60

        current_info = updater.get_current_version_info()
        last_check = current_info.get('last_check')
        current_time = time.time()

        if last_check and (current_time - last_check) < interval_seconds:
            return

        current_info['last_check'] = current_time
        updater.save_version_info(current_info)

        update_info = updater.check_for_updates()
        if update_info:
            updater.show_update_dialog(update_info)
    except Exception as e:
        print(f"Update check failed on startup: {e}")
