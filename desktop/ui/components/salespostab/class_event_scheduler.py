"""
ClassEventScheduler Component
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Modular UI component for SESSION_BASED subscription class scheduling.
Handles day selection, time input, instructor selection, and repeat weeks.
"""

import customtkinter as ctk
from desktop.core.locale import _
from typing import Dict, List, Optional
from desktop.ui.components.time_spinner import TimeSpinner


class ClassEventScheduler(ctk.CTkFrame):
    """
    Standalone component for scheduling class events.
    
    Provides:
    - Instructor selection dropdown
    - Day checkboxes (Mon-Sun) with time inputs
    - Repeat weeks spinner
    - Data collection via get_class_events_payload()
    """
    
    def __init__(self, parent, service: Optional[Dict] = None, api_client=None, plan: Optional[Dict] = None, **kwargs):
        super().__init__(parent, fg_color=("#F5F5F5", "#2B2B2B"), corner_radius=10, **kwargs)
        
        # State variables
        self.service = service or {}
        self.api_client = api_client
        self.plan = plan or {}
        self.instructors: List[Dict] = []
        self.selected_instructor_id: Optional[str] = None
        # Get repeat_weeks from plan or default to 1
        self.selected_repeat_weeks: int = self.plan.get('repeat_weeks', 1) or 1
        
        # Day selection state (0=Monday, 6=Sunday)
        self.selected_days = {
            "monday": ctk.BooleanVar(value=False),
            "tuesday": ctk.BooleanVar(value=False),
            "wednesday": ctk.BooleanVar(value=False),
            "thursday": ctk.BooleanVar(value=False),
            "friday": ctk.BooleanVar(value=False),
            "saturday": ctk.BooleanVar(value=False),
            "sunday": ctk.BooleanVar(value=False)
        }
        self.day_entries: Dict[str, ctk.CTkEntry] = {}
        self.day_times: Dict[str, str] = {}  # {"monday": "14:00", ...}
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build the component UI"""
        # Title
        title_label = ctk.CTkLabel(
            self, 
            text=_("📚 Özel Ders Zamanlaması"), 
            font=("Roboto", 14, "bold"),
            text_color="#2CC985"
        )
        title_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        # Eğitmen seçimi
        ctk.CTkLabel(
            self, 
            text=_("Eğitmen:"), 
            font=("Roboto", 12)
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.combo_instructor = ctk.CTkComboBox(
            self, 
            values=[], 
            state="readonly",
            height=40, 
            font=("Roboto", 13)
        )
        self.combo_instructor.pack(fill="x", padx=15, pady=(0, 15))
        self.combo_instructor._entry.bind("<Button-1>", lambda e: self.combo_instructor._clicked(None))
        
        # Hafta günleri ve saatler
        ctk.CTkLabel(
            self, 
            text=_("Ders Günleri ve Saatleri:"), 
            font=("Roboto", 12, "bold")
        ).pack(anchor="w", padx=15, pady=(0, 10))
        
        days_frame = ctk.CTkFrame(self, fg_color="transparent")
        days_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        day_names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        day_keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        for day_name, day_key in zip(day_names, day_keys):
            self._create_day_row(days_frame, day_name, day_key)
        
        # Tekrar haftalar
        ctk.CTkLabel(
            self, 
            text=_("Tekrar Eden Haftalar:"), 
            font=("Roboto", 12)
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        repeat_frame = ctk.CTkFrame(self, fg_color="transparent")
        repeat_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.lbl_repeat_weeks = ctk.CTkLabel(
            repeat_frame, 
            text=str(self.selected_repeat_weeks), 
            font=("Roboto", 16, "bold"), 
            width=40
        )
        self.lbl_repeat_weeks.pack(side="left", padx=10)
    
    def _create_day_row(self, parent: ctk.CTkFrame, day_name: str, day_key: str):
        """Create a checkbox + time spinners row for a specific day"""
        day_row = ctk.CTkFrame(parent, fg_color="transparent")
        day_row.pack(fill="x", pady=5)
        
        # Checkbox
        chk = ctk.CTkCheckBox(
            day_row, 
            text=day_name, 
            width=30,
            variable=self.selected_days[day_key],
            font=("Roboto", 12),
            command=lambda dk=day_key: self.update_day_state(dk)
        )
        chk.pack(side="left", padx=(0, 10))
        
        # Time spinners frame (initially hidden)
        time_frame = ctk.CTkFrame(day_row, fg_color="transparent")
        # Don't pack yet - will be shown when day is selected
        
        # Store frame reference for enable/disable
        setattr(self, f"{day_key}_time_frame", time_frame)
        setattr(self, f"{day_key}_time_frame_packed", False)
        
        # Hours spinner (0-23, default 14)
        hour_spinner = TimeSpinner(
            time_frame,
            min_val=0,
            max_val=23,
            default=14,
            step=1,
            label_width=30,
        )
        hour_spinner.pack(side="left", padx=3)
        setattr(self, f"{day_key}_hour_spinner", hour_spinner)
        
        # Separator
        ctk.CTkLabel(time_frame, text=_(":"), font=("Roboto", 12, "bold")).pack(side="left", padx=2)
        
        # Minutes spinner (0-59, step 30, default 0)
        minute_spinner = TimeSpinner(
            time_frame,
            default=0,
            values=(0, 30),
            label_width=30,
        )
        minute_spinner.pack(side="left", padx=3)
        setattr(self, f"{day_key}_minute_spinner", minute_spinner)
    
    def update_repeat_weeks(self, delta: int):
        """Update repeat weeks count (1-52 range)"""
        new_value = max(1, min(52, self.selected_repeat_weeks + delta))
        self.selected_repeat_weeks = new_value
        self.lbl_repeat_weeks.configure(text=str(new_value))
    
    def update_day_state(self, day_key: str):
        """Show/hide and enable/disable spinners based on checkbox state"""
        is_checked = self.selected_days[day_key].get()
        time_frame = getattr(self, f"{day_key}_time_frame", None)
        is_packed = getattr(self, f"{day_key}_time_frame_packed", False)
        
        if not time_frame:
            return
        
        if is_checked and not is_packed:
            # Show time frame
            time_frame.pack(side="left", padx=(0, 10))
            setattr(self, f"{day_key}_time_frame_packed", True)
            
            # Enable spinners
            hour_spinner = getattr(self, f"{day_key}_hour_spinner", None)
            minute_spinner = getattr(self, f"{day_key}_minute_spinner", None)
            if hour_spinner:
                hour_spinner.enable()
            if minute_spinner:
                minute_spinner.enable()
        elif not is_checked and is_packed:
            # Hide time frame
            time_frame.pack_forget()
            setattr(self, f"{day_key}_time_frame_packed", False)
            
            # Disable spinners
            hour_spinner = getattr(self, f"{day_key}_hour_spinner", None)
            minute_spinner = getattr(self, f"{day_key}_minute_spinner", None)
            if hour_spinner:
                hour_spinner.disable()
            if minute_spinner:
                minute_spinner.disable()
    
    def load_instructors(self, instructors: List[Dict]):
        """Load and display available instructors
        
        Args:
            instructors: List of instructor dicts with 'id', 'first_name', 'last_name'
        """
        self.instructors = instructors
        instructor_names = [f"{i['first_name']} {i['last_name']}" for i in instructors]
        self.combo_instructor.configure(values=instructor_names)
        
        if self.instructors:
            self.combo_instructor.set(instructor_names[0])
            self.selected_instructor_id = self.instructors[0]["id"]
    
    def get_class_events_payload(self) -> Optional[Dict]:
        """
        Collect selected days/times and return class_events payload.
        
        Returns:
            Dict with keys: days_and_times, instructor_user_id, repeat_weeks, capacity
            None if no days selected or no instructor selected
        """
        # Collect selected days and times
        selected_days_list = []
        for day_key, day_var in self.selected_days.items():
            if day_var.get():
                # Get hour and minute from spinners
                hour_spinner = getattr(self, f"{day_key}_hour_spinner", None)
                minute_spinner = getattr(self, f"{day_key}_minute_spinner", None)
                
                if hour_spinner and minute_spinner:
                    hour = hour_spinner.get_value()
                    minute = minute_spinner.get_value()
                    time_str = f"{hour:02d}:{minute:02d}"
                    selected_days_list.append({
                        "day": day_key,
                        "time": time_str
                    })
        
        # Get instructor
        instructor_name = self.combo_instructor.get()
        instructor = next(
            (i for i in self.instructors if f"{i['first_name']} {i['last_name']}" == instructor_name), 
            None
        )
        
        if not selected_days_list or not instructor:
            return None
        
        return {
            "days_and_times": selected_days_list,
            "instructor_user_id": instructor["id"],
            "repeat_weeks": self.selected_repeat_weeks,
            "capacity": 10  # Default capacity
        }
    
    def reset(self):
        """Reset all fields to default state"""
        # Reset day checkboxes and spinners
        for day_key in self.selected_days:
            self.selected_days[day_key].set(False)
            
            # Reset spinners to default values
            hour_spinner = getattr(self, f"{day_key}_hour_spinner", None)
            minute_spinner = getattr(self, f"{day_key}_minute_spinner", None)
            
            if hour_spinner:
                hour_spinner.set_value(14)
            if minute_spinner:
                minute_spinner.set_value(0)
        
        # Reset repeat weeks to plan value or 1
        self.selected_repeat_weeks = self.plan.get('repeat_weeks', 1) or 1
        self.lbl_repeat_weeks.configure(text=str(self.selected_repeat_weeks))
        
        # Reset instructor (set to first if available)
        if self.instructors:
            instructor_names = [f"{i['first_name']} {i['last_name']}" for i in self.instructors]
            self.combo_instructor.set(instructor_names[0])
