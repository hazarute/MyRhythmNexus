import customtkinter as ctk
from desktop.core.api_client import ApiClient
from desktop.core.locale import _

# Ensure only one check-in dialog is active at a time
_active_checkin_dialog = None

class CheckInDialog(ctk.CTkToplevel):
    def __init__(self, parent, api_client: ApiClient, qr_token: str, on_refresh=None):
        super().__init__(parent)
        # If another dialog is active, focus it and close this one immediately
        global _active_checkin_dialog
        try:
            if _active_checkin_dialog is not None and getattr(_active_checkin_dialog, "winfo_exists", lambda: False)():
                try:
                    _active_checkin_dialog.lift()
                    _active_checkin_dialog.focus_force()
                    _active_checkin_dialog.attributes("-topmost", True)
                    _active_checkin_dialog.attributes("-topmost", False)
                except Exception:
                    pass
                try:
                    self.destroy()
                except Exception:
                    pass
                return
        except Exception:
            pass
        self.api_client = api_client
        self.qr_token = qr_token
        self.on_refresh = on_refresh
        # Track whether we've already invoked the refresh callback to avoid duplicate calls
        self._refresh_called = False
        
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
        # Make dialog modal: keep on top and prevent interaction with parent
        try:
            self.transient(parent)
            self.grab_set()
        except Exception:
            pass
        try:
            self.focus_force()
            self.lift()
            self.attributes("-topmost", True)
        except Exception:
            pass
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        try:
            _active_checkin_dialog = self
        except Exception:
            pass
        self.label_status = ctk.CTkLabel(self, text=_("Kontrol Ediliyor..."), font=("Roboto", 18))
        self.label_status.pack(pady=20)
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Start scan immediately
        self.after(100, self.perform_scan)

    def perform_scan(self):
        try:
            response = self.api_client.get(f"/api/v1/checkin/scan?qr_token={self.qr_token}")
            if response.get("valid"):
                # Do immediate check-in: select first eligible event if any
                events = response.get("eligible_events", [])
                if events:
                    event_id = events[0].get("id")
                else:
                    event_id = None

                # update status
                try:
                    self.label_status.configure(text=_("Giriş Yapılıyor..."), text_color="white")
                except Exception:
                    pass

                try:
                    payload = {"qr_token": self.qr_token, "event_id": event_id}
                    checkin_resp = self.api_client.post("/api/v1/checkin/check-in", json=payload)
                    self.show_success(checkin_resp)
                except Exception as e:
                    self.show_error(str(e))
            else:
                self.show_error(response.get("message", _("Geçersiz QR")))
        except Exception as e:
            self.show_error(f"{_('Bağlantı Hatası')}: {e}")
    
    def _on_close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        try:
            # ensure topmost flag removed before destroy
            self.attributes("-topmost", False)
        except Exception:
            pass
        # Attempt to call on_refresh if provided and not already called
        try:
            if self.on_refresh and not getattr(self, "_refresh_called", False):
                try:
                    self._refresh_called = True
                    self.on_refresh()
                except Exception as e:
                    print(f"Error during refresh on close: {e}")
        except Exception:
            pass

        # clear module-level active dialog marker
        try:
            global _active_checkin_dialog
            if _active_checkin_dialog is self:
                _active_checkin_dialog = None
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    def show_error(self, message):
        self.label_status.configure(text=_("❌ Giriş Başarısız"), text_color="red")
        
        lbl = ctk.CTkLabel(self.content_frame, text=message, font=("Roboto", 16))
        lbl.pack(pady=20)
        
        btn = ctk.CTkButton(self.content_frame, text=_("Kapat"), command=self._on_close, fg_color="gray")
        btn.pack(pady=20)
        
        # Play error sound (placeholder)
        try:
            import winsound
            # Lower-pitched single beep for error (400 Hz, 400 ms). If Beep fails, fall back to MessageBeep with error icon.
            try:
                winsound.Beep(400, 400)
            except Exception:
                try:
                    winsound.MessageBeep(winsound.MB_ICONHAND)
                except Exception:
                    self.bell()
        except Exception:
            self.bell()
        # Auto-close after 3 seconds for errors as well
        try:
            self.after(3000, self._on_close)
        except Exception:
            pass

    # Removed intermediate 'QR Kod Geçerli' UI. Check-in is attempted immediately on scan.

    def do_check_in(self, event_id=None):
        """Perform check-in. If event_id is None, do a lessonless check-in."""
        try:
            if event_id is None:
                event_id_val = None
            else:
                try:
                    event_id_val = int(event_id)
                except Exception:
                    event_id_val = event_id

            payload = {"qr_token": self.qr_token, "event_id": event_id_val}
            response = self.api_client.post("/api/v1/checkin/check-in", json=payload)
            self.show_success(response)
        except Exception as e:
            self.show_error(str(e))

    def do_check_in_without_event(self):
        """Check-in without event selection (for SESSION_BASED or TIME_BASED)"""
        try:
            # Delegate to generic do_check_in with no event
            self.do_check_in(None)
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
        
        def _on_success_close():
            if self.on_refresh:
                try:
                    # mark as called so _on_close doesn't call it again
                    self._refresh_called = True
                    self.on_refresh()
                except Exception as e:
                    print(f"Error during refresh: {e}")
            self._on_close()

        ctk.CTkButton(self.content_frame, text=_("Tamam"), command=_on_success_close).pack(pady=20)
        # Auto-close after 3 seconds
        try:
            self.after(3000, _on_success_close)
        except Exception:
            pass
        
        # Play success sound (placeholder)
        # In Windows, print('\a') might work or winsound
        try:
            import winsound
            # Stronger success beep: higher pitch and longer duration (3000 Hz for 700 ms).
            # Beep amplitude can't be changed via winsound; increasing frequency and duration makes it more noticeable.
            try:
                winsound.Beep(3000, 900)
            except Exception:
                try:
                    winsound.MessageBeep(winsound.MB_OK)
                except Exception:
                    self.bell()
        except Exception:
            self.bell()
