import customtkinter as ctk
from desktop.core.locale import _
from datetime import datetime
from typing import Any, Callable, Optional


class PaymentDetailDialog(ctk.CTkToplevel):
    """Ödeme kartı için detay modalı, ölçüm diyalog stiline paralel."""

    def __init__(self, master: Any, payload: dict[str, Any], on_close: Optional[Callable[[], None]] = None):
        super().__init__(master)
        self.payload = payload
        self._on_close = on_close
        self.title(_("Ödeme Detayı"))
        self.geometry("720x740")
        self.configure(fg_color="#1A1A1A")

        self.lift()
        self.focus_force()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._close)

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="#161616", corner_radius=16)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        header = ctk.CTkFrame(container, fg_color="#3B8ED0", corner_radius=12)
        header.pack(fill="x", padx=15, pady=(15, 8))

        amount = self._format_currency(self.payload.get("amount_paid"))
        date_text = self._format_date(self.payload.get("payment_date"))
        ctk.CTkLabel(
            header,
            text=amount,
            font=("Roboto", 24, "bold"),
            text_color="white",
        ).pack(pady=10)

        ctk.CTkLabel(
            header,
            text=date_text,
            font=("Roboto", 12),
            text_color="#E3F1FF",
        ).pack(pady=(0, 12))

        body = ctk.CTkFrame(container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=15, pady=(0, 12))

        self._detail_row(body, _("Üye"), self.payload.get("member_name", "-"))
        self._detail_row(body, _("Paket"), self.payload.get("package_name", "-"))
        self._detail_row(body, _("Yöntem"), self.payload.get("payment_method", "-"))
        self._detail_row(body, _("Durum"), self.payload.get("status", _("Tamamlandı")))
        self._detail_row(body, _("Çekilen Tutar"), amount)
        self._detail_row(
            body,
            _("İşlem Notu"),
            self.payload.get("notes", self.payload.get("description", "-")),
            wrap=True,
        )

        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            footer,
            text=_("✓ Kapat"),
            font=("Roboto", 14, "bold"),
            fg_color="#3B8ED0",
            hover_color="#2E7AB8",
            command=self._close,
        ).pack(fill="x")

    def _detail_row(self, parent: ctk.CTkFrame, label: str, value: str, wrap: bool = False) -> None:
        frame = ctk.CTkFrame(parent, fg_color="#1F1F1F", corner_radius=8)
        frame.pack(fill="x", pady=6)

        ctk.CTkLabel(
            frame,
            text=label,
            font=("Roboto", 12, "bold"),
            text_color="gray60",
            anchor="w",
        ).pack(fill="x", padx=12, pady=(6, 0))

        kwargs = {"wraplength": 640, "justify": "left"} if wrap else {}
        ctk.CTkLabel(
            frame,
            text=value or "-",
            font=("Roboto", 14),
            text_color="white",
            anchor="w",
            **kwargs,
        ).pack(fill="x", padx=12, pady=(0, 10))

    def _format_currency(self, value: Any) -> str:
        if value is None:
            return "- TL"
        try:
            amount = float(value)
        except (ValueError, TypeError):
            return f"{value} TL"
        return f"{amount:,.2f} TL".replace(",", " ")

    def _format_date(self, iso_value: Any) -> str:
        if not iso_value:
            return "-"
        try:
            cleaned = iso_value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(cleaned)
            return parsed.strftime("%d %b %Y, %H:%M")
        except (ValueError, AttributeError):
            return str(iso_value)[:16]

    def _close(self):
        if self._on_close:
            try:
                self._on_close()
            except Exception:
                pass
        self.destroy()