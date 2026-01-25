@echo off
REM DocSummarizer Setup and Run Script for Windows
REM This script sets up the environment and runs the application

echo ============================================
echo  DocSummarizer - Setup and Run
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.10 or later from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Python found. Checking dependencies...
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies (this may take a few minutes on first run)...
pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Starting DocSummarizer...
echo.

REM Run the application
python run.py

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat
