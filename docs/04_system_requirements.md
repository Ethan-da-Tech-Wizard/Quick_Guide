# QuickGuide (QG) — System Requirements Document (SRD)

**Version:** 1.0
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
| macOS | 12 Monterey | .NET 8 and Python supported |
| Linux | Ubuntu 22.04 / Fedora 38 | .NET 8 and Python supported |
| Android / iOS | Any modern browser | Access via `http://localhost:8080` |

> [!NOTE]
> Mobile access is via the web browser — no native app install needed. The backend must be running on the same network or device.

## 3 Software Dependencies

### 3.1 C# Backend (Primary — built for speed)

| Component | Technology | Version | Rationale |
|---|---|---|---|
| **Runtime** | .NET 8 SDK | 8.0+ | Cross-platform, high-performance |
| **Web framework** | ASP.NET Core Minimal API | 8.0 | Fast HTTP, built-in DI, static file serving |
| **PDF parsing** | PdfPig | latest | Pure C#, no native dependencies, page-level text extraction |
| **Database** | SQLite via Microsoft.Data.Sqlite | latest | Zero-config, file-based, fast |
| **ORM** | Dapper | latest | Lightweight micro-ORM for C# |
| **JSON** | System.Text.Json | built-in | High-performance serialization |
| **Process management** | System.Diagnostics.Process | built-in | Launches Python worker subprocess |

### 3.2 Python ML Worker (for embedding + vector search)

| Component | Technology | Version | Rationale |
|---|---|---|---|
| **Runtime** | Python | 3.11+ | ML ecosystem support |
| **Embedding model** | sentence-transformers | latest | `all-MiniLM-L6-v2`: 80 MB, 384-dim, CPU-friendly |
| **Vector index** | FAISS-cpu | latest | Efficient ANN search, widely supported |
| **HTTP server** | Flask | latest | Lightweight API for C# → Python communication |
| **Protocol** | HTTP on localhost:5001 | — | C# backend calls Python worker via REST |

### 3.3 Frontend

| Component | Technology | Rationale |
|---|---|---|
| **PDF rendering** | PDF.js (Mozilla) | Industry-standard browser PDF viewer |
| **UI** | HTML / CSS / Vanilla JavaScript | Zero build step; served by C# backend |
| **Font** | Nunito (Google Fonts, self-hosted) | Warm, rounded, cozy aesthetic |

### 3.4 Build / Install Prerequisites

| Tool | Version | Notes |
|---|---|---|
| .NET SDK | 8.0+ | For building and running the C# backend |
| Python | 3.11+ | For the ML worker only |
| pip | bundled with Python | Installs sentence-transformers + FAISS |
| Git | any | For version control |

> [!IMPORTANT]
> **Two runtimes required:** .NET 8 SDK (for the C# backend) and Python 3.11+ (for the ML embedding worker). Both are free and cross-platform.

## 4 Performance Targets

| Metric | Target |
|---|---|
| PDF text extraction (1,000 pages) | ≤ 30 s (C# PdfPig) |
| Embedding generation (1,000 pages) | ≤ 90 s (Python worker) |
| Total ingestion (1,000 pages) | ≤ 120 s |
| Query → results | ≤ 3 s |
| App start (backend + browser) | ≤ 5 s |
| Memory (idle, no PDF loaded) | ≤ 200 MB |
| Memory (1,000-page PDF active) | ≤ 500 MB |

## 5 Security & Privacy

- **No telemetry** — no external network calls (except first-time model download).
- **Local-only storage** — PDFs, text, and embeddings stay on the device.
- **Localhost binding** — C# backend binds to `127.0.0.1:8080`; Python worker to `127.0.0.1:5001`.
- **No authentication** — single-user, local application.

## 6 Deployment Strategy

| Platform | Delivery |
|---|---|
| Windows | `qg.bat` double-click launcher → starts backend + opens browser |
| macOS / Linux | `qg.sh` launcher script |
| Mobile | Access via browser on same network |
| Packaged (future) | Self-contained .NET publish + PyInstaller bundle |

## 7 Architecture Constraints

1. **C# for all non-ML logic** — PDF parsing, API, database, file management all in C#.
2. **Python only for ML** — embedding generation and vector search in a separate Python process.
3. **No external servers** — everything on localhost.
4. **Zero frontend build step** — HTML/CSS/JS served as static files by the C# backend.
5. **SQLite only** — no database server installation required.
