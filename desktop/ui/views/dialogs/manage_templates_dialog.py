import customtkinter as ctk
import httpx
from tkinter import messagebox
from desktop.core.api_client import ApiClient


class ManageTemplatesDialog(ctk.CTkToplevel):
    """Dialog for managing ClassTemplates (create, edit, delete, list)."""

    def __init__(self, parent, api_client: ApiClient, on_success=None):
        super().__init__(parent)
        self.api_client = api_client
        self.on_success = on_success

        self.title("Seans Şablonları Yönetimi")
        self.geometry("600x550")

        self.transient(parent)
        self.grab_set()
        self.lift()
        self.focus_force()

        self.templates = []

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            self.main_frame,
            text="Seans Şablonları Yönetimi",
            font=("Roboto", 22, "bold"),
        ).pack(pady=(0, 24))

        # Input frame
        input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        input_frame.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(input_frame, text="Şablon Adı", font=("Roboto", 14), width=100, anchor="w").pack(side="left")
        self.entry_name = ctk.CTkEntry(input_frame, height=36, font=("Roboto", 13))
        self.entry_name.pack(side="left", fill="x", expand=True, padx=(8, 8))

        ctk.CTkButton(
            input_frame,
            text="➕ Ekle",
            width=90,
            fg_color="#3B8ED0",
            hover_color="#2E7AB8",
            command=self.add_template,
        ).pack(side="left")

        # Divider
        ctk.CTkLabel(self.main_frame, text="", fg_color="gray").pack(fill="x", pady=8, ipady=1)

        # Templates list
        ctk.CTkLabel(self.main_frame, text="Mevcut Şablonlar", font=("Roboto", 14, "bold")).pack(anchor="w", pady=(8, 8))

        self.list_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.list_frame.pack(fill="both", expand=True, pady=(0, 16))

        # Buttons
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=0)

        ctk.CTkButton(
            btn_frame,
            text="❌ Kapat",
            fg_color="#555555",
            hover_color="#333333",
            width=110,
            command=self.destroy,
        ).pack(side="left", padx=10, expand=True)

        self.load_templates()

    def load_templates(self):
        """Load templates from API."""
        for w in self.list_frame.winfo_children():
            w.destroy()

        try:
            self.templates = self.api_client.get("/api/v1/operations/templates")

            if not self.templates:
                ctk.CTkLabel(
                    self.list_frame,
                    text="Henüz şablon yok. Yukarıdan yeni şablon ekleyebilirsiniz.",
                    text_color="gray",
                ).pack(pady=20)
                return

            for template in self.templates:
                self.create_template_row(template)

        except Exception as e:
            ctk.CTkLabel(self.list_frame, text=f"Hata: {e}", text_color="red").pack(pady=10)

    def create_template_row(self, template):
        """Create a row for each template with edit/delete buttons."""
        row = ctk.CTkFrame(self.list_frame, fg_color=("gray90", "gray20"), corner_radius=8)
        row.pack(fill="x", pady=4, padx=0)

        # Template name
        ctk.CTkLabel(
            row,
            text=template["name"],
            font=("Roboto", 13, "bold"),
            text_color="#3B8ED0",
        ).pack(side="left", fill="x", expand=True, padx=12, pady=10)

        # Edit button
        ctk.CTkButton(
            row,
            text="✏️ Düzenle",
            width=90,
            font=("Roboto", 12),
            fg_color="#F39C12",
            hover_color="#D68910",
            command=lambda t=template: self.edit_template(t),
        ).pack(side="left", padx=4, pady=10)

        # Delete button
        ctk.CTkButton(
            row,
            text="🗑️ Sil",
            width=80,
            font=("Roboto", 12),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=lambda t=template: self.delete_template(t),
        ).pack(side="left", padx=4, pady=10)

    def add_template(self):
        """Add a new template."""
        name = self.entry_name.get().strip()

        if not name:
            messagebox.showwarning("Uyarı", "Lütfen şablon adı giriniz.")
            return

        try:
            payload = {"name": name}
            self.api_client.post("/api/v1/operations/templates", json=payload)
            messagebox.showinfo("Başarılı", f"'{name}' şablonu oluşturuldu.")
            self.entry_name.delete(0, "end")
            self.load_templates()
            if self.on_success:
                self.on_success()
        except httpx.HTTPStatusError as exc:
            detail = "Bilinmeyen hata"
            try:
                detail = exc.response.json().get("detail") or detail
            except ValueError:
                detail = exc.response.text
            messagebox.showerror("Hata", f"İşlem başarısız: {detail}")
        except Exception as e:
            messagebox.showerror("Hata", f"İşlem başarısız: {e}")

    def edit_template(self, template):
        """Edit an existing template."""
        # Create a simple edit dialog
        edit_dialog = ctk.CTkToplevel(self)
        edit_dialog.title("Şablonu Düzenle")
        edit_dialog.geometry("400x180")
        edit_dialog.transient(self)
        edit_dialog.grab_set()

        ctk.CTkLabel(edit_dialog, text="Yeni Ad", font=("Roboto", 14), padx=10, pady=10).pack(anchor="w")

        entry = ctk.CTkEntry(edit_dialog, font=("Roboto", 13), height=36)
        entry.pack(fill="x", padx=10, pady=5)
        entry.insert(0, template["name"])

        def save_edit():
            new_name = entry.get().strip()
            if not new_name:
                messagebox.showwarning("Uyarı", "Şablon adı boş olamaz.")
                return

            try:
                payload = {"name": new_name}
                self.api_client.put(f"/api/v1/operations/templates/{template['id']}", json=payload)
                messagebox.showinfo("Başarılı", "Şablon güncellendi.")
                edit_dialog.destroy()
                self.load_templates()
                if self.on_success:
                    self.on_success()
            except httpx.HTTPStatusError as exc:
                detail = "Bilinmeyen hata"
                try:
                    detail = exc.response.json().get("detail") or detail
                except ValueError:
                    detail = exc.response.text
                messagebox.showerror("Hata", f"İşlem başarısız: {detail}")
            except Exception as e:
                messagebox.showerror("Hata", f"İşlem başarısız: {e}")

        btn_frame = ctk.CTkFrame(edit_dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=20)

        ctk.CTkButton(btn_frame, text="❌ İptal", width=90, command=edit_dialog.destroy).pack(side="left", padx=5, expand=True)
        ctk.CTkButton(btn_frame, text="💾 Kaydet", width=90, fg_color="#2CC985", hover_color="#27A770", command=save_edit).pack(side="left", padx=5, expand=True)

    def delete_template(self, template):
        """Delete a template after confirmation."""
        if not messagebox.askyesno("Onay", f"'{template['name']}' şablonunu silmek istediğinize emin misiniz?"):
            return

        try:
            self.api_client.delete(f"/api/v1/operations/templates/{template['id']}")
            messagebox.showinfo("Başarılı", "Şablon silindi.")
            self.load_templates()
            if self.on_success:
                self.on_success()
        except httpx.HTTPStatusError as exc:
            detail = "Bilinmeyen hata"
            try:
                detail = exc.response.json().get("detail") or detail
            except ValueError:
                detail = exc.response.text
            messagebox.showerror("Hata", f"Silme başarısız: {detail}")
        except Exception as e:
            messagebox.showerror("Hata", f"Silme başarısız: {e}")
