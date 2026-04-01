"""
PEBD Calculator Functions
This file contains the core calculation functions for the PEBD calculator.
Replace the placeholder functions with your actual implementation from the Jupyter notebook.
"""

from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def validate_date_input(date_value):
    """Validate that a date input is properly formatted."""
    if date_value is None:
        return False
    return True

def date_to_datetime(date_input):
    """Convert date input to datetime object."""
    if isinstance(date_input, str):
        try:
            return datetime.strptime(date_input, '%Y-%m-%d')
        except ValueError:
            return None
    return date_input

def calculate_30_360_days(start_date, end_date):
    """
    Calculate days between dates using 30/360 convention.
    This is a standard convention used in DoD calculations.
    """
    if not start_date or not end_date:
        return 0

    # 30/360 day count convention
    # This is a simplified version - your actual implementation may be more complex
    days = (end_date - start_date).days
    return days

def calculate_service_period(start_date, end_date, lost_time=0, adjust_flag=False):
    """
    Calculate service period details.
    """
    if not start_date or not end_date:
        return 0, 0

    total_days = calculate_30_360_days(start_date, end_date)

    # Apply lost time
    net_days = total_days - lost_time

    # Apply adjustment flag if needed
    if adjust_flag:
        net_days = int(net_days * 0.5)  # Example adjustment

    return total_days, net_days

def calculate_pebd_core(doeaf, initial_active_duty, eos, reentry_date, member_type,
                        service_periods, lost_time_data, adjust_flag):
    """
    Core PEBD calculation function.
    This is where you would integrate your specific DoD FMR logic.
    """

    # Validate inputs
    if not validate_date_input(initial_active_duty) or not validate_date_input(eos):
        raise ValueError("Invalid date inputs")

    # Calculate total service days
    total_service_days, net_service_days = calculate_service_period(
        initial_active_duty, eos, lost_time_data, adjust_flag
    )

    # PEBD calculation based on DoD FMR rules
    # This is a simplified version - replace with your actual logic
    if reentry_date:
        # PEBD is typically calculated by subtracting net service days from reentry date
        calculated_pebd = reentry_date - timedelta(days=net_service_days)
    else:
        # If no reentry date, use a default calculation
        calculated_pebd = datetime.now().date()

    # Handle special cases based on member type
    if member_type == "Officer":
        # Officer-specific rules
        pass
    else:
        # Enlisted-specific rules
        pass

    return {
        'pebd': calculated_pebd,
        'total_service_days': total_service_days,
        'net_service_days': net_service_days,
        'lost_time': lost_time_data,
        'member_type': member_type,
        'adjust_flag': adjust_flag
    }

def process_multiple_service_periods(periods_data):
    """
    Process multiple service periods.
    """
    total_days = 0
    net_days = 0

    for period in periods_data:
        start_date = date_to_datetime(period.get('start_date'))
        end_date = date_to_datetime(period.get('end_date'))
        lost_time = period.get('lost_time', 0)
        adjust_flag = period.get('adjust_flag', False)

        period_days, period_net_days = calculate_service_period(
            start_date, end_date, lost_time, adjust_flag
        )

        total_days += period_days
        net_days += period_net_days

    return total_days, net_days

def calculate_deployment_service(start_date, end_date, dep_service_type):
    """
    Calculate DEP (Delayed Entry Program) service.
    """
    # DEP service rules - replace with your specific logic
    if dep_service_type == "1985-1989":
        # Special rules for this period
        days = calculate_30_360_days(start_date, end_date)
        return days * 0.8  # Example adjustment
    else:
        return calculate_30_360_days(start_date, end_date)

def calculate_break_in_service(start_date, end_date, break_days):
    """
    Handle break-in-service calculations.
    """
    # Break-in-service rules - replace with your specific logic
    if break_days > 30:  # Example threshold
        # Apply special rules for extended breaks
        return calculate_30_360_days(start_date, end_date) * 0.5
    else:
        return calculate_30_360_days(start_date, end_date)

# Add any additional helper functions you might need
def get_branch_code(branch_name):
    """Convert branch name to code."""
    branch_codes = {
        "USMC": "01",
        "USA": "02",
        "USN": "03",
        "USAF": "04",
        "USCG": "05"
    }
    return branch_codes.get(branch_name, "00")

def get_member_type_code(member_type):
    """Convert member type to code."""
    type_codes = {
        "Enlisted": "E",
        "Officer": "O"
    }
    return type_codes.get(member_type, "U")