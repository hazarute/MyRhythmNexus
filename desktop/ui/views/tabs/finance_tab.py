import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from typing import Callable, Optional

from desktop.core.api_client import ApiClient
from desktop.ui.views.dialogs.payment_detail_dialog import PaymentDetailDialog
from desktop.ui.views.dialogs.debt_members_dialog import DebtMembersDialog


class FinanceTab(ctk.CTkFrame):
    def __init__(self, master, api_client: ApiClient, member_id: Optional[str] = None):
        super().__init__(master)
        self.api_client = api_client
        self.member_id = member_id

        self.page = 1
        self.page_size = 10
        self.total_pages = 1
        self.total_records = 0

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=15)

        title_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        title_frame.pack(fill="x")

        self.label_title = ctk.CTkLabel(
            title_frame,
            text="Finansal Geçmiş",
            font=("Roboto", 26, "bold"),
        )
        self.label_title.pack(side="left")

        if self.member_id:
            self.btn_clear_filter = ctk.CTkButton(
                title_frame,
                text="Filtreyi Temizle",
                width=150,
                command=self.clear_filter,
                fg_color="#6C757D",
                hover_color="#5A6268",
                font=("Roboto", 12, "bold"),
            )
            self.btn_clear_filter.pack(side="right")

        info_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        info_frame.pack(fill="x", pady=(6, 0))

        self.label_subtitle = ctk.CTkLabel(
            info_frame,
            text=self._build_subtitle(),
            font=("Roboto", 14),
            text_color=("#666666", "#AAAAAA"),
        )
        self.label_subtitle.pack(side="left")

        self.lbl_summary = ctk.CTkLabel(
            info_frame,
            text="Yükleniyor...",
            font=("Roboto", 12),
            text_color=("#888888", "#CCCCCC"),
        )
        self.lbl_summary.pack(side="right", padx=(0, 8))

        self.summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.summary_values: dict[str, ctk.CTkLabel] = {}
        stats_specs = [
            ("active_members", "Aktif Üyeler", "👥", "#3B8ED0", None),
            ("debt_members_count", "Borçlu Üyeler →", "⚠️", "#F0AD4E", self.show_debt_members),
            ("pending_payments_amount", "Toplam Borç", "💳", "#E04F5F", None),
            ("monthly_revenue", "Aylık Ciro", "💰", "#9C27B0", None),
        ]
        for idx, (key, title, icon, accent, command) in enumerate(stats_specs):
            card, value_label = self._create_stat_card(
                self.summary_frame,
                title,
                icon,
                accent,
                command,
            )
            card.grid(row=0, column=idx, sticky="ew", padx=6)
            self.summary_frame.grid_columnconfigure(idx, weight=1)
            self.summary_values[key] = value_label

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.pack(fill="x", padx=20, pady=15)

        self.btn_prev = ctk.CTkButton(
            self.footer,
            text="< Önceki",
            width=120,
            command=self.prev_page,
        )
        self.btn_prev.pack(side="left")

        self.lbl_page = ctk.CTkLabel(
            self.footer,
            text="Sayfa 1 / 1",
            font=("Roboto", 14),
        )
        self.lbl_page.pack(side="left", expand=True)

        self.btn_next = ctk.CTkButton(
            self.footer,
            text="Sonraki >",
            width=120,
            command=self.next_page,
        )
        self.btn_next.pack(side="right")

    def _build_subtitle(self) -> str:
        return "Üyeye özel kayıtlar" if self.member_id else "Tüm ödemeler"

    def clear_filter(self):
        self.member_id = None
        self.page = 1
        self.label_title.configure(text="Finansal Geçmiş")
        self.label_subtitle.configure(text=self._build_subtitle())
        if hasattr(self, "btn_clear_filter"):
            self.btn_clear_filter.destroy()
            delattr(self, "btn_clear_filter")
        self.load_data()

    def load_data(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        self.load_summary_data()

        params: dict[str, object] = {
            "page": self.page,
            "size": self.page_size,
        }
        if self.member_id:
            params["member_id"] = self.member_id

        try:
            data = self.api_client.get("/api/v1/sales/payments", params=params)
            items = data.get("items", [])
            self.total_pages = max(1, data.get("pages", 1))
            self.total_records = data.get("total", 0)

            self.lbl_page.configure(text=f"Sayfa {self.page} / {self.total_pages}")
            self.btn_prev.configure(state="normal" if self.page > 1 else "disabled")
            self.btn_next.configure(
                state="normal" if self.page < self.total_pages else "disabled"
            )

            summary_text = f"Toplam {self.total_records} kayıt"
            if self.member_id:
                summary_text += " (Üyeye özel)"
            self.lbl_summary.configure(text=summary_text)

            if not items:
                message = (
                    "Üyeye ait ödeme kaydı bulunamadı" if self.member_id else "Henüz ödeme kaydı yok"
                )
                self._show_empty_state(message)
                return

            for item in items:
                self.create_payment_card(item)

        except Exception as exc:
            print(f"Error loading payments: {exc}")
            self._show_empty_state("Bir hata oluştu. Lütfen tekrar dene.")

    def _show_empty_state(self, text: str):
        placeholder = ctk.CTkLabel(
            self.scroll_frame,
            text=text,
            font=("Roboto", 16),
            text_color=("gray45", "gray65"),
        )
        placeholder.pack(pady=80)

    def _create_stat_card(
        self,
        parent,
        title: str,
        icon: str,
        accent_color: str,
        command: Optional[Callable[[], None]] = None,
    ):
        card = ctk.CTkFrame(
            parent,
            corner_radius=16,
            fg_color=("#F8F9FA", "#161616"),
            border_width=1,
            border_color=("#E5E7EB", "#2F2F2F"),
        )
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        ctk.CTkLabel(
            inner,
            text=icon,
            font=("Segoe UI Emoji", 26),
            text_color=accent_color,
        ).pack(anchor="nw")

        value_label = ctk.CTkLabel(inner, text="...", font=("Roboto", 24, "bold"))
        value_label.pack(anchor="w", pady=(6, 0))

        ctk.CTkLabel(
            inner,
            text=title,
            font=("Roboto", 12),
            text_color=("#555555", "#BBBBBB"),
        ).pack(anchor="w")

        if command:
            card.configure(cursor="hand2")
            # Hover efekti geri eklendi - hover counter ile akıllı yönetim
            self._bind_hover_effect(card, accent_color)
            self._bind_card_click(card, command)
        return card, value_label

    def _bind_card_click(self, widget, command: Callable[[], None]):
        widget.bind("<Button-1>", lambda event, fn=command: fn())
        for child in widget.winfo_children():
            self._bind_card_click(child, command)

    def _bind_hover_effect(self, card, accent_color: str):
        """Bind smart hover effect with counter to handle child widgets"""
        hover_counter = {"count": 0}

        def on_enter(e):
            hover_counter["count"] += 1
            card.configure(border_color=accent_color)

        def on_leave(e):
            hover_counter["count"] -= 1
            if hover_counter["count"] <= 0:
                hover_counter["count"] = 0
                card.configure(border_color=("#E5E7EB", "#2F2F2F"))

        # Bind to card and all children
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        for child in card.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)

    def load_summary_data(self):
        if not self.summary_values:
            return
        try:
            stats = self.api_client.get("/api/v1/stats/dashboard")
            self._set_stat_value("active_members", str(stats.get("active_members", 0)))
            self._set_stat_value("debt_members_count", str(stats.get("debt_members_count", 0)))
            pending = stats.get("pending_payments_amount", 0)
            self._set_stat_value("pending_payments_amount", self.format_currency(pending))
            revenue = stats.get("monthly_revenue", 0)
            self._set_stat_value("monthly_revenue", self.format_currency(revenue))
        except Exception as exc:
            print(f"Error loading summary stats: {exc}")
            for key in self.summary_values:
                self._set_stat_value(key, "—")

    def show_debt_members(self):
        DebtMembersDialog(
            self,
            self.api_client,
            refresh_callback=self.load_data,
        )

    def _set_stat_value(self, key: str, text: str):
        label = self.summary_values.get(key)
        if label:
            label.configure(text=text)

    def create_payment_card(self, item):
        card = ctk.CTkFrame(
            self.scroll_frame,
            corner_radius=12,
            fg_color=("#F8F9FA", "#1F1F1F"),
            border_width=1,
            border_color=("#E0E0E0", "#333333"),
            cursor="hand2",
        )
        card.pack(fill="x", pady=8)

        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=20, pady=15)

        date_label = ctk.CTkLabel(
            left,
            text=self.format_date(item.get("payment_date")),
            font=("Roboto", 12, "bold"),
        )
        date_label.pack(anchor="w")

        member_name = item.get("member_name", "Bilinmiyor")
        package_name = item.get("package_name", "Paket belirtilmedi")

        ctk.CTkLabel(
            left,
            text=member_name,
            font=("Roboto", 18, "bold"),
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(
            left,
            text=package_name,
            font=("Roboto", 14),
            text_color=("#555555", "#BBBBBB"),
            anchor="w",
        ).pack(anchor="w", pady=(2, 4))

        method = item.get("payment_method", "-")
        badge = ctk.CTkLabel(
            left,
            text=f"💳 {method}",
            font=("Roboto", 12, "bold"),
            fg_color=("#DDEBF7", "#2A3B54"),
            corner_radius=8,
            padx=10,
            pady=4,
        )
        badge.pack(anchor="w")

        right = ctk.CTkFrame(card, fg_color="transparent")
        right.pack(side="right", padx=20, pady=15)

        amount = self.format_currency(item.get("amount_paid"))
        ctk.CTkLabel(
            right,
            text=amount,
            font=("Roboto", 22, "bold"),
        ).pack(anchor="e")

        btn_frame = ctk.CTkFrame(right, fg_color="transparent")
        btn_frame.pack(anchor="e", pady=(12, 0))

        ctk.CTkButton(
            btn_frame,
            text="🛈 Detay",
            width=110,
            height=32,
            font=("Roboto", 12, "bold"),
            fg_color="#3B8ED0",
            hover_color="#2E7AB8",
            command=lambda payload=item: self.show_payment_detail(payload),
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_frame,
            text="🗑️ Sil",
            width=110,
            height=32,
            font=("Roboto", 12, "bold"),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=lambda payload=item: self.confirm_delete_payment(
                payload.get("id"), member_name
            ),
        ).pack(side="left")

        self._bind_detail(left, item)

    def _bind_detail(self, target, payload):
        target.bind(
            "<Button-1>",
            lambda event, data=payload: self.show_payment_detail(data),
        )
        for child in target.winfo_children():
            self._bind_detail(child, payload)

    def format_currency(self, value):
        if value is None:
            return "- TL"
        try:
            amount = float(value)
        except (ValueError, TypeError):
            return f"{value} TL"
        return f"{amount:,.2f} TL".replace(",", " ")

    def format_date(self, iso_value):
        if not iso_value:
            return "-"
        try:
            cleaned = iso_value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(cleaned)
            return parsed.strftime("%d %b %Y, %H:%M")
        except ValueError:
            return iso_value[:16]

    def show_payment_detail(self, payload):
        PaymentDetailDialog(self, payload, on_close=self.load_data)

    def confirm_delete_payment(self, payment_id, member_name):
        if not payment_id:
            messagebox.showerror("Silme Hatası", "Ödeme kimliği mevcut değil.")
            return

        if not messagebox.askyesno(
            "Ödemeyi Sil", f"{member_name} kaydını silmek istediğinize emin misiniz?"
        ):
            return

        try:
            self.api_client.delete(f"/api/v1/sales/payments/{payment_id}")
            self.load_data()
        except Exception as exc:
            print(f"Error deleting payment: {exc}")
            messagebox.showerror("Silme Hatası", "İşlem başarısız oldu. Lütfen tekrar deneyin.")

    def prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.load_data()

    def next_page(self):
        if self.page < self.total_pages:
            self.page += 1
            self.load_data()