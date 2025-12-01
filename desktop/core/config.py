import os
from pathlib import Path

class DesktopConfig:
    """Desktop application configuration"""

    # Backend URL - Production'da değiştirilebilir
    BACKEND_URL = os.getenv("RHYTHM_NEXUS_BACKEND_URL", "http://localhost:8000")

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
    def save_backend_url(cls, url: str):
        """Save backend URL to config file"""
        cls.ensure_app_data_dir()
        import json
        config = {"backend_url": url}
        with open(cls.CONFIG_FILE, 'w') as f:
            json.dump(config, f)

    @classmethod
    def load_backend_url(cls) -> str:
        """Load backend URL from config file"""
        try:
            import json
            with open(cls.CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get("backend_url", cls.BACKEND_URL)
        except (FileNotFoundError, json.JSONDecodeError):
            return cls.BACKEND_URL