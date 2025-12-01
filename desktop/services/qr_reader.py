import time
import customtkinter as ctk

class QrReaderService:
    def __init__(self, master_window, on_scan_callback):
        self.master = master_window
        self.on_scan = on_scan_callback
        self.buffer = ""
        self.last_key_time = 0
        # Threshold in seconds. Scanners usually send chars within 10-50ms.
        # Humans usually type slower than 50ms per char consistently.
        self.TIMEOUT = 0.1 

        # Bind to the top-level window to capture all key presses
        self.master.bind("<Key>", self.on_key_press, add="+")

    def on_key_press(self, event):
        # Ignore modifier keys or special keys that don't produce char
        if not event.char and event.keysym != "Return":
            return

        current_time = time.time()
        
        # If too much time passed since last key, reset buffer (assume new input stream)
        if current_time - self.last_key_time > self.TIMEOUT:
            self.buffer = ""
            
        self.last_key_time = current_time
        
        if event.keysym == "Return":
            # If we have a buffer and it was typed fast, assume it's a scan
            if self.buffer and len(self.buffer) > 3: # Minimum length for a token
                # Trigger callback
                self.on_scan(self.buffer)
                self.buffer = ""
        else:
            # Append character
            if event.char and event.char.isprintable():
                self.buffer += event.char
