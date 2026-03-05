# QuickGuide (QG) — System Requirements Document (SRD)

**Version:** 1.1
**Date:** 2026-03-05

---

## 1 Hardware Requirements

| Tier | CPU | RAM | Disk |
|---|---|---|---|
| **Minimum** | Dual-core 1.5 GHz | 4 GB | 500 MB free + PDF storage |
| **Recommended** | Quad-core 2.5 GHz | 8 GB | 2 GB free |

## 2 Operating System Support

| Platform | Minimum Version | Notes |
|---|---|---|
| Windows | 10 | Primary development target |
| macOS | 12 Monterey | Python supported |
| Linux | Ubuntu 22.04 / Fedora 38 | Python supported |
| Android / iOS | Any modern browser | Access via `http://localhost:8080` |

> [!NOTE]
> Mobile access is via the web browser — no native app install needed. The backend must be running on the same network or device.

## 3 Software Dependencies

### 3.1 Python Backend (single process — handles all logic and ML)

| Component | Technology | Version | Rationale |
|---|---|---|---|
| **Runtime** | Python | 3.11+ | ML ecosystem support; cross-platform |
| **Web framework** | FastAPI | 0.115.0+ | High-performance async API; built-in data validation |
| **ASGI server** | uvicorn[standard] | 0.30.0+ | Production-grade ASGI server for FastAPI |
| **PDF parsing** | PyMuPDF (fitz) | 1.24.0+ | Fast text extraction with character positions; no native dependencies |
| **File uploads** | python-multipart | 0.0.9+ | Multipart form-data support for FastAPI |
| **Async file I/O** | aiofiles | 24.1.0+ | Async file operations |
| **Database** | SQLite via Python stdlib `sqlite3` | built-in | Zero-config, file-based, fast |
| **Embedding model** | sentence-transformers | 3.0.0+ | `all-MiniLM-L6-v2`: 80 MB, 384-dim, CPU-friendly |
| **Vector index** | faiss-cpu | 1.8.0+ | Efficient ANN search (numpy fallback if unavailable) |
| **Numerics** | numpy | 1.26.0–<2.0.0 | Vector operations and numpy fallback search |

### 3.2 Frontend

| Component | Technology | Rationale |
|---|---|---|
| **PDF rendering** | PDF.js (Mozilla) | Industry-standard browser PDF viewer |
| **UI** | HTML / CSS / Vanilla JavaScript | Zero build step; served as static files by the FastAPI backend |
| **Font** | Nunito (Google Fonts, self-hosted) | Warm, rounded, cozy aesthetic |

### 3.3 Build / Install Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11+ | The only runtime required |
| pip | bundled with Python | Installs all dependencies from `requirements.txt` |
| Git | any | For version control |

> [!IMPORTANT]
> **One runtime required:** Python 3.11+ only. There is no separate .NET or C# dependency.

## 4 Performance Targets

| Metric | Target |
|---|---|
| PDF text extraction (1,000 pages) | ≤ 30 s (Python PyMuPDF) |
| Embedding generation (1,000 pages) | ≤ 90 s (sentence-transformers, batch=32) |
| Total ingestion (1,000 pages) | ≤ 120 s |
| Query → results | ≤ 3 s |
| App start (backend + browser) | ≤ 5 s |
| Memory (idle, no PDF loaded) | ≤ 200 MB |
| Memory (1,000-page PDF active) | ≤ 500 MB |

## 5 Security & Privacy

- **No telemetry** — no external network calls (except first-time model download).
- **Local-only storage** — PDFs, text, and embeddings stay on the device.
- **Localhost binding** — FastAPI backend binds to `127.0.0.1:8080` by default (configurable via `QG_HOST` / `QG_PORT` env vars).
- **No authentication** — single-user, local application.

## 6 Deployment Strategy

| Platform | Delivery |
|---|---|
| Windows | `qg.bat` double-click launcher → creates venv, installs deps, starts Python server, opens browser |
| macOS / Linux | `qg.sh` launcher script |
| Mobile | Access via browser on same network |
| Packaged (future) | PyInstaller bundle for zero-install distribution |

## 7 Architecture Constraints

1. **Python for all logic** — PDF parsing, API, database, file management, embeddings, and vector search all run in a single Python process.
2. **FastAPI as the web framework** — handles all HTTP routing, static file serving, and data validation.
3. **No external servers** — everything on localhost; no inter-process HTTP communication required.
4. **Zero frontend build step** — HTML/CSS/JS served as static files by the FastAPI backend.
5. **SQLite only** — no database server installation required.
6. **FAISS with numpy fallback** — if `faiss-cpu` is unavailable, flat cosine similarity via numpy is used automatically.
