import copy
import customtkinter as ctk
from desktop.core.locale import _
from desktop.ui.components.package_card import PackageCard
from tkinter import messagebox
from datetime import datetime
from desktop.ui.components.date_picker import get_weekday_name


class RecentPurchasesTab(ctk.CTkFrame):
    """Tab showing last purchased 10 subscriptions with buyer name and package."""

    def __init__(self, master, api_client, **kwargs):
        super().__init__(master, **kwargs)
        self.api_client = api_client
        self._member_cache = {}

        self.pack(fill="both", expand=True)

        header = ctk.CTkLabel(self, text=_("Son Satın Almalar"), font=("Roboto", 16, "bold"))
        header.pack(padx=12, pady=(10, 6), anchor="w")

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=12, pady=8)

        self.refresh()

    def refresh(self):
        # Clear
        for w in self.list_frame.winfo_children():
            w.destroy()

        try:
            # Use existing endpoint: list subscriptions (limit=10)
            data = self.api_client.get("/api/v1/sales/subscriptions?skip=0&limit=10")

            if not data:
                ctk.CTkLabel(self.list_frame, text=_("Satın alma bulunamadı."), text_color="gray").pack(pady=12)
                return

            for s in data:
                # Resolve member display name (try several shapes, with member API fallback)
                member = None
                if isinstance(s.get("member"), dict):
                    m = s.get("member")
                    member = "{} {}".format(m.get("first_name", ""), m.get("last_name", "")).strip()

                if not member:
                    mf = s.get('member_first_name') or ''
                    ml = s.get('member_last_name') or ''
                    member = s.get('member_name') or "{} {}".format(mf, ml).strip()

                if not member:
                    member_id = s.get('member_user_id') or s.get('memberId') or s.get('member_id')
                    if member_id:
                        if member_id in self._member_cache:
                            member = self._member_cache[member_id]
                        else:
                            try:
                                mdata = self.api_client.get(f"/api/v1/members/{member_id}")
                                if mdata:
                                    fname = mdata.get('first_name') or mdata.get('firstName') or ''
                                    lname = mdata.get('last_name') or mdata.get('lastName') or ''
                                    member = f"{fname} {lname}".strip()
                                    self._member_cache[member_id] = member
                            except Exception:
                                pass

                # Create a PackageCard for consistent appearance (click opens detail dialog)
                def make_onclick(sub):
                    return lambda: self._open_package_detail(sub)

                # Container: member name on top, package card below
                container = ctk.CTkFrame(self.list_frame, fg_color="transparent")
                container.pack(fill="x", pady=6, padx=6)

                # Ensure the PackageCard shows the member name where it normally
                # displays the package name by injecting the member into the
                # `package.name` field passed to the card.
                sub_for_card = copy.deepcopy(s)
                pkg = sub_for_card.get('package') or {}
                # Determine original package name (if any)
                if isinstance(pkg, dict):
                    orig_name = pkg.get('name') or pkg.get('title') or ''
                    base_pkg = dict(pkg)
                else:
                    orig_name = str(pkg) if pkg else ''
                    base_pkg = {}

                # Compose display name: "Member - Package" (omit dash if one part missing)
                member_part = member or ''
                if orig_name:
                    if member_part:
                        display_name = f"{member_part} - {orig_name}"
                    else:
                        display_name = orig_name
                else:
                    display_name = member_part or 'Bilinmeyen Paket'

                base_pkg['name'] = display_name
                sub_for_card['package'] = base_pkg

                # Determine active state and optional schedule summary like PackagesTab
                is_active = (s.get('status') == 'active')
                schedule_summary = None
                try:
                    plan = s.get('package', {}).get('plan', {})
                    if plan and plan.get('access_type') == 'SESSION_BASED':
                        schedule_summary = self._format_schedule_summary(s.get('class_events', []))
                except Exception:
                    schedule_summary = None

                card = PackageCard(container, sub_for_card, is_active=is_active, on_click=make_onclick(s), on_delete=lambda sub=s: self._confirm_and_delete(sub), schedule_summary=schedule_summary)
                card.pack(fill="x", pady=(0, 6), padx=6)

                # Make the whole card clickable (bind both frame and children)
                # Avoid double-binding when the PackageCard already attaches
                # the click handler for active cards (PackageCard binds clicks
                # when `is_active` and `on_click` are provided).
                if not is_active:
                    try:
                        card.bind("<Button-1>", lambda e, sub=s: self._open_package_detail(sub))
                        card.configure(cursor="hand2")
                        for child in card.winfo_children():
                            try:
                                # Skip binding buttons (delete button) so their click
                                # handlers don't also trigger the detail-open binding.
                                if isinstance(child, ctk.CTkButton):
                                    continue
                                child.bind("<Button-1>", lambda e, sub=s: self._open_package_detail(sub))
                                child.configure(cursor="hand2")
                            except Exception:
                                pass
                    except Exception:
                        pass

        except Exception:
            ctk.CTkLabel(self.list_frame, text=_("Veri yüklenemedi."), text_color="red").pack(pady=12)

    def _open_package_detail(self, subscription: dict):
        """Open package detail dialog for given subscription.

        This attempts to import and instantiate `PackageDetailDialog` from
        `desktop.ui.views.dialogs.package_detail_dialog`. If unavailable,
        shows a simple fallback window with basic information.
        """
        try:
            from desktop.ui.views.dialogs.package_detail_dialog import PackageDetailDialog

            dlg = PackageDetailDialog(self.master, self.api_client, subscription)
            if hasattr(dlg, "show") and callable(dlg.show):
                dlg.show()
            else:
                try:
                    dlg.grab_set()
                except Exception:
                    pass
        except Exception:
            # Fallback: basic Toplevel with json-ish subscription summary
            top = ctk.CTkToplevel(self)
            top.title(_("Paket Detayı"))
            text = ctk.CTkLabel(top, text=str(subscription), wraplength=600)
            text.pack(padx=12, pady=12)

    def _confirm_and_delete(self, subscription: dict):
        """Confirm with a messagebox and delete subscription via API (same as PackagesTab).

        Uses `/api/v1/sales/subscriptions/{id}` and refreshes on success.
        """
        sid = subscription.get('id') or subscription.get('subscription_id') or subscription.get('subscriptionId') or subscription.get('_id')
        if not sid:
            messagebox.showerror(_('Hata'), _('Abonelik kimliği bulunamadı.'))
            return

        if not messagebox.askyesno(_('Onay'), _('Bu aboneliği silmek istediğinize emin misiniz?\n(Bağlı ödemeler de silinecektir)')):
            return

        try:
            self.api_client.delete(f"/api/v1/sales/subscriptions/{sid}")
            messagebox.showinfo(_('Başarılı'), _('Abonelik silindi.'))
            try:
                self.refresh()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror(_('Hata'), _('Silme işlemi başarısız: {}').format(e))
