"""
Service period calculation functions
"""
from calculation_core import calculate_inclusive_days, InvalidDateError
from error_handlers import CalculationError

def calculate_service_period(start_date, end_date, lost_time=0, adjust_flag=False):
    """
    Calculate service period details.
    """
    if not start_date or not end_date:
        raise InvalidDateError("Start and end dates are required")

    try:
        total_days = calculate_inclusive_days(start_date, end_date)
    except InvalidDateError:
        raise

    # Validate lost_time
    if not isinstance(lost_time, (int, float)):
        raise CalculationError("Lost time must be a number")

    # Apply lost time
    net_days = total_days - lost_time

    # Apply adjustment flag if needed
    if adjust_flag:
        net_days = int(net_days * 0.5)  # Example adjustment

    return total_days, net_days

def process_multiple_service_periods(periods_data):
    """
    Process multiple service periods.
    """
    total_days = 0
    net_days = 0

    for period in periods_data:
        start_date = period.get('start_date')
        end_date = period.get('end_date')
        lost_time = period.get('lost_time', 0)
        adjust_flag = period.get('adjust_flag', False)

        try:
            period_days, period_net_days = calculate_service_period(
                start_date, end_date, lost_time, adjust_flag
            )
        except (InvalidDateError, CalculationError) as e:
            raise e  # Re-raise validation errors

        total_days += period_days
        net_days += period_net_days

    return total_days, net_days