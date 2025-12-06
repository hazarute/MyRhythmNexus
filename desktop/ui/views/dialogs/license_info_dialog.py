import customtkinter as ctk
import webbrowser
from tkinter import messagebox
import jwt
from datetime import datetime, timedelta
import requests

from desktop.core.config import DesktopConfig, get_config_path


class LicenseInfoDialog(ctk.CTkToplevel):
    def __init__(self, master, api_client=None):
        super().__init__(master)
        self.title("Lisans Bilgileri")
        self.resizable(False, False)
        self.geometry("460x500")

        # Read config values
        license_key = DesktopConfig.get_value('license_key', '<ayar yok>')
        license_server = DesktopConfig.load_license_server_url()
        backend = DesktopConfig.load_backend_url()

        # Layout
        frame = ctk.CTkFrame(self, corner_radius=8)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(frame, text="Lisans Bilgileri", font=("Roboto", 14, "bold")).pack(anchor="w", pady=(0,8))

        # License key (editable so user can enter a new key and activate it)
        ctk.CTkLabel(frame, text="Lisans Anahtarı:", anchor="w").pack(fill="x")
        lbl_key = ctk.CTkEntry(frame, width=420)
        lbl_key.insert(0, str(license_key))
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

        # Compute two expiries:
        # - server_expiry: the license's real expires_at from server (if online)
        # - token_expiry: the offline token 'exp' claim (if token saved)
        server_expiry = "Bilinmiyor"
        token_expiry = "Bilinmiyor"

        # helper: convert UTC datetime/epoch/ISO string to Turkey time string dd/mm/YYYY HH:MM
        def _to_turkey_str_from_dt(dt_obj) -> str:
            try:
                if dt_obj is None:
                    return "Bilinmiyor"
                # assume dt_obj is a datetime in UTC (naive) or aware; normalize to UTC then add +3
                if isinstance(dt_obj, datetime):
                    dt_utc = dt_obj
                else:
                    return "Bilinmiyor"
                # add +3 hours for Türkiye
                dt_tr = dt_utc + timedelta(hours=3)
                return dt_tr.strftime('%d/%m/%Y %H:%M')
            except Exception:
                return "Bilinmiyor"

        def _to_turkey_str_from_iso_or_dt(value) -> str:
            try:
                if not value:
                    return "Bilinmiyor"
                if isinstance(value, datetime):
                    return _to_turkey_str_from_dt(value)
                s = str(value)
                # strip Z if present
                if s.endswith('Z'):
                    s = s[:-1]
                # try ISO parsing
                try:
                    dt = datetime.fromisoformat(s)
                    return _to_turkey_str_from_dt(dt)
                except Exception:
                    # fallback common format
                    try:
                        dt = datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
                        return _to_turkey_str_from_dt(dt)
                    except Exception:
                        return "Bilinmiyor"
            except Exception:
                return "Bilinmiyor"

        # token_expiry from saved token
        try:
            token = DesktopConfig.get_value("license_token")
            if token:
                payload = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
                exp = payload.get("exp")
                if exp:
                    dt = datetime.utcfromtimestamp(int(exp))
                    token_expiry = _to_turkey_str_from_dt(dt)
        except Exception:
            token_expiry = "Bilinmiyor"

        # server_expiry: try to query license server for the license record
        try:
            license_key_cfg = DesktopConfig.get_value('license_key')
            if license_key_cfg:
                # Always query the license server directly. The provided `api_client`
                # is for the main backend and does not expose license-server endpoints,
                # which caused 404 responses when used here.
                ls = str(license_server).rstrip('/')
                resp = requests.get(f"{ls}/licenses/", timeout=4)
                resp.raise_for_status()
                data = resp.json()

                if isinstance(data, list):
                    for lic in data:
                        if str(lic.get('license_key')) == str(license_key_cfg):
                            expires = lic.get('expires_at') or lic.get('expires')
                            if expires:
                                # format server expiry (ISO or datetime) to Turkey time
                                server_expiry = _to_turkey_str_from_iso_or_dt(expires)
                                break
        except Exception:
            # network failure or unexpected response; keep as unknown
            pass

        ctk.CTkLabel(frame, text="Lisans (Sunucu) Bitiş Tarihi:", anchor="w").pack(fill="x")
        lbl_server_exp = ctk.CTkEntry(frame, width=420)
        lbl_server_exp.insert(0, server_expiry)
        lbl_server_exp.configure(state="readonly")
        lbl_server_exp.pack(pady=(0,8))

        ctk.CTkLabel(frame, text="Offline Token Geçerlilik:", anchor="w").pack(fill="x")
        lbl_token_exp = ctk.CTkEntry(frame, width=420)
        lbl_token_exp.insert(0, token_expiry)
        lbl_token_exp.configure(state="readonly")
        lbl_token_exp.pack(pady=(0,8))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(8,0))

        def copy_key():
            try:
                self.clipboard_clear()
                self.clipboard_append(str(lbl_key.get()))
                messagebox.showinfo("Kopyalandı", "Lisans anahtarı panoya kopyalandı.")
            except Exception:
                messagebox.showerror("Hata", "Panoya kopyalanamadı.")

        btn_copy = ctk.CTkButton(btn_frame, text="Lisansı Kopyala", command=copy_key)
        btn_copy.pack(side="left", padx=(0,8))

        def activate_key():
            new_key = lbl_key.get().strip()
            if not new_key:
                messagebox.showerror("Hata", "Lütfen geçerli bir lisans anahtarı girin.")
                return
            try:
                # Import here to avoid circular imports at module load
                from desktop.core.license_manager import LicenseManager
                from desktop.core.api_client import ApiClient

                client = api_client if api_client else ApiClient()
                lm = LicenseManager(client)

                # Save the new key and clear any existing offline token
                lm.save_license_key(new_key)
                DesktopConfig.set_value("license_token", None)

                # Trigger validation (online preferred, will save token if received)
                result = lm.validate_license_sync()

                if result.get("valid"):
                    messagebox.showinfo("Başarılı", "Lisans doğrulandı ve etkinleştirildi.")
                    # If the validator returned the token, prefer it (avoids relying on disk read)
                    token_to_use = result.get("token") or DesktopConfig.get_value("license_token")
                    token_expiry_local = "Bilinmiyor"
                    try:
                        if token_to_use:
                            payload = jwt.decode(token_to_use, options={"verify_signature": False, "verify_exp": False})
                            exp = payload.get("exp")
                            if exp:
                                dt = datetime.utcfromtimestamp(int(exp))
                                token_expiry_local = _to_turkey_str_from_dt(dt)
                    except Exception:
                        token_expiry_local = "Bilinmiyor"

                    lbl_token_exp.configure(state="normal")
                    lbl_token_exp.delete(0, "end")
                    lbl_token_exp.insert(0, token_expiry_local)
                    lbl_token_exp.configure(state="readonly")

                    # Also try to refresh server expiry by querying server (prefer api_client)
                    server_expiry_local = "Bilinmiyor"
                    try:
                        key = DesktopConfig.get_value('license_key')
                        if key:
                            # Query the license server directly (not the main backend)
                            ls = str(license_server).rstrip('/')
                            resp = requests.get(f"{ls}/licenses/", timeout=4)
                            resp.raise_for_status()
                            data = resp.json()

                            if isinstance(data, list):
                                for lic in data:
                                    if str(lic.get('license_key')) == str(key):
                                        expires = lic.get('expires_at') or lic.get('expires')
                                        if expires:
                                            server_expiry_local = _to_turkey_str_from_iso_or_dt(expires)
                                            break
                    except Exception:
                        pass

                    lbl_server_exp.configure(state="normal")
                    lbl_server_exp.delete(0, "end")
                    lbl_server_exp.insert(0, server_expiry_local)
                    lbl_server_exp.configure(state="readonly")
                else:
                    messagebox.showerror("Hata", result.get("message", "Lisans doğrulanamadı."))
            except Exception as e:
                messagebox.showerror("Hata", f"Lisans etkinleştirme sırasında hata: {e}")

        btn_activate = ctk.CTkButton(btn_frame, text="Etkinleştir", command=activate_key)
        btn_activate.pack(side="left", padx=(0,8))

        btn_close = ctk.CTkButton(frame, text="Kapat", command=self.destroy, fg_color="#555555")
        btn_close.pack(side="right", pady=(12,0))
