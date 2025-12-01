import customtkinter as ctk
from desktop.core.api_client import ApiClient
from tkinter import messagebox

class PaymentsTab:
    def __init__(self, parent_frame, api_client: ApiClient, member: dict):
        self.parent = parent_frame
        self.api_client = api_client
        self.member = member
        
    def setup(self):
        """Setup payments tab content"""
        # Header
        header = ctk.CTkFrame(self.parent, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(10, 5))
        
        ctk.CTkLabel(header, text="💳 Ödeme Geçmişi", 
                    font=("Roboto", 20, "bold")).pack(side="left")

        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(self.parent, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        try:
            subs = self.api_client.get(f"/api/v1/sales/subscriptions?member_id={self.member['id']}")
            payments = []
            for sub in subs:
                for p in sub.get('payments', []):
                    p['package_name'] = sub.get('package', {}).get('name', '-')
                    p['subscription_id'] = sub.get('id')
                    payments.append(p)
            
            # Sort by date (newest first)
            payments.sort(key=lambda x: x.get('payment_date', ''), reverse=True)
            
            if not payments:
                empty_frame = ctk.CTkFrame(scroll_frame, fg_color=("#E0E0E0", "#2B2B2B"), corner_radius=10)
                empty_frame.pack(fill="x", pady=20)
                ctk.CTkLabel(empty_frame, text="📭 Henüz ödeme kaydı bulunmuyor", 
                            font=("Roboto", 16), text_color="gray").pack(pady=40)
                return

            # Payment cards
            for pay in payments:
                self.create_payment_card(scroll_frame, pay)
                
        except Exception as e:
            error_frame = ctk.CTkFrame(scroll_frame, fg_color="#E04F5F", corner_radius=10)
            error_frame.pack(fill="x", pady=20)
            ctk.CTkLabel(error_frame, text=f"❌ Hata: {e}", 
                        font=("Roboto", 14), text_color="white").pack(pady=20)

    def create_payment_card(self, parent, payment: dict):
        """Create a payment record card"""
        card = ctk.CTkFrame(parent, fg_color=("#F5F5F5", "#2B2B2B"), corner_radius=8)
        card.pack(fill="x", pady=5)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=12)
        
        # Left section: Date and package
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        
        # Date with icon
        date_str = payment.get('payment_date', '')[:10]
        try:
            from datetime import datetime
            date_obj = datetime.fromisoformat(payment.get('payment_date', '').replace('Z', '+00:00'))
            date_str = date_obj.strftime("%d.%m.%Y")
        except:
            pass
        
        date_frame = ctk.CTkFrame(left, fg_color="transparent")
        date_frame.pack(anchor="w")
        ctk.CTkLabel(date_frame, text="📅", font=("Segoe UI Emoji", 14)).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(date_frame, text=date_str, 
                    font=("Roboto", 16, "bold")).pack(side="left")
        
        # Package name
        pkg_name = payment.get('package_name', '-')
        ctk.CTkLabel(left, text=f"📦 {pkg_name}", 
                    font=("Roboto", 14), text_color="gray").pack(anchor="w", pady=(2, 0))
        
        # Center section: Amount and method
        center = ctk.CTkFrame(content, fg_color="transparent")
        center.pack(side="left", padx=20)
        
        amount = payment.get('amount_paid', 0)
        try:
            amount_float = float(amount)
            amount_text = f"{amount_float:.2f} TL"
        except (ValueError, TypeError):
            amount_text = f"{amount} TL"
        
        ctk.CTkLabel(center, text=amount_text, 
                    font=("Roboto", 22, "bold"), text_color="#2CC985").pack(anchor="e")
        
        # Payment method with icon
        method = payment.get('payment_method', 'NAKIT')
        method_map = {
            'NAKIT': '💵 Nakit',
            'KREDI_KARTI': '💳 Kredi Kartı',
            'HAVALE_EFT': '🏦 Havale/EFT',
            'DIGER': '📝 Diğer'
        }
        method_display = method_map.get(method, str(method))
        
        ctk.CTkLabel(center, text=method_display, 
                    font=("Roboto", 12), text_color="gray").pack(anchor="e")
        
        # Right section: Delete button
        btn_delete = ctk.CTkButton(content, text="🗑️ Sil", width=80, height=32,
                                   fg_color="#E04F5F", hover_color="#C03E4F",
                                   font=("Roboto", 12, "bold"),
                                   command=lambda: self.delete_payment(payment['id']))
        btn_delete.pack(side="right", padx=(10, 0))
    
    def delete_payment(self, payment_id):
        if messagebox.askyesno("Onay", "Bu ödemeyi silmek istediğinize emin misiniz?\n\n⚠️ Bu işlem geri alınamaz!"):
            try:
                self.api_client.delete(f"/api/v1/sales/payments/{payment_id}")
                messagebox.showinfo("Başarılı", "Ödeme başarıyla silindi.")
                self.refresh()
            except Exception as e:
                messagebox.showerror("Hata", f"Silme işlemi başarısız:\n{e}")
    
    def refresh(self):
        """Refresh the tab"""
        for widget in self.parent.winfo_children():
            widget.destroy()
        self.setup()
