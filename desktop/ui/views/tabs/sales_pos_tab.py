import customtkinter as ctk
from desktop.core.locale import _
from desktop.core.api_client import ApiClient
from desktop.ui.components.salespostab import (
    ClassEventScheduler,
    MemberSelector,
    PaymentDetails,
    DateSelector,
    PackageSelector,
    SubmissionHandler,
)
from tkinter import messagebox
from datetime import datetime, timedelta, date
from typing import Optional


class SalesPOSTab(ctk.CTkFrame):
    """POS (Point of Sale) screen for creating new subscriptions"""
    
    def __init__(self, parent, api_client: ApiClient):
        super().__init__(parent, fg_color="transparent")
        self.api_client = api_client
        
        # State variables
        self.packages = []
        self.selected_member = None
        self.start_date = date.today()
        self.content_scroll = None
        self.class_event_scheduler = None
        
        # Components
        self.member_selector: Optional[MemberSelector] = None
        self.payment_details: Optional[PaymentDetails] = None
        self.date_selector: Optional[DateSelector] = None
        self.package_selector: Optional[PackageSelector] = None
        
        # Handler
        self.submission_handler = SubmissionHandler(self.api_client)
        
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left Side: Member Selection (using MemberSelector component)
        self.frame_left = ctk.CTkFrame(main_container, corner_radius=15)
        self.frame_left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.member_selector = MemberSelector(self.frame_left, on_search_callback=self._search_members_api)
        self.member_selector.pack(fill="both", expand=True)
        
        # Right Side: Package & Payment
        self.frame_right = ctk.CTkFrame(main_container, corner_radius=15)
        self.frame_right.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Header with icon
        header_right = ctk.CTkFrame(self.frame_right, fg_color="#6D28D9", corner_radius=10, height=60)
        header_right.pack(fill="x", padx=15, pady=15)
        header_right.pack_propagate(False)
        
        ctk.CTkLabel(header_right, text=_("💳 Paket ve Ödeme"), 
                    font=("Roboto", 20, "bold"), 
                    text_color="white").pack(expand=True)
        
        # Content scrollable area
        self.content_scroll = ctk.CTkScrollableFrame(self.frame_right, fg_color="transparent")
        self.content_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Package Selection Card (using PackageSelector component)
        self.package_selector = PackageSelector(self.content_scroll, 
                                               api_client=self.api_client,
                                               on_select=self._on_package_select_callback)
        self.package_selector.pack(fill="x", pady=(0, 15))
        
        # Class Event Toggle - kontrolü seans bazlı pakette özel ders zamanlaması yapılıp yapılmayacağını belirler
        # SESSION_BASED paketler için: Ders zamanlaması yapabilir (opsiyonel)
        # TIME_BASED paketler için: Ders zamanlaması yapılmaz (sınırsız katılım zaten otomatik)
        self.enable_class_events = ctk.BooleanVar(value=False)
        self.class_event_toggle_frame = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
        # Always show the checkbox
        
        self.checkbox = ctk.CTkCheckBox(
            self.class_event_toggle_frame,
            text=_("📚 Özel Ders Zamanlaması Ekle"),
            variable=self.enable_class_events,
            font=("Roboto", 16, "bold"),
            text_color="white",
            command=self._toggle_class_events
        )
        self.checkbox.pack(anchor="w", padx=0, pady=0)
        self.class_event_toggle_frame.pack(fill="x", pady=(0, 15))
        
        # Price Override Toggle
        self.enable_price_override = ctk.BooleanVar(value=False)
        self.price_override_frame = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
        
        self.price_override_checkbox = ctk.CTkCheckBox(
            self.price_override_frame,
            text=_("💰 Mevcut Abonelik Ücretini Değiştir"),
            variable=self.enable_price_override,
            font=("Roboto", 16, "bold"),
            text_color="white",
            command=self._toggle_price_override
        )
        self.price_override_checkbox.pack(anchor="w", padx=0, pady=(0, 5))
        
        # Price override input (initially hidden)
        self.price_override_input = ctk.CTkEntry(
            self.price_override_frame,
            placeholder_text=_("Yeni fiyat giriniz (TL)"),
            font=("Roboto", 14),
            height=40
        )
        # Don't pack initially - will be shown when checkbox is enabled
        
        self.price_override_frame.pack(fill="x", pady=(0, 15))
        
        # Date Selection Card (using DateSelector component)
        self.date_selector = DateSelector(self.content_scroll, on_date_change=self.on_date_change)
        self.date_selector.pack(fill="x", pady=(0, 15))
        
        # Payment Details Card (using PaymentDetails component)
        self.payment_details = PaymentDetails(self.content_scroll, default_amount=0)
        self.payment_details.pack(fill="x", pady=(0, 15))
        
        # Class Event Scheduler (initially hidden, shown for SESSION_BASED packages)
        self.class_event_scheduler = ClassEventScheduler(self.content_scroll, plan={})
        # Don't pack yet - will be shown when SESSION_BASED package is selected and checkbox is enabled
        
        # Submit Button
        submit_frame = ctk.CTkFrame(self.frame_right, fg_color="transparent")
        submit_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkButton(submit_frame, text=_("✅ Satışı Tamamla"), 
                     fg_color="#6D28D9", hover_color="#6D28D9", 
                     height=50, corner_radius=10,
                     font=("Roboto", 16, "bold"),
                     command=self.submit_sale).pack(fill="x")
        
        # Data Loading
        self.load_packages()
        self.load_initial_members()
    
    def refresh(self):
        """Refresh the POS tab content"""
        self.load_packages()
        self.load_initial_members()
    
    def load_initial_members(self):
        """Load all members when the page loads"""
        try:
            all_members = self.api_client.get("/api/v1/members/") or []
            if self.member_selector and all_members:
                self.member_selector.members = all_members
                self.member_selector._display_members(all_members)
        except Exception as e:
            print(f"Error loading initial members: {e}")
    
    def _search_members_api(self, term: str):
        """API callback for MemberSelector search"""
        try:
            params = {}
            if term:
                params["search"] = term
            return self.api_client.get("/api/v1/members/", params=params) or []
        except Exception as e:
            messagebox.showerror(_("Hata"), _("Arama hatası: {}").format(e))
            return []
    
    def load_packages(self):
        """Load available packages via PackageSelector"""
        if self.package_selector:
            self.package_selector.load_packages()
            # Load packages list for internal use
            self.packages = self.package_selector.packages
    
    def _on_package_select_callback(self, pkg: dict):
        """Called when package is selected in PackageSelector"""
        if not pkg:
            return
        
        # Update internal packages list
        if not hasattr(self, 'packages'):
            self.packages = []
        if self.package_selector:
            self.packages = self.package_selector.packages
        
        # Update payment details with new price
        price = pkg.get("price", 0)
        try:
            price = float(price) if price else 0.0
        except (ValueError, TypeError):
            price = 0.0
        
        if self.payment_details:
            self.payment_details.set_default_amount(price)
        
        # Update end date display based on plan
        plan = pkg.get("plan", {})
        cycle_period = plan.get("cycle_period", "MONTHLY")
        repeat_weeks = plan.get("repeat_weeks", 4) or 4

        # Check if SESSION_BASED
        access_type = plan.get("access_type", "SESSION_BASED")
        is_session_based = access_type == "SESSION_BASED"

        if self.date_selector:
            self.date_selector.set_end_date_from_plan(cycle_period, repeat_weeks, is_session_based)
        
        if is_session_based:
            # Enable checkbox and prepare class event scheduler
            self.checkbox.configure(state="normal")
            
            # Update ClassEventScheduler with plan info
            if self.class_event_scheduler:
                self.class_event_scheduler.plan = plan
                self.class_event_scheduler.selected_repeat_weeks = plan.get('repeat_weeks', 1) or 1
                self.class_event_scheduler.lbl_repeat_weeks.configure(text=str(self.class_event_scheduler.selected_repeat_weeks))
            
            # Reset checkbox to unchecked
            self.enable_class_events.set(False)
            
            # Load instructors
            try:
                if self.class_event_scheduler:
                    instructors = self.api_client.get("/api/v1/staff/instructors")
                    if instructors:
                        self.class_event_scheduler.load_instructors(instructors)
            except Exception as e:
                print(f"Error loading instructors: {e}")
        else:
            # Disable checkbox for non-SESSION_BASED packages
            self.checkbox.configure(state="disabled")
            
            # Hide class event scheduler
            if self.class_event_scheduler and self.class_event_scheduler.winfo_manager() != "":
                self.class_event_scheduler.pack_forget()
            
            self.enable_class_events.set(False)
    
    def _toggle_class_events(self):
        """Toggle the visibility of ClassEventScheduler based on checkbox"""
        if self.enable_class_events.get() and self.class_event_scheduler:
            # Show ClassEventScheduler
            if self.class_event_scheduler.winfo_manager() == "":
                self.class_event_scheduler.pack(fill="x", pady=(0, 15), after=self.payment_details)
        elif self.class_event_scheduler:
            # Hide ClassEventScheduler
            if self.class_event_scheduler.winfo_manager() != "":
                self.class_event_scheduler.pack_forget()
                # Reset class events selection
                self.class_event_scheduler.reset()
    
    def _toggle_price_override(self):
        """Toggle the visibility of price override input based on checkbox"""
        if self.enable_price_override.get():
            # Show price input
            if self.price_override_input.winfo_manager() == "":
                self.price_override_input.pack(fill="x", pady=(5, 0))
        else:
            # Hide price input and clear value
            if self.price_override_input.winfo_manager() != "":
                self.price_override_input.pack_forget()
            self.price_override_input.delete(0, "end")
    
    def on_package_select(self, choice=None):
        """Legacy method - kept for backward compatibility"""
        pass
    
    def on_date_change(self, start_date: date, end_date: date):
        """Called when date selector changes (dates updated)"""
        # DateSelector handles date display internally
        # This is a callback for any future actions needed on date change
        pass
    
    def submit_sale(self):
        """Submit the sale and create subscription using SubmissionHandler"""
        # Get data from components
        member = self.member_selector.get_selected_member() if self.member_selector else None
        pkg = self.package_selector.get_selected_package() if self.package_selector else None
        payment_data = self.payment_details.get_payment_data() if self.payment_details else None
        start_date_obj = self.date_selector.get_start_date() if self.date_selector else None
        
        # Get class events if SESSION_BASED
        class_events = None
        if pkg and self.class_event_scheduler:
            plan = pkg.get("plan", {})
            access_type = plan.get("access_type", "SESSION_BASED")
            if access_type == "SESSION_BASED":
                class_events = self.class_event_scheduler.get_class_events_payload()
        
        # Get price override if enabled
        price_override = None
        if self.enable_price_override.get():
            try:
                price_text = self.price_override_input.get().strip()
                if price_text:
                    price_override = float(price_text)
            except ValueError:
                messagebox.showerror(_("Hata"), _("Geçersiz fiyat formatı. Lütfen sayı giriniz."))
                return
        
        # Use handler to submit
        success = self.submission_handler.submit_sale(
            member=member,
            package=pkg,
            payment_data=payment_data,
            start_date=start_date_obj,
            class_events=class_events,
            price_override=price_override
        )
        
        if success:
            # Reset UI after successful submission
            self._reset_all_fields()
    
    def _reset_all_fields(self):
        """Reset all UI fields after successful sale"""
        # Reset components
        if self.member_selector:
            self.member_selector.reset()
            # Reload members after reset so the list is not empty
            self.load_initial_members()
        if self.payment_details:
            self.payment_details.reset()
        
        # Reset state
        self.selected_member = None
        
        # Date
        if self.date_selector:
            self.date_selector.reset()
        
        # Package
        if self.package_selector:
            self.package_selector.reset()
        
        # Class event scheduler
        if self.class_event_scheduler:
            self.class_event_scheduler.reset()
        
        # Price override
        self.enable_price_override.set(False)
        self.price_override_input.delete(0, "end")
        if self.price_override_input.winfo_manager() != "":
            self.price_override_input.pack_forget()
