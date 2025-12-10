import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.api_client import ApiClient
from tkinter import messagebox
from desktop.core.ui_utils import safe_grab


class AddMeasurementDialog(ctk.CTkToplevel):
    """Dialog for adding body measurements with categorized form"""
    
    def __init__(self, parent, api_client: ApiClient, member_data: dict, on_success):
        super().__init__(parent)
        self.api_client = api_client
        self.member_data = member_data
        self.on_success = on_success
        
        self.title(_("Yeni Vücut Ölçümü"))
        self.geometry("700x750")
        
        self.lift()
        self.focus_force()
        safe_grab(self)
        
        # Measurement Types and Entries
        self.measurement_entries = {}
        
        # Fetch Measurement Types
        try:
            self.measurement_types = self.api_client.get("/api/v1/measurements/types")
        except Exception as e:
            messagebox.showerror(_("Hata"), _("Ölçüm tipleri yüklenemedi: {err}").format(err=str(e)))
            self.destroy()
            return
        
        # Main Container with Scrollbar
        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text=_("📏 Yeni Vücut Ölçümü"), 
                    font=("Roboto", 22, "bold")).pack()
        
        member_name = f"{member_data.get('first_name')} {member_data.get('last_name')}"
        ctk.CTkLabel(header_frame, text=member_name, font=("Roboto", 14), 
                    text_color="gray").pack(pady=(5, 0))
        
        # Scrollable Form
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent", height=500)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Group measurements by category
        categories = [
            (_("🏋️ Genel Vücut Ölçüleri"), ["height", "weight"]),
            (_("💪 Üst Vücut"), ["neck", "shoulder", "chest", "arm_bicep", "forearm"]),
            (_("🫀 Gövde"), ["waist", "love_handle", "hip", "hip_seat"]),
            (_("🦵 Alt Vücut"), ["thigh", "calf"])
        ]
        
        for category_name, type_keys in categories:
            # Category Header
            ctk.CTkLabel(scroll_frame, text=category_name, 
                        font=("Roboto", 16, "bold"), 
                        text_color="#3B8ED0").pack(anchor="w", pady=(15, 10), padx=10)
            
            # Find and display measurements in this category
            for mt in self.measurement_types:
                if mt['type_key'] in type_keys:
                    self.create_measurement_input(scroll_frame, mt)
        
        # Notes Section
        ctk.CTkLabel(scroll_frame, text=_("📝 Notlar"), 
                    font=("Roboto", 16, "bold"), 
                    text_color="#3B8ED0").pack(anchor="w", pady=(15, 10), padx=10)
        
        self.text_notes = ctk.CTkTextbox(scroll_frame, height=80, font=("Roboto", 12))
        self.text_notes.pack(fill="x", padx=10, pady=5)
        
        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=15, padx=20)
        
        ctk.CTkButton(btn_frame, text=_("❌ İptal"), fg_color="#555555", 
                     hover_color="#333333", width=100, 
                     command=self.destroy).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(btn_frame, text=_("💾 Kaydet"), fg_color="#2CC985", 
                     hover_color="#229966", width=100, 
                     command=self.save).pack(side="left", padx=10, expand=True)
    
    def create_measurement_input(self, parent, measurement_type: dict):
        """Create a measurement input row with label, entry, and unit"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=5)
        
        # Label
        label_text = f"{measurement_type['type_name']}"
        ctk.CTkLabel(row, text=label_text, font=("Roboto", 13), 
                    width=150, anchor="w").pack(side="left", padx=5)
        
        # Entry
        entry = ctk.CTkEntry(row, height=32, font=("Roboto", 13), 
                            width=120, placeholder_text=_("0.0"))
        entry.pack(side="left", padx=5)
        
        # Unit Label
        ctk.CTkLabel(row, text=measurement_type['unit'], font=("Roboto", 12), 
                    text_color="gray", width=30).pack(side="left")
        
        # Store reference
        self.measurement_entries[measurement_type['id']] = entry
    
    def save(self):
        """Validate and save measurements"""
        # Collect values
        values = []
        for type_id, entry in self.measurement_entries.items():
            value_str = entry.get().strip()
            if value_str:  # Only include non-empty values
                try:
                    value = float(value_str)
                    if value <= 0:
                        messagebox.showwarning(_("Geçersiz Değer"), 
                            _("Ölçüm değerleri pozitif olmalıdır."))
                        return
                    values.append({"type_id": type_id, "value": value})
                except ValueError:
                    messagebox.showwarning(_("Geçersiz Değer"), 
                        _("Lütfen sayısal değer giriniz."))
                    return
        
        if not values:
            messagebox.showwarning(_("Uyarı"), _("En az bir ölçüm değeri giriniz."))
            return
        
        notes = self.text_notes.get("1.0", "end").strip()
        
        data = {
            "member_user_id": self.member_data['id'],
            "values": values,
            "notes": notes if notes else None
        }
        
        try:
            self.api_client.post("/api/v1/measurements/sessions", json=data)
            messagebox.showinfo(_("Başarılı"), _("Ölçümler kaydedildi."))
            self.on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror(_("Hata"), _("Kayıt hatası: {err}").format(err=str(e)))
