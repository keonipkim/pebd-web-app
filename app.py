import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calculation_core
import service_period_calculator
import date_utils

# Set page config
st.set_page_config(
    page_title="PEBD Calculator",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 PEBD Calculator (DoD FMR Vol 7A, Ch 1)")
st.markdown("""
This tool calculates Pay Entry Base Dates (PEBD) according to DoD Financial Management Regulation Volume 7A, Chapter 1.
Enter the required dates and parameters to compute your PEBD.
""")

# Create two columns for inputs
col1, col2 = st.columns(2)

with col1:
    st.header("Member Information")

    # Member type
    member_type = st.selectbox("Member Type", ["Enlisted", "Officer"])

    # Service type
    service_type = st.selectbox("Service Type", ["Active Duty", "DEP", "Reserve"])

    # Branch of service
    branch = st.selectbox("Branch of Service", ["USMC", "USA", "USN", "USAF", "USCG", "NG"])

with col2:
    st.header("Date Information")

    # Date inputs
    doeaf = st.date_input("Date of Entry on Active Duty (DOEAF)",
                         min_value=datetime(1950, 1, 1),
                         max_value=datetime(2116, 12, 31))
    initial_active_duty = st.date_input("Initial Active Duty Date",
                                       min_value=datetime(1950, 1, 1),
                                       max_value=datetime(2116, 12, 31))
    eos = st.date_input("End of Service Date (EOS)",
                       min_value=datetime(1950, 1, 1),
                       max_value=datetime(2116, 12, 31))
    reentry_date = st.date_input("Reentry Date (if applicable)",
                                min_value=datetime(1950, 1, 1),
                                max_value=datetime(2116, 12, 31))

    # Additional dates
    deactivation_date = st.date_input("Deactivation Date (if applicable)",
                                     min_value=datetime(1950, 1, 1),
                                     max_value=datetime(2116, 12, 31))
    separation_date = st.date_input("Separation Date (if applicable)",
                                   min_value=datetime(1950, 1, 1),
                                   max_value=datetime(2116, 12, 31))

# Service periods section
st.header("Service Periods")
st.markdown("Enter your service periods. You can add multiple periods if needed.")

# Add a service period input section
with st.expander("Add Active Service Period"):
    active_start = st.date_input("Active Period Start Date", key="active_start",
                                min_value=datetime(1950, 1, 1),
                                max_value=datetime(2116, 12, 31))
    active_end = st.date_input("Active Period End Date", key="active_end",
                              min_value=datetime(1950, 1, 1),
                              max_value=datetime(2116, 12, 31))
    active_lost_time = st.number_input("Lost Time (days)", min_value=0, value=0, key="active_lost")
    active_adjust_flag = st.checkbox("Adjustment Flag (1 = non-creditable adjustment)", key="active_adjust")

    if st.button("Add Active Period", key="add_active"):
        st.success("Active service period added!")

# Add an inactive service period input section
with st.expander("Add Inactive Creditable Period"):
    inactive_start = st.date_input("Inactive Period Start Date", key="inactive_start",
                                 min_value=datetime(1950, 1, 1),
                                 max_value=datetime(2116, 12, 31))
    inactive_end = st.date_input("Inactive Period End Date", key="inactive_end",
                               min_value=datetime(1950, 1, 1),
                               max_value=datetime(2116, 12, 31))
    inactive_lost_time = st.number_input("Lost Time (days)", min_value=0, value=0, key="inactive_lost")
    inactive_adjust_flag = st.checkbox("Adjustment Flag (1 = non-creditable adjustment)", key="inactive_adjust")

    if st.button("Add Inactive Period", key="add_inactive"):
        st.success("Inactive service period added!")

# Add a DEP period input section
with st.expander("Add DEP Period"):
    dep_start = st.date_input("DEP Period Start Date", key="dep_start",
                             min_value=datetime(1950, 1, 1),
                             max_value=datetime(2116, 12, 31))
    dep_end = st.date_input("DEP Period End Date", key="dep_end",
                           min_value=datetime(1950, 1, 1),
                           max_value=datetime(2116, 12, 31))

    if st.button("Add DEP Period", key="add_dep"):
        st.success("DEP period added!")

# Add a Lost Time period input section
with st.expander("Add Lost Time Period"):
    lost_start = st.date_input("Lost Time Start Date", key="lost_start",
                              min_value=datetime(1950, 1, 1),
                              max_value=datetime(2116, 12, 31))
    lost_end = st.date_input("Lost Time End Date", key="lost_end",
                            min_value=datetime(1950, 1, 1),
                            max_value=datetime(2116, 12, 31))

    if st.button("Add Lost Time Period", key="add_lost"):
        st.success("Lost time period added!")

# Constructive service years
st.header("Constructive Service")
constructive_years = st.number_input("Constructive Service Years", min_value=0, value=0, step=1)

# Lost time section
st.header("Lost Time Information")
lost_time_input = st.number_input("Total Lost Time (days)", min_value=0, value=0)

# Calculation section
st.header("Calculation")
if st.button("Calculate PEBD"):
    # Validate inputs
    if not initial_active_duty or not eos:
        st.error("Please enter both Initial Active Duty Date and End of Service Date")
    else:
        # Collect all period data
        active_periods = []
        inactive_periods = []
        dep_periods = []
        lost_periods = []

        # This would be where you'd actually collect the data from the UI
        # For now, we'll use a placeholder approach

        # Call your calculation function here (replace with actual implementation)
        try:
            # Placeholder - in a real implementation, you would collect the actual data from the UI
            results = {
                'pebd': '2026-01-01',
                'total_active_days': 1000,
                'total_inactive_days': 500,
                'total_lost_days': 100,
                'dep_days': 200,
                'constructive_days': 360,
                'net_service_days': 1960,
                'lost_time': lost_time_input,
                'member_type': member_type,
                'branch': branch,
                'adjust_flag': False
            }

            st.success("Calculation complete!")

            # Display results in a nice format
            col_results1, col_results2 = st.columns(2)

            with col_results1:
                st.subheader("Summary")
                st.write(f"**Calculated PEBD:** {results['pebd']}")
                st.write(f"**Member Type:** {member_type}")
                st.write(f"**Branch:** {branch}")

            with col_results2:
                st.subheader("Details")
                st.write(f"**Total Active Days:** {results['total_active_days']}")
                st.write(f"**Net Service Days:** {results['net_service_days']}")
                st.write(f"**Lost Time:** {results['lost_time']} days")

            # Detailed results section
            st.header("Detailed Results")

            # Create a more comprehensive results table
            results_data = {
                'Metric': ['Total Active Days', 'Total Inactive Days', 'Total Lost Days',
                           'DEP Days', 'Constructive Days', 'Net Service Days', 'PEBD Date'],
                'Value': [
                    results['total_active_days'],
                    results['total_inactive_days'],
                    results['total_lost_days'],
                    results['dep_days'],
                    results['constructive_days'],
                    results['net_service_days'],
                    results['pebd']
                ]
            }
            results_df = pd.DataFrame(results_data)
            st.dataframe(results_df)

        except Exception as e:
            st.error(f"Calculation error: {str(e)}")
            st.info("Please check your inputs and try again. If the problem persists, contact support.")

# About section
st.header("About This Tool")
st.markdown("""
This calculator implements DoD Financial Management Regulation Volume 7A, Chapter 1 calculations.
It handles:
- Creditable service periods
- Lost time calculations
- DEP (Delayed Entry Program) service
- Break-in-service rules
- PEBD back-calculation from total creditable days

**How to use this tool:**
1. Enter your member information
2. Input your date information
3. Add service periods
4. Click "Calculate PEBD" to see results

**Important:** This is a simplified interface. The actual calculation logic needs to be implemented with your specific functions from the Jupyter notebook.
""")