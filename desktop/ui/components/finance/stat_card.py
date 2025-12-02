import customtkinter as ctk
from typing import Callable, Optional

from desktop.ui.components.finance.styles import DEFAULT_CARD_BG, CARD_BORDER_COLOR


class StatCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        icon: str,
        accent_color: str,
        on_click: Optional[Callable[[], None]] = None,
    ):
        super().__init__(
            master,
            corner_radius=16,
            fg_color=DEFAULT_CARD_BG,
            border_width=1,
            border_color=CARD_BORDER_COLOR,
        )

        self.accent_color = accent_color
        self.on_click = on_click

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        ctk.CTkLabel(
            inner,
            text=icon,
            font=("Segoe UI Emoji", 26),
            text_color=accent_color,
        ).pack(anchor="nw")

        self.value_label = ctk.CTkLabel(inner, text="...", font=("Roboto", 24, "bold"))
        self.value_label.pack(anchor="w", pady=(6, 0))

        ctk.CTkLabel(
            inner,
            text=title,
            font=("Roboto", 12),
            text_color=("#555555", "#BBBBBB"),
        ).pack(anchor="w")

        if on_click:
            self.configure(cursor="hand2")
            self._bind_hover_effect()
            self._bind_click()

    def set_value(self, text: str):
        """Set the value displayed in the stat card."""
        self.value_label.configure(text=text)

    def _bind_click(self):
        self.bind("<Button-1>", lambda event: self.on_click())
        for child in self.winfo_children():
            self._bind_click_recursive(child)

    def _bind_click_recursive(self, widget):
        widget.bind("<Button-1>", lambda event: self.on_click())
        for child in widget.winfo_children():
            self._bind_click_recursive(child)

    def _bind_hover_effect(self):
        """Bind smart hover effect with counter to handle child widgets"""
        hover_counter = {"count": 0}

        def on_enter(e):
            hover_counter["count"] += 1
            self.configure(border_color=self.accent_color)

        def on_leave(e):
            hover_counter["count"] -= 1
            if hover_counter["count"] <= 0:
                hover_counter["count"] = 0
                self.configure(border_color=CARD_BORDER_COLOR)

        # Bind to card and all children
        self.bind("<Enter>", on_enter)
        self.bind("<Leave>", on_leave)
        for child in self.winfo_children():
            self._bind_hover_recursive(child, on_enter, on_leave)

    def _bind_hover_recursive(self, widget, on_enter, on_leave):
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        for child in widget.winfo_children():
            self._bind_hover_recursive(child, on_enter, on_leave)