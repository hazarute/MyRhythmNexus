import customtkinter as ctk
from desktop.core.locale import _
import tkinter.messagebox as messagebox
from desktop.core.api_client import ApiClient
from datetime import datetime
from desktop.ui.components.activity_item import ActivityItem

class AttendanceTab:
    def __init__(self, parent_frame, api_client: ApiClient, member: dict):
        self.parent = parent_frame
        self.api_client = api_client
        self.member = member
        # State for optimized updates
        self.scroll_frame = None
        self.is_setup = False
        
    def setup(self):
        """Setup attendance tab skeleton (run once)."""
        if self.is_setup:
            return

        # Header (fixed, outside of scroll area)
        header = ctk.CTkFrame(self.parent, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(header, text=_("📊 Katılım Geçmişi"), font=("Roboto", 20, "bold")).pack(pady=(0, 0))

        # Scrollable content (created once)
        self.scroll_frame = ctk.CTkScrollableFrame(self.parent)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.is_setup = True

        # Load initial data
        self.refresh()

    def update_ui(self, checkins):
        """Update scroll_frame content with given checkins list."""
        # Clear existing
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        if not checkins:
            ctk.CTkLabel(self.scroll_frame, text=_("Katılım kaydı bulunamadı."), text_color="gray").pack(pady=20)
            return

        for chk in checkins:
            self.create_activity_item(self.scroll_frame, chk)

    def create_activity_item(self, parent, chk):
        """Create modern activity card with reordered layout"""
        """Use the reusable `ActivityItem` component to render an activity card."""
        ai = ActivityItem(parent, chk, on_delete=self.delete_checkin)
        ai.pack(fill="x", pady=3, padx=5)

    def delete_checkin(self, checkin_id):
        """Delete a check-in record after user confirmation"""
        # Show confirmation dialog
        if not messagebox.askyesno(_("Silme Onayı"), _("Bu katılım kaydını silmek istediğinizden emin misiniz?\nBu işlem geri alınamaz.")):
            return
        
        try:
            # Call delete API
            response = self.api_client.delete(f"/api/v1/checkin/history/{checkin_id}")
            
            # Show success message
            messagebox.showinfo(_("Başarılı"), _("Katılım kaydı başarıyla silindi."))
            
            # Refresh the tab
            self.refresh()
            
        except Exception as e:
            messagebox.showerror(_("Hata"), _("Silme işlemi başarısız: {}").format(str(e)))

    def refresh(self):
        """Refresh data and update UI without rebuilding skeleton."""
        # Ensure skeleton exists
        if not self.is_setup:
            self.setup()

        try:
            checkins = self.api_client.get(f"/api/v1/checkin/history?member_id={self.member['id']}")
        except Exception as e:
            # show error inside scroll_frame
            for w in self.scroll_frame.winfo_children():
                w.destroy()
            ctk.CTkLabel(self.scroll_frame, text=_("Hata: {}" ).format(e), text_color="red").pack(pady=20)
            return

        # Update list UI
        self.update_ui(checkins)
