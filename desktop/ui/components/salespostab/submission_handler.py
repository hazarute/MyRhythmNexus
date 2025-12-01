from datetime import datetime
from typing import Dict, Optional, Callable, Any
from decimal import Decimal
from tkinter import messagebox


class SubmissionHandler:
    """
    Satış gönderimi ve doğrulama handler'ı.
    
    Kullanım:
        handler = SubmissionHandler(api_client)
        result = handler.submit_sale(
            member=member_dict,
            package=package_dict,
            amount_paid=123.45,
            payment_method="NAKIT",
            start_date=date_obj,
            class_events=class_events_list
        )
    """
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def validate_inputs(self, member: Optional[Dict], package: Optional[Dict], 
                       payment_data: Optional[Dict], start_date) -> tuple[bool, str]:
        """
        Giriş verilerini doğrula.
        
        Returns: (is_valid, error_message)
        """
        # Member check
        if not member:
            return False, "Lütfen bir üye seçiniz."
        
        # Package check
        if not package:
            return False, "Lütfen bir paket seçiniz."
        
        # Payment check
        if not payment_data:
            return False, "Ödeme detayları alınamadı."
        
        if not payment_data.get("is_valid"):
            return False, payment_data.get("error", "Ödeme bilgileri geçersiz.")
        
        # Start date check
        if not start_date:
            return False, "Başlangıç tarihi seçilmedi."
        
        return True, ""
    
    def build_payload(self, member: Optional[Dict], package: Optional[Dict], 
                     payment_data: Optional[Dict], start_date, class_events: Optional[Any] = None) -> Optional[Dict]:
        """
        API gönderimi için payload oluştur.
        
        Supports:
        - SESSION_BASED: Creates subscription with optional ClassEvents
        - TIME_BASED: Creates subscription without ClassEvents (unlimited participation via QR)
        
        Returns: Payload dict or None if validation fails
        """
        # Validate inputs
        if not member or not package or not payment_data:
            messagebox.showerror("Hata", "Gerekli veriler eksik.")
            return None
        
        try:
            # Date handling
            start_datetime = datetime.combine(start_date, datetime.now().time())
            
            # Amount validation
            amount_paid = Decimal(str(payment_data.get("amount_paid", 0)))
            pkg_price = Decimal(str(package.get("price", 0)))
            
            if amount_paid > pkg_price:
                messagebox.showwarning(
                    "Uyarı",
                    f"Ödeme tutarı paket fiyatından ({float(pkg_price):.2f} TL) fazla olamaz."
                )
                return None
            
            # Base payload
            payload = {
                "member_user_id": member["id"],
                "package_id": package["id"],
                "start_date": start_datetime.isoformat(),
                "status": "active",
                "initial_payment": {
                    "amount_paid": float(amount_paid),
                    "payment_method": payment_data.get("payment_method", "NAKIT"),
                    "refund_amount": 0,
                    "refund_reason": None
                }
            }
            
            # Add class events if SESSION_BASED
            # TIME_BASED subscriptions don't require events - unlimited participation handled by QR check-in
            plan = package.get("plan", {})
            access_type = plan.get("access_type", "SESSION_BASED")
            
            if access_type == "SESSION_BASED" and class_events:
                payload["class_events"] = class_events
            # For TIME_BASED: no class_events needed, participants scan QR anytime
            
            return payload
            
        except Exception as e:
            messagebox.showerror("Hata", f"Payload oluşturma hatası: {e}")
            return None
    
    def send_to_api(self, payload: Dict) -> bool:
        """
        Payload'ı API'ye gönder.
        
        Returns: True if successful
        """
        try:
            self.api_client.post(
                "/api/v1/sales/subscriptions-with-events",
                json=payload
            )
            messagebox.showinfo(
                "Başarılı",
                "Satış tamamlandı!\nAbonelik oluşturuldu."
            )
            return True
                
        except Exception as e:
            messagebox.showerror("Hata", f"Satış başarısız: {e}")
            return False
            return False
    
    def submit_sale(self, member: Optional[Dict], package: Optional[Dict],
                   payment_data: Optional[Dict], start_date,
                   class_events: Optional[Any] = None) -> bool:
        """
        Satışı baştan sona işle.
        
        SESSION_BASED: Satış + Ders Zamanlaması (Opsiyonel)
        TIME_BASED: Satış + Sınırsız QR Katılım
        
        Returns: True if successful
        """
        # 1. Validate
        is_valid, error_msg = self.validate_inputs(member, package, payment_data, start_date)
        if not is_valid:
            messagebox.showwarning("Uyarı", error_msg)
            return False
        
        # 2. Build payload
        payload = self.build_payload(member, package, payment_data, start_date, class_events)
        if not payload:
            return False
        
        # 3. Send to API
        return self.send_to_api(payload)
