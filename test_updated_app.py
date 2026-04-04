"""
Test script to verify the updated application works with modular components
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_updated_application():
    """Test that the updated app can import and use modular components"""

    try:
        # Test that we can import all the required modules
        import calculation_core
        import service_period_calculator
        import date_utils
        print("✓ All modular components import successfully")

        # Test basic functionality
        result = calculation_core.calculate_inclusive_days("2020-01-01", "2020-01-10")
        assert result == 10, f"Expected 10, got {result}"
        print("✓ Basic calculation works")

        print("✓ Updated application components work correctly!")
        return True

    except Exception as e:
        print(f"✗ Updated application test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_updated_application()
    if not success:
        sys.exit(1)