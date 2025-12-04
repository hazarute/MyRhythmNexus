import customtkinter as ctk
from desktop.core.locale import _
from datetime import datetime
from tkinter import messagebox
from typing import Callable, Optional

from desktop.core.api_client import ApiClient
from desktop.ui.views.dialogs.finance.payment_detail_dialog import PaymentDetailDialog
from desktop.ui.views.dialogs.finance.debt_members_dialog import DebtMembersDialog
from desktop.ui.components.finance.formatters import format_currency, format_date
from desktop.ui.components.finance.pagination import PaginationControls
from desktop.ui.components.finance import styles
from desktop.ui.components.finance.summary_row import SummaryRow
from desktop.ui.components.finance.payment_list import PaymentList


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
            text=_("Finansal Geçmiş"),
            font=("Roboto", 26, "bold"),
        )
        self.label_title.pack(side="left")

        if self.member_id:
            self.btn_clear_filter = ctk.CTkButton(
                title_frame,
                text=_("Filtreyi Temizle"),
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
            text=_("Yükleniyor..."),
            font=("Roboto", 12),
            text_color=("#888888", "#CCCCCC"),
        )
        self.lbl_summary.pack(side="right", padx=(0, 8))

        self.summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_frame.pack(fill="x", padx=20, pady=(0, 10))

        stats_specs = [
            ("active_members", "Aktif Üyeler", "👥", styles.ACCENT_ACTIVE_MEMBERS, None),
            ("debt_members_count", "Borçlu Üyeler →", "⚠️", styles.ACCENT_DEBT_MEMBERS, self.show_debt_members),
            ("pending_payments_amount", "Toplam Borç", "💳", styles.ACCENT_PENDING_PAYMENTS, None),
            ("monthly_revenue", "Aylık Ciro", "💰", styles.ACCENT_MONTHLY_REVENUE, None),
        ]

        self.summary_row = SummaryRow(self.summary_frame, stats_specs)
        self.summary_row.pack(fill="x")

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.payment_list = PaymentList(
            self.scroll_frame,
            self.show_payment_detail,
            self.confirm_delete_payment,
        )
        self.payment_list.pack(fill="both", expand=True)

        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.pack(fill="x", padx=20, pady=15)

        self.pagination = PaginationControls(self.footer, self.prev_page, self.next_page)
        self.pagination.pack(fill="x")

    def _build_subtitle(self) -> str:
        return _("Üyeye özel kayıtlar") if self.member_id else _("Tüm ödemeler")

    def clear_filter(self):
        self.member_id = None
        self.page = 1
        self.label_title.configure(text=_("Finansal Geçmiş"))
        self.label_subtitle.configure(text=self._build_subtitle())
        if hasattr(self, "btn_clear_filter"):
            self.btn_clear_filter.destroy()
            delattr(self, "btn_clear_filter")
        self.load_data()

    def load_data(self):
        # Load summary independently - errors shouldn't block payment list
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

            self.pagination.update_page_info(self.page, self.total_pages)

            summary_text = _("Toplam {} kayıt").format(self.total_records)
            if self.member_id:
                summary_text += _(" (Üyeye özel)")
            self.lbl_summary.configure(text=summary_text)
            
            self.payment_list.load_items(items)

        except Exception:
            self.payment_list.load_items([])
            self.lbl_summary.configure(text=_("Hata oluştu"))

    def _show_empty_state(self, text: str):
        """This method is now deprecated - use payment_list.load_items([]) instead"""
        # For backwards compatibility, this delegates to payment_list
        self.payment_list._show_empty_state(text)

    def load_summary_data(self):
        try:
            stats = self.api_client.get("/api/v1/stats/dashboard")
            
            self.summary_row.set_value("active_members", str(stats.get("active_members", 0)))
            self.summary_row.set_value("debt_members_count", str(stats.get("debt_members_count", 0)))
            pending = stats.get("pending_payments_amount", 0)
            self.summary_row.set_value("pending_payments_amount", format_currency(pending))
            revenue = stats.get("monthly_revenue", 0)
            self.summary_row.set_value("monthly_revenue", format_currency(revenue))
        except Exception:
            # Gracefully handle stats loading failure - don't block payment list
            for key in self.summary_row.stat_cards:
                self.summary_row.set_value(key, "—")

    def show_debt_members(self):
        DebtMembersDialog(
            self,
            self.api_client,
            refresh_callback=self.load_data,
        )

    def show_payment_detail(self, payload):
        PaymentDetailDialog(self, payload, on_close=self.load_data)

    def confirm_delete_payment(self, payment_id, member_name):
        if not payment_id:
            messagebox.showerror(_("Silme Hatası"), _("Ödeme kimliği mevcut değil."))
            return

        if not messagebox.askyesno(
            _("Ödemeyi Sil"), _("{} kaydını silmek istediğinize emin misiniz?").format(member_name)
        ):
            return

        try:
            self.api_client.delete(f"/api/v1/sales/payments/{payment_id}")
            self.load_data()
            # Inform the user that deletion succeeded
            messagebox.showinfo(_("Silme Başarılı"), _("Ödeme kaydı başarıyla silindi."))
        except Exception as exc:
            print(f"Error deleting payment: {exc}")
            messagebox.showerror(_("Silme Hatası"), _("İşlem başarısız oldu. Lütfen tekrar deneyin."))

    def prev_page(self):
        if self.page > 1:
            self.page -= 1
            self.load_data()

    def next_page(self):
        if self.page < self.total_pages:
            self.page += 1
            self.load_data()