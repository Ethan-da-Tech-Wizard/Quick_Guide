@echo off
setlocal enabledelayedexpansion

echo.
echo ============================================
echo   QuickGuide (QG) - PDF Search ^& Navigation
echo ============================================
echo.

:: Check Python
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
