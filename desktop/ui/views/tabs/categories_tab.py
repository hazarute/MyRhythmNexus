import customtkinter as ctk
from tkinter import messagebox
from desktop.core.api_client import ApiClient
from desktop.ui.views.dialogs import AddCategoryDialog


class CategoriesTab(ctk.CTkFrame):
    """Categories management tab"""
    
    def __init__(self, parent, api_client: ApiClient):
        super().__init__(parent, fg_color="transparent")
        self.api_client = api_client
        
        # Toolbar
        frame_toolbar = ctk.CTkFrame(self, fg_color="transparent")
        frame_toolbar.pack(fill="x", pady=(10, 20), padx=10)

        ctk.CTkButton(frame_toolbar, text="🔄 Yenile", width=100, height=32,
                     fg_color="#3B8ED0", hover_color="#2E7AB8",
                     command=self.load_categories).pack(side="left", padx=5)

        ctk.CTkButton(frame_toolbar, text="➕ Yeni Kategori", height=32,
                     fg_color="#2CC985", hover_color="#229966",
                     command=self.open_add_category_dialog).pack(side="right", padx=5)

        # Scrollable Frame for List
        self.frame_categories_list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frame_categories_list.pack(fill="both", expand=True, padx=10)

        self.load_categories()

    def load_categories(self):
        """Load and display categories"""
        # Clear list
        for widget in self.frame_categories_list.winfo_children():
            widget.destroy()

        try:
            categories = self.api_client.get("/api/v1/services/categories")
            for cat in categories:
                self.create_category_row(cat)
        except Exception as e:
            messagebox.showerror("Hata", f"Kategoriler yüklenemedi: {e}")

    def create_category_row(self, category):
        """Create a category card widget"""
        card = ctk.CTkFrame(self.frame_categories_list, corner_radius=10, 
                           fg_color=("#F0F0F0", "#2B2B2B"), border_width=1,
                           border_color=("#CCCCCC", "#404040"))
        card.pack(fill="x", pady=8, padx=5)

        # Left content
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, padx=15, pady=12)

        lbl_name = ctk.CTkLabel(content_frame, text=f"📁 {category['name']}", 
                               font=("Roboto", 15, "bold"), anchor="w")
        lbl_name.pack(anchor="w")

        desc_text = category.get('description', '') or 'Açıklama yok'
        lbl_desc = ctk.CTkLabel(content_frame, text=desc_text, 
                               font=("Roboto", 12), anchor="w",
                               text_color=("#666666", "#999999"))
        lbl_desc.pack(anchor="w", pady=(4, 0))

        # Right side - Delete button
        btn_delete = ctk.CTkButton(card, text="🗑️ Sil", width=80, height=28,
                                  fg_color="#E74C3C", hover_color="#C0392B",
                                  command=lambda: self.delete_category(category['id']))
        btn_delete.pack(side="right", padx=15, pady=12)

    def delete_category(self, category_id):
        """Delete a category after confirmation"""
        from tkinter import messagebox as mb
        import httpx
        if mb.askyesno("Onay", "Bu kategoriyi silmek istediğinizden emin misiniz?"):
            try:
                self.api_client.delete(f"/api/v1/services/categories/{category_id}")
                mb.showinfo("Başarılı", "Kategori silindi.")
                self.load_categories()
            except httpx.HTTPStatusError as e:
                try:
                    error_detail = e.response.json().get('detail', str(e))
                except:
                    error_detail = str(e)
                mb.showerror("Hata", error_detail)
            except Exception as e:
                mb.showerror("Hata", f"Silme işlemi başarısız: {e}")

    def open_add_category_dialog(self):
        """Open dialog for adding a new category"""
        dialog = AddCategoryDialog(self, self.api_client, self.load_categories)
        dialog.focus()
