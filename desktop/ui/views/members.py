import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.api_client import ApiClient
from desktop.ui.views.member_detail import MemberDetailView as MemberDetailTab
from desktop.ui.views.dialogs import AddMemberDialog
from desktop.ui.components.search_bar import SearchBar
from tkinter import messagebox
from datetime import datetime, timezone, timedelta

def get_turkey_time():
    """Get current time in Turkey timezone (UTC+3)"""
    turkey_tz = timezone(timedelta(hours=3))
    return datetime.now(turkey_tz)


class MembersView(ctk.CTkFrame):
    def __init__(self, master, api_client: ApiClient):
        super().__init__(master)
        self.api_client = api_client
        
        self.pack(fill="both", expand=True)
        
        self.current_frame = None
        self.show_list()

    def show_list(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = MemberListView(self, self.api_client, on_detail=self.show_detail)
        self.current_frame.pack(fill="both", expand=True)

    def show_detail(self, member):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = MemberDetailTab(self, self.api_client, member, on_back=self.show_list)
        self.current_frame.pack(fill="both", expand=True)


class MemberListView(ctk.CTkFrame):
    def __init__(self, master, api_client: ApiClient, on_detail):
        super().__init__(master)
        self.api_client = api_client
        self.on_detail = on_detail
        
        # Title
        self.label_title = ctk.CTkLabel(self, text=_("👥 Üye Yönetimi"), font=("Roboto", 28, "bold"))
        self.label_title.pack(pady=20, padx=20, anchor="w")

        # Top Bar: Search and Add
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=20, pady=(0, 20))
        
        # Search section
        search_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        search_frame.pack(side="left", fill="x", expand=True)
        
        self.search_bar = SearchBar(
            search_frame,
            placeholder=_("🔍 Üye Ara (Ad, Email, Tel)..."),
            on_search=self.load_data,
            button_text=_("🔎 Ara"),
            width=400,
            height=40
        )
        self.search_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Checkbox for inactive members only
        self.show_inactive_only = ctk.BooleanVar(value=False)
        self.chk_inactive = ctk.CTkCheckBox(
            search_frame,
            text=_("⛔ Sadece Pasif Üyeler"),
            variable=self.show_inactive_only,
            command=self.load_data,
            font=("Roboto", 12),
            height=40
        )
        self.chk_inactive.pack(side="left", padx=(0, 10))
        
        # Add button
        ctk.CTkButton(self.top_bar, text=_("➕ Yeni Üye"), command=self.show_add_dialog, 
                     height=40, fg_color="#2CC985", hover_color="#229966",
                     font=("Roboto", 14, "bold")).pack(side="right", padx=5)

        # Members List (Scrollable)
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.load_data("")
    
    def load_data(self, search_term: str = ""):
        """Load members data with optional search"""
        # Clear existing
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        params = {}
        if search_term:
            params["search"] = search_term
        
        # Include inactive members if checkbox is checked
        if self.show_inactive_only.get():
            params["include_inactive"] = "true"

        try:
            members_list = self.api_client.get("/api/v1/members/", params=params)
            
            # Filter inactive members only if checkbox is checked
            if self.show_inactive_only.get():
                members_list = [member for member in members_list if not member.get('is_active', True)]
            
            if not members_list:
                suffix = _(" (pasif üyeler)") if self.show_inactive_only.get() else ""
                if not search_term:
                    msg = _("📋 Henüz üye kaydı bulunmuyor{suffix}").format(suffix=suffix)
                else:
                    msg = _("🔍 Arama sonucu bulunamadı{suffix}").format(suffix=suffix)
                no_data = ctk.CTkLabel(self.scroll_frame,
                                      text=msg,
                                      font=("Roboto", 16),
                                      text_color=("gray50", "gray60"))
                no_data.pack(pady=50)
                return
            
            for idx, member in enumerate(members_list):
                self.create_member_card(member, idx)
                
        except Exception as e:
            print(f"Error loading members: {e}")
            error_label = ctk.CTkLabel(self.scroll_frame, 
                                      text=_("❌ Veri yüklenirken hata oluştu"),
                                      font=("Roboto", 16),
                                      text_color="red")
            error_label.pack(pady=50)
    
    def create_member_card(self, member, index):
        """Create a modern member card"""
        card = ctk.CTkFrame(self.scroll_frame, corner_radius=12, 
                           fg_color=("#F5F5F5", "#2B2B2B"), 
                           border_width=2,
                           border_color=("#DDDDDD", "#3A3A3A"),
                           cursor="hand2")
        card.pack(fill="x", pady=8, padx=5)
        
        # Make entire card clickable
        card.bind("<Button-1>", lambda e: self.on_detail(member))
        
        # Left section - Member info
        left_frame = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        left_frame.pack(side="left", fill="both", expand=True, padx=20, pady=15)
        left_frame.bind("<Button-1>", lambda e: self.on_detail(member))
        
        # Name and status
        name_row = ctk.CTkFrame(left_frame, fg_color="transparent", cursor="hand2")
        name_row.pack(anchor="w")
        name_row.bind("<Button-1>", lambda e: self.on_detail(member))
        
        name = f"{member.get('first_name')} {member.get('last_name')}"
        lbl_name = ctk.CTkLabel(name_row, text=f"👤 {name}", 
                               font=("Roboto", 18, "bold"), 
                               anchor="w", cursor="hand2")
        lbl_name.pack(side="left", padx=(0, 15))
        lbl_name.bind("<Button-1>", lambda e: self.on_detail(member))
        
        # Status badge next to name
        is_active = member.get('is_active')
        status_text = _("✅ Aktif") if is_active else _("⛔ Pasif")
        status_color = ("#2CC985", "#229966") if is_active else ("#E74C3C", "#C0392B")
        
        lbl_status = ctk.CTkLabel(name_row, text=status_text,
                                 font=("Roboto", 12, "bold"),
                                 text_color=status_color, cursor="hand2")
        lbl_status.pack(side="left")
        lbl_status.bind("<Button-1>", lambda e: self.on_detail(member))
        
        # Contact info
        info_frame = ctk.CTkFrame(left_frame, fg_color="transparent", cursor="hand2")
        info_frame.pack(anchor="w", pady=(6, 0))
        info_frame.bind("<Button-1>", lambda e: self.on_detail(member))
        
        email = member.get('email')
        lbl_email = ctk.CTkLabel(info_frame, text=f"📧 {email}", 
                                font=("Roboto", 13),
                                text_color=("#555555", "#AAAAAA"),
                                anchor="w", cursor="hand2")
        lbl_email.pack(side="left", padx=(0, 20))
        lbl_email.bind("<Button-1>", lambda e: self.on_detail(member))
        
        phone = member.get('phone_number') or "-"
        lbl_phone = ctk.CTkLabel(info_frame, text=f"📞 {phone}", 
                                font=("Roboto", 13),
                                text_color=("#555555", "#AAAAAA"),
                                anchor="w", cursor="hand2")
        lbl_phone.pack(side="left")
        lbl_phone.bind("<Button-1>", lambda e: self.on_detail(member))
        
        # Right section - Action buttons
        right_frame = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        right_frame.pack(side="right", padx=20, pady=15)
        right_frame.bind("<Button-1>", lambda e: self.on_detail(member))
        
        # Detail button
        btn_detail = ctk.CTkButton(right_frame, text=_("📋 Detay"), 
                                  width=110, height=40,
                                  fg_color="#3B8ED0", 
                                  hover_color="#2E7AB8",
                                  font=("Roboto", 14, "bold"),
                                  command=lambda m=member: self.on_detail(m))
        btn_detail.pack(side="left", padx=(0, 5))
        
        # Activate button if member is inactive
        if not member.get('is_active', True):
            btn_activate = ctk.CTkButton(right_frame, text=_("✅ Aktif Et"), 
                                        width=110, height=40,
                                        fg_color="#2CC985", 
                                        hover_color="#229966",
                                        font=("Roboto", 14, "bold"),
                                        command=lambda m=member: self.activate_member(m))
            btn_activate.pack(side="left", padx=(0, 5))
        
        # Delete button
        btn_delete = ctk.CTkButton(right_frame, text=_("🗑️ Sil"), 
                                  width=80, height=40,
                                  fg_color="red", 
                                  hover_color="darkred",
                                  font=("Roboto", 14, "bold"),
                                  command=lambda m=member: self.delete_member(m))
        btn_delete.pack(side="left")

    def delete_member(self, member):
        """Delete member with confirmation"""
        if messagebox.askyesno(_("Onay"), _("Bu üyeyi silmek istediğinize emin misiniz?")):
            try:
                self.api_client.delete(f"/api/v1/members/{member['id']}")
                messagebox.showinfo(_("Başarılı"), _("Üye silindi."))
                self.load_data(self.search_bar.get_search_term())
            except Exception as e:
                messagebox.showerror(_("Hata"), _("Silme işlemi başarısız: {err}").format(err=str(e)))

    def activate_member(self, member):
        """Activate member and update timestamp"""
        try:
            data = {
                "is_active": True,
                "updated_at": get_turkey_time().isoformat()
            }
            self.api_client.put(f"/api/v1/members/{member['id']}", json=data)
            messagebox.showinfo(_("Başarılı"), _("Üye aktif edildi."))
            self.load_data(self.search_bar.get_search_term())
        except Exception as e:
            messagebox.showerror(_("Hata"), _("Aktif etme işlemi başarısız: {err}").format(err=str(e)))

    def show_add_dialog(self):
        AddMemberDialog(self, self.api_client, self.load_data)
