from datetime import datetime
from desktop.core.locale import _


def format_currency(value):
    """Format a numeric value as Turkish Lira currency string."""
    if value is None:
        return "- TL"
    try:
        amount = float(value)
    except (ValueError, TypeError):
        return f"{value} TL"
    return f"{amount:,.2f} TL".replace(",", " ")


def format_date(iso_value):
    """Format an ISO datetime string to Turkish date format."""
    if not iso_value:
        return "-"
    try:
        cleaned = iso_value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(cleaned)
        return parsed.strftime("%d %b %Y, %H:%M")
    except ValueError:
        return iso_value[:16]