import sys
import os
# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import customtkinter as ctk
from desktop.core.api_client import ApiClient
from desktop.core.config import DesktopConfig
from desktop.core.updater import check_and_update_on_startup
from desktop.core.locale import _, initialize_locale
from desktop.core.license_manager import LicenseManager
from desktop.ui.windows import LoginWindow, MainWindow, LicenseWindow

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize locale from config
        language = DesktopConfig.get_language()
        initialize_locale(language)

        self.title(_("MyRhythmNexus - Admin Panel"))
        # Start the app at the minimum allowed size instead of fullscreen
        self.geometry("1280x720")
        self.minsize(1280, 720)  # Minimum window size
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Load backend URL from config
        backend_url = DesktopConfig.load_backend_url()
        
        # For local development, prefer localhost if available
        if os.getenv("DESKTOP_LOCAL_DEV", "").lower() in ("1", "true", "yes"):
            backend_url = "http://localhost:8000"
            print(f"🔧 Local development mode: Using {backend_url}")
        
        self.api_client = ApiClient(base_url=backend_url)
        self.license_manager = LicenseManager(self.api_client)
        
        self.current_window = None
        
        # Check license first
        self.check_license()

    def check_license(self):
        # Try to validate existing license
        result = self.license_manager.validate_license_sync()
        if result.get("valid"):
            self.show_login()
        else:
            self.show_license_activation()

    def show_license_activation(self):
        if self.current_window:
            self.current_window.destroy()
        
        # LicenseWindow is a Frame, so we pack it into the main window
        self.current_window = LicenseWindow(self, self.license_manager, on_success=self.show_login)

    def show_login(self):
        if self.current_window:
            self.current_window.destroy()
        
        self.current_window = LoginWindow(self, self.api_client, on_login_success=self.show_main)

    def show_main(self):
        if self.current_window:
            self.current_window.destroy()
            
        self.current_window = MainWindow(self, self.api_client, on_logout=self.show_login)

if __name__ == "__main__":
    # Check for updates on startup.
    # By default this runs only in the frozen executable to avoid spamming GitHub
    # during development. To force the check in dev, set env var `FORCE_UPDATE_CHECK=1`.
    # Always check for updates on startup (developer requested behavior)
    check_and_update_on_startup()

    app = App()
    app.mainloop()
