@echo off
REM DocSummarizer Setup and Run Script for Windows
REM This script sets up the environment and runs the application

REM Change to the directory where this script is located
cd /d "%~dp0"

echo.
echo  ============================================
echo       DocSummarizer - Setup and Run
echo  ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo.
    echo  Please install Python 3.10 or later from:
    echo  https://www.python.org/downloads/
    echo.
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Require Python 3.10+ (pyproject.toml says so, and the codebase uses
REM PEP 604 `X | None` type hints).
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    for /f "tokens=*" %%i in ('python --version') do set PYVER=%%i
    echo  [ERROR] %PYVER% is too old. DocSummarizer requires Python 3.10 or later.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYVER=%%i
echo  [OK] %PYVER% found
echo.

REM Check if Windows virtual environment exists and is valid
if not exist "venv\Scripts\activate.bat" (
    if exist "venv" (
        echo  [INFO] Removing incompatible virtual environment...
        rmdir /s /q venv
    )
    echo  [1/3] Creating virtual environment...
    echo       This only happens once.
    echo.
    python -m venv venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment created
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if dependencies need to be installed
pip show llama-cpp-python >nul 2>&1
if errorlevel 1 (
    echo  [2/3] Installing DocSummarizer + dependencies...
    echo       This may take 5-10 minutes on first run.
    echo       (Compiling AI engine for your system)
    echo.
    echo       Please wait...
    echo.
    REM Note: no --quiet. The llama-cpp-python compile is the slow step; if it
    REM fails, we want the user to see the actual error rather than a generic
    REM "Failed to install dependencies" message.
    pip install -e ".[runtime]"
    if errorlevel 1 (
        echo.
        echo  [ERROR] Failed to install dependencies. See output above.
        pause
        exit /b 1
    )
    echo  [OK] Dependencies installed
    echo.
) else (
    echo  [OK] Dependencies already installed
    echo.
)

echo  [3/3] Starting DocSummarizer...
echo.
echo  ============================================
echo       The GUI window will open shortly
echo  ============================================
echo.

REM Run the application
python run.py

REM Deactivate virtual environment
deactivate

echo.
echo  DocSummarizer closed.
pause
