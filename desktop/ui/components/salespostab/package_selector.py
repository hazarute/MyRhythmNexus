import customtkinter as ctk
from typing import Callable, Optional, List, Dict


class PackageSelector(ctk.CTkFrame):
    """
    Paket seçimi bileşeni: Paketleri yükler ve seçimi handle eder.
    
    Kullanım:
        selector = PackageSelector(parent, on_select=callback)
        selector.pack(fill="x", padx=15, pady=15)
        
        # Kullan:
        pkg = selector.get_selected_package()
        price = selector.get_price()
    """
    
    def __init__(self, parent, api_client=None, on_select: Optional[Callable] = None, **kwargs):
        super().__init__(parent, fg_color=("#F5F5F5", "#2B2B2B"), corner_radius=10, **kwargs)
        
        self.api_client = api_client
        self.on_select = on_select
        self.packages: List[Dict] = []
        self.selected_package: Optional[Dict] = None
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(header, text="📦 Paket Seçimi", 
                    font=("Roboto", 18, "bold"),
                    text_color="#3B8ED0").pack(anchor="w")
        
        # Package ComboBox
        ctk.CTkLabel(self, text="Paket:", 
                    font=("Roboto", 14)).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.combo_package = ctk.CTkComboBox(self, values=[], 
                                            command=self._on_package_select,
                                            state="readonly",
                                            height=40, 
                                            font=("Roboto", 16, "bold"),
                                            fg_color="#8B5CF6",
                                            button_color="#7C3AED",
                                            button_hover_color="#6D28D9")
        self.combo_package.pack(fill="x", padx=15, pady=(0, 10))
        self.combo_package._entry.bind("<Button-1>", lambda e: self.combo_package._clicked(None))
    
    def load_packages(self):
        """API'den paketleri yükle"""
        if not self.api_client:
            return
        
        try:
            self.packages = self.api_client.get("/api/v1/services/packages") or []
            package_names = [p["name"] for p in self.packages]
            self.combo_package.configure(values=package_names)
            
            # Default olarak ilk paketi seç ve callback'i manuel çağır
            if self.packages:
                self.combo_package.set(self.packages[0]["name"])
                self._on_package_select(self.packages[0]["name"])
        except Exception as e:
            import traceback
            print(f"Error loading packages: {e}")
            traceback.print_exc()
    
    def _on_package_select(self, choice: str):
        """Paket seçildiğinde çağrılır"""
        pkg = next((p for p in self.packages if p["name"] == choice), None)
        if not pkg:
            return
        
        self.selected_package = pkg
        
        # Call callback
        if self.on_select:
            self.on_select(pkg)
    
    def get_selected_package(self) -> Optional[Dict]:
        """Seçili paketi döndür"""
        return self.selected_package
    
    def get_price(self) -> float:
        """Seçili paketin fiyatını döndür"""
        if self.selected_package:
            return float(self.selected_package.get("price", 0))
        return 0.0
    
    def is_session_based(self) -> bool:
        """Seçili paket SESSION_BASED access_type'a sahip mi?"""
        if not self.selected_package:
            return False
        
        plan = self.selected_package.get("plan", {})
        access_type = plan.get("access_type", "SESSION_BASED")
        return access_type == "SESSION_BASED"
    
    def reset(self):
        """Seçimi sıfırla"""
        if self.packages:
            self.combo_package.set(self.packages[0]["name"])
            self._on_package_select(self.packages[0]["name"])
        else:
            self.selected_package = None
