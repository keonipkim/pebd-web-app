#!/bin/bash

# Setup script for PEBD Web App
echo "Setting up PEBD Web App environment..."

# Create virtual environment
python -m venv venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install requirements
pip install -r requirements.txt

echo "Setup complete! To run the app:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run: streamlit run app.py"