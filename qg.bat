@echo off
REM Program: Quick_Guide - qg.bat
REM Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
REM Last Modified: 2026-11-18
REM Purpose: Windows launcher that checks for Python, creates a virtual environment, installs requirements and starts the QuickGuide server.
setlocal enabledelayedexpansion

echo.
echo ============================================
echo   QuickGuide (QG) - PDF Search ^& Navigation
echo ============================================
echo.

:: Check Python
:: 'where python' succeeds only if python can be found on the PATH
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Please install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Show Python version
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo [OK] %%v detected

:: Navigate to project root
cd /d "%~dp0"

:: Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo.
    echo [*] Creating virtual environment...
    python -m venv .venv
)

:: 'call' runs the activate script and then returns here
:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Install dependencies
echo.
echo [*] Checking dependencies...
pip install -r requirements.txt --quiet 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies failed to install.
    echo           Trying with --no-cache-dir...
    pip install -r requirements.txt --no-cache-dir
)

:: Run main.py from inside src/ so its imports work
:: Start the application
echo.
echo [*] Starting QuickGuide...
echo     Open your browser to http://127.0.0.1:8080
echo     Press Ctrl+C to stop the server.
echo.

cd src
python main.py

:: Deactivate on exit
call deactivate 2>nul
pause
