import customtkinter as ctk
from tkinter import messagebox
from desktop.core.api_client import ApiClient


class AddCategoryDialog(ctk.CTkToplevel):
    """Dialog for adding a new category"""
    
    def __init__(self, parent, api_client: ApiClient, on_success_callback):
        super().__init__(parent)
        self.api_client = api_client
        self.on_success_callback = on_success_callback
        
        self.title("Yeni Kategori Ekle")
        self.geometry("450x350")
        
        self.lift()
        self.focus_force()
        self.grab_set()
        
        # Main Container
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(self.main_frame, text="📁 Yeni Kategori Ekle", 
                    font=("Roboto", 22, "bold")).pack(pady=(20, 30))
        
        # Form Fields
        self.entry_name = self.create_input(self.main_frame, "📝 Kategori Adı")
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

    def create_input(self, parent, label, value=""):
        """Create a labeled input field"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=8)
        
        ctk.CTkLabel(frame, text=label, font=("Roboto", 14), 
                    width=120, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame, height=35, font=("Roboto", 14))
        entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        if value:
            entry.insert(0, value)
        return entry

    def save(self):
        """Save the new category"""
        name = self.entry_name.get()
        desc = self.entry_desc.get()
        
        if not name:
            messagebox.showwarning("Uyarı", "Kategori adı boş olamaz.")
            return

        data = {"name": name, "description": desc}
        try:
            self.api_client.post("/api/v1/services/categories", json=data)
            messagebox.showinfo("Başarılı", "Kategori eklendi.")
            self.destroy()
            self.on_success_callback()
        except Exception as e:
            messagebox.showerror("Hata", f"Ekleme başarısız: {e}")
