import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.ui_utils import safe_grab
from desktop.core.api_client import ApiClient
from tkinter import messagebox

class MeasurementsTab:
    def __init__(self, parent_frame, api_client: ApiClient, member: dict, on_add_measurement):
        self.parent = parent_frame
        self.api_client = api_client
        self.member = member
        self.on_add_measurement = on_add_measurement
        
    def setup(self):
        """Setup measurements tab content"""
        # Top bar with Add Button
        top_bar = ctk.CTkFrame(self.parent, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(top_bar, text=_("📏 Vücut Ölçümleri"), font=("Roboto", 16, "bold")).pack(side="left")
        
        ctk.CTkButton(top_bar, text=_("➕ Yeni Ölçüm Ekle"), 
                     fg_color="#2CC985", hover_color="#229966",
                     command=self.on_add_measurement).pack(side="right", padx=5)
        
        # Scrollable Frame
        frame = ctk.CTkScrollableFrame(self.parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        try:
            sessions = self.api_client.get(f"/api/v1/measurements/sessions?member_id={self.member['id']}")
            if not sessions:
                ctk.CTkLabel(frame, text=_("Ölçüm kaydı bulunamadı."), text_color="gray").pack(pady=20)
                return

            # Comparison card if 2+ sessions
            if len(sessions) >= 2:
                self.create_comparison_card(frame, sessions[0], sessions[1])
                ctk.CTkLabel(frame, text="━" * 100, text_color="gray30", font=("Roboto", 8)).pack(pady=15)
            
            # All measurements list
            ctk.CTkLabel(frame, text=_("📋 Tüm Ölçüm Kayıtları"), 
                        font=("Roboto", 14, "bold"), 
                        text_color="gray60").pack(anchor="w", padx=10, pady=(0, 10))
            
            for sess in sessions:
                self.create_measurement_card(frame, sess)
                
        except Exception as e:
            ctk.CTkLabel(frame, text=_("Hata: {}").format(e)).pack()
    
    def create_comparison_card(self, parent, latest_session, previous_session):
        """Comparison card for last two measurements"""
        bg_color = "#2A2A2A"
        accent_color = "#FFD700"
        
        card = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=12)
        card.pack(fill="x", pady=10, padx=5)
        
        stripe = ctk.CTkFrame(card, fg_color=accent_color, width=6, corner_radius=0)
        stripe.pack(side="left", fill="y")
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        
        # Header
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(header_frame, text=_("📊 Son Ölçüm Karşılaştırması"), 
                    font=("Roboto", 18, "bold"), 
                    text_color=accent_color).pack(side="left")
        
        latest_date = latest_session.get('session_date', '')[:10]
        previous_date = previous_session.get('session_date', '')[:10]
        ctk.CTkLabel(header_frame, text=_("  •  {} ➔ {}").format(previous_date, latest_date), 
                    font=("Roboto", 14), 
                    text_color="gray70").pack(side="left", padx=10)
        
        # Comparison grid
        grid_frame = ctk.CTkFrame(content, fg_color="transparent")
        grid_frame.pack(fill="x")
        
        latest_measurements = {m['measurement_type']['type_name']: m for m in latest_session.get('measurement_values', [])}
        previous_measurements = {m['measurement_type']['type_name']: m for m in previous_session.get('measurement_values', [])}
        
        categories = {
            _("🏋️ Genel"): ["Boy", "Kilo"],
            _("💪 Üst Vücut"): ["Boyun", "Omuz", "Göğüs", "Kol (Pazu)", "Ön Kol"],
            _("🫀 Gövde"): ["Bel", "Simit", "Kalça", "Basen"],
            _("🦵 Alt Vücut"): ["Bacak (Üst)", "Kalf (Baldır)"]
        }
        
        for category, type_names in categories.items():
            comparable = []
            for name in type_names:
                if name in latest_measurements and name in previous_measurements:
                    comparable.append(name)
            
            if comparable:
                ctk.CTkLabel(grid_frame, text=category, 
                            font=("Roboto", 14, "bold"), 
                            text_color="#3B8ED0").pack(anchor="w", pady=(10, 5))
                
                cat_grid = ctk.CTkFrame(grid_frame, fg_color="transparent")
                cat_grid.pack(fill="x", pady=(0, 5))
                
                for idx, name in enumerate(comparable):
                    col = idx % 3
                    row = idx // 3
                    
                    latest_val = float(latest_measurements[name]['value'])
                    previous_val = float(previous_measurements[name]['value'])
                    diff = latest_val - previous_val
                    unit = latest_measurements[name]['measurement_type']['unit']
                    
                    # Determine arrow and color
                    if name == "Boy":
                        if diff > 0:
                            arrow, change_color = "↗", "#3B8ED0"
                        elif diff < 0:
                            arrow, change_color = "↘", "#3B8ED0"
                        else:
                            arrow, change_color = "━", "gray"
                    else:
                        if diff > 0:
                            arrow, change_color = "↗", "#E04F5F"
                        elif diff < 0:
                            arrow, change_color = "↘", "#2CC985"
                        else:
                            arrow, change_color = "━", "gray"
                    
                    m_frame = ctk.CTkFrame(cat_grid, fg_color="#1E1E1E", corner_radius=8)
                    m_frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
                    cat_grid.grid_columnconfigure(col, weight=1)
                    
                    inner = ctk.CTkFrame(m_frame, fg_color="transparent")
                    inner.pack(fill="both", expand=True, padx=10, pady=8)
                    
                    ctk.CTkLabel(inner, text=name, 
                                font=("Roboto", 12, "bold"), 
                                text_color="white").pack(anchor="w")
                    
                    values_frame = ctk.CTkFrame(inner, fg_color="transparent")
                    values_frame.pack(fill="x", pady=(3, 0))
                    
                    ctk.CTkLabel(values_frame, text=_("{} {}").format(previous_val, unit), 
                                font=("Roboto", 11), 
                                text_color="gray60").pack(side="left")
                    
                    ctk.CTkLabel(values_frame, text=_("  {}  ").format(arrow), 
                                font=("Roboto", 14, "bold"), 
                                text_color=change_color).pack(side="left")
                    
                    ctk.CTkLabel(values_frame, text=_("{} {}").format(latest_val, unit), 
                                font=("Roboto", 14, "bold"), 
                                text_color="white").pack(side="left")
                    
                    diff_text = f"{diff:+.1f}" if diff != 0 else "0"
                    ctk.CTkLabel(inner, text=diff_text, 
                                font=("Roboto", 13, "bold"), 
                                text_color=change_color).pack(anchor="w", pady=(2, 0))
    
    def create_measurement_card(self, parent, session):
        """Compact clickable measurement card"""
        bg_color = "#333333"
        accent_color = "#3B8ED0"
        
        card = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=8)
        card.pack(fill="x", pady=4, padx=5)
        
        card.bind("<Button-1>", lambda e, s=session: self.show_detail_dialog(s))
        card.bind("<Enter>", lambda e: card.configure(fg_color="#3A3A3A"))
        card.bind("<Leave>", lambda e: card.configure(fg_color=bg_color))
        
        stripe = ctk.CTkFrame(card, fg_color=accent_color, width=4, corner_radius=0)
        stripe.pack(side="left", fill="y")
        stripe.bind("<Button-1>", lambda e, s=session: self.show_detail_dialog(s))
        
        content = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        content.pack(side="left", fill="both", expand=True, padx=12, pady=8)
        content.bind("<Button-1>", lambda e, s=session: self.show_detail_dialog(s))
        
        date = session.get('session_date', '')[:10]
        date_label = ctk.CTkLabel(content, text=_("📅 {}").format(date), 
                    font=("Roboto", 14, "bold"), 
                    text_color="white", cursor="hand2")
        date_label.pack(side="left")
        date_label.bind("<Button-1>", lambda e, s=session: self.show_detail_dialog(s))
        
        measurement_count = len(session.get('measurement_values', []))
        count_label = ctk.CTkLabel(content, text=_("  •  {} ölçüm").format(measurement_count), 
                    font=("Roboto", 12), 
                    text_color="gray70", cursor="hand2")
        count_label.pack(side="left", padx=8)
        count_label.bind("<Button-1>", lambda e, s=session: self.show_detail_dialog(s))
        
        notes = session.get('notes')
        if notes:
            notes_preview = notes[:40] + "..." if len(notes) > 40 else notes
            notes_label = ctk.CTkLabel(content, text=_("  •  {}").format(notes_preview), 
                        font=("Roboto", 11), 
                        text_color="gray60", cursor="hand2")
            notes_label.pack(side="left")
            notes_label.bind("<Button-1>", lambda e, s=session: self.show_detail_dialog(s))
        
        view_label = ctk.CTkLabel(content, text="👁️", 
                    font=("Segoe UI Emoji", 12),
                    text_color="gray60", cursor="hand2")
        view_label.pack(side="right", padx=5)
        view_label.bind("<Button-1>", lambda e, s=session: self.show_detail_dialog(s))
        
        btn_del = ctk.CTkButton(card, text=_("🗑️"), width=35, height=35, 
                              fg_color="#E74C3C", hover_color="#C0392B",
                              font=("Segoe UI Emoji", 14),
                              command=lambda s=session: self.delete_measurement(s['id']))
        btn_del.pack(side="right", padx=10)
    
    def show_detail_dialog(self, session):
        """Show detailed measurement dialog"""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(_("Vücut Ölçümü Detayları"))
        dialog.geometry("800x700")
        
        dialog.lift()
        dialog.focus_force()
        safe_grab(dialog)
        
        main_frame = ctk.CTkFrame(dialog, corner_radius=15, fg_color="#2B2B2B")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="#3B8ED0", corner_radius=10)
        header_frame.pack(fill="x", padx=15, pady=15)
        
        date = session.get('session_date', '')[:10]
        ctk.CTkLabel(header_frame, text=_("📅  {}").format(date), 
                    font=("Roboto", 22, "bold"), 
                    text_color="white").pack(pady=15)
        
        # Notes
        notes = session.get('notes')
        if notes:
            notes_frame = ctk.CTkFrame(main_frame, fg_color="#333333", corner_radius=8)
            notes_frame.pack(fill="x", padx=15, pady=(0, 15))
            
            ctk.CTkLabel(notes_frame, text=_("📝 Notlar:"), 
                        font=("Roboto", 12, "bold"), 
                        text_color="gray70").pack(anchor="w", padx=12, pady=(8, 2))
            
            ctk.CTkLabel(notes_frame, text=notes, 
                        font=("Roboto", 13), 
                        text_color="white",
                        wraplength=700,
                        justify="left").pack(anchor="w", padx=12, pady=(0, 8))
        
        # Scrollable measurements
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        measurements = session.get('measurement_values', [])
        
        categories = {
            _("🏋️ Genel"): ["Boy", "Kilo"],
            _("💪 Üst Vücut"): ["Boyun", "Omuz", "Göğüs", "Kol (Pazu)", "Ön Kol"],
            _("🫀 Gövde"): ["Bel", "Simit", "Kalça", "Basen"],
            _("🦵 Alt Vücut"): ["Bacak (Üst)", "Kalf (Baldır)"]
        }
        
        for category, type_names in categories.items():
            cat_measurements = [m for m in measurements if m['measurement_type']['type_name'] in type_names]
            
            if cat_measurements:
                cat_header = ctk.CTkFrame(scroll_frame, fg_color="#3B8ED0", corner_radius=6)
                cat_header.pack(fill="x", pady=(15, 8), padx=5)
                
                ctk.CTkLabel(cat_header, text=category, 
                            font=("Roboto", 16, "bold"), 
                            text_color="white").pack(anchor="w", padx=12, pady=8)
                
                grid_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                grid_frame.pack(fill="x", pady=(0, 10))
                
                for idx, m in enumerate(cat_measurements):
                    col = idx % 2
                    row = idx // 2
                    
                    m_frame = ctk.CTkFrame(grid_frame, fg_color="#333333", corner_radius=8)
                    m_frame.grid(row=row, column=col, padx=8, pady=6, sticky="ew")
                    
                    grid_frame.grid_columnconfigure(col, weight=1)
                    
                    name = m['measurement_type']['type_name']
                    value = m['value']
                    unit = m['measurement_type']['unit']
                    
                    info_frame = ctk.CTkFrame(m_frame, fg_color="transparent")
                    info_frame.pack(fill="x", padx=15, pady=12)
                    
                    ctk.CTkLabel(info_frame, text=name, 
                                font=("Roboto", 13), 
                                text_color="gray70").pack(anchor="w")
                    
                    ctk.CTkLabel(info_frame, text=f"{value} {unit}", 
                                font=("Roboto", 20, "bold"), 
                                text_color="white").pack(anchor="w", pady=(2, 0))
        
        # Close button
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkButton(btn_frame, text=_("✓ Kapat"), 
                     font=("Roboto", 14, "bold"),
                     fg_color="#3B8ED0", 
                     hover_color="#2E7AB8",
                     height=40,
                     command=dialog.destroy).pack(fill="x")
    
    def delete_measurement(self, session_id):
        if messagebox.askyesno(_("Onay"), _("Bu ölçüm kaydını silmek istediğinize emin misiniz?")):
            try:
                self.api_client.delete(f"/api/v1/measurements/sessions/{session_id}")
                messagebox.showinfo(_("Başarılı"), _("Ölçüm kaydı silindi."))
                self.refresh()
            except Exception as e:
                messagebox.showerror(_("Hata"), _("Silme işlemi başarısız: {}").format(e))
    
    def refresh(self):
        """Refresh the tab"""
        for widget in self.parent.winfo_children():
            widget.destroy()
        self.setup()
