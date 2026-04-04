"""
Error handling utilities for PEBD calculator
"""

class PEBDError(Exception):
    """Custom exception for PEBD calculation errors."""
    pass

class InvalidDateError(PEBDError):
    """Exception raised for invalid date inputs."""
    pass

class CalculationError(PEBDError):
    """Exception raised for calculation errors."""
    pass

def validate_date_format(date_str):
    """Validate date format and raise appropriate errors."""
    try:
        from datetime import datetime
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        raise InvalidDateError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD.")

def validate_positive_number(value, name):
    """Validate that a value is positive."""
    if value < 0:
        raise CalculationError(f"{name} cannot be negative: {value}")
    return True