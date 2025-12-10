import customtkinter as ctk
from desktop.core.api_client import ApiClient
from desktop.core.locale import _
from desktop.ui.views import DashboardView, MembersView, StaffView, SalesView, DefinitionsView, SchedulerView, FinanceView
from desktop.services.qr_reader import QrReaderService
from desktop.ui.views.checkin_dialog import CheckInDialog
from desktop.core.ui_utils import safe_grab

class MainWindow(ctk.CTkFrame):
    def __init__(self, master, api_client: ApiClient, on_logout: callable):
        super().__init__(master)
        self.api_client = api_client
        self.on_logout = on_logout
        
        # Initialize QR Reader Service
        # We bind to master (Root Window) to capture keys globally
        self.qr_service = QrReaderService(self.master, self.on_qr_scan)

        self.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        self.label_logo = ctk.CTkLabel(self.sidebar, text=_("MyRhythmNexus"), font=("Roboto", 20, "bold"))
        self.label_logo.pack(pady=20, padx=10)

        self.btn_dashboard = ctk.CTkButton(self.sidebar, text=_("Dashboard"), command=lambda: self.show_view("dashboard"))
        self.btn_dashboard.pack(pady=10, padx=10)

        self.btn_scheduler = ctk.CTkButton(self.sidebar, text=_("Ders Programı"), command=lambda: self.show_view("scheduler"))
        self.btn_scheduler.pack(pady=10, padx=10)

        self.btn_members = ctk.CTkButton(self.sidebar, text=_("Üyeler"), command=lambda: self.show_view("members"))
        self.btn_members.pack(pady=10, padx=10)

        self.btn_sales = ctk.CTkButton(self.sidebar, text=_("Satış & Paketler"), command=lambda: self.show_view("sales"))
        self.btn_sales.pack(pady=10, padx=10)

        self.btn_finance = ctk.CTkButton(self.sidebar, text=_("Finans Geçmişi"), command=lambda: self.show_view("finance"))
        self.btn_finance.pack(pady=10, padx=10)

        self.btn_definitions = ctk.CTkButton(self.sidebar, text=_("Tanımlar"), command=lambda: self.show_view("definitions"))
        self.btn_definitions.pack(pady=10, padx=10)

        self.btn_staff = ctk.CTkButton(self.sidebar, text=_("Personel"), command=lambda: self.show_view("staff"))
        self.btn_staff.pack(pady=10, padx=10)

        self.btn_settings = ctk.CTkButton(self.sidebar, text=_("⚙️ Dil Seçimi"), command=self.show_language_dialog, fg_color="#555555", hover_color="#444444")
        self.btn_settings.pack(pady=10, padx=10)

        # License info button
        self.btn_license = ctk.CTkButton(self.sidebar, text=_("Lisans Bilgileri"), command=self.show_license_dialog, fg_color="#555555", hover_color="#444444")
        self.btn_license.pack(pady=10, padx=10)

        self.btn_logout = ctk.CTkButton(self.sidebar, text=_("Çıkış Yap"), fg_color="red", hover_color="darkred", command=self.on_logout)
        self.btn_logout.pack(side="bottom", pady=20, padx=10)

        # Main Content Area
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.current_view = None
        self.show_view("dashboard")

    def on_qr_scan(self, qr_token):
        print(f"QR Scanned: {qr_token}")
        # Ensure we are in the main thread (Tkinter callbacks are usually main thread)
        # Define a safe refresh that updates the current view if it provides `load_data`
        def _refresh_current_view():
            try:
                if getattr(self, 'current_view', None) and hasattr(self.current_view, 'load_data'):
                    try:
                        self.current_view.load_data()
                    except Exception as e:
                        print(f"Error refreshing current view after checkin: {e}")
            except Exception as e:
                print(f"Error in refresh callback: {e}")

        CheckInDialog(self, self.api_client, qr_token, on_refresh=_refresh_current_view)

    def show_view(self, view_name, **kwargs):
        if self.current_view:
            self.current_view.destroy()

        if view_name == "dashboard":
            self.current_view = DashboardView(self.content_area, self.api_client, navigate_callback=self.show_view)
        elif view_name == "members":
            self.current_view = MembersView(self.content_area, self.api_client)
        elif view_name == "staff":
            self.current_view = StaffView(self.content_area, self.api_client)
        elif view_name == "sales":
            self.current_view = SalesView(self.content_area, self.api_client)
        elif view_name == "definitions":
            self.current_view = DefinitionsView(self.content_area, self.api_client)
        elif view_name == "scheduler":
            self.current_view = SchedulerView(self.content_area, self.api_client)
        elif view_name == "finance":
            self.current_view = FinanceView(self.content_area, self.api_client, **kwargs)
        
        if self.current_view:
            self.current_view.pack(fill="both", expand=True)

    def show_language_dialog(self):
        """Show language selection dialog"""
        from desktop.core.locale import get_available_languages, set_language, get_current_language
        from desktop.core.config import DesktopConfig
        
        dialog = ctk.CTkToplevel(self.master)
        dialog.title(_("Dil Seçimi"))
        dialog.geometry("400x280")
        dialog.resizable(False, False)
        
        # Center and grab
        safe_grab(dialog)
        
        # Title
        title = ctk.CTkLabel(dialog, text=_("Dil Seçimi / Language Selection"), 
                            font=("Roboto", 16, "bold"))
        title.pack(pady=15, padx=20)
        
        # Current language
        current_lang = get_current_language()
        lang_names = get_available_languages()
        current_display = lang_names.get(current_lang, current_lang)
        
        info = ctk.CTkLabel(dialog, text=f"{_('Seçili Dil')}: {current_display}", 
                           font=("Roboto", 12), text_color="gray")
        info.pack(pady=10, padx=20)
        
        # Separator
        separator = ctk.CTkFrame(dialog, height=1, fg_color="gray30")
        separator.pack(fill="x", padx=20, pady=10)
        
        # Language buttons frame
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=15, padx=20, fill="both", expand=False)
        
        def select_language(lang: str):
            """Change language and restart application"""
            DesktopConfig.set_language(lang)
            set_language(lang)
            dialog.destroy()
            # Show message
            from tkinter import messagebox
            messagebox.showinfo(_("Başarılı"), 
                              _("Dil değiştirildi. Lütfen uygulamayı yeniden başlatınız."))
            # Restart app
            import os
            os.execl(__import__('sys').executable, __import__('sys').executable, *__import__('sys').argv)
        
        # Turkish button
        btn_tr = ctk.CTkButton(button_frame, text=_("Türkçe (Turkish)"), 
                              command=lambda: select_language("tr"),
                              height=35,
                              fg_color="#3B8ED0", hover_color="#36719F")
        btn_tr.pack(pady=8, fill="x", expand=False)
        
        # English button
        btn_en = ctk.CTkButton(button_frame, text=_("English (İngilizce)"), 
                              command=lambda: select_language("en"),
                              height=35,
                              fg_color="#3B8ED0", hover_color="#36719F")
        btn_en.pack(pady=8, fill="x", expand=False)
        
        # Close button
        btn_close = ctk.CTkButton(dialog, text=_("❌ İptal"), 
                                 command=dialog.destroy,
                                 height=35,
                                 fg_color="#555555", hover_color="#333333")
        btn_close.pack(pady=15, padx=20, fill="x")

    def show_license_dialog(self):
        """Show a dialog with license information and quick actions"""
        try:
            from desktop.ui.views.dialogs.license_info_dialog import LicenseInfoDialog
        except Exception:
            # If dialog import fails, show a simple messagebox
            from tkinter import messagebox
            messagebox.showerror("Hata", "Lisans diyaloğu yüklenemedi.")
            return

        # Create and show dialog
        dialog = LicenseInfoDialog(self.master, self.api_client)
        safe_grab(dialog)