import typing


def safe_grab(widget, retries: int = 10, delay_ms: int = 50):
    """Try to call `grab_set()` on a Tk/Toplevel widget safely.

    On some X11/Wayland setups the window manager may not have mapped the
    window yet and `grab_set()` raises "grab failed: window not viewable".
    This helper schedules retries using `after()` to wait for the window to
    become viewable without blocking the mainloop.

    Usage:
        from desktop.core.ui_utils import safe_grab
        safe_grab(dialog)
    """

    def _try(attempt=0):
        try:
            widget.grab_set()
        except Exception:
            if attempt < retries:
                try:
                    widget.after(delay_ms, lambda: _try(attempt + 1))
                except Exception:
                    # If widget is already destroyed or doesn't support after,
                    # silently ignore—there's nothing safe we can do.
                    return

    # Schedule first attempt shortly after creation so the window has a
    # chance to map.
    try:
        widget.after(delay_ms, lambda: _try(0))
    except Exception:
        # If the widget doesn't support after (unlikely), try immediate
        # but swallow errors to avoid crashing the app.
        try:
            widget.grab_set()
        except Exception:
            return
