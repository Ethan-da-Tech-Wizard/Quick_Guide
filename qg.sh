#!/usr/bin/env bash
set -e

echo ""
echo "============================================"
echo "  QuickGuide (QG) - PDF Search & Navigation"
echo "============================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed."
    echo "        Please install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
fi

echo "[OK] $(python3 --version) detected"

# Navigate to script directory
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo ""
    echo "[*] Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo ""
echo "[*] Checking dependencies..."
pip install -r requirements.txt --quiet 2>/dev/null || \
    pip install -r requirements.txt --no-cache-dir

# Start the application
echo ""
echo "[*] Starting QuickGuide..."
echo "    Open your browser to http://127.0.0.1:8080"
echo "    Press Ctrl+C to stop the server."
echo ""

cd src
python main.py
