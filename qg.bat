@echo off
:: ==============================================================================
:: Program: qg.bat
:: Programmer: Ethan-da-Tech-Wizard
:: Last Modified: November 18, 2026
:: Purpose: Windows environment launcher script for QuickGuide.
::          Verifies Python interpreter availability, establishes a local virtual
::          environment (.venv), installs required packages from requirements.txt,
::          and starts the FastAPI application server.
:: ==============================================================================
setlocal enabledelayedexpansion

echo.
echo ============================================
echo   QuickGuide (QG) - PDF Search ^& Navigation
echo ============================================
echo.

:: Step 1: Check Python availability in system PATH
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Please install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Step 2: Show detected Python version
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v detected

:: Step 3: Navigate to project root directory
cd /d "%~dp0"

:: Step 4: Create virtual environment if it does not exist
if not exist ".venv" (
    echo.
    echo [*] Creating virtual environment...
    python -m venv .venv
)

:: Step 5: Activate virtual environment
call .venv\Scripts\activate.bat

:: Step 6: Install dependencies
echo.
echo [*] Checking dependencies...
pip install -r requirements.txt --quiet 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies failed to install.
    echo           Trying with --no-cache-dir...
    pip install -r requirements.txt --no-cache-dir
)

:: Step 7: Launch QuickGuide server
echo.
echo [*] Starting QuickGuide...
echo     Open your browser to http://127.0.0.1:8080
echo     Press Ctrl+C to stop the server.
echo.

cd src
python main.py

:: Step 8: Deactivate environment on script exit
call deactivate 2>nul
pause
