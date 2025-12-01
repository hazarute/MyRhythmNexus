import customtkinter as ctk
from typing import Callable
from desktop.core.api_client import ApiClient

class LoginWindow(ctk.CTkFrame):
    def __init__(self, master, api_client: ApiClient, on_login_success: Callable):
        super().__init__(master)
        self.api_client = api_client
        self.on_login_success = on_login_success

        self.pack(fill="both", expand=True)

        self.frame = ctk.CTkFrame(self)
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        self.label_title = ctk.CTkLabel(self.frame, text="MyRhythmNexus Admin", font=("Roboto", 24))
        self.label_title.pack(pady=20, padx=40)

        self.entry_username = ctk.CTkEntry(self.frame, placeholder_text="Kullanıcı Adı")
        self.entry_username.pack(pady=10, padx=20)
        self.entry_username.bind("<Return>", lambda e: self.entry_password.focus())

        self.entry_password = ctk.CTkEntry(self.frame, placeholder_text="Şifre", show="*")
        self.entry_password.pack(pady=10, padx=20)
        self.entry_password.bind("<Return>", lambda e: self.handle_login())

        self.button_login = ctk.CTkButton(self.frame, text="Giriş Yap", command=self.handle_login)
        self.button_login.pack(pady=20, padx=20)

        self.label_error = ctk.CTkLabel(self.frame, text="", text_color="red")
        self.label_error.pack(pady=5)

    def handle_login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()

        if not username or not password:
            self.label_error.configure(text="Lütfen tüm alanları doldurun.")
            return

        self.button_login.configure(state="disabled", text="Giriş Yapılıyor...")
        self.update()

        # In a real app, run this in a thread to avoid freezing
        success = self.api_client.login(username, password)

        if success:
            self.on_login_success()
        else:
            self.label_error.configure(text="Giriş başarısız. Bilgileri kontrol edin.")
            self.button_login.configure(state="normal", text="Giriş Yap")
