import customtkinter as ctk
from tkinter import messagebox
from desktop.core.api_client import ApiClient
from desktop.ui.views.dialogs import AddPlanDialog


class PlansTab(ctk.CTkFrame):
    """Plans management tab"""
    
    def __init__(self, parent, api_client: ApiClient):
        super().__init__(parent, fg_color="transparent")
        self.api_client = api_client
        
        # Toolbar
        frame_toolbar = ctk.CTkFrame(self, fg_color="transparent")
        frame_toolbar.pack(fill="x", pady=(10, 20), padx=10)

        ctk.CTkButton(frame_toolbar, text="🔄 Yenile", width=100, height=32,
                     fg_color="#3B8ED0", hover_color="#2E7AB8",
                     command=self.load_plans).pack(side="left", padx=5)

        ctk.CTkButton(frame_toolbar, text="➕ Yeni Plan", height=32,
                     fg_color="#2CC985", hover_color="#229966",
                     command=self.open_add_plan_dialog).pack(side="right", padx=5)

        # Scrollable Frame for List
        self.frame_plans_list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frame_plans_list.pack(fill="both", expand=True, padx=10)

        self.load_plans()

    def load_plans(self):
        """Load and display plans"""
        for widget in self.frame_plans_list.winfo_children():
            widget.destroy()

        try:
            plans = self.api_client.get("/api/v1/services/plans")
            for plan in plans:
                self.create_plan_row(plan)
        except Exception as e:
            messagebox.showerror("Hata", f"Planlar yüklenemedi: {e}")

    def create_plan_row(self, plan):
        """Create a plan card widget"""
        card = ctk.CTkFrame(self.frame_plans_list, corner_radius=10, 
                           fg_color=("#F0F0F0", "#2B2B2B"), border_width=1,
                           border_color=("#CCCCCC", "#404040"))
        card.pack(fill="x", pady=8, padx=5)

        # Left content
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, padx=15, pady=12)

        # Display based on access type
        access_type = plan.get('access_type', 'SESSION_BASED')
        cycle_map = {
            "MONTHLY": "Aylık (28 gün)",
            "QUARTERLY": "3 Aylık (84 gün)",
            "SEMI_ANNUAL": "6 Aylık (168 gün)",
            "YEARLY": "Yıllık (365 gün)",
            "WEEKLY": "Haftalık (7 gün)",
            "FIXED": "Özel Tarih"
        }
        cycle_display = cycle_map.get(plan['cycle_period'], plan['cycle_period'])
        
        sessions = plan.get('sessions_granted', 0) or 0
        repeat_weeks = plan.get('repeat_weeks', 1) or 1
        
        if sessions > 0:
            # Seans sınırlı (hem süre hem seans kontrolü)
            sessions_badge = f"🎯 {sessions} Seans"
        else:
            # Sınırsız seans (sadece süre kontrolü)
            sessions_badge = "♾️ Sınırsız"
        
        lbl_name = ctk.CTkLabel(content_frame, text=f"📋 {plan['name']}  {sessions_badge}", 
                               font=("Roboto", 15, "bold"), anchor="w")
        lbl_name.pack(anchor="w")

        info_text = f"{cycle_display or 'Özel'}  •  🔄 {repeat_weeks} Döngü"
        lbl_info = ctk.CTkLabel(content_frame, text=info_text, 
                               font=("Roboto", 12), anchor="w",
                               text_color=("#666666", "#999999"))
        lbl_info.pack(anchor="w", pady=(4, 0))

        # Right side - Delete button
        right_frame = ctk.CTkFrame(card, fg_color="transparent")
        right_frame.pack(side="right", padx=15, pady=12)

        btn_delete = ctk.CTkButton(right_frame, text="🗑️ Sil", width=80, height=28,
                                  fg_color="#E74C3C", hover_color="#C0392B",
                                  command=lambda: self.delete_plan(plan['id']))
        btn_delete.pack()

    def delete_plan(self, plan_id):
        """Delete a plan after confirmation"""
        from tkinter import messagebox as mb
        import httpx
        if mb.askyesno("Onay", "Bu planı silmek istediğinizden emin misiniz?"):
            try:
                self.api_client.delete(f"/api/v1/services/plans/{plan_id}")
                mb.showinfo("Başarılı", "Plan silindi.")
                self.load_plans()
            except httpx.HTTPStatusError as e:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                except:
                    error_detail = str(e)
                mb.showerror("Hata", error_detail)
            except Exception as e:
                mb.showerror("Hata", f"Silme işlemi başarısız: {e}")

    def open_add_plan_dialog(self):
        """Open dialog for adding a new plan"""
        dialog = AddPlanDialog(self, self.api_client, self.load_plans)
        dialog.focus()
