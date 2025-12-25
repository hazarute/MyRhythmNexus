import customtkinter as ctk
from desktop.core.locale import _
from datetime import datetime
from desktop.ui.components.date_utils import format_ddmmyyyy


class ActivityItem(ctk.CTkFrame):
    """Reusable activity item card.

    Usage:
        ai = ActivityItem(parent, chk)
        ai.pack(fill="x", pady=3, padx=5)
    """

    def __init__(self, parent, chk: dict, on_delete=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.configure(fg_color="#2B2B2B", corner_radius=8, border_width=1, border_color="#404040")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=10)

        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 4))

        event_name = chk.get('event_name', 'Giriş')
        subscription_name = chk.get('subscription_name', '')
        user_name = chk.get('user_name') or ''

        # Icon and accent still determined by event type
        if "Seans Bazlı" in event_name:
            icon = "🎯"
            accent_color = "#E5B00D"
        elif "Zaman Bazlı" in event_name:
            icon = "⏰"
            accent_color = "#3B8ED0"
        else:
            icon = "📅"
            accent_color = "#2CC985"

        # Top (bold) label: user name if present, otherwise subscription name or event name
        if user_name:
            main_display = user_name
        elif subscription_name:
            main_display = subscription_name
        else:
            main_display = event_name

        icon_frame = ctk.CTkFrame(header_frame, fg_color=accent_color, width=32, height=32, corner_radius=6)
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text=icon, font=("Segoe UI Emoji", 14)).pack(expand=True)

        check_in_time_str = chk.get('check_in_time', '')
        if check_in_time_str:
            try:
                # Try ISO parse first
                cleaned = check_in_time_str.replace('Z', '+00:00')
                if isinstance(cleaned, str) and 'T' in cleaned:
                    local_time = datetime.fromisoformat(cleaned)
                else:
                    # fallback to common format
                    local_time = datetime.strptime(check_in_time_str, '%Y-%m-%d %H:%M:%S')

                date_part = format_ddmmyyyy(local_time)
                time_part = local_time.strftime('%H:%M')
            except Exception as e:
                # fallback: try format_ddmmyyyy which will attempt best-effort
                date_part = format_ddmmyyyy(check_in_time_str)
                # try to extract time portion if available
                try:
                    time_info = str(check_in_time_str).replace('T', ' ')[:16]
                    time_parts = time_info.split(' ')
                    time_part = time_parts[1][:5] if len(time_parts) > 1 else ''
                except Exception:
                    time_part = ''
        else:
            date_part = ''
            time_part = ''

        name_label = ctk.CTkLabel(
            header_frame,
            text=main_display,
            font=("Roboto", 16, "bold"),
            text_color="white"
        )
        name_label.pack(side="left", padx=(12, 0))

        time_display = f"{time_part} • {date_part}" if time_part and date_part else ""
        time_label = ctk.CTkLabel(
            header_frame,
            text=time_display,
            font=("Roboto", 14),
            text_color="gray70"
        )
        time_label.pack(side="left", padx=(15, 0))

        # Sub-label (small): prefer showing verifier name if available, otherwise subscription name, else automatic
        verified_by = chk.get('verified_by_name')
        if verified_by and verified_by != 'Sistem':
            sub_label_text = _("✓ {}").format(verified_by)
        elif subscription_name:
            sub_label_text = subscription_name
        else:
            sub_label_text = _("🤖 Otomatik")

        # Optional delete button on the right if a callback is provided
        if on_delete is not None:
            try:
                delete_btn = ctk.CTkButton(
                    header_frame,
                    text="🗑️",
                    width=36,
                    height=36,
                    fg_color="#E74C3C",
                    hover_color="#C0392B",
                    font=("Segoe UI Emoji", 14),
                    command=lambda chk_id=chk.get('id'): on_delete(chk_id)
                )
                delete_btn.pack(side="right", padx=(0, 5))
            except Exception:
                # If CTkButton styling fails for any reason, fall back to a simple label
                pass

        # Show prepared sub label text
        ctk.CTkLabel(content, text=sub_label_text, font=("Roboto", 10), text_color="gray60", anchor="w").pack(fill="x")
