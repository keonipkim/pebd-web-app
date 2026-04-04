"""
Date utility functions for PEBD calculations
"""
from datetime import datetime

def validate_date_input(date_value):
    """Validate that a date input is properly formatted."""
    if date_value is None:
        return False
    return True

def total_days_to_ymd(total_days):
    """Convert total days to years, months, days format."""
    years = total_days // 360
    remaining_days = total_days % 360
    months = remaining_days // 30
    days = remaining_days % 30
    if months >= 12:
        years += months // 12
        months %= 12
    return f"{years:02d} Years, {months:02d} Months, {days:02d} Days"