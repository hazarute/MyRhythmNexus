import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.api_client import ApiClient
from tkinter import messagebox
from desktop.core.ui_utils import safe_grab


class UpdatePasswordDialog(ctk.CTkToplevel):
    """Dialog for updating member password with confirmation"""
    
    def __init__(self, parent, api_client: ApiClient, member_data: dict):
        super().__init__(parent)
        self.api_client = api_client
        self.member_data = member_data
        
        self.title(_("Şifre Güncelle"))
        self.geometry("550x450")
        
        self.lift()
        self.focus_force()
        safe_grab(self)
        
        # Main Container
        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(main_frame, text=_("🔑 Şifre Güncelle"), 
                    font=("Roboto", 20, "bold")).pack(pady=(20, 10))
        
        member_name = f"{member_data.get('first_name')} {member_data.get('last_name')}"
        ctk.CTkLabel(main_frame, text=member_name, font=("Roboto", 14), 
                    text_color="gray").pack(pady=(0, 20))
        
        # Password Fields
        pwd_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        pwd_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(pwd_frame, text=_("Yeni Şifre:"), 
                    font=("Roboto", 12)).pack(anchor="w", pady=(0, 5))
        self.entry_password = ctk.CTkEntry(pwd_frame, show="●", height=35, 
                                          font=("Roboto", 14))
        self.entry_password.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(pwd_frame, text=_("Şifre Tekrar:"), 
                    font=("Roboto", 12)).pack(anchor="w", pady=(0, 5))
        self.entry_password_confirm = ctk.CTkEntry(pwd_frame, show="●", height=35, 
                                                   font=("Roboto", 14))
        self.entry_password_confirm.pack(fill="x")
        
        # Info Label
        info_label = ctk.CTkLabel(main_frame, 
            text=_("ℹ️ Şifre en az 6 karakter olmalıdır"), 
            font=("Roboto", 11), 
            text_color="gray60")
        info_label.pack(pady=15)
        
        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0), padx=20)
        
        ctk.CTkButton(btn_frame, text=_("❌ İptal"), fg_color="#555555", 
                     hover_color="#333333", height=40,
                     command=self.destroy).pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkButton(btn_frame, text=_("💾 Kaydet"), fg_color="#2CC985", 
                     hover_color="#229966", height=40,
                     command=self.save).pack(side="left", padx=5, fill="x", expand=True)
        
    def save(self):
        """Validate and update password"""
        new_password = self.entry_password.get().strip()
        confirm_password = self.entry_password_confirm.get().strip()
        
        # Empty check
        if not new_password:
            messagebox.showwarning(_("Uyarı"), _("Şifre boş olamaz."))
            self.entry_password.focus()
            return
        
        # Length check
        if len(new_password) < 6:
            messagebox.showwarning(_("Zayıf Şifre"), _("Şifre en az 6 karakter olmalıdır."))
            self.entry_password.focus()
            return
        
        # Match check
        if new_password != confirm_password:
            messagebox.showwarning(_("Uyarı"), _("Şifreler eşleşmiyor. Lütfen kontrol ediniz."))
            self.entry_password_confirm.focus()
            return

        try:
            data = {"password": new_password}
            self.api_client.put(f"/api/v1/members/{self.member_data['id']}", json=data)
            messagebox.showinfo(_("Başarılı"), _("Şifre başarıyla güncellendi."))
            self.destroy()
        except Exception as e:
            messagebox.showerror(_("Hata"), _("Şifre güncelleme hatası: {error}").format(error=e))
