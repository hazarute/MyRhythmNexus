import customtkinter as ctk
from desktop.core.locale import _
from desktop.ui.components.date_utils import format_ddmmyyyy


class PackageCard(ctk.CTkFrame):
    """Reusable package/subscription card component with callbacks and active state.

    Constructor:
        PackageCard(parent, sub, is_active=False, on_click=None, on_delete=None, schedule_summary=None)

    Notes:
    - The frame itself is not packed by the component; caller should `pack()` or `grid()` it.
    - `on_click` will be bound to left-click if provided and `is_active` is True.
    - `on_delete` will add a delete button calling the callback with no args.
    - `schedule_summary` can be passed precomputed to avoid recomputing in the component.
    """

    def __init__(self, parent, sub: dict, is_active: bool = False, on_click=None, on_delete=None, schedule_summary=None, compact: bool = False, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # Style variants (compact for profile list, regular for packages tab)
        if compact:
            corner_radius = 6
            stripe_width = 3
            content_padx = 8
            content_pady = 4
            dates_font = ("Roboto", 12)
        else:
            corner_radius = 10
            stripe_width = 5
            content_padx = 15
            content_pady = 10
            dates_font = ("Roboto", 12)

        if is_active:
            bg_color = "#333333"
            accent_color = "#3B8ED0"
            text_color = "white"
            icon = "📦"
        else:
            bg_color = "#222222"
            accent_color = "#444444"
            text_color = "gray50"
            icon = "🗄️"

        self.configure(fg_color=bg_color, corner_radius=corner_radius)

        # Left stripe
        stripe = ctk.CTkFrame(self, fg_color=accent_color, width=stripe_width, height=70, corner_radius=0)
        stripe.pack(side="left", fill="y")

        # Content area
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=content_padx, pady=content_pady)

        # Click binding for active packages
        if is_active and on_click:
            self.bind("<Button-1>", lambda e: on_click())
            content.bind("<Button-1>", lambda e: on_click())
            self.configure(cursor="hand2")
            content.configure(cursor="hand2")

        pkg_name = sub.get('package', {}).get('name', 'Bilinmeyen Paket')
        pkg_label = ctk.CTkLabel(content, text=_("{}  {}").format(icon, pkg_name),
                                font=("Roboto", 16, "bold"),
                                text_color=text_color)
        pkg_label.pack(anchor="w")

        if is_active and on_click:
            pkg_label.bind("<Button-1>", lambda e: on_click())
            pkg_label.configure(cursor="hand2")

        dates = f"{format_ddmmyyyy(sub.get('start_date'))}  ➔  {format_ddmmyyyy(sub.get('end_date'))}"
        ctk.CTkLabel(content, text=dates, font=dates_font, text_color="gray70").pack(anchor="w", pady=(2, 5))

        bottom_row = ctk.CTkFrame(content, fg_color="transparent")
        bottom_row.pack(fill="x", pady=(5, 0))

        plan = sub.get('package', {}).get('plan', {})
        access_type = plan.get('access_type', 'SESSION_BASED')
        used = sub.get('used_sessions', 0)
        limit = plan.get('sessions_granted', 0)

        # Schedule summary (caller may pass precomputed summary)
        if schedule_summary:
            ctk.CTkLabel(content, text=_("📅 Ders Günleri: {}").format(schedule_summary),
                        font=("Roboto", 14, "bold"), text_color="#E6D1CF").pack(anchor="w", pady=(0, 5))

        if access_type == 'TIME_BASED':
            ctk.CTkLabel(bottom_row, text=_("♾️ Zaman Bazlı ({} giriş)").format(used),
                        font=("Roboto", 12, "bold"),
                        text_color=accent_color).pack(side="left")
        elif limit and limit > 0:
            ratio = min(used / limit, 1.0) if limit > 0 else 0
            progress_color = "#2CC985" if is_active else "gray"

            progress = ctk.CTkProgressBar(bottom_row, height=8, progress_color=progress_color)
            progress.set(ratio)
            progress.pack(side="left", fill="x", expand=True, padx=(0, 15))

            ctk.CTkLabel(bottom_row, text=_("{}/{} Ders").format(used, limit),
                        font=("Roboto", 11, "bold"),
                        text_color="gray").pack(side="left")
        else:
            ctk.CTkLabel(bottom_row, text=_("♾️ Sınırsız Erişim"),
                        font=("Roboto", 12, "bold"),
                        text_color=accent_color).pack(side="left")

        # Delete button
        if on_delete:
            btn_del = ctk.CTkButton(self, text=_("🗑️"), width=40, height=40,
                                  fg_color="#E74C3C", hover_color="#C0392B",
                                  font=("Segoe UI Emoji", 16),
                                  command=lambda: on_delete())
            btn_del.pack(side="right", padx=15)

