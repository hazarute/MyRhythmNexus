import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.api_client import ApiClient
from datetime import datetime

class ProfileTab:
    def __init__(self, parent_frame, api_client: ApiClient, member: dict, on_update_callback):
        self.parent = parent_frame
        self.api_client = api_client
        self.member = member
        self.on_update_callback = on_update_callback
        
    def setup(self):
        """Setup profile tab content"""
        # Grid Configuration
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=1)
        self.parent.grid_rowconfigure(1, weight=1)

        # 1. Stats Row (Top)
        stats_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        stats_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Fetch Data for Stats
        try:
            subs = self.api_client.get(f"/api/v1/sales/subscriptions?member_id={self.member['id']}")
            try:
                checkins = self.api_client.get(f"/api/v1/checkin/history?member_id={self.member['id']}")
            except Exception as e:
                print(f"Error loading checkin history: {e}")
                checkins = []
            
            # Calculate Total Debt
            total_debt = 0.0
            for s in subs:
                if s.get('status') == 'cancelled': 
                    continue
                
                price = float(s.get('purchase_price', 0))
                paid = sum(float(p.get('amount_paid', 0)) for p in s.get('payments', []))
                remaining = price - paid
                if remaining > 0:
                    total_debt += remaining
            
            active_packages_count = sum(1 for s in subs if s.get('status') == 'active')
            last_visit = checkins[0].get('check_in_time', '')[:10] if checkins else "Yok"
            status_text = "Aktif" if self.member.get('is_active') else "Pasif"

            # Create Cards
            self.create_stat_card(stats_frame, "Toplam Borç", f"{total_debt:,.2f} TL", "💰", "#E04F5F" if total_debt > 0 else "#2CC985", 0)
            self.create_stat_card(stats_frame, "Aktif Paketler", str(active_packages_count), "📦", "#3B8ED0", 1)
            self.create_stat_card(stats_frame, "Son Ziyaret", last_visit, "🏃", "#E5B00D", 2)
            self.create_stat_card(stats_frame, _("Üyelik Durumu"), status_text, _("✅") if status_text==_("Aktif") else _("❌"), "#26813A" if status_text==_("Aktif") else "#808080", 3)

        except Exception as e:
            print(f"Error loading dashboard stats: {e}")
            ctk.CTkLabel(stats_frame, text=_("İstatistikler yüklenemedi")).pack()

        # 2. Middle Section (Split)
        # Left: Active Packages
        left_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        left_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(left_frame, text=_("📦 Aktif Paketler"), font=("Roboto", 16, "bold")).pack(anchor="w", pady=(0, 10))
        packages_scroll = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        packages_scroll.pack(fill="both", expand=True)

        if subs:
            active_subs = [s for s in subs if s.get('status') == 'active']
            if not active_subs:
                ctk.CTkLabel(packages_scroll, text=_("Aktif paket yok."), text_color="gray").pack(pady=10)
            else:
                for sub in active_subs:
                    self.create_profile_package_card(packages_scroll, sub)
        else:
            ctk.CTkLabel(packages_scroll, text=_("Paket bulunamadı."), text_color="gray").pack(pady=10)

        # Right: Recent Activity
        right_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        right_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(right_frame, text=_("🕒 Son Hareketler (QR)"), font=("Roboto", 16, "bold")).pack(anchor="w", pady=(0, 10))
        activity_scroll = ctk.CTkScrollableFrame(right_frame, fg_color=("gray90", "gray20"))
        activity_scroll.pack(fill="both", expand=True)

        if checkins:
            for chk in checkins[:10]:
                self.create_activity_item(activity_scroll, chk)
        else:
            ctk.CTkLabel(activity_scroll, text=_("Hareket yok."), text_color="gray").pack(pady=10)
    
    def refresh(self):
        """Refresh the tab"""
        for widget in self.parent.winfo_children():
            widget.destroy()
        self.setup()

    def create_stat_card(self, parent, title, value, icon, color, col_idx):
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=8)
        card.grid(row=0, column=col_idx, sticky="ew", padx=5)
        
        ctk.CTkLabel(card, text=icon, font=("Segoe UI Emoji", 24)).pack(side="left", padx=10, pady=10)
        
        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.pack(side="left", fill="y", pady=5)
        
        ctk.CTkLabel(text_frame, text=title, font=("Roboto", 11), text_color="white").pack(anchor="w")
        ctk.CTkLabel(text_frame, text=value, font=("Roboto", 14, "bold"), text_color="white").pack(anchor="w")

    def create_profile_package_card(self, parent, sub):
        bg_color = "#333333"
        accent_color = "#3B8ED0"
        
        card = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=6)
        card.pack(fill="x", pady=2, padx=2)
        
        stripe = ctk.CTkFrame(card, fg_color=accent_color, width=3, corner_radius=0)
        stripe.pack(side="left", fill="y")
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=8, pady=4)
        
        pkg_name = sub.get('package', {}).get('name', 'Paket')
        ctk.CTkLabel(content, text=_("📦 {}").format(pkg_name), 
                    font=("Roboto", 18, "bold"), 
                    text_color="white").pack(anchor="w")
        
        end_date = sub.get('end_date', '')[:10]
        plan = sub.get('package', {}).get('plan', {})
        access_type = plan.get('access_type', 'SESSION_BASED')
        used = sub.get('used_sessions', 0)
        limit = plan.get('sessions_granted', 0)
        
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(fill="x", pady=(1, 0))
        
        ctk.CTkLabel(info_frame, text=_("Bitiş: {}").format(end_date), 
                    font=("Roboto", 15), 
                    text_color="gray70").pack(side="left")
        
        if access_type == 'TIME_BASED':
            ctk.CTkLabel(info_frame, text=_("  •  ♾️ Sınırsız ({} giriş)").format(used), 
                        font=("Roboto", 15, "bold"), 
                        text_color="#3B8ED0").pack(side="left")
        elif limit and limit > 0:
            remaining = limit - used
            progress_text = _("  •  {} ders kaldı").format(remaining)
            color = "#2CC985" if remaining > 3 else "#E5B00D" if remaining > 0 else "#E04F5F"
            ctk.CTkLabel(info_frame, text=progress_text, 
                        font=("Roboto", 15, "bold"), 
                        text_color=color).pack(side="left")
        else:
            ctk.CTkLabel(info_frame, text=_("  •  ♾️ Sınırsız"), 
                        font=("Roboto", 15, "bold"), 
                        text_color="#3B8ED0").pack(side="left")

    def create_activity_item(self, parent, chk):
        # Modern card design for each activity
        card = ctk.CTkFrame(parent, fg_color="#2B2B2B", corner_radius=8, border_width=1, border_color="#404040")
        card.pack(fill="x", pady=3, padx=5)
        
        # Main content frame
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=10)
        
        # Header with icon and time
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 4))
        
        # Determine icon and color based on event type
        event_name = chk.get('event_name', 'Giriş')
        subscription_name = chk.get('subscription_name', 'Bilinmeyen Paket')
        
        if "Seans Bazlı" in event_name:
            icon = "🎯"
            accent_color = "#E5B00D"  # Gold for session-based
            display_name = subscription_name  # Show subscription name for session-based
        elif "Zaman Bazlı" in event_name:
            icon = "⏰"
            accent_color = "#3B8ED0"  # Blue for time-based
            display_name = subscription_name  # Show subscription name for time-based
        else:
            icon = "📅"
            accent_color = "#2CC985"  # Green for class events
            display_name = event_name  # Show event name for class events
        
        # Icon with colored background
        icon_frame = ctk.CTkFrame(header_frame, fg_color=accent_color, width=32, height=32, corner_radius=6)
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text=icon, font=("Segoe UI Emoji", 14)).pack(expand=True)
        
        # Time info - Now automatically converted to local time by ApiClient
        check_in_time_str = chk.get('check_in_time', '')
        if check_in_time_str:
            try:
                # Parse local time (already converted by ApiClient)
                if 'T' in check_in_time_str:
                    local_time = datetime.fromisoformat(check_in_time_str)
                else:
                    local_time = datetime.strptime(check_in_time_str, '%Y-%m-%d %H:%M:%S')
                
                date_part = local_time.strftime('%Y-%m-%d')
                time_part = local_time.strftime('%H:%M')
            except Exception as e:
                print(f"Error parsing datetime {check_in_time_str}: {e}")
                # Fallback
                time_info = check_in_time_str.replace('T', ' ')[:16]
                time_parts = time_info.split(' ')
                date_part = time_parts[0] if len(time_parts) > 0 else ""
                time_part = time_parts[1][:5] if len(time_parts) > 1 else ""
        else:
            date_part = ""
            time_part = ""
        
        # Subscription Name
        name_label = ctk.CTkLabel(
            header_frame, 
            text=display_name, 
            font=("Roboto", 16, "bold"), 
            text_color="white"
        )
        name_label.pack(side="left", padx=(12, 0))
        
        # Time and Date
        time_display = f"{time_part} • {date_part}" if time_part and date_part else ""
        time_label = ctk.CTkLabel(
            header_frame, 
            text=time_display, 
            font=("Roboto", 14), 
            text_color="gray70"
        )
        time_label.pack(side="left", padx=(15, 0))
        
        # Additional info (verified by)
        verified_by = chk.get('verified_by_name', 'Sistem')
        if verified_by != 'Sistem':
            ctk.CTkLabel(content, text=_("✓ {}").format(verified_by), font=("Roboto", 10), text_color="gray60", anchor="w").pack(fill="x")
        else:
            ctk.CTkLabel(content, text=_("🤖 Otomatik"), font=("Roboto", 10), text_color="gray60", anchor="w").pack(fill="x")
