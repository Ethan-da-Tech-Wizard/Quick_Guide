#!/usr/bin/env bash
# Program: Quick_Guide - qg.sh
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Launcher for macOS/Linux that checks for Python 3, creates a virtual environment, installs requirements and starts the QuickGuide server.
# Stop the script immediately if any command fails
set -e

echo ""
echo "============================================"
echo "  QuickGuide (QG) - PDF Search & Navigation"
echo "============================================"
echo ""

# Check Python
# 'command -v' succeeds only if python3 can be found on the PATH
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed."
    echo "        Please install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
fi

echo "[OK] $(python3 --version) detected"

# Navigate to script directory
cd "$(dirname "$0")"

# A virtual environment keeps this project's packages separate from the rest of the system
# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo ""
    echo "[*] Creating virtual environment..."
    python3 -m venv .venv
fi

# 'source' runs the activate script in this shell so python and pip use the .venv copies
# Activate virtual environment
source .venv/bin/activate

# The first pip tries quietly; if it fails, the second retries without the cache
# Install dependencies
echo ""
echo "[*] Checking dependencies..."
pip install -r requirements.txt --quiet 2>/dev/null || \
    pip install -r requirements.txt --no-cache-dir

# Run main.py from inside src/ so its imports work
# Start the application
echo ""
echo "[*] Starting QuickGuide..."
echo "    Open your browser to http://127.0.0.1:8080"
echo "    Press Ctrl+C to stop the server."
echo ""

cd src
python main.py
