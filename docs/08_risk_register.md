# QuickGuide (QG) — Risk Register

**Version:** 1.0
**Date:** 2026-03-05

---

## Risk Matrix Key

| Probability | Impact | Risk Level |
|---|---|---|
| High × High | 🔴 Critical | |
| High × Medium | 🟠 High | |
| Medium × Medium | 🟡 Medium | |
| Low × any | 🟢 Low | |

---

### R-01 🟡 — Embedding Model Download on First Run
| Field | Detail |
|---|---|
| **Category** | User Experience |
| **Probability** | Medium |
| **Impact** | Medium |
| **Description** | First run downloads the `all-MiniLM-L6-v2` model (~80 MB). This requires internet and may be slow. |
| **Mitigation** | Show a clear "Downloading AI model…" progress message. Cache in `data/models/`. Document in QUICKSTART.md. |
| **Contingency** | Bundle the model in the release package or provide a manual download link. |

### R-02 🟡 — Large PDF Ingestion Exceeds 2-Minute Target
| Field | Detail |
|---|---|
| **Category** | Performance |
| **Probability** | Medium |
| **Impact** | Medium |
| **Description** | A 2,000-page PDF with dense tables may exceed the 2-minute ingestion target. |
| **Mitigation** | Python PyMuPDF is fast for extraction. Batch embedding calls (32 chunks/batch). Background ingestion with progress updates. |
| **Contingency** | Show realistic progress; allow the user to search partially-ingested documents. |

### R-03 🟡 — PDF.js Rendering on Mobile Browsers
| Field | Detail |
|---|---|
| **Category** | Technical |
| **Probability** | Medium |
| **Impact** | Medium |
| **Description** | Large PDFs may render slowly or have layout issues on mobile browsers. |
| **Mitigation** | Render one page at a time; lazy-load pages; test on mobile Chrome and Safari. |
| **Contingency** | Offer a text-only snippet view on mobile for very large documents. |

### R-04 🟠 — Vector Search Accuracy Below 90%
| Field | Detail |
|---|---|
| **Category** | Technical |
| **Probability** | Medium |
| **Impact** | High |
| **Description** | `all-MiniLM-L6-v2` may not capture domain-specific terminology (e.g., construction codes). |
| **Mitigation** | Combine vector search with keyword matching (hybrid ranking). Tune chunk size and overlap. |
| **Contingency** | Swap to a larger model (`bge-base-en-v1.5`, 110 MB) or add a BM25 keyword fallback. |

### R-05 🟡 — Setup Complexity (Python + Dependencies)
| Field | Detail |
|---|---|
| **Category** | User Experience |
| **Probability** | Medium |
| **Impact** | Medium |
| **Description** | Users need Python 3.11+ installed. First-time setup includes virtual environment creation and dependency installation (~80 MB model download). |
| **Mitigation** | The `qg.bat` / `qg.sh` launcher automates venv creation and pip install, printing clear instructions if Python is missing. QUICKSTART.md has step-by-step setup. |
| **Contingency** | Provide a Docker Compose option for zero-install. Future: bundle with PyInstaller for a single-executable distribution. |

### R-06 🟢 — FAISS Wheel Unavailable on Some Platforms
| Field | Detail |
|---|---|
| **Category** | Technical |
| **Probability** | Low |
| **Impact** | Medium |
| **Description** | `faiss-cpu` may not have pre-built wheels for every OS/Python version combination. |
| **Mitigation** | Fall back to a pure-Python flat cosine similarity search if FAISS install fails. |
| **Contingency** | Use `usearch` or `hnswlib` as alternative vector indices. |

### R-07 🟢 — SQLite Concurrent Access During Ingestion + Search
| Field | Detail |
|---|---|
| **Category** | Technical |
| **Probability** | Low |
| **Impact** | Medium |
| **Description** | Simultaneous reads (search) and writes (ingestion) could cause lock contention. |
| **Mitigation** | Enable WAL mode on SQLite. Serialize write operations. |

### R-08 🟢 — Highlight Text Matching Drift
| Field | Detail |
|---|---|
| **Category** | Technical |
| **Probability** | Low |
| **Impact** | Medium |
| **Description** | Text extracted by PyMuPDF may not match PDF.js text layer character-for-character. |
| **Mitigation** | Use fuzzy substring matching in the frontend when searching the PDF.js text layer. |

### R-09 🟢 — FastAPI Process Fails to Start
| Field | Detail |
|---|---|
| **Category** | Technical |
| **Probability** | Low |
| **Impact** | High |
| **Description** | The FastAPI Python process may fail to start (missing packages, wrong Python version, port already in use). |
| **Mitigation** | Launcher script validates Python and pip before starting. FastAPI startup errors are logged clearly in the terminal. |
| **Contingency** | Show a clear error in the UI if API calls fail. QUICKSTART.md documents common failure modes and fixes (e.g., `QG_PORT` env var for port conflicts). |

### R-10 🟢 — Scope Creep
| Field | Detail |
|---|---|
| **Category** | Process |
| **Probability** | Low |
| **Impact** | High |
| **Description** | Feature requests for OCR, cloud sync, or LLM integration could derail v1 timeline. |
| **Mitigation** | Scope lock document enforced. Any additions require change control approval. |
