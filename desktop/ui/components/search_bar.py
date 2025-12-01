import customtkinter as ctk
from typing import Callable, Optional, Dict, Any

class SearchBar(ctk.CTkFrame):
    """
    Reusable search bar component with debouncing
    
    Usage:
        search_bar = SearchBar(
            master,
            placeholder="🔍 Search...",
            on_search=lambda term: load_data(term),
            button_text="🔎 Search"
        )
        search_bar.pack(side="left", fill="x", expand=True)
    """
    
    def __init__(self, master, placeholder: str = "🔍 Ara...", 
                 on_search: Optional[Callable[[str], None]] = None,
                 button_text: str = "🔎 Ara",
                 width: int = 400, height: int = 40,
                 fg_color: str = "transparent"):
        super().__init__(master, fg_color=fg_color)
        
        self.on_search = on_search
        self.search_timer = None
        self.last_search_term = ""
        
        # Entry field
        self.entry = ctk.CTkEntry(
            self, 
            placeholder_text=placeholder, 
            height=height, 
            font=("Roboto", 14)
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Bind events
        self.entry.bind("<KeyRelease>", self._on_key_release)
        self.entry.bind("<Return>", lambda e: self.search_immediate())
        
        # Search button
        self.btn_search = ctk.CTkButton(
            self,
            text=button_text,
            command=self.search_immediate,
            width=100,
            height=height,
            fg_color="#3B8ED0",
            hover_color="#2E7AB8",
            font=("Roboto", 14, "bold")
        )
        self.btn_search.pack(side="right")
    
    def _on_key_release(self, event):
        """Handle key release with debouncing"""
        if self.search_timer:
            self.after_cancel(self.search_timer)
        
        search_term = self.entry.get()
        current_length = len(search_term)
        
        # Delay hesaplama: 3+ karakter -> 500ms, 1-2 karakter -> 800ms
        delay = 500 if current_length >= 3 else 800
        
        # Boşsa hemen ara
        if current_length == 0:
            self.search_immediate()
            return
        
        # Yeni timer başlat
        self.search_timer = self.after(delay, self.search_immediate)
    
    def search_immediate(self):
        """Immediately search with current term"""
        if self.search_timer:
            self.after_cancel(self.search_timer)
        
        search_term = self.entry.get()
        
        # Callback'i çağır
        if self.on_search:
            self.on_search(search_term)
    
    def get_search_term(self) -> str:
        """Get current search term"""
        return self.entry.get()
    
    def set_search_term(self, term: str):
        """Set search term"""
        self.entry.delete(0, "end")
        self.entry.insert(0, term)
    
    def clear(self):
        """Clear search field"""
        self.entry.delete(0, "end")
