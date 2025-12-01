"""
Time utility functions for consistent Turkey timezone usage across the application.
"""
import zoneinfo
from datetime import datetime, timezone, timedelta

from .config import settings


def get_turkey_time() -> datetime:
    """
    Get current time in Turkey timezone (Europe/Istanbul).

    This function should be used throughout the application for all date/time operations
    to ensure consistency with Turkey timezone.

    Returns:
        datetime: Current time in Turkey timezone
    """
    turkey_tz = zoneinfo.ZoneInfo(settings.TIMEZONE)
    return datetime.now(turkey_tz)


def get_turkey_timezone() -> timezone:
    """
    Get Turkey timezone object.

    Returns:
        timezone: Turkey timezone (UTC+3)
    """
    return timezone(timedelta(hours=3))


def convert_to_turkey_time(dt: datetime) -> datetime:
    """
    Convert any datetime to Turkey timezone.

    Args:
        dt: Datetime to convert (naive or aware)

    Returns:
        datetime: Datetime in Turkey timezone
    """
    turkey_tz = zoneinfo.ZoneInfo(settings.TIMEZONE)
    if dt.tzinfo is None:
        # Naive datetime, assume UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(turkey_tz)


def get_current_turkey_date() -> str:
    """
    Get current date in Turkey timezone as ISO date string.

    Returns:
        str: Current date in YYYY-MM-DD format
    """
    return get_turkey_time().date().isoformat()


def get_current_turkey_datetime() -> str:
    """
    Get current datetime in Turkey timezone as ISO string.

    Returns:
        str: Current datetime in ISO format
    """
    return get_turkey_time().isoformat()