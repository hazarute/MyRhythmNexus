import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.api_client import ApiClient
from tkinter import messagebox

class PackagesTab:
    def __init__(self, parent_frame, api_client: ApiClient, member: dict, on_refresh_payments):
        self.parent = parent_frame
        self.api_client = api_client
        self.member = member
        self.on_refresh_payments = on_refresh_payments
        
    def setup(self):
        """Setup packages tab content"""
        main_scroll = ctk.CTkScrollableFrame(self.parent, fg_color="transparent")
        main_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        try:
            subs = self.api_client.get(f"/api/v1/sales/subscriptions?member_id={self.member['id']}")
            if not subs:
                ctk.CTkLabel(main_scroll, text=_("Kayıtlı paket bulunamadı."), text_color="gray").pack(pady=20)
                return

            active_subs = [s for s in subs if s.get('status') == 'active']
            # Show only explicitly expired subscriptions in the past list
            inactive_subs = [s for s in subs if s.get('status') == 'expired']
            
            inactive_subs.sort(key=lambda x: x.get('end_date', ''), reverse=True)
            inactive_subs = inactive_subs[:5]

            # Active Packages
            ctk.CTkLabel(main_scroll, text=_("📦 Aktif Paketler ({})").format(len(active_subs)), 
                        font=("Roboto", 16, "bold")).pack(anchor="w", pady=(0, 10))
            
            if not active_subs:
                ctk.CTkLabel(main_scroll, text=_("Aktif paket yok."), text_color="gray").pack(anchor="w", padx=10)
            else:
                for sub in active_subs:
                    self.create_package_card(main_scroll, sub, is_active=True)

            # Past Packages
            ctk.CTkLabel(main_scroll, text=_("🗄️ Geçmiş Paketler (Son 5)"), 
                        font=("Roboto", 16, "bold"), 
                        text_color="gray").pack(anchor="w", pady=(30, 10))
            
            if not inactive_subs:
                ctk.CTkLabel(main_scroll, text=_("Geçmiş paket yok."), text_color="gray").pack(anchor="w", padx=10)
            else:
                for sub in inactive_subs:
                    self.create_package_card(main_scroll, sub, is_active=False)

        except Exception as e:
            ctk.CTkLabel(main_scroll, text=_("Hata: {}").format(e)).pack()
    
    def create_package_card(self, parent, sub, is_active):
        if is_active:
            bg_color = "#333333"
            accent_color = "#3B8ED0"
            text_color = "white"
            icon = "📦"
        else:
            bg_color = "#222222"
            accent_color = "#444444"
            text_color = "gray50"
            icon = "🗄️"
        
        card = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=10)
        card.pack(fill="x", pady=6, padx=5)
        
        # Make card clickable for active packages
        if is_active:
            card.bind("<Button-1>", lambda e, s=sub: self.show_package_detail(s))
            card.configure(cursor="hand2")
        
        stripe = ctk.CTkFrame(card, fg_color=accent_color, width=5, height=70, corner_radius=0)
        stripe.pack(side="left", fill="y")
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        
        # Bind click event to content frame too
        if is_active:
            content.bind("<Button-1>", lambda e, s=sub: self.show_package_detail(s))
            content.configure(cursor="hand2")
        
        pkg_name = sub.get('package', {}).get('name', 'Bilinmeyen Paket')
        pkg_label = ctk.CTkLabel(content, text=_("{}  {}").format(icon, pkg_name), 
                                font=("Roboto", 16, "bold"), 
                                text_color=text_color)
        pkg_label.pack(anchor="w")
        
        if is_active:
            pkg_label.bind("<Button-1>", lambda e, s=sub: self.show_package_detail(s))
            pkg_label.configure(cursor="hand2")
        
        dates = f"{sub.get('start_date', '')[:10]}  ➔  {sub.get('end_date', '')[:10]}"
        ctk.CTkLabel(content, text=dates, font=("Roboto", 12), 
                    text_color="gray70").pack(anchor="w", pady=(2, 5))
        
        bottom_row = ctk.CTkFrame(content, fg_color="transparent")
        bottom_row.pack(fill="x", pady=(5, 0))
        
        plan = sub.get('package', {}).get('plan', {})
        access_type = plan.get('access_type', 'SESSION_BASED')
        used = sub.get('used_sessions', 0)
        limit = plan.get('sessions_granted', 0)
        
        if access_type == 'TIME_BASED':
            ctk.CTkLabel(bottom_row, text=_("♾️ Zaman Bazlı ({} giriş)").format(used), 
                        font=("Roboto", 12, "bold"), 
                        text_color=accent_color).pack(side="left")
        elif limit and limit > 0:
            ratio = min(used / limit, 1.0) if limit > 0 else 0
            progress_color = "#2CC985" if is_active else "gray"
            
            progress = ctk.CTkProgressBar(bottom_row, height=8, progress_color=progress_color)
            progress.set(ratio)
            progress.pack(side="left", fill="x", expand=True, padx=(0, 15))
            
            ctk.CTkLabel(bottom_row, text=_("{}/{} Ders").format(used, limit), 
                        font=("Roboto", 11, "bold"), 
                        text_color="gray").pack(side="left")
        else:
            ctk.CTkLabel(bottom_row, text=_("♾️ Sınırsız Erişim"), 
                        font=("Roboto", 12, "bold"), 
                        text_color=accent_color).pack(side="left")

        btn_del = ctk.CTkButton(card, text=_("🗑️"), width=40, height=40, 
                              fg_color="#E74C3C", hover_color="#C0392B",
                              font=("Segoe UI Emoji", 16),
                              command=lambda s=sub: self.delete_subscription(s['id']))
        btn_del.pack(side="right", padx=15)

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
        """Refresh the tab"""
        for widget in self.parent.winfo_children():
            widget.destroy()
        self.setup()
