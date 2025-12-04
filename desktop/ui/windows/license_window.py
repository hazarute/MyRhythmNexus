import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.license_manager import LicenseManager

class LicenseWindow(ctk.CTkFrame):
    def __init__(self, master, license_manager: LicenseManager, on_success):
        super().__init__(master)
        self.master = master
        self.license_manager = license_manager
        self.on_success = on_success
        
        self.pack(fill="both", expand=True)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Center container
        self.center_frame = ctk.CTkFrame(self)
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.center_frame, 
            text=_("Lisans Aktivasyonu"), 
            font=("Roboto", 24, "bold")
        )
        self.title_label.pack(pady=20, padx=40)
        
        # Info
        self.info_label = ctk.CTkLabel(
            self.center_frame,
            text=_("Lütfen ürün lisans anahtarınızı giriniz.\nFormat: MRN-XXXX-XXXX-XXXX"),
            font=("Roboto", 14)
        )
        self.info_label.pack(pady=10)
        
        # Entry
        self.key_entry = ctk.CTkEntry(
            self.center_frame,
            placeholder_text="MRN-...",
            width=300,
            height=40,
            font=("Roboto", 14)
        )
        self.key_entry.pack(pady=20)
        
        # Machine ID Info (Optional, helpful for support)
        machine_id = self.license_manager.get_machine_id()
        self.machine_id_label = ctk.CTkLabel(
            self.center_frame,
            text=f"Machine ID: {machine_id}",
            font=("Roboto", 10),
            text_color="gray"
        )
        self.machine_id_label.pack(pady=5)

        # Status Label
        self.status_label = ctk.CTkLabel(
            self.center_frame,
            text="",
            text_color="red"
        )
        self.status_label.pack(pady=10)
        
        # Button
        self.activate_btn = ctk.CTkButton(
            self.center_frame,
            text=_("Aktive Et"),
            command=self.activate_license,
            height=40,
            width=200
        )
        self.activate_btn.pack(pady=20)

    def activate_license(self):
        key = self.key_entry.get().strip()
        if not key:
            self.status_label.configure(text=_("Lütfen bir anahtar giriniz."), text_color="red")
            return
            
        self.activate_btn.configure(state="disabled", text=_("Kontrol ediliyor..."))
        self.update_idletasks()
        
        # Save temporarily to try validation
        self.license_manager.save_license_key(key)
        
        result = self.license_manager.validate_license_sync()
        
        if result.get("valid"):
            self.status_label.configure(text=_("Lisans başarıyla aktif edildi!"), text_color="green")
            self.after(1000, self.on_success)
        else:
            msg = result.get("message", _("Bilinmeyen hata"))
            self.status_label.configure(text=msg, text_color="red")
            self.activate_btn.configure(state="normal", text=_("Aktive Et"))
