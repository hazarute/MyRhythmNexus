"""
TimeSpinner Component
━━━━━━━━━━━━━━━━━━━━
Reusable numeric spinner component for time selection (hours, minutes, etc).
Supports configurable min/max values, step size, and callbacks.
"""

import customtkinter as ctk
from desktop.core.locale import _
from typing import Optional, Callable


class TimeSpinner(ctk.CTkFrame):
    """
    A reusable numeric spinner component.
    
    Features:
    - Minus button (wraps to max on boundary)
    - Value display label
    - Plus button (wraps to min on boundary)
    - Configurable range, step, and default value
    - Optional callback on value change
    - Enable/disable state management
    
    Usage:
        spinner = TimeSpinner(
            parent,
            min_val=0,
            max_val=23,
            default=14,
            step=1,
            label_width=30,
            on_change=my_callback
        )
        spinner.pack(side="left", padx=5)
        value = spinner.get_value()
    """
    
    def __init__(
        self,
        parent,
        min_val: int = 0,
        max_val: int = 59,
        default: int = 0,
        step: int = 1,
        label_width: int = 30,
        font: tuple = ("Roboto", 12, "bold"),
        on_change: Optional[Callable[[int], None]] = None,
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.on_change = on_change
        self.font = font
        
        # Internal value variable
        self.value_var = ctk.IntVar(value=default)
        
        # Minus button
        self.btn_minus = ctk.CTkButton(
            self,
            text="−",
            width=30,
            height=30,
            font=font,
            state="normal",
            command=self._on_minus_click,
        )
        self.btn_minus.pack(side="left", padx=1)
        
        # Value display label
        self.lbl_value = ctk.CTkLabel(
            self,
            text=f"{default:02d}",
            font=font,
            width=label_width,
        )
        self.lbl_value.pack(side="left", padx=3)
        
        # Plus button
        self.btn_plus = ctk.CTkButton(
            self,
            text="+",
            width=30,
            height=30,
            font=font,
            state="normal",
            command=self._on_plus_click,
        )
        self.btn_plus.pack(side="left", padx=1)
        
        # Trace value changes to update label
        self.value_var.trace_add("write", self._on_value_changed)
    
    def _on_minus_click(self):
        """Handle minus button click"""
        new_val = self.value_var.get() - self.step
        
        # Wrap around at boundaries
        if new_val < self.min_val:
            new_val = self.max_val
        
        self.value_var.set(new_val)
    
    def _on_plus_click(self):
        """Handle plus button click"""
        new_val = self.value_var.get() + self.step
        
        # Wrap around at boundaries
        if new_val > self.max_val:
            new_val = self.min_val
        
        self.value_var.set(new_val)
    
    def _on_value_changed(self, *args):
        """Handle value variable changes"""
        current_val = self.value_var.get()
        
        # Update label display
        self.lbl_value.configure(text=f"{current_val:02d}")
        
        # Call external callback if provided
        if self.on_change:
            self.on_change(current_val)
    
    def get_value(self) -> int:
        """Get current spinner value"""
        return self.value_var.get()
    
    def set_value(self, value: int):
        """Set spinner value (with bounds checking)"""
        bounded_value = max(self.min_val, min(self.max_val, value))
        self.value_var.set(bounded_value)
    
    def enable(self):
        """Enable spinner buttons"""
        self.btn_minus.configure(state="normal")
        self.btn_plus.configure(state="normal")
    
    def disable(self):
        """Disable spinner buttons"""
        self.btn_minus.configure(state="disabled")
        self.btn_plus.configure(state="disabled")
