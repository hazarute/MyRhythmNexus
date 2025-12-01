import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Optional

from desktop.core.api_client import ApiClient


class AddPlanDialog(ctk.CTkToplevel):
    """Dialog for adding a new plan"""
    
    def __init__(self, parent, api_client: ApiClient, on_success_callback):
        super().__init__(parent)
        self.api_client = api_client
        self.on_success_callback = on_success_callback
        
        self.title("Yeni Plan Ekle")
        self.geometry("500x650")
        
        self.lift()
        self.focus_force()
        self.grab_set()
        
        # Main Container
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(self.main_frame, text="📋 Yeni Plan Ekle", 
                    font=("Roboto", 22, "bold")).pack(pady=(20, 30))
        
        # Form Fields
        self.entry_name = self.create_input(self.main_frame, "📝 Plan Adı", placeholder="Örn: 3 Aylık 24 Seans")
        
        # Cycle period mapping (Turkish -> English)
        self.cycle_map = {
            "📅 Aylık (28 gün)": "MONTHLY",
            "📆 3 Aylık (84 gün)": "QUARTERLY",
            "📊 6 Aylık (168 gün)": "SEMI_ANNUAL",
            "🎯 Yıllık (365 gün)": "YEARLY",
            "📆 Haftalık (7 gün)": "WEEKLY",
            "🔒 Özel Tarih (Manuel)": "FIXED"
        }
        
        self.entry_cycle = self.create_combo(
            self.main_frame,
            "📆 Geçerlilik Süresi",
            list(self.cycle_map.keys()),
            "📅 Aylık (28 gün)",
            command=self._on_cycle_change,
        )
        
        self.entry_sessions = self.create_input(self.main_frame, "🎯 Seans Sayısı", 
                                               placeholder="Boş bırakırsan sınırsız (0 veya boş)")

        self.entry_repeat_weeks = self.create_input(
            self.main_frame,
            "♻️ Tekrarlayan Haftalar",
            placeholder="Girdiğin seans haftada tekrar eder (örnek: 4)",
            value="1",
        )
        self.entry_repeat_weeks.configure(state="disabled")
        self._on_cycle_change(self.entry_cycle.get())
        
        self.entry_desc = self.create_input(self.main_frame, "💬 Açıklama")
        
        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=30, padx=20)
        
        ctk.CTkButton(btn_frame, text="❌ İptal", fg_color="#555555", 
                     hover_color="#333333", width=100, 
                     command=self.destroy).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(btn_frame, text="💾 Kaydet", fg_color="#2CC985", 
                     hover_color="#229966", width=100, 
                     command=self.save).pack(side="left", padx=10, expand=True)

    def create_input(self, parent, label, value="", placeholder=""):
        """Create a labeled input field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=8)
        
        ctk.CTkLabel(frame, text=label, font=("Roboto", 14), 
                    width=150, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame, height=35, font=("Roboto", 14), 
                           placeholder_text=placeholder)
        entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        if value:
            entry.insert(0, value)
        return entry
    
    def create_combo(
        self,
        parent,
        label,
        values,
        default,
        command: Optional[Callable[[str], None]] = None,
    ):
        """Create a labeled combobox field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=8)
        
        ctk.CTkLabel(frame, text=label, font=("Roboto", 14), 
                    width=150, anchor="w").pack(side="left")
        combo = ctk.CTkComboBox(
            frame,
            values=values,
            height=35,
            font=("Roboto", 14),
            state="readonly",
            justify="left",
            command=command,
        )
        combo.pack(side="left", fill="x", expand=True, padx=(10, 0))
        combo.set(default)
        combo._entry.bind("<Button-1>", lambda e: combo._clicked(None))
        return combo

    def _on_cycle_change(self, value: str):
        weekly_label = "📆 Haftalık (7 gün)"
        is_weekly = value == weekly_label
        self.entry_repeat_weeks.configure(state="normal" if is_weekly else "disabled")
        if not is_weekly:
            self.entry_repeat_weeks.delete(0, "end")
            self.entry_repeat_weeks.insert(0, "1")

    def save(self):
        """Save the new plan"""
        name = self.entry_name.get()
        cycle_tr = self.entry_cycle.get()
        sessions_str = self.entry_sessions.get().strip()
        desc = self.entry_desc.get()

        # Convert Turkish selections to English API values
        cycle = self.cycle_map[cycle_tr]

        if not name:
            messagebox.showwarning("Uyarı", "Plan adı zorunludur.")
            return
        
        # Parse sessions (0 or empty = unlimited)
        sessions = 0
        if sessions_str:
            try:
                sessions = int(sessions_str)
                if sessions < 0:
                    messagebox.showwarning("Uyarı", "Seans sayısı negatif olamaz.")
                    return
            except ValueError:
                messagebox.showwarning("Uyarı", "Seans sayısı geçerli bir sayı olmalıdır.")
                return

        repeat_weeks_str = self.entry_repeat_weeks.get().strip()
        repeat_weeks = 1
        if repeat_weeks_str:
            try:
                repeat_weeks = int(repeat_weeks_str)
                if repeat_weeks < 1:
                    messagebox.showwarning("Uyarı", "Tekrarlayan hafta en az 1 olabilir.")
                    return
            except ValueError:
                messagebox.showwarning("Uyarı", "Tekrarlayan hafta geçerli bir sayı olmalıdır.")
                return

        # Determine access_type based on sessions
        access_type = "SESSION_BASED" if sessions > 0 else "TIME_BASED"

        data = {
            "name": name,
            "access_type": access_type,
            "sessions_granted": sessions if sessions > 0 else None,
            "cycle_period": cycle,
            "repeat_weeks": repeat_weeks,
            "description": desc,
            "is_active": True,
        }
        try:
            self.api_client.post("/api/v1/services/plans", json=data)
            messagebox.showinfo("Başarılı", "Plan eklendi.")
            self.destroy()
            self.on_success_callback()
        except Exception as e:
            messagebox.showerror("Hata", f"Ekleme başarısız: {e}")
