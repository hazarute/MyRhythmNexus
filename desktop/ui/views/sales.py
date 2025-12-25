import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.api_client import ApiClient
from desktop.ui.views.tabs.sales_pos_tab import SalesPOSTab
from desktop.ui.views.tabs.recent_purchases_tab import RecentPurchasesTab
from desktop.ui.views.tabs.packages_management_tab import PackagesManagementTab


class SalesView(ctk.CTkFrame):
    """Main sales view container with POS and package management tabs"""
    
    def __init__(self, master, api_client: ApiClient):
        super().__init__(master)
        self.api_client = api_client
        
        self.pack(fill="both", expand=True)
        
        # Create tabview styled like member detail view
        self.tabview = ctk.CTkTabview(
            self,
            height=50,
            segmented_button_fg_color="#2B2B2B",
            segmented_button_selected_color="#3B8ED0",
            segmented_button_selected_hover_color="#2E7AB8",
            segmented_button_unselected_color="#404040",
            segmented_button_unselected_hover_color="#4A4A4A",
            command=self.on_tab_change
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        self.tabview._segmented_button.configure(font=("Roboto", 16, "bold"), border_width=0)
        
        # Add tabs
        self.tab_pos_name = _("Satış Ekranı (POS)")
        self.tab_purchases_name = _("Son Satın Almalar")
        self.tab_packages_name = _("Paket Yönetimi")

        tab_pos = self.tabview.add(self.tab_pos_name)
        tab_purchases = self.tabview.add(self.tab_purchases_name)
        tab_packages = self.tabview.add(self.tab_packages_name)

        # Initialize tab content
        self.pos_tab = SalesPOSTab(tab_pos, self.api_client)
        self.pos_tab.pack(fill="both", expand=True)

        self.purchases_tab = RecentPurchasesTab(tab_purchases, self.api_client)
        self.purchases_tab.pack(fill="both", expand=True, padx=10, pady=10)

        self.packages_tab = PackagesManagementTab(
            tab_packages,
            self.api_client,
            on_packages_updated=self.pos_tab.load_packages,
        )
        self.packages_tab.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bind click events to tab buttons for refresh on every click
        self.bind_tab_click_events()

    def bind_tab_click_events(self):
        """Bind mouse click events to tab buttons for refresh on every click"""
        tab_names = [self.tab_pos_name, self.tab_purchases_name, self.tab_packages_name]
        try:
            buttons = self.tabview._segmented_button._buttons
        except AttributeError:
            buttons = self.tabview._segmented_button.winfo_children()
        
        for i, button in enumerate(buttons):
            if i < len(tab_names):
                tab_name = tab_names[i]
                button.bind("<Button-1>", lambda e, name=tab_name: self.on_tab_button_click(name))

    def on_tab_button_click(self, tab_name):
        """Called when any tab button is clicked - refresh the tab"""
        self.refresh_tab_by_name(tab_name)

    def on_tab_change(self):
        """Called when tab changes - refresh the current tab"""
        current_tab = self.tabview.get()
        self.refresh_tab_by_name(current_tab)

    def refresh_tab_by_name(self, tab_name):
        """Refresh tab by name"""
        if tab_name == self.tab_pos_name:
            self.pos_tab.refresh()
        elif tab_name == self.tab_purchases_name:
            try:
                self.purchases_tab.refresh()
            except Exception:
                pass
        elif tab_name == self.tab_packages_name:
            self.packages_tab.refresh()
