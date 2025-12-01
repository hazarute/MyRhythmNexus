import customtkinter as ctk
from desktop.core.api_client import ApiClient
from tkinter import messagebox

from desktop.ui.views.tabs.profile_tab import ProfileTab
from desktop.ui.views.tabs.packages_tab import PackagesTab
from desktop.ui.views.tabs.payments_tab import PaymentsTab
from desktop.ui.views.tabs.attendance_tab import AttendanceTab
from desktop.ui.views.tabs.measurements_tab import MeasurementsTab


class MemberDetailTab(ctk.CTkFrame):
    """
    Member detail tab - Coordinator for member-related sub-tabs
    Manages header, navigation and delegates tab content to specialized modules
    """
    def __init__(self, master, api_client: ApiClient, member: dict, on_back):
        super().__init__(master)
        self.api_client = api_client
        self.member = member
        self.on_back = on_back
        
        # === HEADER SECTION ===
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=20)
        
        self.btn_back = ctk.CTkButton(self.header, text="< Geri", width=60, 
                                       command=self.on_back, fg_color="gray")
        self.btn_back.pack(side="left", padx=(0, 20))
        
        info_col = ctk.CTkFrame(self.header, fg_color="transparent")
        info_col.pack(side="left")

        name = f"{member.get('first_name')} {member.get('last_name')}"
        self.label_title = ctk.CTkLabel(info_col, text=name, font=("Roboto", 30, "bold"))
        self.label_title.pack(anchor="w")
        
        contact = f"📧 {member.get('email')}   📞 {member.get('phone_number') or '-'}"
        self.label_contact = ctk.CTkLabel(info_col, text=contact, 
                                          font=("Roboto", 18), text_color="gray")
        self.label_contact.pack(anchor="w")
        
        # Action buttons in header
        btn_bar = ctk.CTkFrame(self.header, fg_color="transparent")
        btn_bar.pack(side="right", padx=20)
        
        ctk.CTkButton(btn_bar, text="✏️ Bilgileri Güncelle", 
                     command=self.show_update_dialog).pack(side="left", padx=2)
        ctk.CTkButton(btn_bar, text="🔑 Şifre Değiştir", 
                     command=self.show_password_dialog).pack(side="left", padx=2)
        ctk.CTkButton(btn_bar, text="💰 Borç Öde", fg_color="#2CC985", hover_color="#229966",
                     command=self.show_debt_payment_dialog).pack(side="left", padx=2)
        ctk.CTkButton(btn_bar, text="🗑️ Sil", fg_color="red", hover_color="darkred", 
                     command=self.delete_member).pack(side="left", padx=2)
        
        # === TAB VIEW ===
        self.tabview = ctk.CTkTabview(self, height=50, 
                                      segmented_button_fg_color="#2B2B2B",
                                      segmented_button_selected_color="#3B8ED0",
                                      segmented_button_selected_hover_color="#2E7AB8",
                                      segmented_button_unselected_color="#404040",
                                      segmented_button_unselected_hover_color="#4A4A4A",
                                      command=self.on_tab_change)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        self.tabview._segmented_button.configure(font=("Roboto", 16, "bold"), border_width=0)
        
        self.tab_profile = self.tabview.add("👤  Profil")
        self.tab_packages = self.tabview.add("📦  Paketler")
        self.tab_payments = self.tabview.add("💳  Ödemeler")
        self.tab_attendance = self.tabview.add("✅  Katılım")
        self.tab_measurements = self.tabview.add("📏  Vücut Ölçümleri")
        
        # Initialize tab controllers
        self.profile_tab = ProfileTab(self.tab_profile, self.api_client, self.member, 
                                     self.show_update_dialog)
        self.packages_tab = PackagesTab(self.tab_packages, self.api_client, self.member, 
                                       self.refresh_packages_and_profile)
        self.payments_tab = PaymentsTab(self.tab_payments, self.api_client, self.member)
        self.attendance_tab = AttendanceTab(self.tab_attendance, self.api_client, self.member)
        self.measurements_tab = MeasurementsTab(self.tab_measurements, self.api_client, 
                                               self.member, self.show_add_measurement_dialog)
        
        # Setup all tabs
        self.profile_tab.setup()
        self.packages_tab.setup()
        self.payments_tab.setup()
        self.attendance_tab.setup()
        self.measurements_tab.setup()
        
        # Bind click events to tab buttons for refresh on every click
        self.bind_tab_click_events()

    def bind_tab_click_events(self):
        """Bind mouse click events to tab buttons for refresh on every click"""
        tab_names = ["👤  Profil", "📦  Paketler", "💳  Ödemeler", "✅  Katılım", "📏  Vücut Ölçümleri"]
        buttons = self.tabview._segmented_button.winfo_children()
        
        for i, button in enumerate(buttons):
            if i < len(tab_names):
                tab_name = tab_names[i]
                button.bind("<Button-1>", lambda e, name=tab_name: self.on_tab_button_click(name))

    def on_tab_button_click(self, tab_name):
        """Called when any tab button is clicked - refresh the tab"""
        self.refresh_tab_by_name(tab_name)

    def on_tab_change(self):
        """Called when tab changes - refresh the current tab"""
        current_tab = self.tabview.get()
        self.refresh_tab_by_name(current_tab)

    def refresh_tab_by_name(self, tab_name):
        """Refresh tab by name"""
        if tab_name == "👤  Profil":
            self.profile_tab.refresh()
        elif tab_name == "📦  Paketler":
            self.packages_tab.refresh()
        elif tab_name == "💳  Ödemeler":
            self.payments_tab.refresh()
        elif tab_name == "✅  Katılım":
            self.attendance_tab.refresh()
        elif tab_name == "📏  Vücut Ölçümleri":
            self.measurements_tab.refresh()

    # === DIALOG HANDLERS ===
    def show_update_dialog(self):
        """Open member info update dialog"""
        from desktop.ui.views.dialogs import UpdateMemberDialog
        UpdateMemberDialog(self, self.api_client, self.member, self.refresh_member_data)

    def show_password_dialog(self):
        """Open password change dialog"""
        from desktop.ui.views.dialogs import UpdatePasswordDialog
        UpdatePasswordDialog(self, self.api_client, self.member)
    
    def show_add_measurement_dialog(self):
        """Open add measurement dialog"""
        from desktop.ui.views.dialogs import AddMeasurementDialog
        AddMeasurementDialog(self, self.api_client, self.member, self.measurements_tab.refresh)
    
    def show_debt_payment_dialog(self):
        """Open debt payment dialog"""
        from desktop.ui.views.dialogs import DebtPaymentDialog
        DebtPaymentDialog(self, self.api_client, self.member, self.refresh_after_payment)
    
    # === REFRESH HANDLERS ===
    def refresh_payments_tab(self):
        """Refresh payments tab (called from packages tab after subscription deletion)"""
        self.payments_tab.refresh()
    
    def refresh_packages_and_profile(self):
        """Refresh both packages and profile tabs (called from packages tab after subscription deletion)"""
        self.profile_tab.refresh()
        self.packages_tab.refresh()
        self.payments_tab.refresh()
    
    def refresh_after_payment(self):
        """Refresh all tabs after debt payment"""
        self.profile_tab.refresh()
        self.packages_tab.refresh()
        self.payments_tab.refresh()
    
    def refresh_member_data(self):
        """Refresh member data and update UI after edit"""
        try:
            updated_member = self.api_client.get(f"/api/v1/members/{self.member['id']}")
            self.member = updated_member
            
            # Update header
            name = f"{self.member.get('first_name')} {self.member.get('last_name')}"
            self.label_title.configure(text=name)
            
            contact = f"📧 {self.member.get('email')}   📞 {self.member.get('phone_number') or '-'}"
            self.label_contact.configure(text=contact)
            
            # Update member reference in all tabs
            self.profile_tab.member = updated_member
            self.packages_tab.member = updated_member
            self.payments_tab.member = updated_member
            self.attendance_tab.member = updated_member
            self.measurements_tab.member = updated_member
            
            # Refresh profile tab to show new data
            self.profile_tab.refresh()
        except Exception as e:
            print(f"Error refreshing data: {e}")
    
    # === DELETE HANDLER ===
    def delete_member(self):
        """Delete member with confirmation"""
        if messagebox.askyesno("Onay", "Bu üyeyi silmek istediğinize emin misiniz?"):
            try:
                self.api_client.delete(f"/api/v1/members/{self.member['id']}")
                messagebox.showinfo("Başarılı", "Üye silindi.")
                self.on_back()
            except Exception as e:
                messagebox.showerror("Hata", f"Silme işlemi başarısız: {e}")
