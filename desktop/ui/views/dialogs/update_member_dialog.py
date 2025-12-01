import customtkinter as ctk
from desktop.core.api_client import ApiClient
from tkinter import messagebox
import re


class UpdateMemberDialog(ctk.CTkToplevel):
    """Dialog for updating member information"""
    
    def __init__(self, parent, api_client: ApiClient, member_data: dict, on_success):
        super().__init__(parent)
        self.api_client = api_client
        self.member_data = member_data
        self.on_success = on_success
        
        self.title("Üye Bilgilerini Güncelle")
        self.geometry("450x500")
        
        self.lift()
        self.focus_force()
        self.grab_set()
        
        # Main Container
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(self.main_frame, text="✏️ Bilgileri Düzenle", 
                    font=("Roboto", 22, "bold")).pack(pady=(20, 30))
        
        # Form Fields
        self.entry_first_name = self.create_input(self.main_frame, "👤 Ad", 
                                                  member_data.get('first_name', ''))
        self.entry_last_name = self.create_input(self.main_frame, "👤 Soyad", 
                                                 member_data.get('last_name', ''))
        self.entry_email = self.create_input(self.main_frame, "📧 Email", 
                                            member_data.get('email', ''))
        self.entry_phone = self.create_input(self.main_frame, "📞 Telefon", 
                                            member_data.get('phone_number', '') or '')
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=30, padx=20)
        
        ctk.CTkButton(btn_frame, text="❌ İptal", fg_color="#555555", 
                     hover_color="#333333", width=100, 
                     command=self.destroy).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(btn_frame, text="💾 Kaydet", fg_color="#2CC985", 
                     hover_color="#229966", width=100, 
                     command=self.save).pack(side="left", padx=10, expand=True)

    def create_input(self, parent, label, value):
        """Create a labeled input field with pre-filled value"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=8)
        
        ctk.CTkLabel(frame, text=label, font=("Roboto", 14), 
                    width=80, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame, height=35, font=("Roboto", 14))
        entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        if value:
            entry.insert(0, value)
        return entry
        
    def save(self):
        """Validate and update member information"""
        first_name = self.entry_first_name.get().strip()
        last_name = self.entry_last_name.get().strip()
        email = self.entry_email.get().strip().lower()
        phone = self.entry_phone.get().strip()

        # Required fields check
        if not all([first_name, last_name, email]):
            messagebox.showwarning("Eksik Bilgi", 
                "Lütfen Ad, Soyad ve Email alanlarını doldurunuz.")
            return

        # Email validation (RFC 5322 simplified)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            messagebox.showwarning("Geçersiz Email", 
                "Lütfen geçerli bir email adresi giriniz.\nÖrnek: ornek@domain.com")
            return

        # Phone validation (Turkey format)
        if phone:
            phone_clean = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            
            if phone_clean.startswith("+90"):
                phone_clean = phone_clean[3:]
            elif phone_clean.startswith("90"):
                phone_clean = phone_clean[2:]
            elif phone_clean.startswith("0"):
                phone_clean = phone_clean[1:]
            
            if not phone_clean.isdigit() or len(phone_clean) != 10:
                messagebox.showwarning("Geçersiz Telefon", 
                    "Telefon numarası 10 haneli olmalıdır.\n"
                    "Kabul edilen formatlar:\n"
                    "• 5xxxxxxxxx\n"
                    "• 05xxxxxxxxx\n"
                    "• +905xxxxxxxxx\n"
                    "• 0 5xx xxx xx xx")
                return
            
            if not phone_clean.startswith("5"):
                messagebox.showwarning("Geçersiz Telefon", 
                    "Telefon numarası 5 ile başlamalıdır (cep telefonu).")
                return
            
            phone = phone_clean

        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone_number": phone
        }
        
        try:
            self.api_client.put(f"/api/v1/members/{self.member_data['id']}", json=data)
            self.on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Hata", f"Güncelleme hatası: {e}")
