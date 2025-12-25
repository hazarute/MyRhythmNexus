import platform
import shutil
import subprocess
import os
import shutil


def _run_cmd(cmd):
    try:
        cp = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return cp.returncode == 0
    except Exception:
        return False


def _boost_and_play(cmd):
    """If PulseAudio/pipewire `pactl` is available, increase volume briefly, play, then restore."""
    pactl = shutil.which("pactl")
    if not pactl:
        return _run_cmd(cmd)

    try:
        # increase volume by 30% (works with pactl)
        subprocess.run([pactl, "set-sink-volume", "@DEFAULT_SINK@", "+30%"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cp = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return_code = cp.returncode == 0
    except Exception:
        return_code = False
    finally:
        try:
            # restore volume
            subprocess.run([pactl, "set-sink-volume", "@DEFAULT_SINK@", "-30%"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    return return_code


def play_success_fallback(widget=None):
    """Play a success sound in a cross-platform way. If `widget` (a Tk widget) is provided,
    call its `bell()` as ultimate fallback.
    """
    system = platform.system()

    if system == "Windows":
        try:
            import winsound
            winsound.Beep(3000, 700)
            return True
        except Exception:
            pass

    if system == "Darwin":
        # macOS: try afplay with system sound
        if shutil.which("afplay"):
            # Use system sound if available
            _run_cmd(["afplay", "/System/Library/Sounds/Glass.aiff"])  # best effort
            return True

    # Linux / other unix-like
    # Prefer paplay (works reliably on many Linux desktops)
    paplay = shutil.which("paplay")
    if paplay:
        candidates = [
            "/usr/share/sounds/freedesktop/stereo/complete.oga",
            "/usr/share/sounds/freedesktop/stereo/complete.wav",
            "/usr/share/sounds/alsa/Front_Center.wav",
        ]
        for c in candidates:
            # Try playing even if file checks are conservative; some systems have links or different perms
            try:
                if os.path.isfile(c) or True:
                    if _boost_and_play([paplay, c]):
                        return True
            except Exception:
                pass

    # Prefer libcanberra CLI as secondary option
    if shutil.which("canberra-gtk-play"):
        _run_cmd(["canberra-gtk-play", "-i", "complete"])  # most distros have theme sounds
        return True

    # Try aplay as fallback
    aplay = shutil.which("aplay")
    if aplay:
        candidates = [
            "/usr/share/sounds/alsa/Front_Center.wav",
        ]
        for c in candidates:
            if os.path.isfile(c):
                _run_cmd([aplay, c])
                return True

    # Last resort: bell via widget
    if widget is not None:
        try:
            widget.bell()
            return True
        except Exception:
            pass

    return False


def play_error_fallback(widget=None):
    """Play an error sound in a cross-platform way."""
    system = platform.system()

    if system == "Windows":
        try:
            import winsound
            try:
                winsound.Beep(400, 400)
                return True
            except Exception:
                try:
                    winsound.MessageBeep(winsound.MB_ICONHAND)
                    return True
                except Exception:
                    pass
        except Exception:
            pass

    if system == "Darwin":
        if shutil.which("afplay"):
            _run_cmd(["afplay", "/System/Library/Sounds/Basso.aiff"])  # best effort
            return True

    # Prefer paplay for error sounds as well
    paplay = shutil.which("paplay")
    if paplay:
        candidates = [
            "/usr/share/sounds/freedesktop/stereo/dialog-warning.oga",
            "/usr/share/sounds/freedesktop/stereo/dialog-error.oga",
            "/usr/share/sounds/freedesktop/stereo/complete.oga",
        ]
        for c in candidates:
            try:
                if os.path.isfile(c) or True:
                    if _boost_and_play([paplay, c]):
                        return True
            except Exception:
                pass

    if shutil.which("canberra-gtk-play"):
        _run_cmd(["canberra-gtk-play", "-i", "dialog-error"])
        return True

    if widget is not None:
        try:
            widget.bell()
            return True
        except Exception:
            pass

    return False
