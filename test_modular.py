"""
Test script to verify modular components work correctly
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_modular_components():
    """Test that all modular components can be imported and work correctly"""

    # Test calculation_core
    try:
        from calculation_core import calculate_inclusive_days, subtract_days_from_date, add_days_to_date
        print("✓ calculation_core imports successfully")

        # Test basic functionality
        days = calculate_inclusive_days("2020-01-01", "2020-01-10")
        assert days == 10, f"Expected 10, got {days}"
        print("✓ calculate_inclusive_days works correctly")

        result = subtract_days_from_date("2020-01-10", 5)
        assert result == "2020-01-05", f"Expected 2020-01-05, got {result}"
        print("✓ subtract_days_from_date works correctly")

        result = add_days_to_date("2020-01-05", 5)
        assert result == "2020-01-10", f"Expected 2020-01-10, got {result}"
        print("✓ add_days_to_date works correctly")

    except Exception as e:
        print(f"✗ calculation_core test failed: {e}")
        return False

    # Test date_utils
    try:
        from date_utils import validate_date_input, total_days_to_ymd
        print("✓ date_utils imports successfully")

        # Test validation
        valid = validate_date_input("2020-01-01")
        assert valid == True, "Date validation should return True"
        print("✓ validate_date_input works correctly")

        # Test conversion
        ymd = total_days_to_ymd(400)
        assert "Years" in ymd, "Should return years, months, days format"
        print("✓ total_days_to_ymd works correctly")

    except Exception as e:
        print(f"✗ date_utils test failed: {e}")
        return False

    # Test service_period_calculator
    try:
        from service_period_calculator import calculate_service_period, process_multiple_service_periods
        print("✓ service_period_calculator imports successfully")

        # Test single period
        total, net = calculate_service_period("2020-01-01", "2020-01-10", 2, False)
        assert total == 10, f"Expected total 10, got {total}"
        assert net == 8, f"Expected net 8, got {net}"
        print("✓ calculate_service_period works correctly")

        # Test multiple periods
        periods = [
            {"start_date": "2020-01-01", "end_date": "2020-01-10", "lost_time": 2, "adjust_flag": False},
            {"start_date": "2020-02-01", "end_date": "2020-02-10", "lost_time": 1, "adjust_flag": False}
        ]
        total, net = process_multiple_service_periods(periods)
        assert total == 20, f"Expected total 20, got {total}"
        assert net == 17, f"Expected net 17, got {net}"
        print("✓ process_multiple_service_periods works correctly")

    except Exception as e:
        print(f"✗ service_period_calculator test failed: {e}")
        return False

    print("✓ All modular components work correctly!")
    return True

if __name__ == "__main__":
    success = test_modular_components()
    if not success:
        sys.exit(1)