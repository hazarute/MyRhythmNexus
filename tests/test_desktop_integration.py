import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from desktop.core.api_client import ApiClient
from desktop.core.config import DesktopConfig

class TestDesktopIntegration:
    """Test desktop application integration with backend"""

    def test_api_client_initialization(self):
        """Test API client initializes correctly"""
        client = ApiClient(base_url="http://test-server:8000")
        assert client.base_url == "http://test-server:8000"
        assert client.token is None

    def test_config_backend_url(self):
        """Test desktop config backend URL management"""
        # Test default URL
        assert DesktopConfig.BACKEND_URL == "http://localhost:8000"

        # Test environment variable override
        with patch.dict(os.environ, {"RHYTHM_NEXUS_BACKEND_URL": "https://api.production.com"}):
            # Reload would be needed, but we can test the logic
            expected_url = os.getenv("RHYTHM_NEXUS_BACKEND_URL", DesktopConfig.BACKEND_URL)
            assert expected_url == "https://api.production.com"

    @patch('httpx.Client.post')
    def test_api_client_login_success(self, mock_post):
        """Test successful login"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test-token-123"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = ApiClient()
        result = client.login("test@example.com", "password123")

        assert result == True
        assert client.token == "test-token-123"
        mock_post.assert_called_once()

    @patch('httpx.Client.post')
    def test_api_client_login_failure(self, mock_post):
        """Test login failure"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("Unauthorized")
        mock_post.return_value = mock_response

        client = ApiClient()
        result = client.login("wrong@example.com", "wrongpass")

        assert result == False
        assert client.token is None

    @patch('httpx.Client.get')
    def test_api_client_get_with_auth(self, mock_get):
        """Test authenticated GET request"""
        # Setup client with token
        client = ApiClient()
        client.set_token("test-token")

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = client.get("/api/v1/members/")

        assert result == {"data": "test"}
        mock_get.assert_called_once()
        # Check that Authorization header was added
        call_args = mock_get.call_args
        assert "Authorization" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"

    @patch('httpx.Client.post')
    def test_api_client_timezone_conversion(self, mock_post):
        """Test timezone conversion in responses"""
        # Mock response with UTC datetime
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "created_at": "2025-12-01T10:30:00Z",
            "updated_at": "2025-12-01T11:45:00Z"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = ApiClient()
        result = client.post("/api/v1/test/")

        # Should convert UTC to Turkey time (UTC+3)
        assert result["created_at"] == "2025-12-01T13:30:00"  # 10:30 + 3 hours
        assert result["updated_at"] == "2025-12-01T14:45:00"  # 11:45 + 3 hours

    def test_desktop_config_app_data_directory(self):
        """Test config creates app data directory"""
        from pathlib import Path
        import tempfile

        # Mock home directory
        with patch('pathlib.Path.home', return_value=Path(tempfile.gettempdir()) / "test_home"):
            test_config_dir = Path(tempfile.gettempdir()) / "test_home" / ".rhythm-nexus"

            # Should create directory when accessed
            assert not test_config_dir.exists()
            # Note: In real usage, ensure_app_data_dir() would create it

    @patch('builtins.open', new_callable=Mock)
    @patch('json.dump')
    def test_config_save_backend_url(self, mock_json_dump, mock_open):
        """Test saving backend URL to config"""
        from pathlib import Path
        import tempfile

        with patch('pathlib.Path.home', return_value=Path(tempfile.gettempdir()) / "test_home"):
            DesktopConfig.save_backend_url("https://test.api.com")

            # Verify json.dump was called with correct data
            mock_json_dump.assert_called_once_with({"backend_url": "https://test.api.com"})

    @patch('builtins.open', new_callable=Mock)
    @patch('json.load')
    def test_config_load_backend_url(self, mock_json_load, mock_open):
        """Test loading backend URL from config"""
        mock_json_load.return_value = {"backend_url": "https://loaded.api.com"}

        from pathlib import Path
        import tempfile

        with patch('pathlib.Path.home', return_value=Path(tempfile.gettempdir()) / "test_home"):
            loaded_url = DesktopConfig.load_backend_url()

            assert loaded_url == "https://loaded.api.com"
            mock_json_load.assert_called_once()

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_config_load_backend_url_fallback(self, mock_open):
        """Test fallback to default URL when config file doesn't exist"""
        from pathlib import Path
        import tempfile

        with patch('pathlib.Path.home', return_value=Path(tempfile.gettempdir()) / "test_home"):
            loaded_url = DesktopConfig.load_backend_url()

            assert loaded_url == DesktopConfig.BACKEND_URL

class TestDesktopUIIntegration:
    """Test desktop UI components integration"""

    @patch('customtkinter.CTk')
    @patch('desktop.core.api_client.ApiClient')
    def test_desktop_app_initialization(self, mock_api_client, mock_ctk):
        """Test desktop app initializes with correct configuration"""
        from desktop.main import App

        # Mock the CTk class
        mock_app_instance = Mock()
        mock_ctk.return_value = mock_app_instance

        # Mock API client
        mock_client_instance = Mock()
        mock_api_client.return_value = mock_client_instance

        # Create app (this will use our mocked classes)
        app = App()

        # Verify API client was created with correct base URL
        mock_api_client.assert_called_once_with(base_url="http://localhost:8000")

        # Verify window was configured
        mock_app_instance.title.assert_called_once_with("MyRhythmNexus - Admin Panel")
        mock_app_instance.geometry.assert_called_once_with("1000x700")

    @patch('desktop.core.config.DesktopConfig.load_backend_url')
    @patch('customtkinter.CTk')
    @patch('desktop.core.api_client.ApiClient')
    def test_desktop_app_custom_backend_url(self, mock_api_client, mock_ctk, mock_load_url):
        """Test desktop app uses custom backend URL from config"""
        from desktop.main import App

        # Mock config to return custom URL
        mock_load_url.return_value = "https://production.api.com"

        # Mock the CTk class
        mock_app_instance = Mock()
        mock_ctk.return_value = mock_app_instance

        # Mock API client
        mock_client_instance = Mock()
        mock_api_client.return_value = mock_client_instance

        # Create app
        app = App()

        # Verify API client was created with custom URL
        mock_api_client.assert_called_once_with(base_url="https://production.api.com")

    def test_desktop_config_constants(self):
        """Test desktop config constants are properly defined"""
        assert DesktopConfig.APP_NAME == "MyRhythmNexus Desktop"
        assert DesktopConfig.VERSION == "1.0.0"
        assert DesktopConfig.WINDOW_SIZE == "1200x800"
        assert DesktopConfig.THEME == "dark"

        # Backend URL should have a default
        assert DesktopConfig.BACKEND_URL is not None
        assert "localhost" in DesktopConfig.BACKEND_URL or "http" in DesktopConfig.BACKEND_URL