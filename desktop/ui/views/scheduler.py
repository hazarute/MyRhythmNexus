import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
from desktop.core.api_client import ApiClient
from desktop.ui.views.dialogs.add_event_dialog import AddEventDialog
from desktop.ui.views.dialogs.manage_templates_dialog import ManageTemplatesDialog

class SchedulerView(ctk.CTkFrame):
    def __init__(self, master, api_client: ApiClient):
        super().__init__(master)
        self.api_client = api_client
        
        self.current_week_start = self.get_start_of_week(datetime.now())
        
        self.pack(fill="both", expand=True)
        
        # Top Bar
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=20, pady=10)
        
        self.btn_prev = ctk.CTkButton(self.top_bar, text="< Önceki Hafta", width=100, command=self.prev_week)
        self.btn_prev.pack(side="left")
        
        self.lbl_week = ctk.CTkLabel(self.top_bar, text="", font=("Roboto", 16, "bold"))
        self.lbl_week.pack(side="left", padx=20)
        
        self.btn_next = ctk.CTkButton(self.top_bar, text="Sonraki Hafta >", width=100, command=self.next_week)
        self.btn_next.pack(side="left")
        
        self.btn_add = ctk.CTkButton(self.top_bar, text="+ Seans Ekle", command=self.open_add_dialog)
        self.btn_add.pack(side="right", padx=(0, 10))
        
        self.btn_manage = ctk.CTkButton(self.top_bar, text="⚙️ Şablonlar", command=self.open_templates_dialog)
        self.btn_manage.pack(side="right")

        # Calendar Grid
        self.grid_frame = ctk.CTkFrame(self)
        self.grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure grid columns (7 days)
        for i in range(7):
            self.grid_frame.grid_columnconfigure(i, weight=1)
        self.grid_frame.grid_rowconfigure(1, weight=1) # Row 0 is header, Row 1 is content

        self.day_headers = []
        self.day_frames = []
        
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        for i, day in enumerate(days):
            # Header
            lbl = ctk.CTkLabel(self.grid_frame, text=day, font=("Roboto", 14, "bold"))
            lbl.grid(row=0, column=i, pady=5, sticky="ew")
            self.day_headers.append(lbl)
            
            # Content Frame (Scrollable if needed, but let's use regular frame inside a scrollable container if we want full scroll. 
            # For now, let's make each day a scrollable frame to handle many classes)
            frame = ctk.CTkScrollableFrame(self.grid_frame)
            frame.grid(row=1, column=i, padx=2, pady=2, sticky="nsew")
            self.day_frames.append(frame)

        self.update_week_label()
        self.load_events()

    def get_start_of_week(self, dt):
        start = dt - timedelta(days=dt.weekday())
        return start.replace(hour=0, minute=0, second=0, microsecond=0)

    def prev_week(self):
        self.current_week_start -= timedelta(weeks=1)
        self.update_week_label()
        self.load_events()

    def next_week(self):
        self.current_week_start += timedelta(weeks=1)
        self.update_week_label()
        self.load_events()

    def update_week_label(self):
        end = self.current_week_start + timedelta(days=6)
        self.lbl_week.configure(text=f"{self.current_week_start.strftime('%d %b')} - {end.strftime('%d %b %Y')}")
        
        # Update headers with dates
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        for i, day in enumerate(days):
            date = self.current_week_start + timedelta(days=i)
            self.day_headers[i].configure(text=f"{day}\n{date.strftime('%d.%m')}")

    def load_events(self):
        # Clear existing
        for frame in self.day_frames:
            for widget in frame.winfo_children():
                widget.destroy()
        
        start_str = self.current_week_start.isoformat()
        end_date = self.current_week_start + timedelta(days=7)
        end_str = end_date.isoformat()
        
        try:
            events = self.api_client.get("/api/v1/operations/events", params={"start_date": start_str, "end_date": end_str})
            
            for event in events:
                self.create_event_card(event)
                
        except Exception as e:
            print(f"Error loading events: {e}")

    def create_event_card(self, event):
        start_dt = datetime.fromisoformat(event["start_time"])
        day_idx = start_dt.weekday()
        
        parent = self.day_frames[day_idx]
        
        card = ctk.CTkFrame(parent, fg_color=("gray85", "gray25"), corner_radius=6)
        card.pack(fill="x", pady=4, padx=2)
        
        time_str = start_dt.strftime("%H:%M")
        
        # Event name - try different possible keys
        event_name = (
            event.get("template", {}).get("name") or
            event.get("name") or
            event.get("class_name") or
            "Ders"
        )
        
        # Instructor info
        instructor_info = ""
        if event.get("instructor"):
            instr = event["instructor"]
            if isinstance(instr, dict):
                instructor_info = f"{instr.get('first_name', '')} {instr.get('last_name', '')}".strip()
            else:
                instructor_info = str(instr)
        elif event.get("instructor_name"):
            instructor_info = event["instructor_name"]
        
        # Capacity
        capacity = event.get("capacity", 0)
        
        # Main content frame
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=5, pady=4)
        
        # Row 1: Time + Event Name
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 2))
        
        ctk.CTkLabel(top_row, text=time_str, font=("Roboto", 13, "bold"), text_color="#3B8ED0").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(top_row, text=event_name, font=("Roboto", 12, "bold")).pack(side="left", fill="x", expand=True)
        
        # Row 2: Instructor (if available)
        if instructor_info:
            ctk.CTkLabel(content, text=f"👨‍🏫 {instructor_info}", font=("Roboto", 10), text_color="gray").pack(anchor="w", padx=(20, 0), pady=(0, 2))
        
        # Row 3: Capacity
        ctk.CTkLabel(content, text=f"Kapasite: {capacity}", font=("Roboto", 10), text_color="gray").pack(anchor="w", padx=(20, 0))

        # Click event
        card.bind("<Button-1>", lambda e, ev=event: self.show_event_detail(ev))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, ev=event: self.show_event_detail(ev))

    def show_event_detail(self, event):
        EventDetailDialog(self, self.api_client, event, self.load_events)

    def open_add_dialog(self):
        AddEventDialog(self, self.api_client, self.load_events)

    def open_templates_dialog(self):
        ManageTemplatesDialog(self, self.api_client)


