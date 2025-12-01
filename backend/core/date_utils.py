"""
Date utility functions for consistent date calculations across the application.
"""
from datetime import datetime, timedelta


def calculate_end_date(start_date: datetime, cycle_period: str, repeat_weeks: int = 1) -> datetime:
    """
    Calculate end date based on cycle period with consistent business rules.
    
    Business Rule: MONTHLY = 4 weeks (28 days), NOT 30 days
    
    Args:
        start_date: Start date of subscription/plan
        cycle_period: Period type (MONTHLY, QUARTERLY, SEMI_ANNUAL, YEARLY, WEEKLY, DAILY, FIXED)
        repeat_weeks: Multiplier for week-based cycles (defaults to 1)
    
    Returns:
        Calculated end date based on cycle
    """
    cycle_upper = cycle_period.upper()
    
    if cycle_upper == "FIXED":
        raise ValueError("FIXED cycle requires manual end_date setting")

    duration_days = get_cycle_duration_days(cycle_upper)
    total_days = duration_days * max(repeat_weeks, 1)
    return start_date + timedelta(days=total_days)


def get_cycle_duration_days(cycle_period: str) -> int:
    """
    Get duration in days for a cycle period.
    
    Returns:
        Number of days for the cycle
    """
    cycle_upper = cycle_period.upper()
    
    duration_map = {
        "DAILY": 1,
        "WEEKLY": 7,
        "MONTHLY": 28,  # 4 weeks standard
        "QUARTERLY": 84,  # 3 months (3 x 28 days)
        "SEMI_ANNUAL": 168,  # 6 months (6 x 28 days)
        "YEARLY": 365
    }
    
    return duration_map.get(cycle_upper, 28)  # Default to monthly
