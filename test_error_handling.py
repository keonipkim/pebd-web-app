"""
Test script to verify error handling works correctly
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_error_handling():
    """Test that error handling works for invalid inputs"""

    try:
        # Test calculation_core error handling
        from calculation_core import calculate_inclusive_days, InvalidDateError
        print("✓ calculation_core imports successfully")

        # Test invalid date format
        try:
            calculate_inclusive_days("invalid-date", "2023-01-01")
            print("✗ Should have raised InvalidDateError")
            return False
        except InvalidDateError as e:
            print("✓ Invalid date format properly handled")

        # Test valid calculation
        days = calculate_inclusive_days("2020-01-01", "2020-01-10")
        assert days == 10
        print("✓ Valid calculation works correctly")

        # Test service_period_calculator error handling
        from service_period_calculator import calculate_service_period, InvalidDateError, CalculationError
        print("✓ service_period_calculator imports successfully")

        # Test invalid dates in service period
        try:
            calculate_service_period("invalid-date", "2020-01-10")
            print("✗ Should have raised InvalidDateError")
            return False
        except InvalidDateError as e:
            print("✓ Invalid dates in service period properly handled")

        # Test valid service period calculation
        total, net = calculate_service_period("2020-01-01", "2020-01-10", 2, False)
        assert total == 10
        assert net == 8
        print("✓ Valid service period calculation works correctly")

        print("✓ All error handling tests passed!")
        return True

    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_error_handling()
    if not success:
        sys.exit(1)