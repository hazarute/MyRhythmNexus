"""
MemberSelector Component
━━━━━━━━━━━━━━━━━━━━━━━
Modular component for member search and selection.
Handles member list display, search, and selection state.
"""

import customtkinter as ctk
from typing import Dict, List, Optional, Callable


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
        
        self.entry_search = ctk.CTkEntry(
            search_container, 
            placeholder_text="🔍 İsim, soyisim veya telefon...", 
            height=40, 
            font=("Roboto", 13)
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_search.bind("<Return>", lambda e: self.search_members())
        
        ctk.CTkButton(
            search_container, 
            text="Ara", 
            width=80, 
            height=40,
            font=("Roboto", 13, "bold"),
            command=self.search_members
        ).pack(side="left")
        
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
    
    def search_members(self):
        """Search for members using the search term"""
        if not self.on_search_callback:
            print("Warning: on_search_callback not set")
            return
        
        term = self.entry_search.get()
        
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
                       font=("Roboto", 14),
                       text_color="gray").pack()
            return
        
        # Display members
        for m in members:
            self._create_member_card(m)
    
    def _create_member_card(self, member: Dict):
        """Create a clickable member card"""
        member_card = ctk.CTkFrame(
            self.list_members, 
            fg_color=("#FFFFFF", "#2B2B2B"),
            corner_radius=10,
            cursor="hand2"
        )
        member_card.pack(fill="x", pady=5, padx=5)
        
        # Card content
        card_content = ctk.CTkFrame(member_card, fg_color="transparent")
        card_content.pack(fill="x", padx=15, pady=12)
        
        # Member info
        name_label = ctk.CTkLabel(
            card_content, 
            text=f"{member['first_name']} {member['last_name']}", 
            font=("Roboto", 14, "bold"),
            anchor="w"
        )
        name_label.pack(side="left", fill="x", expand=True)
        
        phone_label = ctk.CTkLabel(
            card_content, 
            text=f"📱 {member['phone_number']}", 
            font=("Roboto", 11),
            text_color="gray"
        )
        phone_label.pack(side="right")
        
        # Click event
        for widget in [member_card, card_content, name_label, phone_label]:
            widget.bind("<Button-1>", lambda e, m=member: self.select_member(m))
        
        self.member_buttons[member['id']] = member_card
    
    def select_member(self, member: Dict):
        """Select a member"""
        self.selected_member = member
        self.lbl_selected_member.configure(
            text=f"✅ {member['first_name']} {member['last_name']}", 
            text_color=("white", "white")
        )
        self.selected_member_card.configure(fg_color=("#2CC985", "#1B5E20"))
        
        # Highlight selected card
        for uid, member_card in self.member_buttons.items():
            if uid == member['id']:
                member_card.configure(
                    fg_color=("#E8F5E9", "#1B5E20"), 
                    border_width=2, 
                    border_color="#2CC985"
                )
            else:
                member_card.configure(fg_color=("#FFFFFF", "#2B2B2B"), border_width=0)
    
    def get_selected_member(self) -> Optional[Dict]:
        """Get the selected member or None"""
        return self.selected_member
    
    def reset(self):
        """Reset selection state"""
        self.selected_member = None
        self.lbl_selected_member.configure(
            text="Seçili Üye: Henüz seçilmedi", 
            text_color="gray"
        )
        self.selected_member_card.configure(fg_color=("#E8F5E9", "#1B5E20"))
        self.entry_search.delete(0, "end")
        self._display_members([])
