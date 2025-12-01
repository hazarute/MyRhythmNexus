"""
MemberSelector Component
━━━━━━━━━━━━━━━━━━━━━━━
Modular component for member search and selection.
Handles member list display, search, and selection state.
"""

import customtkinter as ctk
from typing import Dict, List, Optional, Callable
from desktop.ui.components.search_bar import SearchBar


class MemberSelector(ctk.CTkFrame):
    """
    Standalone component for member search and selection.
    
    Provides:
    - Member search input with search button
    - Scrollable member list display
    - Selected member indicator
    - Data retrieval via get_selected_member()
    - Search callback for API integration
    
    Usage:
        selector = MemberSelector(parent, on_search_callback=my_api_search_func)
        selector.pack(fill="both", expand=True)
        
        # On button click or elsewhere:
        selected = selector.get_selected_member()
    """
    
    def __init__(self, parent, on_search_callback: Optional[Callable] = None, **kwargs):
        """
        Initialize MemberSelector component.
        
        Args:
            parent: Parent frame
            on_search_callback: Callable(search_term) that returns list of members
                               {id, first_name, last_name, phone_number, ...}
        """
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        # State
        self.members: List[Dict] = []
        self.selected_member: Optional[Dict] = None
        self.member_buttons: Dict[str, ctk.CTkFrame] = {}
        self.on_search_callback = on_search_callback
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build the component UI"""
        # Header
        header = ctk.CTkFrame(self, fg_color="#3B8ED0", corner_radius=10, height=60)
        header.pack(fill="x", padx=15, pady=15)
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="👥 Üye Seçimi", 
                    font=("Roboto", 20, "bold"), 
                    text_color="white").pack(expand=True)
        
        # Search section
        search_container = ctk.CTkFrame(self, fg_color="transparent")
        search_container.pack(fill="x", padx=15, pady=(0, 10))
        
        self.search_bar = SearchBar(
            search_container,
            placeholder="🔍 İsim, soyisim veya telefon...",
            on_search=self.search_members,
            button_text="Ara",
            height=40
        )
        self.search_bar.pack(side="left", fill="x", expand=True)
        
        # Members list
        self.list_members = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_members.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Selected member indicator
        self.selected_member_card = ctk.CTkFrame(
            self, 
            fg_color=("#E8F5E9", "#1B5E20"), 
            corner_radius=10, 
            height=60
        )
        self.selected_member_card.pack(fill="x", padx=15, pady=(0, 15))
        self.selected_member_card.pack_propagate(False)
        
        self.lbl_selected_member = ctk.CTkLabel(
            self.selected_member_card, 
            text="Seçili Üye: Henüz seçilmedi", 
            font=("Roboto", 14, "bold"),
            text_color=("gray", "#4CAF50")
        )
        self.lbl_selected_member.pack(expand=True)
    
    def search_members(self, term: str = ""):
        """Search for members using the search term"""
        if not self.on_search_callback:
            print("Warning: on_search_callback not set")
            return
        
        try:
            self.members = self.on_search_callback(term)
            self._display_members(self.members)
        except Exception as e:
            print(f"Error searching members: {e}")
    
    def _display_members(self, members: List[Dict]):
        """Display member list in the scrollable frame"""
        # Clear existing
        for widget in self.list_members.winfo_children():
            widget.destroy()
        self.member_buttons = {}
        
        if not members:
            empty_frame = ctk.CTkFrame(self.list_members, fg_color="transparent")
            empty_frame.pack(expand=True)
            ctk.CTkLabel(empty_frame, text="🔍", 
                       font=("Segoe UI Emoji", 48)).pack(pady=(20, 10))
            ctk.CTkLabel(empty_frame, text="Sonuç bulunamadı", 
                       font=("Roboto", 16),
                       text_color=("gray50", "gray60")).pack()
            return
        
        # Display members
        for m in members:
            self._create_member_card(m)
    
    def _create_member_card(self, member: Dict):
        """Create a modern clickable member card"""
        # Main card container
        card = ctk.CTkFrame(
            self.list_members, 
            corner_radius=12, 
            fg_color=("#F5F5F5", "#2B2B2B"), 
            border_width=2,
            border_color=("#DDDDDD", "#3A3A3A"),
            cursor="hand2"
        )
        card.pack(fill="x", pady=8, padx=5)
        
        # Make entire card clickable
        card.bind("<Button-1>", lambda e, m=member: self.select_member(m))
        
        # Left section - Member info
        left_frame = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        left_frame.pack(side="left", fill="both", expand=True, padx=20, pady=15)
        left_frame.bind("<Button-1>", lambda e, m=member: self.select_member(m))
        
        # Name and status row
        name_row = ctk.CTkFrame(left_frame, fg_color="transparent", cursor="hand2")
        name_row.pack(anchor="w")
        name_row.bind("<Button-1>", lambda e, m=member: self.select_member(m))
        
        # Name
        name = f"{member['first_name']} {member['last_name']}"
        lbl_name = ctk.CTkLabel(
            name_row, 
            text=f"👤 {name}", 
            font=("Roboto", 16, "bold"), 
            anchor="w", 
            cursor="hand2"
        )
        lbl_name.pack(side="left", padx=(0, 15))
        lbl_name.bind("<Button-1>", lambda e, m=member: self.select_member(m))
        
        # Status badge (if available)
        if 'is_active' in member:
            is_active = member.get('is_active', True)
            status_text = "✅ Aktif" if is_active else "⛔ Pasif"
            status_color = ("#2CC985", "#229966") if is_active else ("#E74C3C", "#C0392B")
            
            lbl_status = ctk.CTkLabel(
                name_row, 
                text=status_text,
                font=("Roboto", 12, "bold"),
                text_color=status_color, 
                cursor="hand2"
            )
            lbl_status.pack(side="left")
            lbl_status.bind("<Button-1>", lambda e, m=member: self.select_member(m))
        
        # Contact info row
        info_frame = ctk.CTkFrame(left_frame, fg_color="transparent", cursor="hand2")
        info_frame.pack(anchor="w", pady=(6, 0))
        info_frame.bind("<Button-1>", lambda e, m=member: self.select_member(m))
        
        # Email
        email = member.get('email', '')
        if email:
            lbl_email = ctk.CTkLabel(
                info_frame, 
                text=f"📧 {email}", 
                font=("Roboto", 12),
                text_color=("#555555", "#AAAAAA"),
                anchor="w", 
                cursor="hand2"
            )
            lbl_email.pack(side="left", padx=(0, 20))
            lbl_email.bind("<Button-1>", lambda e, m=member: self.select_member(m))
        
        # Phone
        phone = member.get('phone_number', '')
        if phone:
            lbl_phone = ctk.CTkLabel(
                info_frame, 
                text=f"📞 {phone}", 
                font=("Roboto", 12),
                text_color=("#555555", "#AAAAAA"),
                anchor="w", 
                cursor="hand2"
            )
            lbl_phone.pack(side="left")
            lbl_phone.bind("<Button-1>", lambda e, m=member: self.select_member(m))
        
        # Right section - Selection indicator
        right_frame = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        right_frame.pack(side="right", padx=20, pady=15)
        right_frame.bind("<Button-1>", lambda e, m=member: self.select_member(m))
        
        # Selection button
        btn_select = ctk.CTkButton(
            right_frame, 
            text="👆 Seç", 
            width=80, 
            height=40,
            fg_color="#3B8ED0", 
            hover_color="#2E7AB8",
            font=("Roboto", 14, "bold"),
            command=lambda m=member: self.select_member(m)
        )
        btn_select.pack()
        
        self.member_buttons[member['id']] = card
    
    def select_member(self, member: Dict):
        """Select a member and update UI"""
        self.selected_member = member
        self.lbl_selected_member.configure(
            text=f"✅ {member['first_name']} {member['last_name']}", 
            text_color=("white", "white")
        )
        self.selected_member_card.configure(fg_color=("#2CC985", "#1B5E20"))
        
        # Highlight selected card with border
        for uid, member_card in self.member_buttons.items():
            if uid == member['id']:
                member_card.configure(
                    fg_color=("#E8F5E9", "#1B5E20"), 
                    border_width=3, 
                    border_color="#2CC985"
                )
            else:
                member_card.configure(
                    fg_color=("#F5F5F5", "#2B2B2B"), 
                    border_width=2,
                    border_color=("#DDDDDD", "#3A3A3A")
                )
    
    def get_selected_member(self) -> Optional[Dict]:
        """Get the selected member or None"""
        return self.selected_member
    
    def reset(self):
        """Reset selection state"""
        self.selected_member = None
        self.lbl_selected_member.configure(
            text="Seçili Üye: Henüz seçilmedi", 
            text_color=("gray", "#4CAF50")
        )
        self.selected_member_card.configure(fg_color=("#E8F5E9", "#1B5E20"))
        
        # Reset all card borders
        for member_card in self.member_buttons.values():
            member_card.configure(
                fg_color=("#F5F5F5", "#2B2B2B"), 
                border_width=2,
                border_color=("#DDDDDD", "#3A3A3A")
            )
        
        self.search_bar.clear()
        self._display_members([])
