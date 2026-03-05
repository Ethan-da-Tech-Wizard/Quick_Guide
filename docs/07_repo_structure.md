# QuickGuide (QG) — Repository Structure Plan

**Version:** 1.0
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
├── src/
│   ├── QuickGuide.Api/               # C# ASP.NET Core project
│   │   ├── QuickGuide.Api.csproj     # Project file with NuGet refs
│   │   ├── Program.cs                # Entry point, DI, route mapping
│   │   ├── Models/
│   │   │   ├── Document.cs           # Document entity
│   │   │   ├── TextChunk.cs          # Text chunk entity
│   │   │   ├── Highlight.cs          # Highlight entity
│   │   │   └── ApiModels.cs          # Request/response DTOs
│   │   ├── Services/
│   │   │   ├── PdfParserService.cs   # PdfPig text extraction
│   │   │   ├── TextChunkerService.cs # Token-windowed text splitting
│   │   │   ├── DocumentService.cs    # Document lifecycle (upload, list, delete)
│   │   │   ├── SearchService.cs      # Search orchestration (calls Python)
│   │   │   ├── HighlightService.cs   # Highlight CRUD
│   │   │   └── PythonBridgeService.cs# HTTP client → Python worker
│   │   ├── Data/
│   │   │   └── DatabaseService.cs    # SQLite setup, migrations, Dapper queries
│   │   └── wwwroot/                  # Static frontend files
│   │       ├── index.html            # App shell
│   │       ├── css/
│   │       │   └── app.css           # Cozy design system
│   │       ├── js/
│   │       │   ├── app.js            # UI logic, API calls, state
│   │       │   └── pdfviewer.js      # PDF.js integration + highlights
│   │       ├── lib/
│   │       │   └── pdfjs/            # PDF.js library (vendored)
│   │       └── img/
│   │           └── qg-logo.png       # QG logo for favicon + launcher
│   │
│   └── python_worker/                # Python ML microservice
│       ├── worker.py                 # Flask app: /embed, /search, /health
│       ├── embedder.py               # sentence-transformers wrapper
│       ├── vector_store.py           # FAISS index management
│       └── requirements.txt          # Python dependencies
│
├── tests/
│   ├── QuickGuide.Tests/             # C# xUnit test project
│   │   ├── QuickGuide.Tests.csproj
│   │   ├── PdfParserServiceTests.cs
│   │   ├── TextChunkerServiceTests.cs
│   │   └── SearchServiceTests.cs
│   └── python_worker/                # Python tests
│       ├── test_embedder.py
│       └── test_vector_store.py
│
├── data/                             # Created at runtime (gitignored)
│   ├── qg.db                         # SQLite database
│   ├── pdfs/                         # User's uploaded PDF files
│   └── vectors/                      # FAISS index files per document
│
├── qg.bat                            # Windows launcher (double-click to start)
├── qg.sh                             # macOS/Linux launcher
├── QuickGuide.sln                    # .NET solution file
├── README.md                         # Project overview + quickstart
├── QUICKSTART.md                     # Detailed setup instructions
├── LICENSE                           # MIT License
├── .gitignore                        # Ignores data/, bin/, obj/, .venv/, etc.
└── .editorconfig                     # Consistent code style
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
| C# files | PascalCase | `PdfParserService.cs` |
| C# classes | PascalCase | `DocumentService` |
| C# methods | PascalCase | `ExtractText()` |
| C# properties | PascalCase | `PageNumber` |
| Python modules | snake_case | `vector_store.py` |
| Python functions | snake_case | `generate_embeddings()` |
| API routes | kebab-case paths | `/api/documents/upload` |
| DB tables | snake_case | `text_chunks` |
| JS functions | camelCase | `loadPdf()` |
| CSS classes | BEM-like `qg-` prefix | `qg-search-input` |

## 4 Key Directories Explained

| Directory | Purpose | Gitignored? |
|---|---|---|
| `src/QuickGuide.Api/` | All C# backend code | No |
| `src/python_worker/` | Python ML worker (embedding + vector search) | No |
| `src/QuickGuide.Api/wwwroot/` | Static frontend (HTML/CSS/JS) served by C# | No |
| `data/` | Runtime data (DB, PDFs, FAISS indexes) | **Yes** |
| `tests/` | All automated tests (C# + Python) | No |
| `docs/` | Planning and reference documents | No |
