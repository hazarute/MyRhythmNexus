import os
from pathlib import Path

class DesktopConfig:
    """Desktop application configuration"""

    # Backend URL - Production'da değiştirilebilir
    BACKEND_URL = os.getenv("RHYTHM_NEXUS_BACKEND_URL", "http://localhost:8000")
    
    # License Server URL
    LICENSE_SERVER_URL = os.getenv("RHYTHM_NEXUS_LICENSE_SERVER_URL", "http://localhost:8001/api/v1")

    # App settings
    APP_NAME = "MyRhythmNexus Desktop"
    VERSION = "1.0.0"

    # UI Settings
    WINDOW_SIZE = "1200x800"
    THEME = "dark"  # dark, light, system

    # Paths
    APP_DATA_DIR = Path.home() / ".rhythm-nexus"
    CONFIG_FILE = APP_DATA_DIR / "config.json"
    LOG_FILE = APP_DATA_DIR / "app.log"

    @classmethod
    def ensure_app_data_dir(cls):
        """Ensure application data directory exists"""
        cls.APP_DATA_DIR.mkdir(exist_ok=True)

    @classmethod
    def _load_config(cls) -> dict:
        try:
            import json
            if cls.CONFIG_FILE.exists():
                with open(cls.CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return {}

    @classmethod
    def _save_config(cls, config: dict):
        cls.ensure_app_data_dir()
        import json
        with open(cls.CONFIG_FILE, 'w') as f:
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
    def load_backend_url(cls) -> str:
        """Load backend URL from config file"""
        return cls.get_value("backend_url", cls.BACKEND_URL)

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