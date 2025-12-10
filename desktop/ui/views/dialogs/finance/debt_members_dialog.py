import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.ui_utils import safe_grab
from tkinter import messagebox
from typing import Callable, Optional

from desktop.core.api_client import ApiClient
from .debt_payment_dialog import DebtPaymentDialog


class DebtMembersDialog(ctk.CTkToplevel):
    def __init__(self, parent, api_client: ApiClient, refresh_callback: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self.api_client = api_client
        self.refresh_callback = refresh_callback

        self.title(_("Borçlu Üyeler"))
        self.geometry("640x640")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        safe_grab(self)

        container = ctk.CTkFrame(self, corner_radius=18)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            header_frame,
            text=_("Borçlu Üyeler"),
            font=("Roboto", 24, "bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_frame,
            text=_("Her üye sadece bir kere listelenir; detay için ödeme işlemini başlatabilirsiniz."),
            font=("Roboto", 12),
            text_color="gray",
        ).pack(anchor="w", pady=4)

        table_header = ctk.CTkFrame(container, fg_color=("#F0F0F0", "#1F1F1F"), corner_radius=8)
        table_header.pack(fill="x", pady=(0, 8))
        table_header.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            table_header,
            text=_("Üye"),
            font=("Roboto", 12, "bold"),
            text_color="#555555",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=8)
        ctk.CTkLabel(
            table_header,
            text=_("Toplam Borç"),
            font=("Roboto", 12, "bold"),
            text_color="#555555",
        ).grid(row=0, column=1, sticky="e", padx=16, pady=8)
        ctk.CTkLabel(
            table_header,
            text=_("İşlem"),
            font=("Roboto", 12, "bold"),
            text_color="#555555",
        ).grid(row=0, column=2, sticky="e", padx=16, pady=8)

        self.list_frame = ctk.CTkScrollableFrame(container, fg_color="transparent", height=420)
        self.list_frame.pack(fill="both", expand=True)

        self.load_data()

    def load_data(self):
        for child in self.list_frame.winfo_children():
            child.destroy()

        try:
            members = self.api_client.get("/api/v1/stats/debt-members")
        except Exception as exc:
            messagebox.showerror(_("Hata"), _("Borçlu üyeler alınamadı."))
            print(f"Error loading debt members: {exc}")
            return

        if not members:
            ctk.CTkLabel(
                self.list_frame,
                text=_("Şu anda borçlu üye bulunmuyor."),
                font=("Roboto", 14),
                text_color="gray",
            ).pack(pady=60)
            return

        for member in members:
            self._create_member_row(member)

    def _create_member_row(self, member: dict):
        row = ctk.CTkFrame(
            self.list_frame,
            corner_radius=12,
            fg_color=("#FFFFFF", "#1F1F1F"),
            border_width=1,
            border_color=("#E5E5E5", "#333333"),
        )
        row.pack(fill="x", padx=4, pady=4)
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=1)
        row.grid_columnconfigure(2, weight=0)

        full_name = f"{member.get('first_name', '')} {member.get('last_name', '')}".strip()
        ctk.CTkLabel(
            row,
            text=full_name or _("Bilinmeyen Üye"),
            font=("Roboto", 14, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(14, 8), pady=12)

        debt_amount = float(member.get("debt_amount", 0))
        ctk.CTkLabel(
            row,
            text=f"{debt_amount:,.2f} TL",
            font=("Roboto", 14, "bold"),
            text_color="#E74C3C",
        ).grid(row=0, column=1, sticky="e", padx=8, pady=12)

        btn = ctk.CTkButton(
            row,
            text=_("Ödeme"),
            width=110,
            height=30,
            fg_color="#2CC985",
            hover_color="#25A86F",
            command=lambda payload=member: self._open_payment(payload),
        )
        btn.grid(row=0, column=2, padx=(8, 12), pady=10)

    def _open_payment(self, member: dict):
        DebtPaymentDialog(
            self,
            self.api_client,
            member={
                "id": member.get("id"),
                "first_name": member.get("first_name"),
                "last_name": member.get("last_name"),
            },
            on_success=self._handle_payment_success,
        )

    def _handle_payment_success(self):
        if self.refresh_callback:
            self.refresh_callback()
        self.load_data()
