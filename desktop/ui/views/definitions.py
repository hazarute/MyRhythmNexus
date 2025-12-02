import customtkinter as ctk
from desktop.core.api_client import ApiClient
from desktop.core.locale import _
from desktop.ui.views.tabs.categories_tab import CategoriesTab
from desktop.ui.views.tabs.offerings_tab import OfferingsTab
from desktop.ui.views.tabs.plans_tab import PlansTab


class DefinitionsView(ctk.CTkFrame):
    """Service definitions view - orchestrator for categories, offerings, and plans tabs"""
    
    def __init__(self, master, api_client: ApiClient):
        super().__init__(master)
        self.api_client = api_client

        # Title
        self.lbl_title = ctk.CTkLabel(self, text=_("Hizmet Tanımları (Sözlükler)"), font=("Roboto", 24, "bold"))
        self.lbl_title.pack(pady=20, padx=20, anchor="w")

        # Tabview with custom styling
        self.tabview = ctk.CTkTabview(self, height=50, 
                                      segmented_button_fg_color="#2B2B2B",
                                      segmented_button_selected_color="#3B8ED0",
                                      segmented_button_selected_hover_color="#2E7AB8",
                                      segmented_button_unselected_color="#404040",
                                      segmented_button_unselected_hover_color="#4A4A4A")
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        self.tabview._segmented_button.configure(font=("Roboto", 16, "bold"), border_width=0)

        # Create tabs with icons
        tab_categories = self.tabview.add(_("📁  Kategoriler"))
        tab_offerings = self.tabview.add(_("🏋️ Hizmetler (Dersler)"))
        tab_plans = self.tabview.add(_("📋  Planlar"))

        # Initialize tab content
        CategoriesTab(tab_categories, self.api_client).pack(fill="both", expand=True)
        OfferingsTab(tab_offerings, self.api_client).pack(fill="both", expand=True)
        PlansTab(tab_plans, self.api_client).pack(fill="both", expand=True)
