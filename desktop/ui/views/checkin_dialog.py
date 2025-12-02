import customtkinter as ctk
from desktop.core.api_client import ApiClient
from desktop.core.locale import _
from datetime import datetime

class CheckInDialog(ctk.CTkToplevel):
    def __init__(self, parent, api_client: ApiClient, qr_token: str, on_refresh=None):
        super().__init__(parent)
        self.api_client = api_client
        self.qr_token = qr_token
        self.on_refresh = on_refresh
        
        self.title(_("Giriş Kontrol"))
        self.geometry("500x600")
        
        # Center the window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.grid_columnconfigure(0, weight=1)
        
        self.label_status = ctk.CTkLabel(self, text=_("Kontrol Ediliyor..."), font=("Roboto", 18))
        self.label_status.pack(pady=20)
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.selected_event_id = ctk.StringVar()
        
        # Start scan immediately
        self.after(100, self.perform_scan)

    def perform_scan(self):
        try:
            response = self.api_client.get(f"/api/v1/checkin/scan?qr_token={self.qr_token}")
            if response.get("valid"):
                self.show_valid_result(response)
            else:
                self.show_error(response.get("message", _("Geçersiz QR")))
        except Exception as e:
            self.show_error(f"{_('Bağlantı Hatası')}: {e}")

    def show_error(self, message):
        self.label_status.configure(text=_("❌ Giriş Başarısız"), text_color="red")
        
        lbl = ctk.CTkLabel(self.content_frame, text=message, font=("Roboto", 16))
        lbl.pack(pady=20)
        
        btn = ctk.CTkButton(self.content_frame, text=_("Kapat"), command=self.destroy, fg_color="gray")
        btn.pack(pady=20)
        
        # Play error sound (placeholder)
        self.bell()

    def show_valid_result(self, data):
        self.label_status.configure(text=_("✅ QR Kod Geçerli"), text_color="green")
        
        # Member Info
        info_frame = ctk.CTkFrame(self.content_frame)
        info_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(info_frame, text=_("Üye: {}").format(data.get('member_name')), font=("Roboto", 16, "bold")).pack(anchor="w", padx=10, pady=5)
        ctk.CTkLabel(info_frame, text=_("Paket: {}").format(data.get('subscription_name')), font=("Roboto", 14)).pack(anchor="w", padx=10, pady=2)
        
        rem = data.get('remaining_sessions')
        rem_text = _("Kalan Hak: {}").format(rem) if rem is not None else _("Kalan Hak: Sınırsız")
        ctk.CTkLabel(info_frame, text=rem_text, font=("Roboto", 14), text_color="orange").pack(anchor="w", padx=10, pady=5)

        # Events
        events = data.get("eligible_events", [])
        
        ctk.CTkLabel(self.content_frame, text=_("Giriş Yapılacak Ders:"), font=("Roboto", 14, "bold")).pack(anchor="w", pady=(10, 5))
        
        if not events:
            ctk.CTkLabel(self.content_frame, text=_("Şu an uygun ders bulunamadı."), text_color="orange").pack(pady=10)
            ctk.CTkLabel(self.content_frame, text=_("Ders seçmeden giriş yapabilirsiniz."), font=("Roboto", 12)).pack(pady=5)
            
            # Allow check-in without event
            btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            btn_frame.pack(fill="x", pady=20)
            
            ctk.CTkButton(btn_frame, text=_("İptal"), command=self.destroy, fg_color="gray", width=100).pack(side="left", padx=10)
            ctk.CTkButton(btn_frame, text=_("Giriş Yap (Ders Seçmeden)"), command=self.do_check_in_without_event, fg_color="green", width=200).pack(side="right", padx=10)
            return

        self.events_frame = ctk.CTkScrollableFrame(self.content_frame, height=200)
        self.events_frame.pack(fill="x", pady=5)
        
        for event in events:
            eid = event['id']
            name = event['name']
            start = event['start_time'][11:16] # HH:MM
            instr = event['instructor_name']
            
            rb = ctk.CTkRadioButton(
                self.events_frame, 
                text=_("{} - {} ({})").format(start, name, instr),
                variable=self.selected_event_id,
                value=eid
            )
            rb.pack(anchor="w", pady=5, padx=5)
            
        # Select first by default
        if events:
            self.selected_event_id.set(events[0]['id'])

        # Action Buttons
        btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(btn_frame, text=_("İptal"), command=self.destroy, fg_color="gray", width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text=_("Giriş Yap"), command=self.do_check_in, fg_color="green", width=150).pack(side="right", padx=10)

    def do_check_in(self):
        event_id = self.selected_event_id.get()
        if not event_id:
            return
            
        try:
            payload = {
                "qr_token": self.qr_token,
                "event_id": event_id
            }
            response = self.api_client.post("/api/v1/checkin/check-in", json=payload)
            self.show_success(response)
                
        except Exception as e:
            self.show_error(str(e))

    def do_check_in_without_event(self):
        """Check-in without event selection (for SESSION_BASED or TIME_BASED)"""
        try:
            payload = {
                "qr_token": self.qr_token,
                "event_id": None  # No event selected
            }
            response = self.api_client.post("/api/v1/checkin/check-in", json=payload)
            self.show_success(response)
                
        except Exception as e:
            self.show_error(str(e))

    def show_success(self, res):
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        self.label_status.configure(text=_("🎉 Giriş Başarılı!"), text_color="green")
        
        ctk.CTkLabel(self.content_frame, text=_("Hoşgeldin, {}").format(res.get('member_name')), font=("Roboto", 18)).pack(pady=20)
        
        rem = res.get('remaining_sessions')
        ctk.CTkLabel(self.content_frame, text=_("Kalan Hak: {}").format(rem), font=("Roboto", 24, "bold")).pack(pady=10)
        
        def on_close():
            if self.on_refresh:
                try:
                    self.on_refresh()
                except Exception as e:
                    print(f"Error during refresh: {e}")
            self.destroy()
        
        ctk.CTkButton(self.content_frame, text=_("Tamam"), command=on_close).pack(pady=20)
        
        # Play success sound (placeholder)
        # In Windows, print('\a') might work or winsound
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_OK)
        except:
            self.bell()
