import customtkinter as ctk
from desktop.core.locale import _
from typing import Optional

from desktop.core.api_client import ApiClient
from desktop.ui.views.tabs.finance_tab import FinanceTab


class FinanceView(ctk.CTkFrame):
    def __init__(self, master, api_client: ApiClient, member_id: Optional[str] = None):
        super().__init__(master)
        FinanceTab(self, api_client, member_id).pack(fill="both", expand=True)
