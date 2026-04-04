"""
Final integration test for all PEBD calculator components
"""
import sys
import os

def test_final_integration():
    """Test that all components work together."""
    print("Testing final integration...")

    try:
        # Test imports work
        import calculation_core
        import service_period_calculator
        import error_handlers
        import date_utils
        print("✓ All modules import successfully")

        # Test basic functionality
        result = calculation_core.calculate_inclusive_days("2020-01-01", "2020-01-10")
        assert result == 10, f"Expected 10, got {result}"
        print("✓ Basic calculation works")

        # Test error handling
        try:
            calculation_core.calculate_inclusive_days("invalid", "2020-01-01")
            print("✗ Error handling should have failed")
            return False
        except:
            print("✓ Error handling works")

        print("✓ All integration tests pass!")
        return True

    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_final_integration()
    if not success:
        sys.exit(1)
    print("Final integration test completed successfully!")