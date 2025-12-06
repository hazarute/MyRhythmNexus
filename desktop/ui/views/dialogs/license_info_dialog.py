import customtkinter as ctk
import webbrowser
from tkinter import messagebox

from desktop.core.config import DesktopConfig, get_config_path


class LicenseInfoDialog(ctk.CTkToplevel):
    def __init__(self, master, api_client=None):
        super().__init__(master)
        self.title("Lisans Bilgileri")
        self.resizable(False, False)
        self.geometry("460x240")

        # Read config values
        license_key = DesktopConfig.get_value('license_key', '<ayar yok>')
        license_server = DesktopConfig.load_license_server_url()
        backend = DesktopConfig.load_backend_url()

        # Layout
        frame = ctk.CTkFrame(self, corner_radius=8)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(frame, text="Lisans Bilgileri", font=("Roboto", 14, "bold")).pack(anchor="w", pady=(0,8))

        # License key
        ctk.CTkLabel(frame, text="Lisans Anahtarı:", anchor="w").pack(fill="x")
        lbl_key = ctk.CTkEntry(frame, width=420)
        lbl_key.insert(0, str(license_key))
        lbl_key.configure(state="readonly")
        lbl_key.pack(pady=(0,8))

        # License server
        ctk.CTkLabel(frame, text="Lisans Sunucusu:", anchor="w").pack(fill="x")
        lbl_ls = ctk.CTkEntry(frame, width=420)
        lbl_ls.insert(0, str(license_server))
        lbl_ls.configure(state="readonly")
        lbl_ls.pack(pady=(0,8))

        # Backend URL
        ctk.CTkLabel(frame, text="Backend URL:", anchor="w").pack(fill="x")
        lbl_be = ctk.CTkEntry(frame, width=420)
        lbl_be.insert(0, str(backend))
        lbl_be.configure(state="readonly")
        lbl_be.pack(pady=(0,8))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(8,0))

        def copy_key():
            try:
                self.clipboard_clear()
                self.clipboard_append(str(license_key))
                messagebox.showinfo("Kopyalandı", "Lisans anahtarı panoya kopyalandı.")
            except Exception:
                messagebox.showerror("Hata", "Panoya kopyalanamadı.")

        def open_license_server():
            if not license_server:
                messagebox.showwarning("Uyarı", "Lisans sunucusu adresi ayarlı değil.")
                return
            webbrowser.open(license_server)

        btn_copy = ctk.CTkButton(btn_frame, text="Lisansı Kopyala", command=copy_key)
        btn_copy.pack(side="left", padx=(0,8))

        btn_open = ctk.CTkButton(btn_frame, text="Lisans Sunucusunu Aç", command=open_license_server)
        btn_open.pack(side="left")

        btn_close = ctk.CTkButton(frame, text="Kapat", command=self.destroy, fg_color="#555555")
        btn_close.pack(side="right", pady=(12,0))
