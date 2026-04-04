"""
Core PEBD calculation functions
"""
from datetime import datetime, timedelta
from error_handlers import InvalidDateError, CalculationError

# Cache for date parsing to improve performance
_date_cache = {}

def _parse_date(date_str):
    """Parse date with caching for performance."""
    if date_str in _date_cache:
        return _date_cache[date_str]

    try:
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
        _date_cache[date_str] = parsed_date
        return parsed_date
    except ValueError as e:
        raise InvalidDateError(f"Invalid date format: {e}")

def calculate_inclusive_days(start_date, end_date):
    """Calculate inclusive days between dates."""
    try:
        # Validate inputs
        if not isinstance(start_date, str) or not isinstance(end_date, str):
            raise InvalidDateError("Date inputs must be strings")

        d1 = _parse_date(start_date)
        d2 = _parse_date(end_date)

        # Handle special end-of-month cases
        if d2.day == 31:
            d2 = d2.replace(day=30)
        elif d2.month == 2 and d2.day == 29:
            # Check if it's a leap year
            is_leap_year = (d2.year % 4 == 0 and (d2.year % 100 != 0 or d2.year % 400 == 0))
            if not is_leap_year:
                d2 = d2.replace(day=28)
        raw_days = (d2 - d1).days
        inclusive_days = raw_days + 1
        return inclusive_days
    except ValueError as e:
        raise InvalidDateError(f"Invalid date format: {e}")

def subtract_days_from_date(reference_date, days_to_subtract):
    """Subtract days from a date."""
    if not isinstance(reference_date, str):
        raise InvalidDateError("Reference date must be a string")
    if not isinstance(days_to_subtract, (int, float)):
        raise CalculationError("Days to subtract must be a number")

    ref_date = _parse_date(reference_date)
    result_date = ref_date - timedelta(days=days_to_subtract)
    return result_date.strftime('%Y-%m-%d')

def add_days_to_date(reference_date, days_to_add):
    """Add days to a date."""
    if not isinstance(reference_date, str):
        raise InvalidDateError("Reference date must be a string")
    if not isinstance(days_to_add, (int, float)):
        raise CalculationError("Days to add must be a number")

    ref_date = _parse_date(reference_date)
    result_date = ref_date + timedelta(days=days_to_add)
    return result_date.strftime('%Y-%m-%d')