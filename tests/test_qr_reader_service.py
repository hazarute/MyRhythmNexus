import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from desktop.services.qr_reader import QrReaderService


def test_qr_reader_service_initialization():
    """Test QR reader service initialization."""
    master = MagicMock()
    callback = Mock()
    service = QrReaderService(master, callback)

    assert service.master == master
    assert service.on_scan == callback
    assert service.buffer == ""
    assert service.last_key_time == 0
    assert service.TIMEOUT == 0.1
    master.bind.assert_called_once()


def test_qr_reader_detects_fast_input():
    """Test that service detects rapid character input as QR scan."""
    master = MagicMock()
    callback = Mock()
    service = QrReaderService(master, callback)

    # Simulate fast QR code input
    qr_code = "TEST_QR_CODE_123"

    # Mock time to simulate fast input
    with patch('time.time') as mock_time:
        mock_time.return_value = 1000.0  # Start time

        # Send characters quickly
        for i, char in enumerate(qr_code):
            mock_time.return_value = 1000.0 + (i * 0.01)  # Each char 10ms apart
            event = MagicMock()
            event.char = char
            event.keysym = None
            service.on_key_press(event)

        # Send Enter key to trigger scan
        event = MagicMock()
        event.char = ""
        event.keysym = "Return"
        service.on_key_press(event)

        # Should trigger callback with the QR code
        callback.assert_called_once_with(qr_code)


def test_qr_reader_ignores_slow_input():
    """Test that service ignores slow manual typing."""
    master = MagicMock()
    callback = Mock()
    service = QrReaderService(master, callback)

    # Simulate slow manual input - only last character should remain
    with patch('time.time') as mock_time:
        # First character
        mock_time.return_value = 1000.0
        event = MagicMock()
        event.char = 'h'
        event.keysym = None
        service.on_key_press(event)

        # Second character after timeout - buffer should reset
        mock_time.return_value = 1000.0 + 0.2  # 200ms later
        event.char = 'e'
        service.on_key_press(event)

        # Third character after another timeout
        mock_time.return_value = 1000.0 + 0.4  # 400ms later
        event.char = 'l'
        service.on_key_press(event)

        # Fourth character after another timeout
        mock_time.return_value = 1000.0 + 0.6  # 600ms later
        event.char = 'l'
        service.on_key_press(event)

        # Fifth character after another timeout
        mock_time.return_value = 1000.0 + 0.8  # 800ms later
        event.char = 'o'
        service.on_key_press(event)

        # Send Enter key - should not trigger callback because buffer only has 'o'
        event = MagicMock()
        event.char = ""
        event.keysym = "Return"
        service.on_key_press(event)

        # Should not trigger callback (buffer too short)
        callback.assert_not_called()

        # Buffer should contain only the last character
        assert service.buffer == "o"


def test_qr_reader_handles_enter_key():
    """Test that Enter key triggers scan."""
    master = MagicMock()
    callback = Mock()
    service = QrReaderService(master, callback)

    qr_code = "QR123"

    with patch('time.time') as mock_time:
        mock_time.return_value = 1000.0

        # Send QR code characters
        for char in qr_code:
            event = MagicMock()
            event.char = char
            event.keysym = None
            service.on_key_press(event)

        # Send Enter key
        event = MagicMock()
        event.char = ""
        event.keysym = "Return"
        service.on_key_press(event)

        # Should trigger callback
        callback.assert_called_once_with(qr_code)


def test_qr_reader_resets_buffer_on_timeout():
    """Test that buffer resets after timeout."""
    master = MagicMock()
    callback = Mock()
    service = QrReaderService(master, callback)

    with patch('time.time') as mock_time:
        # Send some characters
        mock_time.return_value = 1000.0
        event = MagicMock()
        event.char = 'A'
        event.keysym = None
        service.on_key_press(event)

        event.char = 'B'
        service.on_key_press(event)

        # Wait longer than timeout
        mock_time.return_value = 1000.0 + 0.2  # 200ms later
        event.char = 'C'
        service.on_key_press(event)

        # Should not trigger callback (buffer was reset)
        callback.assert_not_called()

        # Buffer should only contain 'C'
        assert service.buffer == "C"