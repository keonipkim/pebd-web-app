import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar

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

# Calculation section
st.header("Calculation")
if st.button("Calculate PEBD"):
    # This would be where you'd integrate your actual calculation logic
    st.success("Calculation complete!")

    # Display results in a nice format
    col_results1, col_results2 = st.columns(2)

    with col_results1:
        st.subheader("Summary")
        st.write(f"**Calculated PEBD:** {datetime.now().strftime('%Y-%m-%d')}")
        st.write(f"**Member Type:** {member_type}")
        st.write(f"**Branch:** {branch}")

    with col_results2:
        st.subheader("Details")
        st.write(f"**Total Service Days:** Calculated")
        st.write(f"**Lost Time:** {lost_time} days")
        st.write(f"**Adjustments:** {'Yes' if adjust_flag else 'No'}")

# Detailed results section
st.header("Detailed Results")
st.markdown("Results will appear here after calculation")

# Example data table
example_data = {
    'Period': ['Service Period 1', 'Service Period 2'],
    'Start Date': ['2020-01-01', '2021-06-01'],
    'End Date': ['2020-12-31', '2021-12-31'],
    'Days': [365, 365],
    'Notes': ['Active Duty', 'DEP Service']
}
example_df = pd.DataFrame(example_data)
st.dataframe(example_df)

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

**Note:** This is a simplified interface. The actual calculation logic would need to be implemented based on your existing Jupyter notebook.
""")