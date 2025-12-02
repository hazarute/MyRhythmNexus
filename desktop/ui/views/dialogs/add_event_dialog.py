import customtkinter as ctk
from desktop.core.locale import _
import httpx
from datetime import datetime, timedelta, date
from tkinter import messagebox
from desktop.core.api_client import ApiClient
from desktop.ui.components.date_picker import DatePickerDialog
from desktop.ui.components.time_spinner import TimeSpinner


class AddEventDialog(ctk.CTkToplevel):
    """Dialog for creating new class events (sessions)."""

    def __init__(self, parent, api_client: ApiClient, on_success):
        super().__init__(parent)
        self.api_client = api_client
        self.on_success = on_success

        self.title(_("Yeni Seans Ekle"))
        self.geometry("480x620")

        self.transient(parent)
        self.grab_set()
        self.lift()
        self.focus_force()

        self.templates = []
        self.instructors = []

        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            self.main_frame,
            text=_("Yeni Seans Ekle"),
            font=("Roboto", 22, "bold"),
        ).pack(pady=(0, 24))

        self.combo_template = self.create_combo(_("Seans Şablonu"))
        self.combo_instructor = self.create_combo(_("Eğitmen"))
        
        # Date picker button
        self.selected_date = datetime.now().date()
        self.btn_date = self.create_date_button()
        
        # Time spinners
        self.hour_spinner, self.minute_spinner = self.create_time_spinners()
        
        self.entry_duration = self.create_input(_("Süre (dk)"))
        self.entry_capacity = self.create_input(_("Kapasite"))

        for combo in (self.combo_template, self.combo_instructor):
            self._bind_combo_dropdown(combo)

        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=30)

        ctk.CTkButton(
            btn_frame,
            text=_("❌ İptal"),
            fg_color="#555555",
            hover_color="#333333",
            width=110,
            command=self.destroy,
        ).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(
            btn_frame,
            text=_("💾 Kaydet"),
            fg_color="#2CC985",
            hover_color="#229966",
            width=110,
            command=self.save,
        ).pack(side="right", padx=10, expand=True)

        # Set default values
        # Time spinners already have defaults (9:00)
        self.entry_duration.insert(0, "60")
        self.entry_capacity.insert(0, "10")

        self.load_options()

    def create_input(self, label_text):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.pack(fill="x", pady=6)

        ctk.CTkLabel(frame, text=label_text, font=("Roboto", 14), width=110, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame, height=36, font=("Roboto", 13))
        entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
        return entry

    def create_date_button(self):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.pack(fill="x", pady=6)

        ctk.CTkLabel(frame, text=_("Tarih"), font=("Roboto", 14), width=110, anchor="w").pack(side="left")
        btn = ctk.CTkButton(
            frame,
            text=self.selected_date.strftime("%d.%m.%Y"),
            height=36,
            font=("Roboto", 13),
            fg_color="#3B8ED0",
            hover_color="#2E7AB8",
            command=self.open_date_picker,
        )
        btn.pack(side="left", fill="x", expand=True, padx=(8, 0))
        return btn

    def create_time_spinners(self):
        """Create hour and minute spinners for time selection"""
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.pack(fill="x", pady=6)

        ctk.CTkLabel(frame, text=_("Saat"), font=("Roboto", 14), width=110, anchor="w").pack(side="left")
        
        # Hour spinner (0-23)
        hour_spinner = TimeSpinner(
            frame,
            min_val=0,
            max_val=23,
            default=9,
            step=1,
            label_width=35,
            font=("Roboto", 13, "bold")
        )
        hour_spinner.pack(side="left", padx=(8, 5))
        
        # Separator label
        ctk.CTkLabel(frame, text=":", font=("Roboto", 16, "bold")).pack(side="left")
        
        # Minute spinner (only 0 and 30)
        minute_spinner = TimeSpinner(
            frame,
            min_val=0,
            max_val=30,
            default=0,
            step=30,  # Step 30 will toggle between 0 and 30
            label_width=35,
            font=("Roboto", 13, "bold")
        )
        minute_spinner.pack(side="left", padx=(5, 0))
        
        return hour_spinner, minute_spinner

    def open_date_picker(self):
        picker = DatePickerDialog(self, initial_date=self.selected_date, title=_("Seans Tarihi"))
        selected = picker.get_date()
        if selected:
            self.selected_date = selected
            self.btn_date.configure(text=self.selected_date.strftime("%d.%m.%Y"))

    def create_combo(self, label_text):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.pack(fill="x", pady=6)

        ctk.CTkLabel(frame, text=label_text, font=("Roboto", 14), width=110, anchor="w").pack(side="left")
        combo = ctk.CTkComboBox(
            frame,
            values=[_("Yükleniyor...")],
            state="readonly",
            height=36,
            font=("Roboto", 13),
        )
        combo.pack(side="left", fill="x", expand=True, padx=(8, 0))
        return combo

    def _bind_combo_dropdown(self, combo: ctk.CTkComboBox):
        combo.bind("<Button-1>", lambda e, c=combo: c._clicked(None))
        combo._entry.bind("<Button-1>", lambda e, c=combo: c._clicked(None))

    def load_options(self):
        try:
            self.templates = self.api_client.get("/api/v1/operations/templates")
            self.instructors = self.api_client.get("/api/v1/staff/")

            self.combo_template.configure(values=[t["name"] for t in self.templates])
            self.combo_instructor.configure(values=[f"{i['first_name']} {i['last_name']}" for i in self.instructors])

            if self.templates:
                self.combo_template.set(self.templates[0]["name"])
            else:
                self.combo_template.configure(values=[_("Şablon Yok")])

            if self.instructors:
                self.combo_instructor.set(f"{self.instructors[0]['first_name']} {self.instructors[0]['last_name']}")
            else:
                self.combo_instructor.configure(values=[_("Eğitmen Yok")])

        except Exception as e:
            print(f"Error loading options: {e}")

    def save(self):
        try:
            # Validate inputs
            tmpl_name = self.combo_template.get()
            instr_name = self.combo_instructor.get()

            tmpl_id = next((t["id"] for t in self.templates if t["name"] == tmpl_name), None)
            instr_id = next((i["id"] for i in self.instructors if f"{i['first_name']} {i['last_name']}" == instr_name), None)

            if not tmpl_id or not instr_id:
                messagebox.showwarning(_("Uyarı"), _("Lütfen tüm alanları doldurunuz."))
                return

            time_str = f"{self.hour_spinner.get_value():02d}:{self.minute_spinner.get_value():02d}"

            # Validate time format
            try:
                start_dt = datetime.combine(self.selected_date, datetime.strptime(time_str, "%H:%M").time())
            except ValueError:
                messagebox.showwarning(_("Geçersiz Format"), _("Saat formatı: HH:MM"))
                return

            # Validate numeric inputs
            try:
                duration = int(self.entry_duration.get().strip())
                capacity = int(self.entry_capacity.get().strip())
            except ValueError:
                messagebox.showwarning(_("Geçersiz Değer"), _("Süre ve Kapasite sayısal değer olmalıdır."))
                return

            if duration <= 0 or capacity <= 0:
                messagebox.showwarning(_("Geçersiz Değer"), _("Süre ve Kapasite 0'dan büyük olmalıdır."))
                return

            end_dt = start_dt + timedelta(minutes=duration)

            data = {
                "template_id": tmpl_id,
                "instructor_user_id": instr_id,
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
                "capacity": capacity,
                "is_cancelled": False,
            }

            self.api_client.post("/api/v1/operations/events", json=data)
            messagebox.showinfo(_("Başarılı"), _("Seans eklendi."))
            self.on_success()
            self.destroy()

        except httpx.HTTPStatusError as exc:
            detail = _("Bilinmeyen hata")
            try:
                detail = exc.response.json().get("detail") or detail
            except ValueError:
                detail = exc.response.text
            messagebox.showerror(_("Hata"), _("İşlem başarısız: {detail}").format(detail=detail))
        except Exception as e:
            messagebox.showerror(_("Hata"), _("İşlem başarısız: {err}").format(err=str(e)))
