import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar
import pebd_calculations

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
    branch = st.selectbox("Branch of Service", ["USMC", "USA", "USN", "USAF", "USCG"])

with col2:
    st.header("Date Information")

    # Date inputs
    doeaf = st.date_input("Date of Entry on Active Duty (DOEAF)")
    initial_active_duty = st.date_input("Initial Active Duty Date")
    eos = st.date_input("End of Service Date (EOS)")
    reentry_date = st.date_input("Reentry Date (if applicable)")

    # Additional dates
    deactivation_date = st.date_input("Deactivation Date (if applicable)")
    separation_date = st.date_input("Separation Date (if applicable)")

# Service periods section
st.header("Service Periods")
st.markdown("Enter your service periods. You can add multiple periods if needed.")

# Add a service period input section
with st.expander("Add Service Period"):
    period_start = st.date_input("Period Start Date")
    period_end = st.date_input("Period End Date")
    period_type = st.selectbox("Period Type", ["Active Duty", "DEP", "Reserve", "Other"])
    lost_time = st.number_input("Lost Time (days)", min_value=0, value=0)
    adjust_flag = st.checkbox("Adjustment Flag (1 = non-creditable adjustment)")

    if st.button("Add Period"):
        st.success("Service period added!")

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
        # Call your calculation function here (replace with actual implementation)
        try:
            results = pebd_calculations.calculate_pebd_core(
                doeaf,
                initial_active_duty,
                eos,
                reentry_date,
                member_type,
                1,  # number of periods
                lost_time_input,
                adjust_flag
            )

            st.success("Calculation complete!")

            # Display results in a nice format
            col_results1, col_results2 = st.columns(2)

            with col_results1:
                st.subheader("Summary")
                st.write(f"**Calculated PEBD:** {results['pebd'].strftime('%Y-%m-%d')}")
                st.write(f"**Member Type:** {member_type}")
                st.write(f"**Branch:** {branch}")

            with col_results2:
                st.subheader("Details")
                st.write(f"**Total Service Days:** {results['total_service_days']}")
                st.write(f"**Net Service Days:** {results['net_service_days']}")
                st.write(f"**Lost Time:** {results['lost_time']} days")

            # Detailed results section
            st.header("Detailed Results")

            # Example data table - replace with actual calculation results
            example_data = {
                'Period': ['Service Period 1'],
                'Start Date': [str(initial_active_duty)],
                'End Date': [str(eos)],
                'Days': [results['total_service_days']],
                'Notes': ['Based on DoD FMR calculations']
            }
            example_df = pd.DataFrame(example_data)
            st.dataframe(example_df)

        except Exception as e:
            st.error(f"Calculation error: {str(e)}")

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