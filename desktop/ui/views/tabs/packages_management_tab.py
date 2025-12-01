import customtkinter as ctk
from desktop.core.api_client import ApiClient
from tkinter import messagebox
from typing import Callable, Optional

from desktop.ui.views.dialogs import AddPackageDialog


class PackagesManagementTab(ctk.CTkFrame):
    """Card-based package management experience aligned with member cards."""

    def __init__(
        self,
        parent,
        api_client: ApiClient,
        on_packages_updated: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.api_client = api_client
        self.on_packages_updated = on_packages_updated
        self.selected_package_id = None
        self.package_cards = {}

        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 12), padx=20)

        ctk.CTkButton(
            top_bar,
            text="+ Yeni Paket",
            command=self.show_add_package_dialog,
        ).pack(side="right")

        self.packages_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.packages_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.load_packages()

    def refresh(self):
        """Refresh the packages management tab"""
        self.load_packages()

    def load_packages(self):
        for child in self.packages_scroll.winfo_children():
            child.destroy()

        self.selected_package_id = None
        self.package_cards = {}

        try:
            packages = self.api_client.get("/api/v1/services/packages")
        except Exception as e:
            messagebox.showerror("Hata", f"Paketler yüklenemedi: {e}")
            return

        if not packages:
            ctk.CTkLabel(
                self.packages_scroll,
                text="Henüz paket bulunmuyor.",
                font=("Roboto", 16),
                text_color=("gray50", "gray70"),
            ).pack(pady=60)
            self._notify_packages_updated()
            return

        ctk.CTkLabel(
            self.packages_scroll,
            text="Tanımlı Paketler",
            font=("Roboto", 24, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 12))

        for pkg in packages:
            self._render_package_card(pkg)

        self._notify_packages_updated()

    def _render_package_card(self, package_data: dict):
        card_bg = "#1F1F1F"
        hover_bg = "#2A2A2A"
        card = ctk.CTkFrame(
            self.packages_scroll,
            fg_color=card_bg,
            corner_radius=14,
            border_width=1,
            border_color="#2A2A2A",
        )
        card.pack(fill="x", pady=8)

        handler = lambda e, pkg=package_data: self.on_package_click(pkg)
        card.configure(cursor="hand2")
        card.bind("<Button-1>", handler)
        card.bind("<Enter>", lambda e, c=card: c.configure(fg_color=hover_bg))
        card.bind("<Leave>", lambda e, c=card: c.configure(fg_color=card_bg))

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(12, 6))

        title = ctk.CTkLabel(
            header,
            text=package_data.get("name", "Bilinmeyen Paket"),
            font=("Roboto", 18, "bold"),
            anchor="w",
        )
        title.pack(side="left", anchor="w")

        badge_text = "Aktif" if package_data.get("is_active") else "Pasif"
        badge_color = "#3B8ED0" if package_data.get("is_active") else "#6C757D"
        status_label = ctk.CTkLabel(
            header,
            text=f"{badge_text}",
            font=("Roboto", 12, "bold"),
            text_color=badge_color,
        )
        status_label.pack(side="left", padx=(12, 0))

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(0, 10))

        offering = package_data.get("offering", {}).get("name", "-")
        plan = package_data.get("plan", {}).get("name", "-")
        price = float(package_data.get("price", 0))
        base_text = f"{offering} · {plan} · ₺{price:.2f}"
        description_label = ctk.CTkLabel(
            body,
            text=base_text,
            font=("Roboto", 12),
            text_color="gray70",
            anchor="w",
        )
        description_label.pack(anchor="w")

        dates = f"{package_data.get('start_date', '')[:10]} → {package_data.get('end_date', '')[:10]}"
        dates_label = ctk.CTkLabel(
            body,
            text=dates,
            font=("Roboto", 12),
            text_color="gray50",
            anchor="w",
        )
        dates_label.pack(anchor="w", pady=(6, 0))

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(0, 12))

        price_label = ctk.CTkLabel(
            footer,
            text=f"₺{price:.2f}",
            font=("Roboto", 18, "bold"),
        )
        price_label.pack(side="left")

        del_btn = ctk.CTkButton(
            footer,
            text="Sil",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            width=78,
            command=lambda pid=package_data["id"]: self.delete_package(pid),
        )
        del_btn.pack(side="right")

        self.package_cards[package_data["id"]] = {
            "frame": card,
            "labels": [title, status_label],
            "data": package_data,
        }

        self._bind_package_card_widgets(
            handler,
            header,
            title,
            status_label,
            body,
            description_label,
            dates_label,
            footer,
            price_label,
        )

    def _clear_card_highlight(self):
        if not self.selected_package_id:
            return
        record = self.package_cards.get(self.selected_package_id)
        if not record:
            return
        record["frame"].configure(border_width=1, border_color="#2A2A2A")
        for lbl in record["labels"]:
            lbl.configure(text_color=("black", "white"))

    def select_package(self, package_id):
        if not package_id or package_id not in self.package_cards:
            return
        self._clear_card_highlight()
        self.selected_package_id = package_id
        record = self.package_cards[package_id]
        record["frame"].configure(border_width=2, border_color="#3B8ED0")
        for lbl in record["labels"]:
            lbl.configure(text_color=("#1F6AA5", "#3B8ED0"))

    def delete_package(self, package_id=None):
        target_id = package_id or self.selected_package_id
        if not target_id:
            return
        target = self.package_cards.get(target_id, {}).get("data")
        if not target:
            return
        confirm = messagebox.askyesno(
            "Paket Sil",
            f"'{target['name']}' paketini silmek istediğinize emin misiniz?\n\n"
            "DİKKAT: Eğer bu pakete bağlı aktif abonelikler varsa silme işlemi engellenecektir."
        )
        if not confirm:
            return
        try:
            self.api_client.delete(f"/api/v1/services/packages/{target_id}")
            messagebox.showinfo("Başarılı", "Paket silindi.")
            self.load_packages()
        except Exception as e:
            messagebox.showerror("Hata", f"Silme başarısız:\n{e}")

    def edit_package(self):
        if not self.selected_package_id:
            return
        self.open_edit_dialog(self.package_cards[self.selected_package_id]["data"])

    def on_package_click(self, package_data: dict):
        self.select_package(package_data["id"])
        self.open_edit_dialog(package_data)

    def open_edit_dialog(self, package_data):
        AddPackageDialog(
            self,
            self.api_client,
            self.load_packages,
            package_to_edit=package_data,
        )

    def show_add_package_dialog(self):
        AddPackageDialog(self, self.api_client, self.load_packages)

    def _bind_package_card_widgets(self, handler, *widgets):
        for widget in widgets:
            widget.bind("<Button-1>", handler)

    def _notify_packages_updated(self):
        if not self.on_packages_updated:
            return
        try:
            self.on_packages_updated()
        except Exception as exc:
            print(f"Failed to refresh linked package consumers: {exc}")

