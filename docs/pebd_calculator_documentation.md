# PEBD Calculator Documentation

## Overview
This calculator implements DoD Financial Management Regulation Volume 7A, Chapter 1 calculations for Pay Entry Base Dates (PEBD).

## Features
- Calculate PEBD based on DoD FMR regulations
- Support for different member types and service branches
- Service period calculations
- Lost time handling
- DEP (Delayed Entry Program) service calculation
- Break-in-service rules

## Architecture
The calculator is built with a modular architecture:
- `calculation_core.py`: Core calculation functions
- `date_utils.py`: Date utility functions
- `service_period_calculator.py`: Service period calculations
- `error_handlers.py`: Error handling utilities
- `javascript_calculator.js`: Client-side JavaScript implementation

## Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the web app: `streamlit run app.py`

## Usage
1. Enter member information (type, service type, branch)
2. Input date information (DOEAF, active duty dates, etc.)
3. Add service periods
4. Click "Calculate PEBD" to see results

## Client-Side Implementation
The calculator can also be run client-side in a browser:
- HTML/CSS/JavaScript implementation
- No server-side dependencies
- Self-contained functionality

## Testing
The calculator includes comprehensive tests to ensure accuracy:
- Unit tests for calculation functions
- Integration tests for full workflows
- Error handling tests
- Performance tests

## Contributing
Contributions are welcome. Please follow the existing code style and add tests for new features.