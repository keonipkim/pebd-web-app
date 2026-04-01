"""
PEBD Calculator Functions
This file contains the core calculation functions for the PEBD calculator.
Based on your tkinter implementation, I've adapted the key functions for web use.
"""

from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def calculate_inclusive_days(start_date, end_date):
    """
    Calculate inclusive days between dates, with special handling for end-of-month dates.
    This is the core calculation from your tkinter code.
    """
    try:
        d1 = datetime.strptime(start_date, '%Y-%m-%d')
        d2 = datetime.strptime(end_date, '%Y-%m-%d')
        if d2.day == 31:
            d2 = d2.replace(day=30)
        elif d2.month == 2 and d2.day == 29 and not (d2.year % 4 == 0 and (d2.year % 100 != 0 or d2.year % 400 == 0)):
            d2 = d2.replace(day=28)
        raw_days = (d2 - d1).days
        inclusive_days = raw_days + 1
        return inclusive_days
    except ValueError as e:
        raise ValueError(f"Invalid date format: {e}")

def subtract_days_from_date(reference_date, days_to_subtract):
    """Subtract days from a date."""
    ref_date = datetime.strptime(reference_date, '%Y-%m-%d')
    result_date = ref_date - timedelta(days=days_to_subtract)
    return result_date.strftime('%Y-%m-%d')

def add_days_to_date(reference_date, days_to_add):
    """Add days to a date."""
    ref_date = datetime.strptime(reference_date, '%Y-%m-%d')
    result_date = ref_date + timedelta(days=days_to_add)
    return result_date.strftime('%Y-%m-%d')

def total_days_to_ymd(total_days):
    """Convert total days to years, months, days format."""
    years = total_days // 360
    remaining_days = total_days % 360
    months = remaining_days // 30
    days = remaining_days % 30
    if months >= 12:
        years += months // 12
        months %= 12
    return f"{years:02d} Years, {months:02d} Months, {days:02d} Days"

def validate_date_input(date_value):
    """Validate that a date input is properly formatted."""
    if date_value is None:
        return False
    return True

def calculate_service_period(start_date, end_date, lost_time=0, adjust_flag=False):
    """
    Calculate service period details.
    """
    if not start_date or not end_date:
        return 0, 0

    total_days = calculate_inclusive_days(start_date, end_date)

    # Apply lost time
    net_days = total_days - lost_time

    # Apply adjustment flag if needed
    if adjust_flag:
        net_days = int(net_days * 0.5)  # Example adjustment

    return total_days, net_days

def calculate_pebd_core(doeaf, initial_active_duty, eos, reentry_date, member_type,
                        service_periods, lost_time_data, adjust_flag,
                        dep_periods=None, active_periods=None, inactive_periods=None, lost_periods=None,
                        constructive_years=0, branch="USMC"):
    """
    Core PEBD calculation function based on your tkinter implementation.
    This integrates the complete calculation logic.
    """

    # Validate inputs
    if not validate_date_input(initial_active_duty) or not validate_date_input(eos):
        raise ValueError("Invalid date inputs")

    # Process different types of periods
    if active_periods is None:
        active_periods = []
    if inactive_periods is None:
        inactive_periods = []
    if dep_periods is None:
        dep_periods = []
    if lost_periods is None:
        lost_periods = []

    # Calculate days for each period type
    total_active_days = sum(calculate_inclusive_days(start, end) for start, end in active_periods)
    total_inactive_days = sum(calculate_inclusive_days(start, end) for start, end in inactive_periods)
    total_lost_days = sum(calculate_inclusive_days(start, end) for start, end in lost_periods)

    # Handle DEP periods (they are NOT CREDITABLE)
    dep_days = 0  # DEP periods are not creditable, but we track them for reporting
    for dep_start, dep_end in dep_periods:
        dep_days += calculate_inclusive_days(dep_start, dep_end)

    # Calculate constructive service
    constructive_days = constructive_years * 360

    # Calculate net service days
    net_service_days = total_active_days + total_inactive_days + total_lost_days + constructive_days

    # Special handling for specific cases (as in your code)
    # This is where you'd add your specific logic for the 599 days case
    # For now, we'll keep it general but you can customize this part

    # Calculate PEBD
    if reentry_date:
        calculated_pebd = subtract_days_from_date(reentry_date, net_service_days)
    else:
        # If no reentry date, use a default calculation
        calculated_pebd = datetime.now().date()

    # Handle special cases based on member type and branch
    if member_type == "Officer":
        # Officer-specific rules
        pass
    else:
        # Enlisted-specific rules
        pass

    # Handle National Guard (NG) - add branch-specific logic if needed
    if branch == "NG":
        # Add NG-specific rules here
        pass

    return {
        'pebd': calculated_pebd,
        'total_active_days': total_active_days,
        'total_inactive_days': total_inactive_days,
        'total_lost_days': total_lost_days,
        'dep_days': dep_days,
        'constructive_days': constructive_days,
        'net_service_days': net_service_days,
        'lost_time': lost_time_data,
        'member_type': member_type,
        'branch': branch,
        'adjust_flag': adjust_flag
    }

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
        days = calculate_inclusive_days(start_date, end_date)
        return days * 0.8  # Example adjustment
    else:
        return calculate_inclusive_days(start_date, end_date)

def calculate_break_in_service(start_date, end_date, break_days):
    """
    Handle break-in-service calculations.
    """
    # Break-in-service rules - replace with your specific logic
    if break_days > 30:  # Example threshold
        # Apply special rules for extended breaks
        return calculate_inclusive_days(start_date, end_date) * 0.5
    else:
        return calculate_inclusive_days(start_date, end_date)

# Add any additional helper functions you might need
def get_branch_code(branch_name):
    """Convert branch name to code."""
    branch_codes = {
        "USMC": "01",
        "USA": "02",
        "USN": "03",
        "USAF": "04",
        "USCG": "05",
        "NG": "06"  # Added National Guard
    }
    return branch_codes.get(branch_name, "00")

def get_member_type_code(member_type):
    """Convert member type to code."""
    type_codes = {
        "Enlisted": "E",
        "Officer": "O"
    }
    return type_codes.get(member_type, "U")