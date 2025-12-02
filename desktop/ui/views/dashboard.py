import customtkinter as ctk
from desktop.core.api_client import ApiClient
from desktop.core.locale import _
from datetime import datetime

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, api_client: ApiClient, navigate_callback=None):
        super().__init__(master)
        self.api_client = api_client
        self.navigate_callback = navigate_callback
        
        # Grid Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1) # Content area expands

        # --- Header Section ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))
        
        self.label_title = ctk.CTkLabel(self.header_frame, text=_("Genel Bakış"), font=("Roboto", 24, "bold"))
        self.label_title.pack(side="left")

        # Quick Actions
        self.actions_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.actions_frame.pack(side="right")

        self.btn_add_member = ctk.CTkButton(self.actions_frame, text=_("+ Üye Ekle"), width=100, fg_color="#3B8ED0", hover_color="#36719F", command=self.show_add_member_dialog) # Blue
        self.btn_add_member.pack(side="left", padx=5)
        
        self.btn_quick_sale = ctk.CTkButton(self.actions_frame, text=_("+ Satış Yap"), width=100, fg_color="#2CC985", hover_color="#25A86F", command=lambda: self.navigate("sales")) # Green
        self.btn_quick_sale.pack(side="left", padx=5)

        self.btn_qr_checkin = ctk.CTkButton(self.actions_frame, text=_("📷 QR Giriş"), width=100, fg_color="#E5B00D", hover_color="#C4960B", text_color="black", command=self.manual_qr_checkin) # Yellow
        self.btn_qr_checkin.pack(side="left", padx=5)
        
        self.btn_refresh = ctk.CTkButton(self.actions_frame, text=_("🔄"), width=40, command=self.load_data)
        self.btn_refresh.pack(side="left", padx=5)

        # --- Stats Cards Section ---
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_members = self.create_stat_card(self.cards_frame, _("Aktif Üyeler"), "👥", "#3B8ED0", 0)
        self.card_classes = self.create_stat_card(self.cards_frame, _("Bugünkü Dersler"), "🧘", "#2CC985", 1)
        self.card_pending = self.create_stat_card(self.cards_frame, _("Toplam Borç"), "💳", "#E04F5F", 2)
        self.card_revenue = self.create_stat_card(self.cards_frame, _("Aylık Ciro"), "💰", "#9C27B0", 3)

        # --- Content Section (Split View) ---
        # Left: Today's Schedule
        self.schedule_frame = ctk.CTkFrame(self)
        self.schedule_frame.grid(row=2, column=0, sticky="nsew", padx=(20, 10), pady=20)
        
        ctk.CTkLabel(self.schedule_frame, text=_("Bugünün Programı"), font=("Roboto", 16, "bold")).pack(pady=10, padx=10, anchor="w")
        self.schedule_list = ctk.CTkScrollableFrame(self.schedule_frame, fg_color="transparent")
        self.schedule_list.pack(fill="both", expand=True, padx=5, pady=5)

        # Right: Activity Feed
        self.activity_frame = ctk.CTkFrame(self)
        self.activity_frame.grid(row=2, column=1, sticky="nsew", padx=(10, 20), pady=20)
        
        ctk.CTkLabel(self.activity_frame, text=_("Son Hareketler"), font=("Roboto", 16, "bold")).pack(pady=10, padx=10, anchor="w")
        self.activity_list = ctk.CTkScrollableFrame(self.activity_frame, fg_color=("gray90", "gray20"))
        self.activity_list.pack(fill="both", expand=True, padx=5, pady=5)

        self.start_auto_refresh()

    def start_auto_refresh(self):
        try:
            if self.winfo_exists():
                self.load_data()
                self.after(60000, self.start_auto_refresh)
        except Exception:
            pass

    def navigate(self, view_name):
        if self.navigate_callback:
            self.navigate_callback(view_name)

    def show_add_member_dialog(self):
        """Open add member dialog"""
        from desktop.ui.views.dialogs import AddMemberDialog
        AddMemberDialog(self.winfo_toplevel(), self.api_client, on_success=self.load_data)
    
    def manual_qr_checkin(self):
        dialog = ctk.CTkInputDialog(text=_("QR Kodu Giriniz:"), title=_("Manuel Giriş"))
        qr_token = dialog.get_input()
        if qr_token:
            from desktop.ui.views.checkin_dialog import CheckInDialog
            CheckInDialog(self.winfo_toplevel(), self.api_client, qr_token)


    def create_stat_card(self, parent, title, icon, color, col_idx):
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=10)
        card.grid(row=0, column=col_idx, sticky="ew", padx=10)
        
        # Icon
        lbl_icon = ctk.CTkLabel(card, text=icon, font=("Segoe UI Emoji", 32), text_color="white")
        lbl_icon.pack(side="left", padx=15, pady=15)
        
        # Text Container
        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.pack(side="left", fill="y", pady=10)
        
        lbl_title = ctk.CTkLabel(text_frame, text=title, font=("Roboto", 12), text_color="white")
        lbl_title.pack(anchor="w")
        
        lbl_value = ctk.CTkLabel(text_frame, text=_("..."), font=("Roboto", 20, "bold"), text_color="white")
        lbl_value.pack(anchor="w")
        
        return lbl_value # Return label to update later

    def load_data(self):
        try:
            data = self.api_client.get("/api/v1/stats/dashboard")
            
            # Update Cards
            self.card_members.configure(text=str(data.get("active_members", 0)))
            self.card_classes.configure(text=str(data.get("todays_classes", 0)))
            
            pending = data.get("pending_payments_amount", 0.0)
            self.card_pending.configure(text=f"₺{pending:,.2f}")
            
            revenue = data.get("monthly_revenue", 0.0)
            self.card_revenue.configure(text=f"₺{revenue:,.2f}")

            # Update Schedule List
            for widget in self.schedule_list.winfo_children():
                widget.destroy()
                
            schedule = data.get("todays_schedule", [])
            if not schedule:
                ctk.CTkLabel(self.schedule_list, text=_("Bugün ders yok."), text_color="gray").pack(pady=10)
            else:
                for item in schedule:
                    self.create_schedule_item(item)

            # Update Activity Feed
            for widget in self.activity_list.winfo_children():
                widget.destroy()
                
            activities = data.get("recent_activities", [])
            if not activities:
                ctk.CTkLabel(self.activity_list, text=_("Henüz hareket yok."), text_color="gray").pack(pady=10)
            else:
                for item in activities:
                    self.create_activity_item(item)

        except Exception as e:
            print(f"Error loading dashboard data: {e}")
            self.card_members.configure(text=_("Err"))

    def create_schedule_item(self, item):
        frame = ctk.CTkFrame(self.schedule_list, fg_color=("gray90", "gray20"))
        frame.pack(fill="x", pady=2, padx=2)
        
        start_dt = datetime.fromisoformat(item['start_time'].replace('Z', '+00:00'))
        time_str = start_dt.strftime("%H:%M")
        
        ctk.CTkLabel(frame, text=time_str, font=("Roboto", 14, "bold"), width=60).pack(side="left", padx=5)
        ctk.CTkLabel(frame, text=item['title'], font=("Roboto", 14)).pack(side="left", padx=5, expand=True, anchor="w")
        
        occupancy_color = "red" if item['occupancy'] == "Dolu" else "green"
        ctk.CTkLabel(frame, text=item['occupancy'], text_color=occupancy_color, font=("Roboto", 12, "bold")).pack(side="right", padx=10)

    def create_activity_item(self, item):
        # Modern card design for each activity
        # Different background color for check-ins
        bg_color = "#2B2B2B"  # Default dark
        if item['type'] == 'checkin':
            bg_color = "#698FAA"  # Light blue for check-ins
        
        card = ctk.CTkFrame(self.activity_list, fg_color=bg_color, corner_radius=8, border_width=1, border_color="#404040")
        card.pack(fill="x", pady=3, padx=5)
        
        # Main content frame
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=10)
        
        # Header with icon and time
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 4))
        
        # Icon based on type with colored background
        icon = "🔹"
        accent_color = "#666666"  # Default gray
        if item['type'] == 'checkin':
            icon = "📲"
            accent_color = "#3B8ED0"  # Blue for checkin
        elif item['type'] == 'sale':
            icon = "💳"
            accent_color = "#2CC985"  # Green for sale
        elif item['type'] == 'booking':
            icon = "📅"
            accent_color = "#E5B00D"  # Gold for booking
        
        # Icon with colored background
        icon_frame = ctk.CTkFrame(header_frame, fg_color=accent_color, width=32, height=32, corner_radius=6)
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text=icon, font=("Segoe UI Emoji", 14)).pack(expand=True)
        
        # User Name
        name_text_color = "white" if item['type'] != 'checkin' else "#1976D2"
        name_label = ctk.CTkLabel(
            header_frame, 
            text=item['user_name'], 
            font=("Roboto", 16, "bold"), 
            text_color=name_text_color
        )
        name_label.pack(side="left", padx=(12, 0))
        
        # Time info
        dt = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
        date_part = dt.strftime('%Y-%m-%d')
        time_part = dt.strftime('%H:%M')
        time_display = f"{time_part} • {date_part}"
        time_text_color = "gray70" if item['type'] != 'checkin' else "#424242"
        time_label = ctk.CTkLabel(
            header_frame, 
            text=time_display, 
            font=("Roboto", 14), 
            text_color=time_text_color
        )
        time_label.pack(side="left", padx=(15, 0))
        
        # Description
        desc_text_color = "gray70" if item['type'] != 'checkin' else "black"
        desc_font = ("Roboto", 12) if item['type'] != 'checkin' else ("Roboto", 14, "bold")
        ctk.CTkLabel(content, text=item['description'], font=desc_font, text_color=desc_text_color, anchor="w").pack(fill="x")
