import customtkinter as ctk
from typing import List, Tuple, Optional, Callable

from desktop.ui.components.finance.stat_card import StatCard
from desktop.ui.components.finance.styles import *


class SummaryRow(ctk.CTkFrame):
    def __init__(
        self,
        master,
        stat_specs: List[Tuple[str, str, str, str, Optional[Callable[[], None]]]],
        debt_card_light: str = DEBT_CARD_LIGHT,
    ):
        super().__init__(master, fg_color="transparent")

        self.stat_cards: dict[str, StatCard] = {}

        for idx, (key, title, icon, accent, command) in enumerate(stat_specs):
            card = StatCard(
                self,
                title,
                icon,
                accent,
                command,
            )
            card.grid(row=0, column=idx, sticky="ew", padx=6)
            self.grid_columnconfigure(idx, weight=1)
            self.stat_cards[key] = card

            # Make the debt-members stat card background slightly lighter
            if key == "debt_members_count":
                try:
                    card.configure(fg_color=debt_card_light)
                except Exception:
                    # Fallback: set single color if theme tuple isn't supported
                    card.configure(fg_color="#FBF5EC")

    def set_value(self, key: str, text: str):
        """Set the value for a specific stat card."""
        card = self.stat_cards.get(key)
        if card:
            card.set_value(text)