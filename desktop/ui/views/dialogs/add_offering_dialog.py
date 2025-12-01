import customtkinter as ctk
from tkinter import messagebox
from desktop.core.api_client import ApiClient


class AddOfferingDialog(ctk.CTkToplevel):
    """Dialog for adding a new offering (service)"""
    
    def __init__(self, parent, api_client: ApiClient, on_success_callback):
        super().__init__(parent)
        self.api_client = api_client
        self.on_success_callback = on_success_callback
        
        self.title("Yeni Hizmet Ekle")
        self.geometry("450x400")
        
        self.lift()
        self.focus_force()
        self.grab_set()
        
        # Main Container
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(self.main_frame, text="🏋️ Yeni Hizmet Ekle", 
                    font=("Roboto", 22, "bold")).pack(pady=(20, 30))
        
        # Form Fields
        self.entry_name = self.create_input(self.main_frame, "📝 Hizmet Adı", placeholder="Örn: Reformer")
        self.entry_dur = self.create_input(self.main_frame, "⏱️ Varsayılan Süre (dk)", value="60")
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

    def save(self):
        """Save the new offering"""
        name = self.entry_name.get()
        dur_str = self.entry_dur.get()
        desc = self.entry_desc.get()

        if not name or not dur_str:
            messagebox.showwarning("Uyarı", "Ad ve süre zorunludur.")
            return
        
        try:
            duration = int(dur_str)
        except ValueError:
            messagebox.showwarning("Uyarı", "Süre sayı olmalıdır.")
            return

        data = {"name": name, "default_duration_minutes": duration, "description": desc}
        try:
            self.api_client.post("/api/v1/services/offerings", json=data)
            messagebox.showinfo("Başarılı", "Hizmet eklendi.")
            self.destroy()
            self.on_success_callback()
        except Exception as e:
            messagebox.showerror("Hata", f"Ekleme başarısız: {e}")
