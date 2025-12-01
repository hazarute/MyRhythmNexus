import customtkinter as ctk
import tkinter.messagebox as messagebox
from desktop.core.api_client import ApiClient
from datetime import datetime

class AttendanceTab:
    def __init__(self, parent_frame, api_client: ApiClient, member: dict):
        self.parent = parent_frame
        self.api_client = api_client
        self.member = member
        
    def setup(self):
        """Setup attendance tab content"""
        # Main scrollable frame
        main_frame = ctk.CTkScrollableFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        ctk.CTkLabel(
            main_frame,
            text="📊 Katılım Geçmişi",
            font=("Roboto", 20, "bold")
        ).pack(pady=(0, 20))

        try:
            checkins = self.api_client.get(f"/api/v1/checkin/history?member_id={self.member['id']}")
            if not checkins:
                ctk.CTkLabel(main_frame, text="Katılım kaydı bulunamadı.", text_color="gray").pack(pady=20)
                return

            # Create modern activity cards
            for chk in checkins:
                self.create_activity_item(main_frame, chk)

        except Exception as e:
            ctk.CTkLabel(main_frame, text=f"Hata: {e}", text_color="red").pack(pady=20)

    def create_activity_item(self, parent, chk):
        """Create modern activity card with reordered layout"""
        # Modern card design for each activity
        card = ctk.CTkFrame(parent, fg_color="#2B2B2B", corner_radius=8, border_width=1, border_color="#404040")
        card.pack(fill="x", pady=3, padx=5)
        
        # Main content frame
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=10)
        
        # Top row: Emoji + Subscription Name + Time/Date + Delete Button
        top_frame = ctk.CTkFrame(content, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 6))
        
        # Determine icon and color based on event type
        event_name = chk.get('event_name', 'Giriş')
        subscription_name = chk.get('subscription_name', 'Bilinmeyen Paket')
        
        if "Seans Bazlı" in event_name:
            icon = "🎯"
            accent_color = "#E5B00D"  # Gold for session-based
            display_name = subscription_name  # Show subscription name for session-based
        elif "Zaman Bazlı" in event_name:
            icon = "⏰"
            accent_color = "#3B8ED0"  # Blue for time-based
            display_name = subscription_name  # Show subscription name for time-based
        else:
            icon = "📅"
            accent_color = "#2CC985"  # Green for class events
            display_name = event_name  # Show event name for class events
        
        # 1. Emoji (Icon)
        icon_frame = ctk.CTkFrame(top_frame, fg_color=accent_color, width=32, height=32, corner_radius=6)
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text=icon, font=("Segoe UI Emoji", 14)).pack(expand=True)
        
        # 2. Subscription Name
        name_label = ctk.CTkLabel(
            top_frame, 
            text=display_name, 
            font=("Roboto", 14, "bold"), 
            text_color="white"
        )
        name_label.pack(side="left", padx=(12, 0))
        
        # 3. Time and Date
        check_in_time_str = chk.get('check_in_time', '')
        if check_in_time_str:
            try:
                # Parse local time (already converted by ApiClient)
                if 'T' in check_in_time_str:
                    local_time = datetime.fromisoformat(check_in_time_str)
                else:
                    local_time = datetime.strptime(check_in_time_str, '%Y-%m-%d %H:%M:%S')
                
                date_part = local_time.strftime('%Y-%m-%d')
                time_part = local_time.strftime('%H:%M')
                time_display = f"{time_part} • {date_part}"
            except Exception as e:
                print(f"Error parsing datetime {check_in_time_str}: {e}")
                time_display = check_in_time_str.replace('T', ' ')[:16]
        else:
            time_display = ""
        
        time_label = ctk.CTkLabel(
            top_frame, 
            text=time_display, 
            font=("Roboto", 11), 
            text_color="gray70"
        )
        time_label.pack(side="left", padx=(15, 0))
        
        # Delete button on the right (unchanged)
        delete_btn = ctk.CTkButton(
            top_frame,
            text="🗑️",
            width=40,
            height=40,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            font=("Segoe UI Emoji", 16),
            command=lambda chk_id=chk.get('id'): self.delete_checkin(chk_id)
        )
        delete_btn.pack(side="right", padx=(0, 5))
        
        # Bottom row: Verified by (Kaydı yapan)
        verified_by = chk.get('verified_by_name', 'Sistem')
        if verified_by != 'Sistem':
            verifier_text = f"✓ {verified_by}"
            verifier_color = "gray60"
        else:
            verifier_text = "🤖 Otomatik"
            verifier_color = "gray60"
        
        ctk.CTkLabel(
            content, 
            text=verifier_text, 
            font=("Roboto", 10), 
            text_color=verifier_color, 
            anchor="w"
        ).pack(fill="x")

    def delete_checkin(self, checkin_id):
        """Delete a check-in record after user confirmation"""
        # Show confirmation dialog
        if not messagebox.askyesno("Silme Onayı", "Bu katılım kaydını silmek istediğinizden emin misiniz?\nBu işlem geri alınamaz."):
            return
        
        try:
            # Call delete API
            response = self.api_client.delete(f"/api/v1/checkin/history/{checkin_id}")
            
            # Show success message
            messagebox.showinfo("Başarılı", "Katılım kaydı başarıyla silindi.")
            
            # Refresh the tab
            self.refresh()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Silme işlemi başarısız: {str(e)}")

    def refresh(self):
        """Refresh the tab content"""
        # Clear existing content
        for widget in self.parent.winfo_children():
            widget.destroy()
        # Re-setup
        self.setup()
