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
        self.grid_rowconfigure(3, weight=1) # New row for pending approvals

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

        # Left: Pending Member Approvals
        self.pending_frame = ctk.CTkFrame(self)
        self.pending_frame.grid(row=3, column=0, sticky="nsew", padx=(20, 10), pady=20)
        
        ctk.CTkLabel(self.pending_frame, text=_("Yeni Üye Onayları"), font=("Roboto", 16, "bold")).pack(pady=10, padx=10, anchor="w")
        self.pending_list = ctk.CTkScrollableFrame(self.pending_frame, fg_color="transparent")
        self.pending_list.pack(fill="both", expand=True, padx=5, pady=5)

        # Right: Activity Feed
        self.activity_frame = ctk.CTkFrame(self)
        self.activity_frame.grid(row=2, column=1, rowspan=2, sticky="nsew", padx=(10, 20), pady=20)
        
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
            # Provide `on_refresh` so the dashboard reloads when the dialog closes
            CheckInDialog(self.winfo_toplevel(), self.api_client, qr_token, on_refresh=self.load_data)


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

            # Update Pending Approvals List
            for widget in self.pending_list.winfo_children():
                widget.destroy()

            try:
                pending_members = self.api_client.get("/api/v1/members/pending")
                if not pending_members:
                    ctk.CTkLabel(self.pending_list, text=_("Onay bekleyen üye yok."), text_color="gray").pack(pady=10)
                else:
                    for member in pending_members:
                        self.create_pending_member_card(member)
            except Exception as e:
                print(f"Error loading pending members: {e}")
                ctk.CTkLabel(self.pending_list, text=_("Onay listesi yüklenemedi."), text_color="red").pack(pady=10)

            # Update Activity Feed (Only Check-ins)
            for widget in self.activity_list.winfo_children():
                widget.destroy()

            activities = data.get("recent_activities", [])
            checkin_activities = [item for item in activities if item['type'] == 'checkin']

            if not checkin_activities:
                ctk.CTkLabel(self.activity_list, text=_("Henüz hareket yok."), text_color="gray").pack(pady=10)
            else:
                for item in checkin_activities:
                    self.create_activity_item(item)

        except Exception as e:
            print(f"Error loading dashboard data: {e}")
            self.card_members.configure(text=_("Err"))

    def create_schedule_item(self, item):
        # Modern card design for schedule items — improved layout
        frame = ctk.CTkFrame(self.schedule_list, fg_color=("#2B2B2B", "#1E1E1E"), corner_radius=8, border_width=1, border_color="#404040")
        frame.pack(fill="x", pady=6, padx=6)

        # Main content frame using grid for consistent alignment
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=10)
        content.grid_columnconfigure(1, weight=1)

        # Time info (fixed-width column)
        start_dt = datetime.fromisoformat(item.get('start_time', '').replace('Z', '+00:00')) if item.get('start_time') else None
        time_str = start_dt.strftime("%H:%M") if start_dt else "--:--"
        time_label = ctk.CTkLabel(
            content,
            text=time_str,
            font=("Roboto", 14, "bold"),
            text_color="#3B8ED0",
            width=72,
            anchor="w"
        )
        time_label.grid(row=0, column=0, sticky="w")

        # Details column: title and optional subtitle (instructor/location)
        details_frame = ctk.CTkFrame(content, fg_color="transparent")
        details_frame.grid(row=0, column=1, sticky="w")

        title_label = ctk.CTkLabel(
            details_frame,
            text=item.get('title', _('Ders')), 
            font=("Roboto", 14, "bold"),
            text_color="white"
        )
        title_label.pack(anchor="w")

        # Subtitle (use instructor/location if available) — muted color
        subtitle_parts = []
        if item.get('instructor'):
            subtitle_parts.append(item['instructor'])
        if item.get('location'):
            subtitle_parts.append(item['location'])
        subtitle = " • ".join(subtitle_parts) if subtitle_parts else item.get('subtitle', '')
        if subtitle:
            ctk.CTkLabel(details_frame, text=subtitle, font=("Roboto", 11), text_color="#A8A8A8").pack(anchor="w", pady=(2,0))

        # Occupancy badge (right aligned)
        occ_text = item.get('occupancy', '')
        occ_is_full = occ_text.lower() in ("dolu", "full", "tam")
        occupancy_color = "#E04F5F" if occ_is_full else "#2CC985"
        badge_frame = ctk.CTkFrame(content, fg_color=occupancy_color, corner_radius=8)
        badge_frame.grid(row=0, column=2, sticky="e", padx=(8,0))
        occ_label = ctk.CTkLabel(badge_frame, text=occ_text or "-", font=("Roboto", 11, "bold"), text_color="white")
        occ_label.pack(padx=8, pady=6)

    def create_activity_item(self, item):
        # Improved activity card design with consistent colors
        card_bg = ("#2B2B2B", "#1E1E1E")
        card = ctk.CTkFrame(self.activity_list, fg_color=card_bg, corner_radius=8, border_width=1, border_color="#404040")
        card.pack(fill="x", pady=6, padx=6)

        # Main content using grid: icon | details | time
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=10)
        content.grid_columnconfigure(1, weight=1)

        # Icon badge
        icon_bg = "#3B8ED0"
        icon_frame = ctk.CTkFrame(content, fg_color=icon_bg, width=38, height=38, corner_radius=8)
        icon_frame.grid(row=0, column=0, sticky="w")
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text="📲", font=("Segoe UI Emoji", 14), text_color="white").pack(expand=True)

        # Details (name + description)
        details = ctk.CTkFrame(content, fg_color="transparent")
        details.grid(row=0, column=1, sticky="w", padx=(10,8))

        name_label = ctk.CTkLabel(
            details,
            text=item.get('user_name', _('Bilinmiyor')),
            font=("Roboto", 13, "bold"),
            text_color="#3B8ED0"
        )
        name_label.pack(anchor="w")

        desc_text = item.get('description', '')
        if desc_text:
            ctk.CTkLabel(details, text=desc_text, font=("Roboto", 12), text_color="#CFCFCF").pack(anchor="w", pady=(2,0))

        # Time info (right aligned, muted)
        time_frame = ctk.CTkFrame(content, fg_color="transparent")
        time_frame.grid(row=0, column=2, sticky="e")
        if item.get('timestamp'):
            try:
                dt = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                date_part = dt.strftime('%Y-%m-%d')
                time_part = dt.strftime('%H:%M')
                time_display = f"{time_part}\n{date_part}"
            except Exception:
                time_display = item['timestamp']
        else:
            time_display = ""
        ctk.CTkLabel(time_frame, text=time_display, font=("Roboto", 11, "bold"), text_color="#8F8F8F", justify="right").pack()

    def create_pending_member_card(self, member):
        """Create a pending member approval card"""
        card = ctk.CTkFrame(self.pending_list, corner_radius=12, 
                           fg_color=("#F5F5F5", "#2B2B2B"), 
                           border_width=2,
                           border_color=("#DDDDDD", "#3A3A3A"))
        card.pack(fill="x", pady=8, padx=5)
        
        # Left section - Member info
        left_frame = ctk.CTkFrame(card, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=20, pady=15)
        
        # Name and status
        name_row = ctk.CTkFrame(left_frame, fg_color="transparent")
        name_row.pack(anchor="w")
        
        name = f"{member.get('first_name')} {member.get('last_name')}"
        lbl_name = ctk.CTkLabel(name_row, text=f"👤 {name}", 
                               font=("Roboto", 18, "bold"), 
                               anchor="w")
        lbl_name.pack(side="left", padx=(0, 15))
        
        # Status badge (pending)
        status_text = _("⏳ Onay Bekliyor")
        status_color = ("#F39C12", "#F39C12")  # Orange
        
        lbl_status = ctk.CTkLabel(name_row, text=status_text,
                                 font=("Roboto", 12, "bold"),
                                 text_color=status_color)
        lbl_status.pack(side="left")
        
        # Contact info
        info_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        info_frame.pack(anchor="w", pady=(6, 0))
        
        email = member.get('email')
        lbl_email = ctk.CTkLabel(info_frame, text=f"📧 {email}", 
                                font=("Roboto", 13),
                                text_color=("#555555", "#AAAAAA"),
                                anchor="w")
        lbl_email.pack(side="left", padx=(0, 20))
        
        phone = member.get('phone_number') or "-"
        lbl_phone = ctk.CTkLabel(info_frame, text=f"📞 {phone}", 
                                font=("Roboto", 13),
                                text_color=("#555555", "#AAAAAA"),
                                anchor="w")
        lbl_phone.pack(side="left")
        
        # Right section - Action buttons
        right_frame = ctk.CTkFrame(card, fg_color="transparent")
        right_frame.pack(side="right", padx=20, pady=15)
        
        # Approve button
        btn_approve = ctk.CTkButton(right_frame, text=_("✅ Onayla"), 
                                  width=100, height=40,
                                  fg_color="#2CC985", 
                                  hover_color="#229966",
                                  font=("Roboto", 14, "bold"),
                                  command=lambda m=member: self.approve_member(m))
        btn_approve.pack(side="left", padx=(0, 5))
        
        # Reject button
        btn_reject = ctk.CTkButton(right_frame, text=_("❌ Reddet"), 
                                  width=100, height=40,
                                  fg_color="#E04F5F", 
                                  hover_color="#C0392B",
                                  font=("Roboto", 14, "bold"),
                                  command=lambda m=member: self.reject_member(m))
        btn_reject.pack(side="left")

    def approve_member(self, member):
        """Approve pending member"""
        try:
            self.api_client.put(f"/api/v1/members/{member['id']}", json={"is_active": True})
            self.load_data()  # Refresh the dashboard
        except Exception as e:
            print(f"Error approving member: {e}")

    def reject_member(self, member):
        """Reject pending member"""
        try:
            self.api_client.delete(f"/api/v1/members/{member['id']}")
            self.load_data()  # Refresh the dashboard
        except Exception as e:
            print(f"Error rejecting member: {e}")
