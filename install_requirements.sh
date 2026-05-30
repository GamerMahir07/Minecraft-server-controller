#!/bin/bash

# Check if the requirements installer exists
if [ ! -f "install_requirements.py" ]; then
    echo ""
    echo "ERROR: install_requirements.py was not found!"
    echo "Make sure this script is in the same folder as install_requirements.py."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 >/dev/null 2>&1; then
    echo ""
    echo "ERROR: Python 3 is not installed or not in PATH!"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Run installer
python3 install_requirements.py

echo ""
read -p "Press Enter to continue..."