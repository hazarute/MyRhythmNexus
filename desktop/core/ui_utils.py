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


def bring_to_front_and_modal(dialog, parent=None, topmost_duration_ms: int = 50):
    """Bring a dialog to front and make it modal in a cross-platform way.

    Steps:
    - Set transient(parent) if parent is provided to bind window manager behaviour.
    - Lift and focus the dialog.
    - Temporarily set `-topmost` to True then clear it to force z-order.
    - Use `safe_grab()` to attempt `grab_set()` with retries (handles X11/Wayland timing).

    Usage: call this after dialog creation (inside dialog.__init__):
        bring_to_front_and_modal(self, parent)
    """
    try:
        if parent is None:
            parent = getattr(dialog, "master", None)

        if parent:
            try:
                dialog.transient(parent)
            except Exception:
                # Some widget types or platforms may not support transient
                pass

        try:
            dialog.lift()
        except Exception:
            pass

        try:
            dialog.focus_force()
        except Exception:
            pass

        # Short topmost trick to force z-order on Windows and some Linux WMs
        try:
            dialog.attributes('-topmost', True)

            def _clear_topmost():
                try:
                    dialog.attributes('-topmost', False)
                except Exception:
                    pass

            # Schedule clearing the topmost flag shortly after creation
            try:
                dialog.after(topmost_duration_ms, _clear_topmost)
            except Exception:
                # If after() is not available, attempt to clear synchronously later
                pass
        except Exception:
            pass

        # Use safe_grab to attempt modal grab with retries on X11/Wayland
        try:
            safe_grab(dialog)
        except Exception:
            # Fallback to direct grab_set but swallow errors
            try:
                dialog.grab_set()
            except Exception:
                pass

    except Exception:
        # Never let this helper raise — UI code should remain resilient
        return
