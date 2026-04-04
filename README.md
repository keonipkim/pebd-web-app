# PEBD Calculator Web App

This is a web application for calculating Pay Entry Base Dates (PEBD) according to DoD Financial Management Regulation Volume 7A, Chapter 1.

## Features
- User-friendly interface for entering service period data
- Calculation of PEBD based on DoD FMR regulations
- Display of detailed service period information
- Support for different member types and service branches
- Client-side implementation option

## Installation
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `streamlit run app.py`

## Client-Side Implementation
The calculator can also be run client-side in a browser:
- No server-side dependencies
- Self-contained JavaScript implementation
- HTML/CSS interface

## Usage
1. Enter your member information (type, service type, branch)
2. Input your date information (DOEAF, active duty dates, etc.)
3. Add service periods
4. Click "Calculate PEBD" to see results

## Repository Structure
- `app.py` - Main Streamlit application
- `pebd_calculations.py` - Original calculation functions
- `calculation_core.py` - Core calculation functions (refactored)
- `date_utils.py` - Date utility functions
- `service_period_calculator.py` - Service period calculations
- `error_handlers.py` - Error handling utilities
- `javascript_calculator.js` - Client-side JavaScript implementation
- `requirements.txt` - Python dependencies
- `README.md` - This file
- `test_pebd_calculator.py` - Unit tests
- `docs/pebd_calculator_documentation.md` - Documentation

## Testing
Run tests with: `python -m pytest test_pebd_calculator.py -v`

## Contributing
Contributions are welcome. Please follow the existing code style and add tests for new features.