class EventDetailDialog(ctk.CTkToplevel):
    def __init__(self, parent, api_client, event, on_close):
        super().__init__(parent)
        self.api_client = api_client
        self.event = event
        self.on_close = on_close
        
        self.title("Seans Detayı")
        self.geometry("600x500")
        
        # Info
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        tmpl_name = event.get("template", {}).get("name", "Ders")
        start_dt = datetime.fromisoformat(event["start_time"])
        time_str = start_dt.strftime("%d.%m.%Y %H:%M")
        
        ctk.CTkLabel(info_frame, text=tmpl_name, font=("Roboto", 20, "bold")).pack(anchor="w", padx=10)
        ctk.CTkLabel(info_frame, text=f"Zaman: {time_str}").pack(anchor="w", padx=10)
        ctk.CTkLabel(info_frame, text=f"Kapasite: {event['capacity']}").pack(anchor="w", padx=10)
        
        # Participants
        ctk.CTkLabel(self, text="Katılımcılar", font=("Roboto", 16, "bold")).pack(pady=(20, 5))
        
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Add Participant
        add_frame = ctk.CTkFrame(self)
        add_frame.pack(fill="x", padx=10, pady=10)
        
        self.entry_search = ctk.CTkEntry(add_frame, placeholder_text="Üye Ara (Ad/Tel)...")
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(add_frame, text="Ara & Ekle", command=self.search_and_add).pack(side="left")
        
        # Cancel Class Button
        ctk.CTkButton(self, text="Seansı İptal Et", fg_color="red", hover_color="darkred", command=self.cancel_class).pack(pady=10)
        
        self.load_participants()

    def load_participants(self):
        for w in self.list_frame.winfo_children(): w.destroy()
        
        try:
            bookings = self.api_client.get(f"/api/v1/operations/events/{self.event['id']}/bookings")
            
            if not bookings:
                ctk.CTkLabel(self.list_frame, text="Henüz katılımcı yok.").pack(pady=10)
                return
                
            for b in bookings:
                row = ctk.CTkFrame(self.list_frame)
                row.pack(fill="x", pady=2)
                
                ctk.CTkLabel(row, text=b.get("member_name", "Bilinmeyen Üye")).pack(side="left", padx=10)
                ctk.CTkLabel(row, text=b.get("status", "-")).pack(side="left", padx=10)
                
                ctk.CTkButton(row, text="Sil", width=50, fg_color="red", height=24, 
                            command=lambda bid=b["id"]: self.remove_booking(bid)).pack(side="right", padx=5)
                            
        except Exception as e:
            ctk.CTkLabel(self.list_frame, text=f"Hata: {e}").pack()

    def search_and_add(self):
        term = self.entry_search.get()
        if not term: return
        
        # 1. Search Member
        try:
            members = self.api_client.get("/api/v1/members/", params={"search": term})
            if not members:
                messagebox.showwarning("Uyarı", "Üye bulunamadı.")
                return
            
            # If multiple, show selection dialog (Simplified: pick first or show list)
            # For now, let's pick first for speed, or better, show a small popup
            member = members[0] # TODO: Better selection
            
            # 2. Find Active Subscription
            subs = self.api_client.get(f"/api/v1/sales/subscriptions?member_id={member['id']}")
            active_sub = next((s for s in subs if s["status"] == "active"), None)
            
            if not active_sub:
                messagebox.showwarning("Uyarı", f"{member['first_name']} {member['last_name']} için aktif abonelik bulunamadı.")
                return
                
            # 3. Create Booking
            payload = {
                "member_user_id": member["id"],
                "event_id": self.event["id"],
                "subscription_id": active_sub["id"]
            }
            
            self.api_client.post("/api/v1/operations/bookings", json=payload)
            messagebox.showinfo("Başarılı", "Üye eklendi.")
            self.entry_search.delete(0, "end")
            self.load_participants()
        except Exception as e:
            messagebox.showerror("Hata", f"İşlem hatası: {e}")

    def remove_booking(self, booking_id):
        if not messagebox.askyesno("Onay", "Bu rezervasyonu silmek istediğinize emin misiniz?"):
            return
            
        try:
            self.api_client.delete(f"/api/v1/operations/bookings/{booking_id}")
            self.load_participants()
        except Exception as e:
            messagebox.showerror("Hata", f"Silme başarısız: {e}")

    def cancel_class(self):
        if not messagebox.askyesno("Onay", "Bu seansı iptal etmek istediğinize emin misiniz?"):
            return
            
        try:
            self.api_client.delete(f"/api/v1/operations/events/{self.event['id']}")
            messagebox.showinfo("Başarılı", "Seans iptal edildi.")
            self.destroy()
            self.on_close()
        except Exception as e:
            messagebox.showerror("Hata", f"İptal başarısız: {e}")
