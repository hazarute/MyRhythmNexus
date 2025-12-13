import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Any, Callable
from desktop.core.ui_utils import safe_grab, bring_to_front_and_modal

class UpdateDialog:
    """Dialog to show update information and handle user action."""

    def __init__(self, update_info: Dict[str, Any], on_update_callback: Callable[[Dict[str, Any], Callable], bool]):
        self.update_info = update_info
        self.on_update_callback = on_update_callback
        self.update_now = False

    def show(self) -> bool:
        """Show the dialog and return True if update was initiated."""
        dialog = ctk.CTkToplevel()
        dialog.title("Güncelleme Mevcut")
        dialog.geometry("500x400")
        dialog.resizable(False, False)

        # Make dialog transient and modal / focused using central helper
        bring_to_front_and_modal(dialog, None)

        title_label = ctk.CTkLabel(
            dialog,
            text=f"Yeni Sürüm Mevcut: v{self.update_info['version']}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(20, 10))

        changelog_frame = ctk.CTkScrollableFrame(dialog, width=450, height=200)
        changelog_frame.pack(pady=(0, 20), padx=20)

        changelog_text = ctk.CTkLabel(
            changelog_frame,
            text=self.update_info.get('changelog', 'Değişiklik günlüğü bulunamadı'),
            wraplength=400,
            justify="left"
        )
        changelog_text.pack(pady=10, padx=10)

        progress_bar = ctk.CTkProgressBar(dialog, width=400)
        progress_bar.pack(pady=(0, 20))
        progress_bar.pack_forget()

        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=(0, 20))

        def on_update():
            self.update_now = True
            update_button.configure(state="disabled", text="İndiriliyor...")
            skip_button.configure(state="disabled")
            progress_bar.pack(pady=(0, 20))

            def progress_callback(progress):
                progress_bar.set(progress / 100)

            # Call the callback provided by the manager/controller
            success = self.on_update_callback(self.update_info, progress_callback)

            if success:
                messagebox.showinfo("Başarılı", "Güncelleme tamamlandı! Uygulama yeniden başlatılacak.")
                dialog.destroy()
            else:
                messagebox.showerror("Hata", "Güncelleme başarısız oldu.")
                update_button.configure(state="normal", text="Şimdi Güncelle")
                skip_button.configure(state="normal")
                progress_bar.pack_forget()

        def on_skip():
            dialog.destroy()

        update_button = ctk.CTkButton(
            button_frame,
            text="Şimdi Güncelle",
            command=on_update
        )
        update_button.pack(side="left", padx=(0, 10))

        skip_button = ctk.CTkButton(
            button_frame,
            text="Daha Sonra",
            command=on_skip,
            fg_color="transparent",
            border_width=2
        )
        skip_button.pack(side="left")

        dialog.wait_window()
        return self.update_now
