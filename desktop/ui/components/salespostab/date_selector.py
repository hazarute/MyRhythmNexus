import customtkinter as ctk
from desktop.core.locale import _
from tkinter import messagebox
from datetime import date, timedelta, datetime
from typing import Callable, Optional
from desktop.ui.components.date_picker import DatePickerDialog, get_weekday_name
import sys
from pathlib import Path

# Add backend to path for date_utils import
backend_path = Path(__file__).parent.parent.parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from backend.core.date_utils import calculate_end_date


class DateSelector(ctk.CTkFrame):
    """
    Tarih seçimi bileşeni: Başlangıç tarihi seçer ve otomatik bitiş tarihini hesaplar.
    
    Kullanım:
        selector = DateSelector(parent, on_date_change=callback)
        selector.pack(fill="x", padx=15, pady=15)
        
        # Kullan:
        start = selector.get_start_date()
        end = selector.get_end_date()
    """
    
    def __init__(self, parent, on_date_change: Optional[Callable] = None, **kwargs):
        super().__init__(parent, fg_color=("#F5F5F5", "#2B2B2B"), corner_radius=10, **kwargs)
        
        self.on_date_change = on_date_change
        self.start_date: date = date.today()
        
        # Store plan info for end date calculation
        self.cycle_period: str = "MONTHLY"
        self.repeat_weeks: int = 4
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(header, text=_("📅 Tarih Seçimi"), 
                    font=("Roboto", 18, "bold"),
                    text_color="#3B8ED0").pack(anchor="w")
        
        # Start Date Section
        ctk.CTkLabel(self, text=_("Başlangıç Tarihi:"), 
                    font=("Roboto", 14)).pack(anchor="w", padx=15, pady=(10, 5))
        
        date_frame = ctk.CTkFrame(self, fg_color="transparent")
        date_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # Start Date Button
        self.btn_start_date = ctk.CTkButton(date_frame, 
                           text=self._format_start_button_text(),
                                           font=("Roboto", 16, "bold"),
                                           fg_color="#21415A", 
                                           hover_color="#0A1B2C",
                                           height=40, 
                                           corner_radius=8,
                                           command=self.open_date_picker)
        self.btn_start_date.pack(fill="x")
        
        # End Date Display
        ctk.CTkLabel(self, text=_("Bitiş Tarihi:"), 
                    font=("Roboto", 14)).pack(anchor="w", padx=15, pady=(10, 5))
        
        end_date_frame = ctk.CTkFrame(self, fg_color=("#E3F2FD", "#0A1B2C"), corner_radius=8)
        end_date_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.lbl_end_date = ctk.CTkLabel(end_date_frame,                                         
                                        font=("Roboto", 14, "bold"),
                                        text_color=("#0D1925", "#E3F2FD"))
        self.lbl_end_date.pack(pady=10)
    
    def open_date_picker(self):
        """DatePickerDialog'u aç ve seçilen tarihi al"""
        dialog = DatePickerDialog(self.master, initial_date=self.start_date)
        selected = dialog.get_date()
        
        if selected:
            # If a past date is chosen, reset to today and inform the user
            if selected < date.today():
                messagebox.showwarning(
                    _("Uyarı"),
                    _("Geçmiş tarih seçilemez; tarih bugüne sıfırlandı.")
                )
                selected = date.today()

            self.start_date = selected
            self.btn_start_date.configure(text=self._format_start_button_text())
            
            # Update end date when start date changes
            self.set_end_date_from_plan(self.cycle_period, self.repeat_weeks)
            
            if self.on_date_change:
                self.on_date_change(self.start_date, None)
    
    def set_end_date_from_plan(self, cycle_period: str, repeat_weeks: int):
        """Plan verilerine göre bitiş tarihini hesapla ve göster
        
        Args:
            cycle_period: "MONTHLY", "WEEKLY" gibi periyot
            repeat_weeks: Tekrar sayısı (haftalar cinsinden)
        """
        # Store plan info for later date picker updates
        self.cycle_period = cycle_period
        self.repeat_weeks = repeat_weeks
        
        try:
            # Use backend's calculate_end_date for consistent business logic
            end_datetime = calculate_end_date(
                datetime.combine(self.start_date, datetime.min.time()),
                cycle_period,
                repeat_weeks
            )
            end_date = end_datetime.date()
            weeks = (end_date - self.start_date).days // 7
            
            self.lbl_end_date.configure(
                text=_("{} ({}) hafta").format(end_date.strftime('%d/%m/%Y'), weeks)
            )
        except Exception as e:
            self.lbl_end_date.configure(text=_("Bitiş Tarihi: Hata"))
    
    
    def get_start_date(self) -> date:
        """Başlangıç tarihini döndür"""
        return self.start_date
    
    def reset(self):
        """Tarihleri sıfırla"""
        self.start_date = date.today()
        self.btn_start_date.configure(text=self._format_start_button_text())
        self.lbl_end_date.configure()

    def _format_start_button_text(self) -> str:
        day_label = get_weekday_name(self.start_date)
        formatted_date = self.start_date.strftime("%d/%m/%Y")
        return _("Değiştirmek İçin Tıklayın - {}" ).format(f"({day_label}) - {formatted_date}")
