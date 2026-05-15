#!/bin/bash
# DocSummarizer Setup and Run Script for Linux/macOS
# This script sets up the environment and runs the application
set -u

# Get script directory and cd to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo " ============================================"
echo "      DocSummarizer - Setup and Run"
echo " ============================================"
echo ""

# Check if Python is installed
if ! command -v python3 &>/dev/null; then
	echo " [ERROR] Python 3 is not installed."
	echo ""
	echo " Please install Python 3.10 or later:"
	echo "   Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
	echo "   macOS: brew install python3"
	echo "   Fedora: sudo dnf install python3 python3-pip"
	echo ""
	exit 1
fi

# Require Python 3.10+ (pyproject.toml says so, and we use PEP 604 `X | None`).
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
	PYVER=$(python3 --version)
	echo " [ERROR] $PYVER is too old. DocSummarizer requires Python 3.10 or later."
	exit 1
fi

PYVER=$(python3 --version)
echo " [OK] $PYVER found"
echo ""

# Check if virtual environment exists and is valid
if [ ! -f "venv/bin/activate" ]; then
	if [ -d "venv" ]; then
		echo " [INFO] Removing incompatible virtual environment..."
		rm -rf venv
	fi
	echo " [1/3] Creating virtual environment..."
	echo "       This only happens once."
	echo ""
	if ! python3 -m venv venv; then
		echo " [ERROR] Failed to create virtual environment."
		exit 1
	fi
	echo " [OK] Virtual environment created"
	echo ""
fi

# Activate virtual environment
# shellcheck source=/dev/null
source venv/bin/activate

# Check if dependencies need to be installed
if ! pip show llama-cpp-python &>/dev/null; then
	echo " [2/3] Installing DocSummarizer + dependencies..."
	echo "       This may take 5-10 minutes on first run."
	echo "       (Compiling AI engine for your system)"
	echo ""
	echo "       Please wait..."
	echo ""
	# Note: no --quiet. The llama-cpp-python compile is the slow step; if it
	# fails, we want the user to see the actual error rather than a generic
	# "Failed to install dependencies" message.
	if ! pip install -e .; then
		echo ""
		echo " [ERROR] Failed to install dependencies. See output above."
		exit 1
	fi
	echo " [OK] Dependencies installed"
	echo ""
else
	echo " [OK] Dependencies already installed"
	echo ""
fi

echo " [3/3] Starting DocSummarizer..."
echo ""
echo " ============================================"
echo "      The GUI window will open shortly"
echo " ============================================"
echo ""

# Run the application
python run.py

# Deactivate virtual environment
deactivate

echo ""
echo " DocSummarizer closed."
