"""
Analysis of current PEBD calculator structure
"""

import os
import sys

def analyze_structure():
    """Analyze the current project structure"""
    print("=== Current PEBD Calculator Structure Analysis ===")

    # List all files
    files = os.listdir('.')
    print(f"Files in current directory: {files}")

    # Analyze key files
    print("\n=== File Analysis ===")

    # Check app.py
    if 'app.py' in files:
        with open('app.py', 'r') as f:
            app_content = f.read()
        print(f"app.py: {len(app_content)} characters")
        print(f"app.py imports: {app_content.count('import')}")

    # Check pebd_calculations.py
    if 'pebd_calculations.py' in files:
        with open('pebd_calculations.py', 'r') as f:
            calc_content = f.read()
        print(f"pebd_calculations.py: {len(calc_content)} characters")
        print(f"pebd_calculations.py functions: {calc_content.count('def ')}")

    # Check requirements.txt
    if 'requirements.txt' in files:
        with open('requirements.txt', 'r') as f:
            req_content = f.read()
        print(f"requirements.txt: {len(req_content)} lines")
        print(f"Dependencies: {req_content.strip().split(chr(10))}")

    print("\n=== Current Architecture ===")
    print("1. Main application: app.py (Streamlit interface)")
    print("2. Core calculations: pebd_calculations.py (functions)")
    print("3. Dependencies: requirements.txt (streamlit, pandas, numpy)")

    print("\n=== Key Issues Identified ===")
    print("1. All logic in single file (pebd_calculations.py)")
    print("2. No clear separation of concerns")
    print("3. Limited error handling")
    print("4. No modular design")
    print("5. No performance optimizations")
    print("6. No comprehensive testing")

    print("\n=== Improvement Areas ===")
    print("1. Modularize calculations into separate files")
    print("2. Add comprehensive error handling")
    print("3. Implement performance optimizations")
    print("4. Add unit tests")
    print("5. Create client-side implementation")
    print("6. Improve code documentation")

if __name__ == "__main__":
    analyze_structure()