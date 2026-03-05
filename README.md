# QuickGuide (QG) 📖🔍

**Upload a PDF. Ask a question. Get taken straight to the answer — highlighted and ready to read.**

QuickGuide is a local-first PDF search and navigation tool. It uses **semantic search** (AI-powered vector embeddings) to understand your questions and find the right answers inside large PDF documents. All processing happens on your own device — no cloud, no internet required for core features.

---

## ✨ Features

- **🔍 Natural-Language Search** — Ask questions in plain English, not just keywords
- **📄 One-Click Navigation** — Click a result to jump directly to the relevant page
- **🖍️ Smart Highlighting** — Matching phrases are highlighted in your chosen color (yellow default)
- **◀ ▶ Multi-Match Jumping** — Navigate between all highlighted sections with one click
- **🎨 Color Customization** — Change highlight colors with a picker or preset swatches
- **📱 Cross-Platform** — Works on Windows, macOS, Linux, and mobile browsers
- **🔒 100% Local** — Your documents never leave your device

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** — [Download here](https://www.python.org/downloads/)

### Run

**Windows:**
```bash
qg.bat
```

**macOS / Linux:**
```bash
chmod +x qg.sh
./qg.sh
```

That's it! Your browser will open automatically to `http://127.0.0.1:8080`.

### Manual Setup
```bash
# Clone the repo
git clone https://github.com/Ethan_da_Tech_Wizard/Quick_Guide.git
cd Quick_Guide

# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the app
cd src
python main.py
```

## 📖 How to Use

1. **Select a Document** — Click "Select a Document" and pick any PDF from your file system
2. **Wait for Indexing** — The app extracts text and creates AI embeddings (1-2 minutes for 1,000 pages)
3. **Ask a Question** — Type a natural-language question in the search box
4. **Navigate & Highlight** — Click a result to jump to the answer. Use ◀ ▶ to jump between matches
5. **Customize Colors** — Use the color picker to change highlight colors

## 📂 Where Are PDFs Stored?

When you select a PDF in the UI, it is **automatically copied** to:
```
Quick_Guide/data/pdfs/
```
You don't need to put files there manually. The `data/` directory is created on first run and is gitignored.

## 🏗️ Architecture

| Component | Technology | Purpose |
|---|---|---|
| **Backend** | Python + FastAPI | REST API, PDF parsing, database |
| **PDF Parsing** | PyMuPDF | Text extraction from PDFs |
| **Embeddings** | sentence-transformers | AI-powered semantic understanding |
| **Vector Search** | FAISS | Fast similarity search |
| **Database** | SQLite | Documents, chunks, highlights |
| **Frontend** | HTML/CSS/JS + PDF.js | Cozy web interface + PDF viewer |

## 📄 Documentation

All planning and design documents are in the [`docs/`](docs/) directory:
- [Problem Statement](docs/01_problem_statement.md)
- [Product Requirements](docs/02_product_requirements.md)
- [Functional Requirements](docs/03_functional_requirements.md)
- [System Requirements](docs/04_system_requirements.md)
- [Architecture](docs/05_architecture.md)
- [Scope & Milestones](docs/06_scope_and_milestones.md)
- [Repository Structure](docs/07_repo_structure.md)
- [Risk Register](docs/08_risk_register.md)

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.
