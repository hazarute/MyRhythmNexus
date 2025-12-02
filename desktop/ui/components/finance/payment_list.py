import customtkinter as ctk
from typing import List, Dict, Any, Callable

from desktop.ui.components.finance.payment_card import PaymentCard


class PaymentList(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_detail: Callable[[Dict[str, Any]], None],
        on_delete: Callable[[str, str], None],
    ):
        super().__init__(master, fg_color="transparent")
        self.on_detail = on_detail
        self.on_delete = on_delete

    def load_items(self, items: List[Dict[str, Any]]):
        """Load and display payment items."""
        # Clear existing items
        for widget in self.winfo_children():
            widget.destroy()

        if not items:
            self._show_empty_state("Henüz ödeme kaydı yok")
            return

        for item in items:
            PaymentCard(self, item, self.on_detail, self.on_delete).pack(fill="x", pady=8)

    def _show_empty_state(self, text: str):
        """Show empty state message."""
        placeholder = ctk.CTkLabel(
            self,
            text=text,
            font=("Roboto", 16),
            text_color=("gray45", "gray65"),
        )
        placeholder.pack(pady=80)

    def _show_empty_state(self, text: str):
        """Show empty state message."""
        placeholder = ctk.CTkLabel(
            self,
            text=text,
            font=("Roboto", 16),
            text_color=("gray45", "gray65"),
        )
        placeholder.pack(pady=80)