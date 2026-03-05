# QuickGuide — Detailed Setup Guide

## Step 1: Install Python 3.11+

### Windows
1. Go to https://www.python.org/downloads/
2. Download the latest Python 3.11+ installer
3. **Important:** Check "Add Python to PATH" during installation
4. Click "Install Now"
5. Verify: Open Command Prompt and type `python --version`

### macOS
```bash
brew install python@3.12
```
Or download from https://www.python.org/downloads/

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

## Step 2: Get QuickGuide

### Option A: Clone from GitHub
```bash
git clone https://github.com/Ethan_da_Tech_Wizard/Quick_Guide.git
cd Quick_Guide
```

### Option B: Download ZIP
Download from GitHub and extract to a folder of your choice.

## Step 3: Run QuickGuide

### Windows (Easiest)
Double-click `qg.bat` in the Quick_Guide folder.

### macOS / Linux
```bash
chmod +x qg.sh
./qg.sh
```

### Manual Method
```bash
cd Quick_Guide
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cd src
python main.py
```

## Step 4: First Run

On first run, the app will:
1. Download the AI model (~80 MB) — this requires internet ONE TIME
2. After downloading, everything works offline
3. Your browser opens to `http://127.0.0.1:8080`

## Where to Store Your PDFs

You don't need to pre-load PDFs anywhere! Simply:
1. Click "Select a Document" in the app
2. Pick any PDF from your computer
3. The app copies it to `Quick_Guide/data/pdfs/` automatically

## Troubleshooting

| Problem | Solution |
|---|---|
| `python` not found | Reinstall Python with "Add to PATH" checked |
| Port 8080 in use | Set `QG_PORT=8081` environment variable |
| FAISS install fails | The app falls back to numpy search automatically |
| Slow first search | The AI model loads on first query (~2-3 seconds) |
| PDF doesn't render | Make sure the PDF contains text (not scanned images) |
