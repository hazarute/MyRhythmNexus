import customtkinter as ctk
from typing import Callable, Dict, Any

from desktop.ui.components.finance.formatters import format_currency, format_date
from desktop.ui.components.finance.styles import *


class PaymentCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        item: Dict[str, Any],
        on_detail: Callable[[Dict[str, Any]], None],
        on_delete: Callable[[str, str], None],
    ):
        super().__init__(
            master,
            corner_radius=12,
            fg_color=PAYMENT_CARD_BG,
            border_width=1,
            border_color=PAYMENT_CARD_BORDER,
            cursor="hand2",
        )
        self.item = item
        self.on_detail = on_detail
        self.on_delete = on_delete

        self._build_ui()

    def _build_ui(self):
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=20, pady=15)

        date_label = ctk.CTkLabel(
            left,
            text=format_date(self.item.get("payment_date")),
            font=("Roboto", 12, "bold"),
        )
        date_label.pack(anchor="w")

        member_name = self.item.get("member_name", "Bilinmiyor")
        package_name = self.item.get("package_name", "Paket belirtilmedi")

        ctk.CTkLabel(
            left,
            text=member_name,
            font=("Roboto", 18, "bold"),
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(
            left,
            text=package_name,
            font=("Roboto", 14),
            text_color=("#555555", "#BBBBBB"),
            anchor="w",
        ).pack(anchor="w", pady=(2, 4))

        method = self.item.get("payment_method", "-")
        badge = ctk.CTkLabel(
            left,
            text=f"💳 {method}",
            font=("Roboto", 12, "bold"),
            fg_color=BADGE_BG,
            corner_radius=8,
            padx=10,
            pady=4,
        )
        badge.pack(anchor="w")

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=20, pady=15)

        amount = format_currency(self.item.get("amount_paid"))
        ctk.CTkLabel(
            right,
            text=amount,
            font=("Roboto", 22, "bold"),
        ).pack(anchor="e")

        btn_frame = ctk.CTkFrame(right, fg_color="transparent")
        btn_frame.pack(anchor="e", pady=(12, 0))

        ctk.CTkButton(
            btn_frame,
            text="🛈 Detay",
            width=110,
            height=32,
            font=("Roboto", 12, "bold"),
            fg_color=BTN_DETAIL_FG,
            hover_color=BTN_DETAIL_HOVER,
            command=lambda: self.on_detail(self.item),
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_frame,
            text="🗑️ Sil",
            width=110,
            height=32,
            font=("Roboto", 12, "bold"),
            fg_color=BTN_DELETE_FG,
            hover_color=BTN_DELETE_HOVER,
            command=lambda: self.on_delete(self.item.get("id"), member_name),
        ).pack(side="left")

        self._bind_detail(left)

    def _bind_detail(self, target):
        target.bind(
            "<Button-1>",
            lambda event: self.on_detail(self.item),
        )
        for child in target.winfo_children():
            self._bind_detail(child)