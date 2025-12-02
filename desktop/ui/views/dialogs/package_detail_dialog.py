import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.api_client import ApiClient
from datetime import datetime
from desktop.ui.views.checkin_dialog import CheckInDialog


class PackageDetailDialog(ctk.CTkToplevel):
    """Dialog showing detailed package information"""
    
    def __init__(self, parent, api_client: ApiClient, subscription: dict, on_refresh=None):
        super().__init__(parent)
        self.api_client = api_client
        self.subscription = subscription
        self.on_refresh = on_refresh
        
        self.title(_("Paket Detayları"))
        self.geometry("600x700")
        self.lift()
        self.focus_force()
        self.grab_set()
        
        # Main Container
        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header with package icon
        header_frame = ctk.CTkFrame(main_frame, fg_color="#3B8ED0", corner_radius=10)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        pkg_name = subscription.get('package', {}).get('name', _('Paket'))
        ctk.CTkLabel(header_frame, text="📦", 
                    font=("Segoe UI Emoji", 28)).pack(pady=(10, 3))
        ctk.CTkLabel(header_frame, text=pkg_name, 
                    font=("Roboto", 20, "bold"), 
                    text_color="white").pack(pady=(0, 10))
        
        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Status badge
        status = subscription.get('status', 'active')
        status_map = {
            'active': (_('🟢 Aktif'), '#2CC985'),
            'expired': (_('🔴 Süresi Dolmuş'), '#E04F5F'),
            'cancelled': (_('⚫ İptal Edildi'), '#888888')
        }
        status_text, status_color = status_map.get(status, (_('⚪ Bilinmiyor'), '#888888'))
        
        status_badge = ctk.CTkFrame(scroll_frame, fg_color=status_color, corner_radius=20, height=40)
        status_badge.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(status_badge, text=status_text, 
                    font=("Roboto", 14, "bold"), 
                    text_color="white").pack(pady=8)
        
        # Date Information
        self.create_info_section(scroll_frame, _("📅 Tarih Bilgileri"))
        
        start_date = self.format_date(subscription.get('start_date', ''))
        end_date = self.format_date(subscription.get('end_date', ''))
        
        self.create_info_row(scroll_frame, _("Başlangıç"), start_date)
        self.create_info_row(scroll_frame, _("Bitiş"), end_date)
        
        # Session Information
        self.create_info_section(scroll_frame, _("🎯 Ders Kullanımı"), top_padding=20)
        
        plan = subscription.get('package', {}).get('plan', {})
        access_type = plan.get('access_type', 'SESSION_BASED')
        used = subscription.get('used_sessions', 0)
        limit = plan.get('sessions_granted', 0)
        
        if access_type == 'TIME_BASED':
            # Time-based plan - show check-in count and unlimited access
            infinity_frame = ctk.CTkFrame(scroll_frame, fg_color="#3B8ED0", corner_radius=10)
            infinity_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(infinity_frame, text=_("♾️ Zaman Bazlı Erişim"), 
                        font=("Roboto", 16, "bold"), 
                        text_color="white").pack(pady=(12, 5))
            ctk.CTkLabel(infinity_frame, text=_("Paket süresi boyunca sınırsız ders ({used} giriş yapıldı)").format(used=used), 
                        font=("Roboto", 12), 
                        text_color="white").pack(pady=(0, 12))
        elif limit and limit > 0:
            # Session-based plan - show progress
            remaining = limit - used
            ratio = min(used / limit, 1.0) if limit > 0 else 0
            
            # Progress bar
            progress_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            progress_frame.pack(fill="x", pady=10)
            
            progress = ctk.CTkProgressBar(progress_frame, height=20, progress_color="#3B8ED0")
            progress.set(ratio)
            progress.pack(fill="x", padx=10)
            
            # Stats row
            stats_row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            stats_row.pack(fill="x", pady=5)
            
            self.create_stat_box(stats_row, _("Kullanılan"), str(used), "#3B8ED0", 0)
            self.create_stat_box(stats_row, _("Kalan"), str(remaining), 
                               "#2CC985" if remaining > 0 else "#E04F5F", 1)
            self.create_stat_box(stats_row, _("Toplam"), str(limit), "#888888", 2)
        else:
            # Legacy or unlimited plan
            infinity_frame = ctk.CTkFrame(scroll_frame, fg_color="#3B8ED0", corner_radius=10)
            infinity_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(infinity_frame, text=_("♾️ Sınırsız"), 
                        font=("Roboto", 18, "bold"), 
                        text_color="white").pack(pady=15)
        
        # Payment Information
        self.create_info_section(scroll_frame, _("💰 Ödeme Bilgileri"), top_padding=20)
        
        try:
            purchase_price = float(subscription.get('purchase_price', 0))
        except (ValueError, TypeError):
            purchase_price = 0.0
        
        payments = subscription.get('payments', [])
        total_paid = sum(float(p.get('amount_paid', 0)) for p in payments)
        remaining_debt = purchase_price - total_paid
        
        self.create_info_row(scroll_frame, _("Toplam Fiyat"), f"{purchase_price:.2f} TL")
        self.create_info_row(scroll_frame, _("Ödenen"), f"{total_paid:.2f} TL", 
                            text_color="#2CC985" if total_paid > 0 else "gray")
        self.create_info_row(scroll_frame, _("Kalan Borç"), f"{remaining_debt:.2f} TL", 
                            text_color="#E04F5F" if remaining_debt > 0 else "#2CC985")
        
        # Payment History
        if payments:
            self.create_info_section(scroll_frame, _("📝 Ödeme Geçmişi ({count})").format(count=len(payments)), top_padding=20)
            
            for payment in payments[:5]:  # Show last 5 payments
                self.create_payment_item(scroll_frame, payment)
        
        # Close button
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkButton(btn_frame, text=_("QR Kod OKUT"), width=150, height=40,
                     font=("Roboto", 14, "bold"),
                     fg_color="#2CC985",
                     command=self.simulate_qr_scan).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text=_("Kapat"), width=150, height=40,
                     font=("Roboto", 14, "bold"),
                     command=self.destroy).pack(side="left", padx=5)
    
    def format_date(self, date_str: str) -> str:
        """Format ISO date to DD.MM.YYYY"""
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime("%d.%m.%Y")
        except:
            return date_str[:10] if date_str else "-"
    
    def create_info_section(self, parent, title: str, top_padding: int = 0):
        """Create a section header"""
        ctk.CTkLabel(parent, text=title, 
                    font=("Roboto", 16, "bold"), 
                    text_color="#3B8ED0").pack(anchor="w", pady=(top_padding, 10))
    
    def create_info_row(self, parent, label: str, value: str, text_color: str = "white"):
        """Create an info row with label and value"""
        row = ctk.CTkFrame(parent, fg_color=("#E0E0E0", "#2B2B2B"), corner_radius=5)
        row.pack(fill="x", pady=3)
        
        content = ctk.CTkFrame(row, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(content, text=label, 
                    font=("Roboto", 13), 
                    text_color="gray").pack(side="left")
        
        ctk.CTkLabel(content, text=value, 
                    font=("Roboto", 14, "bold"), 
                    text_color=text_color).pack(side="right")
    
    def create_stat_box(self, parent, label: str, value: str, color: str, col: int):
        """Create a stat box in a grid"""
        box = ctk.CTkFrame(parent, fg_color=color, corner_radius=8)
        box.grid(row=0, column=col, sticky="ew", padx=5)
        parent.grid_columnconfigure(col, weight=1)
        
        ctk.CTkLabel(box, text=label, 
                    font=("Roboto", 11), 
                    text_color="white").pack(pady=(10, 0))
        ctk.CTkLabel(box, text=value, 
                    font=("Roboto", 20, "bold"), 
                    text_color="white").pack(pady=(0, 10))
    
    def create_payment_item(self, parent, payment: dict):
        """Create a compact payment history item"""
        item = ctk.CTkFrame(parent, fg_color=("#F5F5F5", "#1E1E1E"), corner_radius=5)
        item.pack(fill="x", pady=2)
        
        content = ctk.CTkFrame(item, fg_color="transparent")
        content.pack(fill="x", padx=10, pady=8)
        
        # Date
        date_str = self.format_date(payment.get('payment_date', ''))
        ctk.CTkLabel(content, text=f"📅 {date_str}", 
                    font=("Roboto", 11)).pack(side="left")
        
        # Method
        method = payment.get('payment_method', 'NAKIT')
        method_icons = {'NAKIT': '💵', 'KREDI_KARTI': '💳', 'HAVALE_EFT': '🏦', 'DIGER': '📝'}
        method_icon = method_icons.get(method, '💵')
        
        ctk.CTkLabel(content, text=method_icon, 
                    font=("Segoe UI Emoji", 11)).pack(side="left", padx=(10, 5))
        
        # Amount
        amount = payment.get('amount_paid', 0)
        try:
            amount_float = float(amount)
            amount_text = f"{amount_float:.2f} TL"
        except (ValueError, TypeError):
            amount_text = f"{amount} TL"
        
        ctk.CTkLabel(content, text=amount_text, 
                    font=("Roboto", 12, "bold"), 
                    text_color="#2CC985").pack(side="right")
    
    def simulate_qr_scan(self):
        """QR kod okut - Aboneliğin QR kodunu sisteme okut"""
        try:
            subscription_id = self.subscription.get('id')
            if not subscription_id:
                self.show_error(_("Abonelik ID'si bulunamadı"))
                return
            
            # Aboneliğin QR kodunu al
            qr_data = self.api_client.get(f"/api/v1/checkin/subscriptions/{subscription_id}/qr-code")
            
            qr_token = qr_data.get('qr_token')
            
            if qr_token:
                # Her iki tip abonelik için de doğrudan check-in yap
                # SESSION_BASED için ders olmadan check-in mümkün
                try:
                    response = self.api_client.post(
                        "/api/v1/checkin/check-in",
                        json={"qr_token": qr_token, "event_id": None}
                    )
                    self.show_success(_("✅ Giriş Başarılı"), 
                                    _("Katılım kaydedildi.\n{member_name}\nKalan Hak: {remaining}").format(
                                        member_name=response.get('member_name', _('Üye')),
                                        remaining=response.get('remaining_sessions', 'N/A')
                                    ))
                except Exception as e:
                    error_msg = self._parse_error_message(e)
                    self.show_error(_("Check-in hatası: {error}").format(error=error_msg))
            else:
                self.show_error(_("QR token bulunamadı"))
                
        except Exception as e:
            self.show_error(_("Hata: {error}").format(error=str(e)))
    
    def show_error(self, message: str):
        """Hata göster"""
        error_window = ctk.CTkToplevel(self)
        error_window.title(_("Hata"))
        error_window.geometry("350x200")
        error_window.grab_set()
        
        ctk.CTkLabel(error_window, text=_("❌ Hata\n\n{message}").format(message=message), 
                    font=("Roboto", 14),
                    text_color="#E04F5F",
                    justify="center").pack(pady=20, padx=20)
        
        ctk.CTkButton(error_window, text=_("Tamam"), 
                     fg_color="gray",
                     command=error_window.destroy).pack(pady=10)
    
    def show_success(self, title: str, message: str):
        """Başarı göster"""
        success_window = ctk.CTkToplevel(self)
        success_window.title(title)
        success_window.geometry("350x200")
        success_window.grab_set()
        
        ctk.CTkLabel(success_window, text=f"{title}\n\n{message}", 
                    font=("Roboto", 14),
                    text_color="#2CC985",
                    justify="center").pack(pady=20, padx=20)
        
        def on_close():
            success_window.destroy()
            # Schedule refresh and dialog close async to avoid blocking
            self.after(100, self._do_refresh_and_close)
        
        ctk.CTkButton(success_window, text=_("Tamam"), 
                     fg_color="#2CC985",
                     command=on_close).pack(pady=10)
    
    def _do_refresh_and_close(self):
        """Refresh parent and close dialog after a small delay"""
        if self.on_refresh:
            try:
                self.on_refresh()
            except Exception as e:
                print(f"Error during refresh: {e}")
        self.destroy()

    def _parse_error_message(self, exception):
        """Parse error message from API response"""
        import json
        import httpx
        
        # Check if it's an HTTP error
        if isinstance(exception, httpx.HTTPStatusError):
            try:
                error_data = json.loads(exception.response.text)
                if "detail" in error_data:
                    return error_data["detail"]
            except json.JSONDecodeError:
                pass
            # Fallback to status code and reason
            return f"HTTP {exception.response.status_code}: {exception.response.reason_phrase}"
        
        # Fallback to original message
        return str(exception)
