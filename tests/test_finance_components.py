"""Basic tests for finance components."""

import pytest
from unittest.mock import Mock

# Test imports
def test_formatters_import():
    """Test that formatters can be imported."""
    from desktop.ui.components.finance.formatters import format_currency, format_date
    assert callable(format_currency)
    assert callable(format_date)

def test_styles_import():
    """Test that styles can be imported."""
    from desktop.ui.components.finance import styles
    assert hasattr(styles, 'DEFAULT_CARD_BG')

def test_stat_card_import():
    """Test that StatCard can be imported."""
    from desktop.ui.components.finance.stat_card import StatCard
    assert callable(StatCard)

def test_summary_row_import():
    """Test that SummaryRow can be imported."""
    from desktop.ui.components.finance.summary_row import SummaryRow
    assert callable(SummaryRow)

def test_payment_card_import():
    """Test that PaymentCard can be imported."""
    from desktop.ui.components.finance.payment_card import PaymentCard
    assert callable(PaymentCard)

def test_payment_list_import():
    """Test that PaymentList can be imported."""
    from desktop.ui.components.finance.payment_list import PaymentList
    assert callable(PaymentList)

def test_pagination_import():
    """Test that PaginationControls can be imported."""
    from desktop.ui.components.finance.pagination import PaginationControls
    assert callable(PaginationControls)

# Basic functionality tests
def test_format_currency():
    """Test currency formatting."""
    from desktop.ui.components.finance.formatters import format_currency
    assert format_currency(1234.56) == "1 234.56 TL"
    assert format_currency(None) == "- TL"

def test_format_date():
    """Test date formatting."""
    from desktop.ui.components.finance.formatters import format_date
    assert format_date("2023-12-01T10:30:00Z") == "01 Dec 2023, 10:30"
    assert format_date(None) == "-"