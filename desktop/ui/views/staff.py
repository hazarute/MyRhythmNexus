import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.api_client import ApiClient
from desktop.ui.views.dialogs.add_staff_dialog import AddStaffDialog
from desktop.ui.views.dialogs.edit_staff_dialog import EditStaffDialog
from desktop.ui.components.search_bar import SearchBar
from tkinter import messagebox

class StaffView(ctk.CTkFrame):
    def __init__(self, master, api_client: ApiClient):
        super().__init__(master)
        self.api_client = api_client
        
        self.pack(fill="both", expand=True)
        
        self.show_list()

    def show_list(self):
        self.destroy_children()
        list_view = StaffListView(self, self.api_client)
        list_view.pack(fill="both", expand=True)
    
    def destroy_children(self):
        for widget in self.winfo_children():
            widget.destroy()


class StaffListView(ctk.CTkFrame):
    def __init__(self, master, api_client: ApiClient):
        super().__init__(master)
        self.api_client = api_client
        
        # Title
        self.label_title = ctk.CTkLabel(self, text=_("👔 Personel Yönetimi"), font=("Roboto", 28, "bold"))
        self.label_title.pack(pady=20, padx=20, anchor="w")

        # Top Bar: Search and Add
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=20, pady=(0, 20))
        
        # Search section
        search_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        search_frame.pack(side="left", fill="x", expand=True)
        
        self.search_bar = SearchBar(
            search_frame,
            placeholder=_("🔍 Personel Ara (Ad, Email, Tel)..."),
            on_search=self.load_data,
            button_text="🔎 Ara",
            width=400,
            height=40
        )
        self.search_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Add button
        ctk.CTkButton(self.top_bar, text=_("➕ Yeni Personel"), command=self.show_add_dialog, 
                     height=40, fg_color="#2CC985", hover_color="#229966",
                     font=("Roboto", 14, "bold")).pack(side="right", padx=5)

        # Staff List (Scrollable)
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.load_data("")
    
    def load_data(self, search_term: str = ""):
        """Load staff data with optional search"""
        # Clear existing
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        params = {}
        if search_term:
            params["search"] = search_term

        try:
            staff_list = self.api_client.get("/api/v1/staff/", params=params)
            
            if not staff_list:
                if not search_term:
                    msg = _("📋 Henüz personel kaydı bulunmuyor")
                else:
                    msg = _("🔍 Arama sonucu bulunamadı")
                no_data = ctk.CTkLabel(self.scroll_frame,
                                      text=msg,
                                      font=("Roboto", 16),
                                      text_color=("gray50", "gray60"))
                no_data.pack(pady=50)
                return
            
            for idx, staff in enumerate(staff_list):
                self.create_staff_card(staff, idx)
                
        except Exception as e:
            print(f"Error loading staff: {e}")
            error_label = ctk.CTkLabel(self.scroll_frame, 
                                      text=_("❌ Veri yüklenirken hata oluştu"),
                                      font=("Roboto", 16),
                                      text_color="red")
            error_label.pack(pady=50)
    
    def create_staff_card(self, staff, index):
        """Create a modern staff card"""
        card = ctk.CTkFrame(self.scroll_frame, corner_radius=12, 
                           fg_color=("#F5F5F5", "#2B2B2B"), 
                           border_width=2,
                           border_color=("#DDDDDD", "#3A3A3A"))
        card.pack(fill="x", pady=8, padx=5)
        
        # Left section - Staff info
        left_frame = ctk.CTkFrame(card, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=20, pady=15)
        
        # Name and status
        name_row = ctk.CTkFrame(left_frame, fg_color="transparent")
        name_row.pack(anchor="w")
        
        name = f"{staff.get('first_name')} {staff.get('last_name')}"
        # Roles for display in name
        roles = staff.get('roles', [])
        role_names = []
        for r in roles:
            if isinstance(r, dict):
                role_name = r.get('role_name', '')
                if role_name == 'ADMIN':
                    role_names.append(_('Yönetici'))
                elif role_name == 'INSTRUCTOR':
                    role_names.append(_('Antrenör'))
                else:
                    role_names.append(role_name)
            else:
                role_names.append(str(r))
        role_str = f" ({', '.join(role_names)})" if role_names else ""
        lbl_name = ctk.CTkLabel(name_row, text=f"👔 {name}{role_str}", 
                               font=("Roboto", 18, "bold"), 
                               anchor="w")
        lbl_name.pack(side="left", padx=(0, 15))
        
        # Status badge next to name
        is_active = staff.get('is_active')
        status_text = _("✅ Aktif") if is_active else _("⛔ Pasif")
        status_color = ("#2CC985", "#229966") if is_active else ("#E74C3C", "#C0392B")
        
        lbl_status = ctk.CTkLabel(name_row, text=status_text,
                                 font=("Roboto", 12, "bold"),
                                 text_color=status_color)
        lbl_status.pack(side="left")
        
        # Contact info
        info_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        info_frame.pack(anchor="w", pady=(6, 0))
        
        email = staff.get('email')
        lbl_email = ctk.CTkLabel(info_frame, text=f"📧 {email}", 
                                font=("Roboto", 13),
                                text_color=("#555555", "#AAAAAA"),
                                anchor="w")
        lbl_email.pack(side="left", padx=(0, 20))
        
        phone = staff.get('phone_number') or "-"
        lbl_phone = ctk.CTkLabel(info_frame, text=f"📞 {phone}", 
                                font=("Roboto", 13),
                                text_color=("#555555", "#AAAAAA"),
                                anchor="w")
        lbl_phone.pack(side="left", padx=(0, 20))
        
        # Right section - Action buttons
        right_frame = ctk.CTkFrame(card, fg_color="transparent")
        right_frame.pack(side="right", padx=20, pady=15)
        
        # Edit button
        btn_edit = ctk.CTkButton(right_frame, text=_("✏️ Düzenle"), 
                                width=110, height=40,
                                fg_color="#F39C12", 
                                hover_color="#D68910",
                                font=("Roboto", 14, "bold"),
                                command=lambda: self.show_edit_dialog(staff))
        btn_edit.pack(side="left", padx=5)
        
        # Delete button
        btn_delete = ctk.CTkButton(right_frame, text=_("🗑️ Sil"), 
                                  width=100, height=40,
                                  fg_color="#E74C3C", 
                                  hover_color="#C0392B",
                                  font=("Roboto", 14, "bold"),
                                  command=lambda: self.delete_staff(staff))
        btn_delete.pack(side="left", padx=5)

    def show_add_dialog(self):
        AddStaffDialog(self, self.api_client, self.load_data)
    
    def show_edit_dialog(self, staff):
        """Open edit dialog for a staff member"""
        staff_id = staff.get('id')
        if not staff_id:
            messagebox.showerror(_("Hata"), _("Personel ID bulunamadı"))
            return
        EditStaffDialog(self, self.api_client, staff_id, staff, self.load_data)
    
    def delete_staff(self, staff):
        """Delete a staff member with confirmation"""
        staff_id = staff.get('id')
        name = f"{staff.get('first_name')} {staff.get('last_name')}"
        
        if not staff_id:
            messagebox.showerror(_("Hata"), _("Personel ID bulunamadı"))
            return
        
        # Confirmation dialog
        confirm = messagebox.askyesno(
            _("Silme Onayı"),
            _("'{name}' personelini silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz!").format(name=name)
        )
        
        if not confirm:
            return
        
        try:
            self.api_client.delete(f"/api/v1/staff/{staff_id}")
            messagebox.showinfo(_("Başarılı"), _("'{name}' personeli silindi.").format(name=name))
            self.load_data()  # Refresh the list
        except Exception as e:
            print(f"Error deleting staff: {e}")
            messagebox.showerror(_("Hata"), _("Personel silinirken hata oluştu: {err}").format(err=str(e)))
