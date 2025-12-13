import customtkinter as ctk
import httpx
from desktop.core.locale import _
from desktop.core.api_client import ApiClient
from tkinter import messagebox
from desktop.core.ui_utils import safe_grab, bring_to_front_and_modal


class AddPackageDialog(ctk.CTkToplevel):
    """Dialog for creating or editing service packages."""

    def __init__(self, parent, api_client: ApiClient, on_success, package_to_edit=None):
        super().__init__(parent)
        self.api_client = api_client
        self.on_success = on_success
        self.package_to_edit = package_to_edit

        self.title("Paket Düzenle" if package_to_edit else "Yeni Paket Oluştur")
        self.geometry("480x520")

        # Ensure dialog is brought to front and made modal
        bring_to_front_and_modal(self, parent)

        self.categories = []
        self.offerings = []
        self.plans = []

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        header_text = _("Paket Düzenle") if package_to_edit else _("Yeni Paket Oluştur")
        ctk.CTkLabel(
            self.main_frame,
            text=header_text,
            font=("Roboto", 22, "bold"),
        ).pack(pady=(0, 24))

        self.entry_name = self.create_input("Paket Adı")
        self.combo_category = self.create_combo("Kategori")
        self.combo_offering = self.create_combo("Hizmet (Offering)")
        self.combo_plan = self.create_combo("Plan")
        self.entry_price = self.create_input("Fiyat (TL)")
        self.entry_desc = self.create_input("Açıklama")

        for combo in (self.combo_category, self.combo_offering, self.combo_plan):
            self._bind_combo_dropdown(combo)

        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=30)

        ctk.CTkButton(
            btn_frame,
            text=_("❌ İptal"),
            fg_color="#555555",
            hover_color="#333333",
            width=110,
            command=self.destroy,
        ).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(
            btn_frame,
            text=_("💾 Kaydet"),
            fg_color="#2CC985",
            hover_color="#229966",
            width=110,
            command=self.save,
        ).pack(side="right", padx=10, expand=True)

        self.load_options()

        if self.package_to_edit:
            self.entry_name.insert(0, self.package_to_edit.get("name", ""))
            self.entry_price.insert(0, str(self.package_to_edit.get("price", 0)))
            self.entry_desc.insert(0, self.package_to_edit.get("description", ""))

    def create_input(self, label_text):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.pack(fill="x", pady=6)

        ctk.CTkLabel(frame, text=label_text, font=("Roboto", 14), width=110, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame, height=36, font=("Roboto", 13))
        entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
        return entry

    def create_combo(self, label_text):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.pack(fill="x", pady=6)

        ctk.CTkLabel(frame, text=label_text, font=("Roboto", 14), width=110, anchor="w").pack(side="left")
        combo = ctk.CTkComboBox(
            frame,
            values=["Yükleniyor..."],
            state="readonly",
            height=36,
            font=("Roboto", 13),
        )
        combo.pack(side="left", fill="x", expand=True, padx=(8, 0))
        return combo

    def _bind_combo_dropdown(self, combo: ctk.CTkComboBox):
        combo.bind("<Button-1>", lambda e, c=combo: c._clicked(None))
        combo._entry.bind("<Button-1>", lambda e, c=combo: c._clicked(None))

    def load_options(self):
        try:
            self.categories = self.api_client.get("/api/v1/services/categories")
            self.offerings = self.api_client.get("/api/v1/services/offerings")
            self.plans = self.api_client.get("/api/v1/services/plans")

            self.combo_category.configure(values=[c["name"] for c in self.categories])
            self.combo_offering.configure(values=[o["name"] for o in self.offerings])
            self.combo_plan.configure(values=[p["name"] for p in self.plans])

            if self.package_to_edit:
                cat_name = self.package_to_edit.get("category", {}).get("name")
                off_name = self.package_to_edit.get("offering", {}).get("name")
                plan_name = self.package_to_edit.get("plan", {}).get("name")

                if cat_name:
                    self.combo_category.set(cat_name)
                if off_name:
                    self.combo_offering.set(off_name)
                if plan_name:
                    self.combo_plan.set(plan_name)
            else:
                if self.categories:
                    self.combo_category.set(self.categories[0]["name"])
                if self.offerings:
                    self.combo_offering.set(self.offerings[0]["name"])
                if self.plans:
                    self.combo_plan.set(self.plans[0]["name"])

        except Exception as e:
            print(f"Error loading options: {e}")

    def save(self):
        try:
            cat_name = self.combo_category.get()
            off_name = self.combo_offering.get()
            plan_name = self.combo_plan.get()

            cat_id = next((c["id"] for c in self.categories if c["name"] == cat_name), None)
            off_id = next((o["id"] for o in self.offerings if o["name"] == off_name), None)
            plan_id = next((p["id"] for p in self.plans if p["name"] == plan_name), None)

            if not all([cat_id, off_id, plan_id]):
                messagebox.showwarning("Uyarı", "Lütfen tüm alanları doldurunuz.")
                return

            price_text = self.entry_price.get().strip()
            try:
                price_value = float(price_text)
            except ValueError:
                messagebox.showwarning("Geçersiz Fiyat", "Lütfen geçerli bir fiyat giriniz.")
                return

            payload = {
                "name": self.entry_name.get().strip(),
                "category_id": cat_id,
                "offering_id": off_id,
                "plan_id": plan_id,
                "price": price_value,
                "description": self.entry_desc.get().strip() or None,
                "is_active": True,
            }

            if self.package_to_edit:
                self.api_client.put(
                    f"/api/v1/services/packages/{self.package_to_edit['id']}",
                    json=payload,
                )
                messagebox.showinfo("Başarılı", "Paket güncellendi.")
            else:
                self.api_client.post("/api/v1/services/packages", json=payload)
                messagebox.showinfo("Başarılı", "Paket oluşturuldu.")

            self.on_success()
            self.destroy()
        except httpx.HTTPStatusError as exc:
            detail = "Bilinmeyen hata"
            try:
                detail = exc.response.json().get("detail") or detail
            except ValueError:
                detail = exc.response.text
            messagebox.showerror("Hata", f"İşlem başarısız: {detail}")
        except Exception as e:
            messagebox.showerror("Hata", f"İşlem başarısız: {e}")
