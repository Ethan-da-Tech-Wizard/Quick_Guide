# Files 1 of 1 — QuickGuide

[All pages](../FILE_GUIDE.md) · [Project guide](../PROJECT_GUIDE.md)

| File | Role and useful details |
| --- | --- |
| [.editorconfig](../../.editorconfig) | Tracked .editorconfig resource in .; 228 bytes. |
| [.github/workflows/ci.yml](../../.github/workflows/ci.yml) | GitHub Actions workflow for ci; defines automation triggers, jobs, and build/check steps. |
| [.gitignore](../../.gitignore) | Defines local data, credentials, dependencies, and generated outputs that Git should leave untracked. |
| [LICENSE](../../LICENSE) | Preserved license, copyright, or attribution terms; read the full text before reusing the covered component. |
| [PROJECT_NOTES.md](../../PROJECT_NOTES.md) | Preserved detailed setup, usage, architecture, and development notes from the earlier README. |
| [QUICKSTART.md](../../QUICKSTART.md) | Documentation: QuickGuide — Detailed Setup Guide. Covers Step 1: Install Python 3.11+; Windows; macOS. |
| [README.md](../../README.md) | Project overview, current status, entry points, setup navigation, and documentation links. |
| [debug_browser.py](../../debug_browser.py) | Python implementation of debug browser. Defines `run`. |
| [docs/01_problem_statement.md](../../docs/01_problem_statement.md) | Documentation: QuickGuide (QG) — Problem Statement. Covers The Problem; Who It Affects; Why Existing Solutions Fall Short. |
| [docs/02_product_requirements.md](../../docs/02_product_requirements.md) | Documentation: QuickGuide (QG) — Product Requirements Document (PRD). Covers 1 Product Vision; 2 Target Personas; 3 User Stories. |
| [docs/03_functional_requirements.md](../../docs/03_functional_requirements.md) | Documentation: QuickGuide (QG) — Functional Requirements Document (FRD). Covers 1 PDF Ingestion Module; FR-ING-01 — Select & Upload PDF; FR-ING-02 — Extract Text. |
| [docs/04_system_requirements.md](../../docs/04_system_requirements.md) | Documentation: QuickGuide (QG) — System Requirements Document (SRD). Covers 1 Hardware Requirements; 2 Operating System Support; 3 Software Dependencies. |
| [docs/05_architecture.md](../../docs/05_architecture.md) | Documentation: QuickGuide (QG) — Architecture Document. Covers 1 High-Level Architecture; 2 Data-Flow Pipeline; 2.1 Ingestion Flow. |
| [docs/06_scope_and_milestones.md](../../docs/06_scope_and_milestones.md) | Documentation: QuickGuide (QG) — Scope Lock & Milestones. Covers 1 Scope Boundary; In Scope (v1.0); Out of Scope (v1.0). |
| [docs/07_repo_structure.md](../../docs/07_repo_structure.md) | Documentation: QuickGuide (QG) — Repository Structure. Covers 1 Project Layout; 2 PDF Storage Location; 3 Naming Conventions. |
| [docs/08_risk_register.md](../../docs/08_risk_register.md) | Documentation: QuickGuide (QG) — Risk Register. Covers Risk Matrix Key; R-01 🟡 — Embedding Model Download on First Run; R-02 🟡 — Large PDF Ingestion Exceeds 2-Minute Target. |
| [docs/DEPENDENCIES.csv](../../docs/DEPENDENCIES.csv) | Machine-readable inventory of declared and locked dependencies, versions, reported licenses, and evidence URLs. |
| [docs/FILE_GUIDE.md](../../docs/FILE_GUIDE.md) | Index of the complete tracked-file guide, with one entry for every file and links to the paginated descriptions. |
| [docs/LICENSE_REVIEW.md](../../docs/LICENSE_REVIEW.md) | Original-code license, preserved component notices, dependency-license evidence, and unresolved distribution questions. |
| [docs/PROJECT_GUIDE.md](../../docs/PROJECT_GUIDE.md) | Maintainer orientation: purpose, important entry points, source layout, commands, and project-specific boundaries. |
| [docs/file-guide/files-001.md](../../docs/file-guide/files-001.md) | One page of the tracked-file catalog; links each listed path to its role and source-derived details. |
| [generate_test_pdf.py](../../generate_test_pdf.py) | Python implementation of generate test pdf. Connects `fitz`, `os`. |
| [qg.bat](../../qg.bat) | Command-line automation for qg; review prerequisites and side effects before executing. |
| [qg.sh](../../qg.sh) | Command-line automation for qg; review prerequisites and side effects before executing. |
| [requirements.txt](../../requirements.txt) | Python dependency requirements and optional dependency groups; install with the project’s documented interpreter and environment. |
| [src/config.py](../../src/config.py) | QuickGuide (QG) — Application Configuration Connects `os`, `pathlib`. |
| [src/database.py](../../src/database.py) | QuickGuide (QG) — Database Service SQLite setup, migrations, and Dapper-style queries. Defines `get_connection`, `init_db`. |
| [src/main.py](../../src/main.py) | QuickGuide (QG) — FastAPI Application Defines `lifespan`, `serve_frontend`, `upload_document`, `list_documents`, `get_document`, `get_document_status` and 8 more top-level symbols. |
| [src/models.py](../../src/models.py) | QuickGuide (QG) — Pydantic Models Request/response DTOs and API models. Defines `SearchRequest`, `HighlightCreate`, `HighlightUpdate`, `DocumentResponse`, `SearchResult`, `HighlightResponse` and 1 more top-level symbols. |
| [src/services/__init__.py](../../src/services/__init__.py) | Initializes the src/services Python package and its public imports. |
| [src/services/chunker.py](../../src/services/chunker.py) | QuickGuide (QG) — Text Chunker Service Splits extracted text into overlapping token-windowed chunks. Defines `chunk_text`, `_find_word_offset`. |
| [src/services/documents.py](../../src/services/documents.py) | QuickGuide (QG) — Document Service Document lifecycle: upload, ingest, list, delete. Defines `get_progress`, `_set_progress`, `upload_and_ingest`, `list_documents`, `get_document`, `get_pdf_path` and 2 more top-level symbols. |
| [src/services/embedder.py](../../src/services/embedder.py) | QuickGuide (QG) — Embedding Service Generates vector embeddings using sentence-transformers. Defines `get_model`, `embed_texts`, `embed_query`. |
| [src/services/highlights.py](../../src/services/highlights.py) | QuickGuide (QG) — Highlight Service CRUD operations for persistent highlights. Defines `add_highlight`, `get_highlights`, `get_highlight`, `update_highlight`, `delete_highlight`. |
| [src/services/pdf_parser.py](../../src/services/pdf_parser.py) | QuickGuide (QG) — PDF Parser Service Extracts text from PDF files using PyMuPDF (fitz). Defines `extract_text`, `get_page_count`, `search_text_on_page`. |
| [src/services/search.py](../../src/services/search.py) | QuickGuide (QG) — Search Service Orchestrates semantic search: embed query → FAISS search → enrich results. Defines `semantic_search`. |
| [src/services/vector_store.py](../../src/services/vector_store.py) | QuickGuide (QG) — Vector Store Service FAISS index management with numpy fallback. Defines `VectorStore`, `get_store`, `delete_store`. |
| [src/static/css/app.css](../../src/static/css/app.css) | Presentation rules for app; controls layout, typography, color, states, and responsive behavior. |
| [src/static/img/qg-favicon.svg](../../src/static/img/qg-favicon.svg) | Image or interface asset for qg favicon. Source/asset rights remain separate from software-license terms. |
| [src/static/index.html](../../src/static/index.html) | Browser document: QuickGuide — PDF Search & Navigation; provides page structure and may include inline styles or application logic. |
| [src/static/js/app.js](../../src/static/js/app.js) | Source module for app; defines `api`, `showToast`, `loadDocuments`, `uploadDocument`, `selectDocument`, `deleteDocument`, `initScrollContainer` and 19 more symbols. |
| [test_doc.pdf](../../test_doc.pdf) | PDF document for test doc; 1,330 bytes. Consult the project guide and component notices for its purpose and distribution limits. |
| [tests/__init__.py](../../tests/__init__.py) | Initializes the tests Python package and its public imports. |
| [tests/test_chunker.py](../../tests/test_chunker.py) | QuickGuide — Text Chunker Tests Defines `test_chunk_text_basic`, `test_chunk_text_empty`, `test_chunk_text_short`, `test_chunk_text_overlap`, `test_chunk_text_preserves_page_number`, `test_chunk_text_sequential_index`. |
| [tests/test_database.py](../../tests/test_database.py) | QuickGuide — Database Tests Defines `test_database_schema`, `test_cascade_delete`. |
