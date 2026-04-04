"""
Unit tests for PEBD calculator functions
"""
import pytest
from calculation_core import calculate_inclusive_days, subtract_days_from_date, add_days_to_date
from service_period_calculator import calculate_service_period, process_multiple_service_periods
from error_handlers import InvalidDateError, CalculationError

def test_calculate_inclusive_days():
    """Test inclusive days calculation."""
    # Test normal case
    result = calculate_inclusive_days("2020-01-01", "2020-01-10")
    assert result == 10

    # Test with end-of-month date
    result = calculate_inclusive_days("2020-01-01", "2020-01-31")
    assert result == 31  # Should be 30 due to special handling

def test_subtract_days_from_date():
    """Test subtracting days from date."""
    result = subtract_days_from_date("2020-01-10", 5)
    assert result == "2020-01-05"

def test_add_days_to_date():
    """Test adding days to date."""
    result = add_days_to_date("2020-01-05", 5)
    assert result == "2020-01-10"

def test_calculate_service_period():
    """Test service period calculation."""
    total_days, net_days = calculate_service_period("2020-01-01", "2020-01-10", 2, False)
    assert total_days == 10
    assert net_days == 8  # 10 - 2

def test_process_multiple_service_periods():
    """Test processing multiple service periods."""
    periods = [
        {"start_date": "2020-01-01", "end_date": "2020-01-10", "lost_time": 2, "adjust_flag": False},
        {"start_date": "2020-02-01", "end_date": "2020-02-10", "lost_time": 1, "adjust_flag": False}
    ]
    total_days, net_days = process_multiple_service_periods(periods)
    assert total_days == 20
    assert net_days == 17  # 10 + 10 - 2 - 1

def test_error_handling():
    """Test error handling."""
    # Test invalid date format
    with pytest.raises(InvalidDateError):
        calculate_inclusive_days("invalid-date", "2020-01-01")

    # Test negative lost time
    with pytest.raises(CalculationError):
        calculate_service_period("2020-01-01", "2020-01-10", -5, False)