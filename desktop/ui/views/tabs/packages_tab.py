import customtkinter as ctk
from datetime import datetime
from desktop.ui.components.date_utils import format_ddmmyyyy
from desktop.core.locale import _
from desktop.core.api_client import ApiClient
from desktop.ui.components.date_picker import get_weekday_name
from tkinter import messagebox
from desktop.ui.components.package_card import PackageCard

class PackagesTab:
    def __init__(self, parent_frame, api_client: ApiClient, member: dict, on_refresh_payments):
        self.parent = parent_frame
        self.api_client = api_client
        self.member = member
        self.on_refresh_payments = on_refresh_payments
        # State for optimized UI updates
        self.lbl_active_header = None
        self.frame_active_list = None
        self.lbl_past_header = None
        self.frame_past_list = None
        self.main_scroll = None
        self.is_setup = False
        
    def setup(self):
        """Setup static UI skeleton (runs once)."""
        if self.is_setup:
            return

        # Main scroll container (created once)
        self.main_scroll = ctk.CTkScrollableFrame(self.parent, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Active Packages header + container
        self.lbl_active_header = ctk.CTkLabel(self.main_scroll, text=_("📦 Aktif Paketler (0)"),
                                              font=("Roboto", 16, "bold"))
        self.lbl_active_header.pack(anchor="w", pady=(0, 10))

        self.frame_active_list = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.frame_active_list.pack(fill="both", expand=False)

        # Past Packages header + container
        self.lbl_past_header = ctk.CTkLabel(self.main_scroll, text=_("🗄️ Geçmiş Paketler (Son 5)"),
                                            font=("Roboto", 16, "bold"), text_color="gray")
        self.lbl_past_header.pack(anchor="w", pady=(30, 10))

        self.frame_past_list = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.frame_past_list.pack(fill="both", expand=False)

        self.is_setup = True

        # Initial data load
        self.refresh()
    
    

    def _format_schedule_summary(self, class_events):
        if not class_events:
            return None

        seen = set()
        schedule_parts = []
        for event in class_events:
            if event.get('is_cancelled'):
                continue

            start_time = event.get('start_time')
            if isinstance(start_time, str):
                try:
                    start_dt = datetime.fromisoformat(start_time)
                except ValueError:
                    continue
            elif isinstance(start_time, datetime):
                start_dt = start_time
            else:
                continue

            time_key = (start_dt.weekday(), start_dt.strftime('%H:%M'))
            if time_key in seen:
                continue
            seen.add(time_key)

            weekday_name = get_weekday_name(start_dt.date())
            schedule_parts.append(f"{weekday_name} {start_dt.strftime('%H:%M')}")
            if len(schedule_parts) >= 3:
                break

        if not schedule_parts:
            return None

        return ", ".join(schedule_parts)

    def update_ui(self, active_subs, inactive_subs):
        """Update only the parts of the UI that display subscription lists."""
        # Update header count
        self.lbl_active_header.configure(text=_("📦 Aktif Paketler ({})").format(len(active_subs)))

        # Active list
        for w in self.frame_active_list.winfo_children():
            w.destroy()

        if not active_subs:
            ctk.CTkLabel(self.frame_active_list, text=_("Aktif paket yok."), text_color="gray").pack(anchor="w", padx=10)
        else:
            for sub in active_subs:
                schedule_summary = None
                if sub and sub.get('package', {}).get('plan', {}).get('access_type') == 'SESSION_BASED':
                    schedule_summary = self._format_schedule_summary(sub.get('class_events', []))
                pc = PackageCard(self.frame_active_list, sub, is_active=True,
                                 on_click=lambda s=sub: self.show_package_detail(s),
                                 on_delete=lambda s=sub: self.delete_subscription(s['id']),
                                 schedule_summary=schedule_summary)
                pc.pack(fill="x", pady=6, padx=5)

        # Past list
        for w in self.frame_past_list.winfo_children():
            w.destroy()

        if not inactive_subs:
            ctk.CTkLabel(self.frame_past_list, text=_("Geçmiş paket yok."), text_color="gray").pack(anchor="w", padx=10)
        else:
            for sub in inactive_subs:
                pc = PackageCard(self.frame_past_list, sub, is_active=False)
                pc.pack(fill="x", pady=6, padx=5)

    def show_package_detail(self, subscription: dict):
        """Show detailed package information dialog"""
        from desktop.ui.views.dialogs import PackageDetailDialog
        PackageDetailDialog(self.parent, self.api_client, subscription, on_refresh=self.refresh)
    
    def delete_subscription(self, sub_id):
        if messagebox.askyesno(_("Onay"), _("Bu aboneliği silmek istediğinize emin misiniz?\n(Bağlı ödemeler de silinecektir)")):
            try:
                self.api_client.delete(f"/api/v1/sales/subscriptions/{sub_id}")
                messagebox.showinfo(_("Başarılı"), _("Abonelik silindi."))
                self.refresh()
                self.on_refresh_payments()
            except Exception as e:
                messagebox.showerror(_("Hata"), _("Silme işlemi başarısız: {}").format(e))
    
    def refresh(self):
        """Refresh data and update UI without rebuilding the whole layout."""
        try:
            subs = self.api_client.get(f"/api/v1/sales/subscriptions?member_id={self.member['id']}")
        except Exception as e:
            # Show error in the main scroll if available
            if self.main_scroll is not None:
                for w in self.main_scroll.winfo_children():
                    if isinstance(w, ctk.CTkLabel) and "Hata" in w.cget('text'):
                        return
                ctk.CTkLabel(self.main_scroll, text=_("Hata: {}").format(e)).pack()
            return

        active_subs = [s for s in subs if s.get('status') == 'active']
        inactive_subs = [s for s in subs if s.get('status') == 'expired']
        inactive_subs.sort(key=lambda x: x.get('end_date', ''), reverse=True)
        inactive_subs = inactive_subs[:5]

        # Ensure skeleton is present
        if not self.is_setup:
            self.setup()

        # Update lists
        self.update_ui(active_subs, inactive_subs)
