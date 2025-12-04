import customtkinter as ctk
from desktop.core.locale import _
from datetime import datetime, date
import calendar

WEEKDAY_NAMES = [
    "Pazartesi",
    "Salı",
    "Çarşamba",
    "Perşembe",
    "Cuma",
    "Cumartesi",
    "Pazar",
]


def get_weekday_name(target_date: date) -> str:
    return _(WEEKDAY_NAMES[target_date.weekday()])


class DatePickerDialog(ctk.CTkToplevel):
    """Modern tarih seçer dialog — CustomTkinter tarzı, gün/ay/yıl spinner'ları"""
    
    def __init__(self, parent, initial_date: date | None = None, title: str | None = None):
        super().__init__(parent)
        self.title(title or _("Tarih Seçin"))
        self.geometry("420x450")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        # Initialize date
        if initial_date is None:
            initial_date = date.today()
        elif isinstance(initial_date, datetime):
            initial_date = initial_date.date()
        
        self.selected_date = initial_date
        self.result = None
        
        # Configure style
        self.configure(fg_color=("#FFFFFF", "#1a1a1a"))
        
        # Main frame
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkLabel(main_frame, text=_("📅 Tarih Seçimi"),
                            font=("Roboto", 16, "bold"),
                            text_color="#3B8ED0")
        header.pack(anchor="w", pady=(0, 15))
        
        # Date display frame
        display_frame = ctk.CTkFrame(main_frame, fg_color=("#F0F0F0", "#2B2B2B"),
                                    corner_radius=12)
        display_frame.pack(fill="x", pady=(0, 20))
        
        self.lbl_display = ctk.CTkLabel(display_frame, text="",
                                       font=("Roboto", 16, "bold"),
                                       text_color="#2CC985")
        self.lbl_display.pack(pady=14)
        self.update_display()
        
        # Controls frame (3 columns: Gün - Ay - Yıl)
        controls_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        controls_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # GÜN (Day) - Left column
        day_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        day_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(day_frame, text=_("Gün"), font=("Roboto", 11, "bold"),
                    text_color=("#666", "#ccc")).pack(anchor="center", pady=(0, 10))
        
        ctk.CTkButton(day_frame, text="▲", width=50, height=35,
                     font=("Roboto", 14, "bold"),
                     fg_color="#3B8ED0", hover_color="#2E7AB8",
                     command=self.next_day).pack(fill="x", pady=(0, 5))
        
        self.lbl_day = ctk.CTkLabel(day_frame, text="",
                                   font=("Roboto", 24, "bold"),
                                   text_color="#3B8ED0")
        self.lbl_day.pack(pady=12)
        
        ctk.CTkButton(day_frame, text="▼", width=50, height=35,
                     font=("Roboto", 14, "bold"),
                     fg_color="#3B8ED0", hover_color="#2E7AB8",
                     command=self.prev_day).pack(fill="x", pady=(5, 0))
        
        # AY (Month) - Center column
        month_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        month_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(month_frame, text=_("Ay"), font=("Roboto", 11, "bold"),
                    text_color=("#666", "#ccc")).pack(anchor="center", pady=(0, 10))
        
        ctk.CTkButton(month_frame, text="▲", width=50, height=35,
                     font=("Roboto", 14, "bold"),
                     fg_color="#2CC985", hover_color="#24B76F",
                     command=self.next_month).pack(fill="x", pady=(0, 5))
        
        self.lbl_month = ctk.CTkLabel(month_frame, text="",
                                     font=("Roboto", 24, "bold"),
                                     text_color="#2CC985",
                                     width=120)
        self.lbl_month.pack(pady=12)
        
        ctk.CTkButton(month_frame, text="▼", width=50, height=35,
                     font=("Roboto", 14, "bold"),
                     fg_color="#2CC985", hover_color="#24B76F",
                     command=self.prev_month).pack(fill="x", pady=(5, 0))
        
        # YIL (Year) - Right column
        year_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        year_frame.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(year_frame, text=_("Yıl"), font=("Roboto", 11, "bold"),
                    text_color=("#666", "#ccc")).pack(anchor="center", pady=(0, 10))
        
        ctk.CTkButton(year_frame, text="▲", width=50, height=35,
                     font=("Roboto", 14, "bold"),
                     fg_color="#F39C12", hover_color="#D68910",
                     command=self.next_year).pack(fill="x", pady=(0, 5))
        
        self.lbl_year = ctk.CTkLabel(year_frame, text=str(self.selected_date.year),
                                    font=("Roboto", 24, "bold"),
                                    text_color="#F39C12")
        self.lbl_year.pack(pady=12)
        
        ctk.CTkButton(year_frame, text="▼", width=50, height=35,
                     font=("Roboto", 14, "bold"),
                     fg_color="#F39C12", hover_color="#D68910",
                     command=self.prev_year).pack(fill="x", pady=(5, 0))
        
        self.update_day_label()
        self.update_month_label()
        
        # Buttons frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(15, 0))
        
        ctk.CTkButton(button_frame, text=_("✅ Seç"), height=40,
                     fg_color="#2CC985", hover_color="#27A770",
                     font=("Roboto", 13, "bold"),
                     command=self.confirm).pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkButton(button_frame, text=_("❌ İptal"), height=40,
                     fg_color="#E74C3C", hover_color="#C0392B",
                     font=("Roboto", 13, "bold"),
                     command=self.cancel).pack(side="left", fill="both", expand=True)
        
        # Center window
        self.after(100, self._center_window)
    
    def _center_window(self):
        """Center dialog on parent"""
        self.update_idletasks()
        parent = self.master
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def update_display(self):
        """Güncelle tarih gösterimi: GÜN_ADI, GÜN/AYNO/YIL formatında"""
        day_name = get_weekday_name(self.selected_date)
        date_str = f"{day_name}, {self.selected_date.day:02d}/{self.selected_date.month:02d}/{self.selected_date.year}"
        self.lbl_display.configure(text=date_str)
    
    def update_day_label(self):
        """Gün labelını güncelle"""
        self.lbl_day.configure(text=f"{self.selected_date.day:02d}")
    
    def update_month_label(self):
        """Ay labelını güncelle — Türkçe ay ismi"""
        months_tr = [_("Ocak"), _("Şubat"), _("Mart"), _("Nisan"), _("Mayıs"), _("Haziran"),
                    _("Temmuz"), _("Ağustos"), _("Eylül"), _("Ekim"), _("Kasım"), _("Aralık")]
        month_name = months_tr[self.selected_date.month - 1]
        self.lbl_month.configure(text=month_name)
    
    def get_max_days(self) -> int:
        """Seçilen ay için maksimum gün sayısı"""
        _, max_day = calendar.monthrange(self.selected_date.year, self.selected_date.month)
        return max_day
    
    def next_day(self):
        """Bir gün ileriye git"""
        max_days = self.get_max_days()
        if self.selected_date.day < max_days:
            self.selected_date = date(self.selected_date.year, self.selected_date.month,
                                     self.selected_date.day + 1)
        else:
            # Sonraki aya ilk gün
            if self.selected_date.month < 12:
                next_month = self.selected_date.month + 1
                next_year = self.selected_date.year
            else:
                next_month = 1
                next_year = self.selected_date.year + 1
            
            self.selected_date = date(next_year, next_month, 1)
            self.update_month_label()
            self.lbl_year.configure(text=str(self.selected_date.year))
        
        self.update_display()
        self.update_day_label()
    
    def prev_day(self):
        """Bir gün geriye git"""
        if self.selected_date.day > 1:
            self.selected_date = date(self.selected_date.year, self.selected_date.month,
                                     self.selected_date.day - 1)
        else:
            # Önceki aya son gün
            if self.selected_date.month > 1:
                prev_month = self.selected_date.month - 1
                prev_year = self.selected_date.year
            else:
                prev_month = 12
                prev_year = self.selected_date.year - 1
            
            max_day = calendar.monthrange(prev_year, prev_month)[1]
            self.selected_date = date(prev_year, prev_month, max_day)
            self.update_month_label()
            self.lbl_year.configure(text=str(self.selected_date.year))
        
        self.update_display()
        self.update_day_label()
    
    def next_month(self):
        """Bir ay ileriye git"""
        if self.selected_date.month < 12:
            next_month = self.selected_date.month + 1
            next_year = self.selected_date.year
        else:
            next_month = 1
            next_year = self.selected_date.year + 1
        
        max_days = calendar.monthrange(next_year, next_month)[1]
        new_day = min(self.selected_date.day, max_days)
        
        self.selected_date = date(next_year, next_month, new_day)
        self.lbl_year.configure(text=str(self.selected_date.year))
        self.update_display()
        self.update_day_label()
        self.update_month_label()
    
    def prev_month(self):
        """Bir ay geriye git"""
        if self.selected_date.month > 1:
            prev_month = self.selected_date.month - 1
            prev_year = self.selected_date.year
        else:
            prev_month = 12
            prev_year = self.selected_date.year - 1
        
        max_days = calendar.monthrange(prev_year, prev_month)[1]
        new_day = min(self.selected_date.day, max_days)
        
        self.selected_date = date(prev_year, prev_month, new_day)
        self.lbl_year.configure(text=str(self.selected_date.year))
        self.update_display()
        self.update_day_label()
        self.update_month_label()
    
    def next_year(self):
        """Bir yıl ileriye git"""
        self.selected_date = date(self.selected_date.year + 1, self.selected_date.month,
                                 self.selected_date.day)
        self.lbl_year.configure(text=str(self.selected_date.year))
        self.update_display()
    
    def prev_year(self):
        """Bir yıl geriye git"""
        self.selected_date = date(self.selected_date.year - 1, self.selected_date.month,
                                 self.selected_date.day)
        self.lbl_year.configure(text=str(self.selected_date.year))
        self.update_display()
    
    def confirm(self):
        """Tarihi onayla ve dialog'u kapat"""
        self.result = self.selected_date
        self.destroy()
    
    def cancel(self):
        """Dialog'u iptal et"""
        self.result = None
        self.destroy()
    
    def get_date(self) -> date | None:
        """Seçilen tarihi döner (dialog kapanana kadar bekler)"""
        self.wait_window()
        return self.result
