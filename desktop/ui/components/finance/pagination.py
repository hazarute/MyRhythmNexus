import customtkinter as ctk
from desktop.core.locale import _
from typing import Callable


class PaginationControls(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_prev: Callable[[], None],
        on_next: Callable[[], None],
    ):
        super().__init__(master, fg_color="transparent")
        self.on_prev = on_prev
        self.on_next = on_next

        self.btn_prev = ctk.CTkButton(
            self,
            text=_("< Önceki"),
            width=120,
            command=self.on_prev,
        )
        self.btn_prev.pack(side="left")

        self.lbl_page = ctk.CTkLabel(
            self,
            text=_("Sayfa 1 / 1"),
            font=("Roboto", 14),
        )
        self.lbl_page.pack(side="left", expand=True)

        self.btn_next = ctk.CTkButton(
            self,
            text=_("Sonraki >"),
            width=120,
            command=self.on_next,
        )
        self.btn_next.pack(side="right")

    def update_page_info(self, current_page: int, total_pages: int):
        """Update the page label and button states."""
        page_text = _("Sayfa") + f" {current_page} / {total_pages}"
        self.lbl_page.configure(text=page_text)
        self.btn_prev.configure(state="normal" if current_page > 1 else "disabled")
        self.btn_next.configure(state="normal" if current_page < total_pages else "disabled")