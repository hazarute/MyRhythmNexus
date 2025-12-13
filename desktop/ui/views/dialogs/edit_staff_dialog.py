import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.api_client import ApiClient
from tkinter import messagebox
import re
from desktop.core.ui_utils import safe_grab, bring_to_front_and_modal


class EditStaffDialog(ctk.CTkToplevel):
    """Dialog for editing an existing staff member with validation"""
    
    def __init__(self, parent, api_client: ApiClient, staff_id: int, staff_data: dict, on_success):
        super().__init__(parent)
        self.api_client = api_client
        self.staff_id = staff_id
        self.on_success = on_success
        
        self.title(_("Personel Düzenle"))
        self.geometry("450x620")
        
        # Ensure dialog is brought to front and made modal
        bring_to_front_and_modal(self, parent)
        
        # Main Container
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(self.main_frame, text=_("✏️ Personel Düzenle"), 
                    font=("Roboto", 22, "bold")).pack(pady=(20, 30))
        
        # Form Fields with existing data
        self.entry_first_name = self.create_input(self.main_frame, _("👤 Ad"), 
                                                  staff_data.get('first_name', ''))
        self.entry_last_name = self.create_input(self.main_frame, _("👤 Soyad"), 
                                                staff_data.get('last_name', ''))
        self.entry_email = self.create_input(self.main_frame, _("📧 Email"), 
                                            staff_data.get('email', ''))
        self.entry_phone = self.create_input(self.main_frame, _("📞 Telefon"), 
                                            staff_data.get('phone_number', ''))
        
        # Password field (optional for edit - leave empty to keep current password)
        password_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        password_frame.pack(fill="x", padx=20, pady=8)
        
        ctk.CTkLabel(password_frame, text=_("🔑 Şifre"), font=("Roboto", 14), 
                    width=80, anchor="w").pack(side="left")
        
        self.entry_password = ctk.CTkEntry(password_frame, height=35, font=("Roboto", 14), 
                                          show="*")
        self.entry_password.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        password_help = ctk.CTkLabel(password_frame, text=_("(boş bırakılırsa değişmez)"), 
                                    font=("Roboto", 10), 
                                    text_color=("gray50", "gray60"))
        
        # Role Selection - get current roles
        role_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        role_frame.pack(fill="x", padx=20, pady=8)
        
        ctk.CTkLabel(role_frame, text=_("💼 Rol"), font=("Roboto", 14), 
                    width=80, anchor="w").pack(side="left")
        
        self.combo_role = ctk.CTkComboBox(role_frame, 
                                         values=["INSTRUCTOR", "ADMIN"],
                                         state="readonly",
                                         height=35,
                                         font=("Roboto", 14))
        self.combo_role.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Set current role (default to first role if exists)
        current_role = "INSTRUCTOR"
        if staff_data.get('roles') and len(staff_data['roles']) > 0:
            role = staff_data['roles'][0]
            if isinstance(role, dict):
                current_role = role.get('role_name', 'INSTRUCTOR')
            else:
                current_role = str(role)
        self.combo_role.set(current_role)
        
        # Status checkbox
        status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        status_frame.pack(fill="x", padx=20, pady=15)
        
        self.check_active = ctk.CTkCheckBox(status_frame, text=_("Aktif"), 
                                           font=("Roboto", 14))
        self.check_active.pack(anchor="w")
        self.check_active.select() if staff_data.get('is_active') else self.check_active.deselect()
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=30, padx=20)
        
        ctk.CTkButton(btn_frame, text=_("❌ İptal"), fg_color="#555555", 
                     hover_color="#333333", width=100, 
                     command=self.destroy).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(btn_frame, text=_("💾 Kaydet"), fg_color="#2CC985", 
                     hover_color="#229966", width=100, 
                     command=self.save).pack(side="left", padx=10, expand=True)

    def create_input(self, parent, label, value="", show=None):
        """Create a labeled input field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=8)
        
        ctk.CTkLabel(frame, text=label, font=("Roboto", 14), 
                    width=80, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame, height=35, font=("Roboto", 14))
        if show:
            entry.configure(show=show)
        entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        if value:
            entry.insert(0, value)
        return entry
        
    def save(self):
        """Validate and save staff member changes"""
        first_name = self.entry_first_name.get().strip()
        last_name = self.entry_last_name.get().strip()
        email = self.entry_email.get().strip().lower()
        phone = self.entry_phone.get().strip()
        password = self.entry_password.get().strip()
        role = self.combo_role.get()
        is_active = self.check_active.get()

        # Required fields check
        if not all([first_name, last_name, email, role]):
            messagebox.showwarning(_("Eksik Bilgi"), 
                _("Lütfen Ad, Soyad, Email ve Rol alanlarını doldurunuz."))
            return

        # Email validation (RFC 5322 simplified)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            messagebox.showwarning(_("Geçersiz Email"), 
                _("Lütfen geçerli bir email adresi giriniz.\nÖrnek: ornek@domain.com"))
            return

        # Phone validation (Turkey format) - optional for staff
        if phone:
            phone_clean = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            
            if phone_clean.startswith("+90"):
                phone_clean = phone_clean[3:]
            elif phone_clean.startswith("90"):
                phone_clean = phone_clean[2:]
            elif phone_clean.startswith("0"):
                phone_clean = phone_clean[1:]
            
            if not phone_clean.isdigit() or len(phone_clean) != 10:
                messagebox.showwarning(_("Geçersiz Telefon"), 
                    _("Telefon numarası 10 haneli olmalıdır.\n"
                    "Kabul edilen formatlar:\n"
                    "• 5xxxxxxxxx\n"
                    "• 05xxxxxxxxx\n"
                    "• +905xxxxxxxxx\n"
                    "• 0 5xx xxx xx xx"))
                return
            
            if not phone_clean.startswith("5"):
                messagebox.showwarning(_("Geçersiz Telefon"), 
                    _("Telefon numarası 5 ile başlamalıdır (cep telefonu)."))
                return
            
            phone = phone_clean

        # Password strength check (if provided)
        if password and len(password) < 6:
            messagebox.showwarning(_("Zayıf Şifre"), _("Şifre en az 6 karakter olmalıdır."))
            return

        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone_number": phone,
            "is_active": is_active
        }
        
        # Only include password if provided
        if password:
            data["password"] = password
        
        try:
            # Send PATCH request to update staff member
            self.api_client.patch(f"/api/v1/staff/{self.staff_id}", json=data)
            self.on_success()
            self.destroy()
        except Exception as e:
            print(f"Error updating staff: {e}")
            messagebox.showerror(_("Hata"), _("Personel güncellenemedi: {err}").format(err=str(e)))
