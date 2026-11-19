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
# set -e aborts the script on the first failing command, so a failed venv creation or
# an unreadable requirements file stops the launch instead of starting a half-set-up app.
# (The `|| ...` fallback on the pip line is how an expected failure is tolerated.)
set -e

echo ""
echo "============================================"
echo "  QuickGuide (QG) - PDF Search & Navigation"
echo "============================================"
echo ""

# Only checks that python3 exists, not its version. The README asks for 3.11+, and the
# code uses `X | None` annotations, which need at least 3.10.
# Step 1: Check Python 3 runtime availability
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed."
    echo "        Please install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
fi

echo "[OK] $(python3 --version) detected"

# Step 2: Navigate to script root directory
# Run from the script's own folder so .venv and requirements.txt resolve no matter
# where the script was invoked from. "$0" is quoted to survive spaces in the path.
cd "$(dirname "$0")"

# Step 3: Create virtual environment if not already initialized
# The virtual environment keeps dependencies (PyTorch etc.) out of the system Python.
# It is created once and reused on later launches.
if [ ! -d ".venv" ]; then
    echo ""
    echo "[*] Creating virtual environment..."
    python3 -m venv .venv
fi

# Step 4: Activate local virtual environment
# `source` modifies this shell, so later `pip` and `python` resolve to the venv copies.
source .venv/bin/activate

# Step 5: Install and verify dependencies
echo ""
echo "[*] Checking dependencies..."
# First try a quiet install using pip's cache. If that fails (network error, corrupt
# cache), retry once with --no-cache-dir and visible output so the user can see why.
# On a repeat run with everything installed this is a fast no-op. The first run
# downloads large packages and needs network access.
pip install -r requirements.txt --quiet 2>/dev/null || \
    pip install -r requirements.txt --no-cache-dir

# Step 6: Launch application server
echo ""
echo "[*] Starting QuickGuide..."
echo "    Open your browser to http://127.0.0.1:8080"
echo "    Press Ctrl+C to stop the server."
echo ""

# main.py uses flat imports (`from config import ...`), so it must run with src/ as
# the working directory. This `cd` is deliberate.
cd src
# Runs in the foreground until Ctrl+C. main.py also opens the default browser.
python main.py
