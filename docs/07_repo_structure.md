# QuickGuide (QG) — Repository Structure

**Version:** 1.1
**Date:** 2026-03-05

---

## 1 Project Layout

```
Quick_Guide/
├── .github/
│   └── workflows/
│       └── ci.yml                     # GitHub Actions CI (build + test)
│
├── docs/                              # All planning documents
│   ├── 01_problem_statement.md
│   ├── 02_product_requirements.md
│   ├── 03_functional_requirements.md
│   ├── 04_system_requirements.md
│   ├── 05_architecture.md
│   ├── 06_scope_and_milestones.md
│   ├── 07_repo_structure.md
│   └── 08_risk_register.md
│
├── src/                               # All application source code
│   ├── main.py                        # FastAPI entry point, all route definitions
│   ├── config.py                      # Paths, server settings, model/search params
│   ├── models.py                      # Pydantic request/response models
│   ├── database.py                    # SQLite connection, schema init, CRUD queries
│   │
│   ├── services/                      # Business logic layer
│   │   ├── __init__.py
│   │   ├── pdf_parser.py              # PyMuPDF text extraction + bounding-box search
│   │   ├── chunker.py                 # Overlapping token-windowed text splitting
│   │   ├── embedder.py                # sentence-transformers wrapper (lazy load + batch)
│   │   ├── vector_store.py            # FAISS index management (with numpy fallback)
│   │   ├── search.py                  # Semantic search orchestration
│   │   ├── documents.py               # Document lifecycle + ingestion pipeline
│   │   └── highlights.py              # Highlight CRUD
│   │
│   └── static/                        # Frontend static files (served by FastAPI)
│       ├── index.html                 # App shell — layout, search panel, PDF viewer
│       ├── css/
│       │   └── app.css                # Cozy design system — warm colors, rounded corners
│       ├── js/
│       │   └── app.js                 # UI logic, API calls, PDF.js integration, state
│       └── img/
│           └── qg-favicon.svg         # QG logo used as favicon and launcher icon
│
├── tests/
│   ├── __init__.py
│   ├── test_chunker.py                # Unit tests for text chunking logic
│   └── test_database.py              # Unit tests for SQLite schema and cascade deletes
│
├── data/                             # Created at runtime (gitignored)
│   ├── qg.db                         # SQLite database
│   ├── pdfs/                         # User's uploaded PDF files
│   ├── vectors/                      # FAISS index files per document
│   └── models/                       # Cached sentence-transformers model (~80 MB)
│
├── qg.bat                            # Windows launcher (double-click to start)
├── qg.sh                             # macOS/Linux launcher
├── requirements.txt                  # Python package dependencies
├── README.md                         # Project overview + quickstart
├── QUICKSTART.md                     # Detailed setup instructions + troubleshooting
├── LICENSE                           # MIT License
├── .gitignore                        # Ignores data/, __pycache__/, .venv/, etc.
└── .editorconfig                     # Consistent code style across editors
```

## 2 PDF Storage Location

> [!IMPORTANT]
> **User PDF files are stored at:** `Quick_Guide/data/pdfs/`
>
> When a user clicks "Select a Document" in the UI, the selected PDF is **automatically copied** from wherever it lives on the user's file system into this managed directory. The user never needs to manually place files here.
>
> This directory is created automatically on first run and is gitignored (PDFs are not committed to version control).

## 3 Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Python modules | snake_case | `pdf_parser.py` |
| Python functions | snake_case | `extract_text()` |
| Python classes | PascalCase | `VectorStore` |
| Pydantic models | PascalCase | `SearchRequest` |
| API routes | kebab-case paths | `/api/documents/upload` |
| DB tables | snake_case | `text_chunks` |
| JS functions | camelCase | `loadDocuments()` |
| CSS classes | BEM-like `qg-` prefix | `qg-search-input` |

## 4 Key Directories Explained

| Directory | Purpose | Gitignored? |
|---|---|---|
| `src/` | All Python backend source code | No |
| `src/services/` | Modular business logic (parsing, embedding, search, highlights) | No |
| `src/static/` | Static frontend (HTML/CSS/JS) served by FastAPI | No |
| `data/` | Runtime data (DB, PDFs, FAISS indexes, model cache) | **Yes** |
| `tests/` | Automated Python unit tests | No |
| `docs/` | Planning and reference documents | No |
