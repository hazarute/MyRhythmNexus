import sys
import os
# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import customtkinter as ctk
from desktop.core.api_client import ApiClient
from desktop.core.config import DesktopConfig
from desktop.core.updater import check_and_update_on_startup
from desktop.core.locale import _, initialize_locale
from desktop.ui.windows import LoginWindow, MainWindow

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize locale from config
        language = DesktopConfig.get_language()
        initialize_locale(language)

        self.title(_("MyRhythmNexus - Admin Panel"))
        self.geometry("1000x700")
        self.minsize(1280, 720)  # Minimum window size
        self.after(0, lambda: self.state('zoomed'))
        
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Load backend URL from config
        backend_url = DesktopConfig.load_backend_url()
        self.api_client = ApiClient(base_url=backend_url)
        
        self.current_window = None
        self.show_login()

    def show_login(self):
        if self.current_window:
            self.current_window.destroy()
        
        self.current_window = LoginWindow(self, self.api_client, on_login_success=self.show_main)

    def show_main(self):
        if self.current_window:
            self.current_window.destroy()
            
        self.current_window = MainWindow(self, self.api_client, on_logout=self.show_login)

if __name__ == "__main__":
    # Check for updates on startup (only in compiled version)
    if getattr(sys, 'frozen', False):
        check_and_update_on_startup()

    app = App()
    app.mainloop()
