import customtkinter as ctk
from desktop.core.api_client import ApiClient
from desktop.ui.views import DashboardView, MembersView, StaffView, SalesView, DefinitionsView, SchedulerView, FinanceView
from desktop.services.qr_reader import QrReaderService
from desktop.ui.views.checkin_dialog import CheckInDialog

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

        self.label_logo = ctk.CTkLabel(self.sidebar, text="MyRhythmNexus", font=("Roboto", 20, "bold"))
        self.label_logo.pack(pady=20, padx=10)

        self.btn_dashboard = ctk.CTkButton(self.sidebar, text="Dashboard", command=lambda: self.show_view("dashboard"))
        self.btn_dashboard.pack(pady=10, padx=10)

        self.btn_scheduler = ctk.CTkButton(self.sidebar, text="Ders Programı", command=lambda: self.show_view("scheduler"))
        self.btn_scheduler.pack(pady=10, padx=10)

        self.btn_members = ctk.CTkButton(self.sidebar, text="Üyeler", command=lambda: self.show_view("members"))
        self.btn_members.pack(pady=10, padx=10)

        self.btn_sales = ctk.CTkButton(self.sidebar, text="Satış & Paketler", command=lambda: self.show_view("sales"))
        self.btn_sales.pack(pady=10, padx=10)

        self.btn_finance = ctk.CTkButton(self.sidebar, text="Finans Geçmişi", command=lambda: self.show_view("finance"))
        self.btn_finance.pack(pady=10, padx=10)

        self.btn_definitions = ctk.CTkButton(self.sidebar, text="Tanımlar", command=lambda: self.show_view("definitions"))
        self.btn_definitions.pack(pady=10, padx=10)

        self.btn_staff = ctk.CTkButton(self.sidebar, text="Personel", command=lambda: self.show_view("staff"))
        self.btn_staff.pack(pady=10, padx=10)

        self.btn_logout = ctk.CTkButton(self.sidebar, text="Çıkış Yap", fg_color="red", hover_color="darkred", command=self.on_logout)
        self.btn_logout.pack(side="bottom", pady=20, padx=10)

        # Main Content Area
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.current_view = None
        self.show_view("dashboard")

    def on_qr_scan(self, qr_token):
        print(f"QR Scanned: {qr_token}")
        # Ensure we are in the main thread (Tkinter callbacks are usually main thread)
        CheckInDialog(self, self.api_client, qr_token)

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
