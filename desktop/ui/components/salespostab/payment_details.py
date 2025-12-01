"""
PaymentDetails Component
━━━━━━━━━━━━━━━━━━━━━━━
Modular component for payment method and amount input.
"""

import customtkinter as ctk
from decimal import Decimal
from typing import Dict, Optional


class PaymentDetails(ctk.CTkFrame):
    """
    Standalone component for payment information input.
    
    Provides:
    - Payment method dropdown (NAKIT, KREDI_KARTI, HAVALE_EFT)
    - Payment amount entry
    - Data retrieval via get_payment_data()
    - Reset functionality
    """
    
    def __init__(self, parent, default_amount: float = 0.0, **kwargs):
        """
        Initialize PaymentDetails component.
        
        Args:
            parent: Parent frame
            default_amount: Default amount to display in placeholder
        """
        super().__init__(parent, fg_color=("#F5F5F5", "#2B2B2B"), 
                        corner_radius=10, **kwargs)
        
        self.default_amount = default_amount
        self._build_ui()
    
    def _build_ui(self):
        """Build the component UI"""
        # Header
        ctk.CTkLabel(
            self, 
            text="💰 Ödeme Detayları", 
            font=("Roboto", 18, "bold"),
            text_color="#3B8ED0"
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        # Payment Method
        ctk.CTkLabel(
            self, 
            text="Ödeme Yöntemi:", 
            font=("Roboto", 14)
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.combo_payment_method = ctk.CTkComboBox(
            self, 
            values=["NAKIT", "KREDI_KARTI", "HAVALE_EFT"], 
            state="readonly",
            height=40, 
            font=("Roboto", 16, "bold"),
            fg_color="#8B5CF6",
            button_color="#7C3AED",
            button_hover_color="#6D28D9"
        )
        self.combo_payment_method.pack(fill="x", padx=15, pady=(0, 10))
        self.combo_payment_method.set("NAKIT")
        self.combo_payment_method._entry.bind("<Button-1>", 
            lambda e: self.combo_payment_method._clicked(None))
        
        # Payment Amount
        ctk.CTkLabel(
            self, 
            text="Ödenen Tutar (TL):", 
            font=("Roboto", 14)
        ).pack(anchor="w", padx=15, pady=(5, 5))
        
        self.entry_payment_amount = ctk.CTkEntry(
            self, 
            height=40, 
            font=("Roboto", 14),
            fg_color="#8B5CF6",
            placeholder_text=f"{self.default_amount:.2f}"
        )
        self.entry_payment_amount.pack(fill="x", padx=15, pady=(0, 15))
    
    def set_default_amount(self, amount):
        """Update default amount (e.g., when package changes)"""
        try:
            # Convert to float if string
            amount_float = float(amount) if isinstance(amount, str) else amount
            self.default_amount = amount_float
            self.entry_payment_amount.delete(0, "end")
            self.entry_payment_amount.configure(placeholder_text=f"{amount_float:.2f}")
        except (ValueError, TypeError):
            # Default to 0 if invalid
            self.default_amount = 0.0
            self.entry_payment_amount.delete(0, "end")
            self.entry_payment_amount.configure(placeholder_text="0.00")
    
    def get_payment_data(self) -> Dict:
        """
        Get payment data as a dictionary.
        
        Returns:
            {
                "payment_method": "NAKIT|KREDI_KARTI|HAVALE_EFT",
                "amount_paid": Decimal,
                "is_valid": bool,
                "error": str (if not valid)
            }
        """
        try:
            amount_str = self.entry_payment_amount.get()
            if not amount_str:
                amount_str = "0"  # If no amount entered, treat as 0
            
            amount = Decimal(amount_str)
            
            if amount < 0:
                return {
                    "is_valid": False,
                    "error": "Tutar negatif olamaz."
                }
            
            if amount > Decimal("100000000"):
                return {
                    "is_valid": False,
                    "error": "Tutar 100.000.000 TL den küçük olmalıdır."
                }
            
            return {
                "is_valid": True,
                "payment_method": self.combo_payment_method.get(),
                "amount_paid": amount
            }
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"Geçersiz tutar: {str(e)}"
            }
    
    def reset(self):
        """Reset to default state"""
        self.combo_payment_method.set("NAKIT")
        self.entry_payment_amount.delete(0, "end")
        self.entry_payment_amount.configure(
            placeholder_text=f"{self.default_amount:.2f}"
        )
