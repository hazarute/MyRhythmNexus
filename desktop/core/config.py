import os
import json
from pathlib import Path
from typing import Any, Dict, Optional


APP_DIR_NAME = "MyRhythmNexus"
CONFIG_FILENAME = "config.json"


def get_app_config_dir() -> Path:
    """Return the appropriate app config directory for the current OS/user.
    Windows: %APPDATA%\\MyRhythmNexus
    macOS/Linux: $XDG_CONFIG_HOME or ~/.config/MyRhythmNexus
    """
    if os.name == 'nt':
        base = os.getenv('APPDATA') or Path.home() / 'AppData' / 'Roaming'
    else:
        base = os.getenv('XDG_CONFIG_HOME') or (Path.home() / '.config')
    cfg_dir = Path(base) / APP_DIR_NAME
    try:
        cfg_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # If we can't create it, fall back to home directory
        cfg_dir = Path.home() / f'.{APP_DIR_NAME.lower()}'
        cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir


def get_config_path() -> Path:
    return get_app_config_dir() / CONFIG_FILENAME


def load_config() -> Dict[str, Any]:
    cfg_path = get_config_path()
    if not cfg_path.exists():
        return {"backend_urls": [], "settings": {}}
    try:
        with open(cfg_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"backend_urls": [], "settings": {}}


def save_config(cfg: Dict[str, Any]) -> None:
    cfg_path = get_config_path()
    try:
        with open(cfg_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        # Best-effort only
        pass


def get_backend_url() -> Optional[str]:
    """Return the primary backend URL from config, or None if not set."""
    cfg = load_config()
    urls = cfg.get('backend_urls') or []
    if isinstance(urls, list) and urls:
        return urls[0]
    # fallback to explicit key
    return cfg.get('backend_url')


def add_backend_url(url: str) -> None:
    cfg = load_config()
    urls = cfg.get('backend_urls') or []
    if url not in urls:
        urls.append(url)
        cfg['backend_urls'] = urls
        save_config(cfg)


def get_license_server_url() -> Optional[str]:
    """Return license server url from config if present, otherwise None."""
    cfg = load_config()
    return cfg.get('license_server_url')


def save_license_server_url(url: str) -> None:
    cfg = load_config()
    cfg['license_server_url'] = url
    save_config(cfg)

# ---------------------------------------------------------------------------
# Backwards-compatible DesktopConfig class
# Other parts of the desktop app reference DesktopConfig; keep it here
# but reuse the functions above for config storage location.
# ---------------------------------------------------------------------------

class DesktopConfig:
    """Desktop application configuration"""

    # Backend URL - Production'da değiştirilebilir
    BACKEND_URL = os.getenv("RHYTHM_NEXUS_BACKEND_URL", "http://localhost:8000")
    # License Server URL
    LICENSE_SERVER_URL = os.getenv("RHYTHM_NEXUS_LICENSE_SERVER_URL", "http://localhost:8001/api/v1")

    # App settings
    APP_NAME = "MyRhythmNexus Desktop"
    VERSION = "1.0.6"
    # Update check interval in minutes (default 60 = hourly)
    CHECK_UPDATE_INTERVAL_MINUTES = 60

    # UI Settings
    WINDOW_SIZE = "1200x800"
    THEME = "dark"  # dark, light, system

    # Paths: reuse helper to select platform-appropriate config dir
    APP_DATA_DIR = get_app_config_dir()
    CONFIG_FILE = get_config_path()
    LOG_FILE = APP_DATA_DIR / "app.log"

    @classmethod
    def ensure_app_data_dir(cls):
        """Ensure application data directory exists"""
        cls.APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _load_config(cls) -> dict:
        try:
            import json
            if cls.CONFIG_FILE.exists():
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return {}

    @classmethod
    def _save_config(cls, config: dict):
        cls.ensure_app_data_dir()
        import json
        with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

    @classmethod
    def get_value(cls, key: str, default=None):
        config = cls._load_config()
        return config.get(key, default)

    @classmethod
    def set_value(cls, key: str, value):
        config = cls._load_config()
        config[key] = value
        cls._save_config(config)

    @classmethod
    def save_backend_url(cls, url: str):
        """Save backend URL to config file"""
        cls.set_value("backend_url", url)

    @classmethod
    def save_license_server_url(cls, url: str):
        """Save license server URL to config file"""
        cls.set_value("license_server_url", url)

    @classmethod
    def load_backend_url(cls) -> str:
        """Load backend URL from config file"""
        # Support packaged config which writes a `backend_urls` list
        try:
            cfg = cls._load_config()
            urls = cfg.get('backend_urls') or []
            if isinstance(urls, list) and urls:
                return urls[0]
            # fallback to single-key `backend_url` for backward compatibility
            val = cfg.get('backend_url')
            if val:
                return val
        except Exception:
            pass
        return cls.BACKEND_URL

    @classmethod
    def load_license_server_url(cls) -> str:
        """Load license server URL from config file or fallback to default."""
        # Prefer explicit config value (lowercase key), then support legacy
        # uppercase ENV-style key written by packagers, then fall back to
        # the class-level default which itself reads the RHYTHM_NEXUS_LICENSE_SERVER_URL env var.
        cfg_val = cls.get_value("license_server_url")
        if cfg_val:
            return cfg_val
        cfg_val_upper = cls.get_value("LICENSE_SERVER_URL")
        if cfg_val_upper:
            return cfg_val_upper
        return cls.LICENSE_SERVER_URL

    @classmethod
    def get_language(cls) -> str:
        """Get user's preferred language (tr or en)"""
        lang = cls.get_value("language", "tr")
        return lang if lang in ["tr", "en"] else "tr"

    @classmethod
    def set_language(cls, language: str):
        """Save user's language preference"""
        if language in ["tr", "en"]:
            cls.set_value("language", language)