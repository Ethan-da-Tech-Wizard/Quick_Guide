#!/usr/bin/env bash
# ==============================================================================
# Program: qg.sh
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Unix/macOS environment launcher script for QuickGuide.
#          Verifies Python 3 runtime availability, creates and activates a
#          local virtual environment (.venv), installs project dependencies,
#          and launches the FastAPI backend web server.
# ==============================================================================
set -e

echo ""
echo "============================================"
echo "  QuickGuide (QG) - PDF Search & Navigation"
echo "============================================"
echo ""

# Step 1: Check Python 3 runtime availability
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed."
    echo "        Please install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
fi

echo "[OK] $(python3 --version) detected"

# Step 2: Navigate to script root directory
cd "$(dirname "$0")"

# Step 3: Create virtual environment if not already initialized
if [ ! -d ".venv" ]; then
    echo ""
    echo "[*] Creating virtual environment..."
    python3 -m venv .venv
fi

# Step 4: Activate local virtual environment
source .venv/bin/activate

# Step 5: Install and verify dependencies
echo ""
echo "[*] Checking dependencies..."
pip install -r requirements.txt --quiet 2>/dev/null || \
    pip install -r requirements.txt --no-cache-dir

# Step 6: Launch application server
echo ""
echo "[*] Starting QuickGuide..."
echo "    Open your browser to http://127.0.0.1:8080"
echo "    Press Ctrl+C to stop the server."
echo ""

cd src
python main.py
