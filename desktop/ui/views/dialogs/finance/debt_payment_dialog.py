import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.api_client import ApiClient
from tkinter import messagebox
from datetime import datetime
from desktop.core.ui_utils import safe_grab


class DebtPaymentDialog(ctk.CTkToplevel):
    """
    Debt payment dialog - Shows member's debts from all packages
    Allows paying total or partial debt with smart distribution to oldest packages first
    """
    def __init__(self, parent, api_client: ApiClient, member: dict, on_success):
        super().__init__(parent)
        self.api_client = api_client
        self.member = member
        self.on_success = on_success
        self.packages_with_debt = []
        
        # Ensure this toplevel is transient to its parent so the window
        # manager treats it as a dialog for stacking/focus purposes.
        try:
            self.transient(parent)
        except Exception:
            # Some widget types or tests may not support transient; ignore safely
            pass

        self.title(_("Borç Ödeme"))
        self.geometry("700x700")
        # Try to ensure the dialog is raised and receives focus
        self.lift()
        try:
            self.focus_set()
        except Exception:
            pass
        try:
            self.focus_force()
        except Exception:
            pass
        self.attributes("-topmost", True)
        safe_grab(self)
        
        # Main Container
        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(20, 10), padx=20)
        
        ctk.CTkLabel(header_frame, text=_("💰 Borç Ödeme"), 
                    font=("Roboto", 24, "bold")).pack(side="left")
        
        member_name = f"{member.get('first_name')} {member.get('last_name')}"
        ctk.CTkLabel(header_frame, text=member_name, 
                    font=("Roboto", 16), text_color="gray").pack(side="left", padx=(15, 0))
        
        # Load and display debts
        self.load_debts()
        
        if not self.packages_with_debt:
            ctk.CTkLabel(main_frame, text=_("✅ Bu üyenin borcu bulunmamaktadır"), 
                        font=("Roboto", 18), text_color="green").pack(pady=50)
            
            ctk.CTkButton(main_frame, text=_("Kapat"), command=self.destroy, 
                         width=150).pack(pady=20)
            return
        
        # Total debt display
        total_debt = sum(pkg['debt'] for pkg in self.packages_with_debt)
        debt_frame = ctk.CTkFrame(main_frame, fg_color="#FF6B6B", corner_radius=10)
        debt_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        ctk.CTkLabel(debt_frame, text=_("Toplam Borç"), 
                    font=("Roboto", 14, "bold"), text_color="white").pack(pady=(10, 0))
        ctk.CTkLabel(debt_frame, text=f"{total_debt:.2f} TL", 
                    font=("Roboto", 28, "bold"), text_color="white").pack(pady=(0, 10))
        
        # Debt list
        list_label = ctk.CTkLabel(main_frame, text=_("📋 Borçlu Paketler (Eskiden Yeniye)"), 
                                 font=("Roboto", 16, "bold"))
        list_label.pack(anchor="w", padx=20, pady=(0, 10))
        
        scroll_frame = ctk.CTkScrollableFrame(main_frame, height=200)
        scroll_frame.pack(fill="both", expand=True, padx=20)
        
        for pkg in self.packages_with_debt:
            self.create_debt_card(scroll_frame, pkg)
        
        # Payment input
        payment_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        payment_frame.pack(fill="x", padx=20, pady=15)
        
        # Amount input
        amount_row = ctk.CTkFrame(payment_frame, fg_color="transparent")
        amount_row.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(amount_row, text=_("💵 Ödeme Tutarı:"), 
                    font=("Roboto", 16, "bold")).pack(side="left", padx=(0, 10))
        
        self.entry_payment = ctk.CTkEntry(amount_row, font=("Roboto", 18), 
                                         height=40, width=200, placeholder_text=_("0.00"))
        self.entry_payment.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(amount_row, text=_("TL"), 
                    font=("Roboto", 16)).pack(side="left")
        
        # Payment method selection
        method_row = ctk.CTkFrame(payment_frame, fg_color="transparent")
        method_row.pack(fill="x")
        
        ctk.CTkLabel(method_row, text=_("💳 Ödeme Şekli:"), 
                    font=("Roboto", 16, "bold")).pack(side="left", padx=(0, 10))
        
        self.payment_method = ctk.CTkSegmentedButton(
            method_row,
            values=[_("Nakit"), _("Kredi Kartı"), _("Havale/EFT"), _("Diğer")],
            font=("Roboto", 14),
            height=35
        )
        self.payment_method.set(_("Nakit"))
        self.payment_method.pack(side="left")
        
        # Quick payment buttons
        quick_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        quick_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(quick_frame, text=_("Hızlı Tutar:"), 
                    font=("Roboto", 12), text_color="gray").pack(side="left", padx=(0, 10))
        
        # Fixed quick amounts + "Tümü" button
        quick_amounts = [100, 250, 500]
        for amount in quick_amounts:
            ctk.CTkButton(quick_frame, text=f"{amount} TL", width=70, height=30,
                         command=lambda a=amount: self.set_amount(a)).pack(side="left", padx=2)
        
        # "Tümü" button (always shows total debt)
        ctk.CTkButton(quick_frame, text=_("Tümü"), width=70, height=30,
                     fg_color="#E5B00D", hover_color="#D4A00B",
                     command=lambda: self.set_amount(total_debt)).pack(side="left", padx=2)
        
        # Action buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20, padx=20)
        
        btn_cancel = ctk.CTkButton(btn_frame, text=_("❌ İptal"), fg_color="#555555", 
                                   hover_color="#333333", width=150, height=40,
                                   font=("Roboto", 14, "bold"),
                                   command=self.destroy)
        btn_cancel.pack(side="left", padx=10, expand=True)
        
        btn_save = ctk.CTkButton(btn_frame, text=_("✅ Ödemeyi Kaydet"), fg_color="#2CC985", 
                                hover_color="#229966", width=150, height=40,
                                font=("Roboto", 14, "bold"),
                                command=self.process_payment)
        btn_save.pack(side="left", padx=10, expand=True)
    
    def load_debts(self):
        """Load packages with outstanding debt, sorted by creation date (oldest first)"""
        try:
            subscriptions = self.api_client.get(f"/api/v1/sales/subscriptions?member_id={self.member['id']}")
            
            # Filter packages with debt and sort by created_at
            for sub in subscriptions:
                if sub.get('status') == 'cancelled':
                    continue
                
                total_price = float(sub.get('purchase_price', 0))
                paid_amount = sum(float(p.get('amount_paid', 0)) for p in sub.get('payments', []))
                debt = total_price - paid_amount
                
                if debt > 0:
                    package_name = sub.get('package', {}).get('name', _('Unknown'))
                    self.packages_with_debt.append({
                        'id': sub['id'],
                        'service_name': package_name,
                        'total_price': total_price,
                        'paid_amount': paid_amount,
                        'debt': debt,
                        'created_at': sub.get('created_at', '')
                    })
            
            # Sort by created_at (oldest first)
            self.packages_with_debt.sort(key=lambda x: x['created_at'])
            
        except Exception as e:
            print(f"Error loading debts: {e}")
    
    def create_debt_card(self, parent, pkg: dict):
        """Create a card displaying package debt information"""
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#2B2B2B")
        card.pack(fill="x", pady=5)
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=12)
        
        # Left: Service name and date
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(left, text=pkg['service_name'], 
                    font=("Roboto", 16, "bold")).pack(anchor="w")
        
        try:
            date_obj = datetime.fromisoformat(pkg['created_at'].replace('Z', '+00:00'))
            date_str = date_obj.strftime("%d.%m.%Y")
        except:
            date_str = pkg['created_at'][:10]
        
        info_text = _("Tarih: {date} | Toplam: {total:.2f} TL | Ödenen: {paid:.2f} TL").format(
            date=date_str, total=pkg['total_price'], paid=pkg['paid_amount'])
        ctk.CTkLabel(left, text=info_text, font=("Roboto", 12), 
                    text_color="gray").pack(anchor="w")
        
        # Right: Debt amount
        debt_label = ctk.CTkLabel(content, text=f"{pkg['debt']:.2f} TL", 
                                 font=("Roboto", 20, "bold"), text_color="#FF6B6B")
        debt_label.pack(side="right")
    
    def set_amount(self, amount: float):
        """Set payment amount from quick buttons"""
        self.entry_payment.delete(0, "end")
        self.entry_payment.insert(0, str(amount))
    
    def process_payment(self):
        """Process payment and distribute to packages starting from oldest"""
        try:
            payment_str = self.entry_payment.get().strip().replace(',', '.')
            if not payment_str:
                messagebox.showwarning(_("Uyarı"), _("Lütfen ödeme tutarı giriniz"))
                return
            
            payment_amount = float(payment_str)
            
            if payment_amount <= 0:
                messagebox.showwarning(_("Uyarı"), _("Ödeme tutarı 0'dan büyük olmalıdır"))
                return
            
            total_debt = sum(pkg['debt'] for pkg in self.packages_with_debt)
            
            if payment_amount > total_debt:
                response = messagebox.askyesno(_("Uyarı"), 
                    _("Ödeme tutarı ({amount:.2f} TL) toplam borcu ({total:.2f} TL) aşıyor.\n\n"
                    "Yine de devam etmek istiyor musunuz?\n(Fazla tutar ilk pakete eklenecektir)").format(
                        amount=payment_amount, total=total_debt))
                if not response:
                    return
            
            # Distribute payment starting from oldest package
            remaining = payment_amount
            payment_records = []
            
            for pkg in self.packages_with_debt:
                if remaining <= 0:
                    break
                
                # Calculate how much to pay for this package
                payment_for_pkg = min(remaining, pkg['debt'])
                
                # Get selected payment method
                method_map = {
                    _("Nakit"): "NAKIT",
                    _("Kredi Kartı"): "KREDI_KARTI",
                    _("Havale/EFT"): "HAVALE_EFT",
                    _("Diğer"): "DIGER"
                }
                selected_method = method_map.get(self.payment_method.get(), "NAKIT")
                
                # Record payment (backend will automatically update paid_amount)
                payment_data = {
                    'subscription_id': pkg['id'],
                    'amount_paid': payment_for_pkg,
                    'payment_method': selected_method
                }
                self.api_client.post("/api/v1/sales/payments", json=payment_data)
                
                payment_records.append({
                    'service': pkg['service_name'],
                    'amount': payment_for_pkg,
                    'remaining_debt': pkg['debt'] - payment_for_pkg
                })
                
                remaining -= payment_for_pkg
            
            # Show success message with distribution details
            message = _("✅ Toplam {amount:.2f} TL ödeme başarıyla kaydedildi!\n\n").format(amount=payment_amount)
            message += _("📊 Dağılım:\n")
            for record in payment_records:
                message += _("• {service}: {amount:.2f} TL").format(service=record['service'], amount=record['amount'])
                if record['remaining_debt'] > 0:
                    message += _(" (Kalan: {remaining:.2f} TL)").format(remaining=record['remaining_debt'])
                else:
                    message += _(" (Tamamlandı ✓)")
                message += "\n"
            
            if remaining > 0:
                message += _("\n⚠️ Fazla ödeme: {remaining:.2f} TL (İlk pakete eklendi)").format(remaining=remaining)
            
            messagebox.showinfo(_("Başarılı"), message)
            
            # Refresh parent view and close
            self.on_success()
            self.destroy()
            
        except ValueError:
            messagebox.showerror(_("Hata"), _("Geçersiz ödeme tutarı"))
        except Exception as e:
            messagebox.showerror(_("Hata"), _("Ödeme işlemi başarısız: {error}").format(error=e))
