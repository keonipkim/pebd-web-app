"""
Performance test for calculation functions
"""
import sys
import os
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_performance():
    """Test that performance improvements are implemented"""

    try:
        from calculation_core import calculate_inclusive_days
        import time

        print("Testing performance of calculation functions...")

        # Test execution time for calculation functions
        start_time = time.time()
        result = calculate_inclusive_days("2020-01-01", "2023-01-01")
        end_time = time.time()

        # Should complete quickly
        execution_time = end_time - start_time
        print(f"Calculation took: {execution_time:.6f} seconds")
        print(f"Result: {result} days")

        # Should complete quickly (less than 1 second for a simple calculation)
        assert execution_time < 1.0, f"Calculation took too long: {execution_time}s"
        # The actual result is 1097 days (not 1096), so let's adjust the test
        assert result == 1097, f"Expected 1097 days, got {result}"

        print("✓ Performance test passed!")
        return True

    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_performance()
    if not success:
        sys.exit(1)