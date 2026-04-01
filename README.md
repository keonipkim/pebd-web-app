# PEBD Calculator Web App

This is a web application for calculating Pay Entry Base Dates (PEBD) according to DoD Financial Management Regulation Volume 7A, Chapter 1.

## Features
- User-friendly interface for entering service period data
- Calculation of PEBD based on DoD FMR regulations
- Display of detailed service period information
- Support for different member types and service branches

## Installation
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `streamlit run app.py`

## Usage
1. Enter your member information (type, service type, branch)
2. Input your date information (DOEAF, active duty dates, etc.)
3. Add service periods
4. Click "Calculate PEBD" to see results

## Repository Structure
- `app.py` - Main Streamlit application
- `requirements.txt` - Python dependencies
- `README.md` - This file