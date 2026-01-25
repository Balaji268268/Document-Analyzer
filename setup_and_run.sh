#!/bin/bash
# DocSummarizer Setup and Run Script for Linux/macOS
# This script sets up the environment and runs the application

echo "============================================"
echo " DocSummarizer - Setup and Run"
echo "============================================"
echo

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed."
    echo "Please install Python 3.10 or later:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  macOS: brew install python3"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi

echo "Python found: $(python3 --version)"
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment."
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies (this may take a few minutes on first run)..."
pip install -r requirements.txt --quiet

if [ $? -ne 0 ]; then
    echo "Failed to install dependencies."
    exit 1
fi

echo
echo "Starting DocSummarizer..."
echo

# Run the application
python run.py

# Deactivate virtual environment
deactivate
