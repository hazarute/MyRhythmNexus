import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.api_client import ApiClient
import tkinter.messagebox as messagebox
from datetime import datetime
from desktop.ui.components.package_card import PackageCard
from desktop.ui.components.activity_item import ActivityItem

class ProfileTab:
    def __init__(self, parent_frame, api_client: ApiClient, member: dict, on_update_callback):
        self.parent = parent_frame
        self.api_client = api_client
        self.member = member
        self.on_update_callback = on_update_callback

        # State Management (UI References)
        self.lbl_total_debt = None
        self.lbl_active_packages = None
        self.lbl_last_visit = None
        self.lbl_status = None

        self.packages_scroll = None
        self.activity_scroll = None

        self.is_setup = False
        
    def setup(self):
        """Setup profile tab content skeleton (runs once)"""
        if self.is_setup:
            return

        # Grid Configuration
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=1)
        self.parent.grid_rowconfigure(1, weight=1)

        # 1. Stats Row (Top)
        stats_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        stats_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Create Cards (initial placeholder state, will be updated in refresh)
        self.lbl_total_debt = self.create_stat_card(stats_frame, "Toplam Borç", "-", "💰", "#C92C2C", 0)
        self.lbl_active_packages = self.create_stat_card(stats_frame, "Aktif Paketler", "-", "📦", "#3B8ED0", 1)
        self.lbl_last_visit = self.create_stat_card(stats_frame, "Son Ziyaret", "-", "🏃", "#E5B00D", 2)
        self.lbl_status = self.create_stat_card(stats_frame, _("Üyelik Durumu"), "-", _("❌"), "#808080", 3)

        # 2. Middle Section (Split)
        # Left: Active Packages
        left_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        left_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(left_frame, text=_("📦 Aktif Paketler"), font=("Roboto", 16, "bold")).pack(anchor="w", pady=(0, 10))
        self.packages_scroll = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        self.packages_scroll.pack(fill="both", expand=True)

        # Right: Recent Activity
        right_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        right_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(right_frame, text=_("🕒 Son Hareketler (QR)"), font=("Roboto", 16, "bold")).pack(anchor="w", pady=(0, 10))
        self.activity_scroll = ctk.CTkScrollableFrame(right_frame, fg_color=("gray90", "gray20"))
        self.activity_scroll.pack(fill="both", expand=True)

        self.is_setup = True

        # Trigger initial data load
        self.refresh()
    
    def refresh(self):
        """Refresh data and update UI without destroying the layout"""
        if not self.is_setup:
            self.setup()
            return

        subs = []
        checkins = []
        try:
            subs = self.api_client.get(f"/api/v1/sales/subscriptions?member_id={self.member['id']}")
            try:
                checkins = self.api_client.get(f"/api/v1/checkin/history?member_id={self.member['id']}")
            except Exception as e:
                print(f"Error loading checkin history: {e}")
                checkins = []

            # Calculate Total Debt (unchanged logic)
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

            self.update_ui(total_debt, active_packages_count, last_visit, status_text, subs, checkins)

        except Exception as e:
            print(f"Error loading dashboard stats: {e}")
            # Keep skeleton; optionally show error in stats area
            if self.lbl_total_debt is not None:
                self.lbl_total_debt.configure(text="-")
    def update_ui(self, total_debt, active_packages_count, last_visit, status_text, subs, checkins):
        """Update existing widgets with new data (no full redraw)."""

        # 1) Stats
        if self.lbl_total_debt is not None:
            self.lbl_total_debt.configure(text=f"{total_debt:,.2f} TL")
            debt_color = "#E04F5F" if total_debt > 0 else "#2CC985"
            if hasattr(self.lbl_total_debt, 'card_frame'):
                self.lbl_total_debt.card_frame.configure(fg_color=debt_color)

        if self.lbl_active_packages is not None:
            self.lbl_active_packages.configure(text=str(active_packages_count))

        if self.lbl_last_visit is not None:
            self.lbl_last_visit.configure(text=last_visit)

        if self.lbl_status is not None:
            self.lbl_status.configure(text=status_text)
            is_active = (status_text == _("Aktif")) or (status_text == "Aktif")
            status_color = "#26813A" if is_active else "#808080"
            status_icon = _("✅") if is_active else _("❌")
            if hasattr(self.lbl_status, 'card_frame'):
                self.lbl_status.card_frame.configure(fg_color=status_color)
            if hasattr(self.lbl_status, 'icon_label'):
                self.lbl_status.icon_label.configure(text=status_icon)

        # 2) Packages list (destroy children only)
        if self.packages_scroll is not None:
            for widget in self.packages_scroll.winfo_children():
                widget.destroy()

            if subs:
                active_subs = [s for s in subs if s.get('status') == 'active']
                if not active_subs:
                    ctk.CTkLabel(self.packages_scroll, text=_("Aktif paket yok."), text_color="gray").pack(pady=10)
                else:
                    for sub in active_subs:
                        self.create_profile_package_card(self.packages_scroll, sub)
            else:
                ctk.CTkLabel(self.packages_scroll, text=_("Paket bulunamadı."), text_color="gray").pack(pady=10)

        # 3) Activity list (destroy children only)
        if self.activity_scroll is not None:
            for widget in self.activity_scroll.winfo_children():
                widget.destroy()

            if checkins:
                for chk in checkins[:10]:
                    self.create_activity_item(self.activity_scroll, chk)
            else:
                ctk.CTkLabel(self.activity_scroll, text=_("Hareket yok."), text_color="gray").pack(pady=10)

    def create_stat_card(self, parent, title, value, icon, color, col_idx):
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=8)
        card.grid(row=0, column=col_idx, sticky="ew", padx=5)

        icon_lbl = ctk.CTkLabel(card, text=icon, font=("Segoe UI Emoji", 24))
        icon_lbl.pack(side="left", padx=10, pady=10)
        
        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.pack(side="left", fill="y", pady=5)
        
        ctk.CTkLabel(text_frame, text=title, font=("Roboto", 11), text_color="white").pack(anchor="w")
        value_lbl = ctk.CTkLabel(text_frame, text=value, font=("Roboto", 14, "bold"), text_color="white")
        value_lbl.pack(anchor="w")

        # Return a small wrapper that exposes card_frame and icon_label for type-checkers
        class StatWidget:
            def __init__(self, label, card_frame, icon_label):
                self._label = label
                self.card_frame = card_frame
                self.icon_label = icon_label

            def configure(self, *args, **kwargs):
                return self._label.configure(*args, **kwargs)

            def __getattr__(self, name):
                # Delegate other attribute access to the underlying label
                return getattr(self._label, name)

        return StatWidget(value_lbl, card, icon_lbl)

    def create_profile_package_card(self, parent, sub):
        # Deprecated: moved to desktop.ui.components.package_card.PackageCard
        # Kept for compatibility but should not be used anymore.
        # Use the full-style PackageCard so profile list matches packages tab visuals
        pc = PackageCard(parent, sub, is_active=True)
        pc.pack(fill="x", pady=6, padx=5)

    def create_activity_item(self, parent, chk):
        # Create ActivityItem with delete callback so profile tab can remove checkins
        ai = ActivityItem(parent, chk, on_delete=self.delete_checkin)
        ai.pack(fill="x", pady=3, padx=5)

    def delete_checkin(self, checkin_id):
        """Delete a check-in record after user confirmation (used by activity items)."""
        if not messagebox.askyesno(_("Silme Onayı"), _("Bu katılım kaydını silmek istediğinizden emin misiniz?\nBu işlem geri alınamaz.")):
            return

        try:
            self.api_client.delete(f"/api/v1/checkin/history/{checkin_id}")
            messagebox.showinfo(_("Başarılı"), _("Katılım kaydı başarıyla silindi."))
            # Refresh the tab content
            self.refresh()
        except Exception as e:
            messagebox.showerror(_("Hata"), _("Silme işlemi başarısız: {}").format(str(e)))
