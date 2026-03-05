# QuickGuide (QG) — Functional Requirements Document (FRD)

**Version:** 1.0
**Date:** 2026-03-05

---

## 1 PDF Ingestion Module

### FR-ING-01 — Select & Upload PDF
| Field | Detail |
|---|---|
| **Description** | User clicks "Select a Document" and picks a PDF from their local file system. |
| **Input** | PDF file (≤ 200 MB, ≤ 2,000 pages). |
| **Output** | File is copied to the app's managed storage directory (`data/pdfs/`), and a document record is created in the database. |
| **Rules** | Reject non-PDF files with a clear error toast. Show file size warnings for files > 100 MB. |

### FR-ING-02 — Extract Text
| Field | Detail |
|---|---|
| **Description** | System extracts text from every page, preserving page numbers and character positions. |
| **Input** | Stored PDF file path. |
| **Output** | Per-page text records stored in the SQLite database with page number and character offsets. |
| **Rules** | Pages with no extractable text are flagged as "no text content" (future OCR placeholder). |

### FR-ING-03 — Chunk Text
| Field | Detail |
|---|---|
| **Description** | Extracted text is split into overlapping chunks suitable for embedding. |
| **Input** | Full-page text content. |
| **Output** | Chunk records with `document_id`, `page_number`, `chunk_index`, `text_content`, `start_char`, `end_char`. |
| **Rules** | Chunk size ≤ 512 tokens. Overlap of 50 tokens between adjacent chunks. Chunks do not cross page boundaries. |

### FR-ING-04 — Generate Embeddings
| Field | Detail |
|---|---|
| **Description** | Each text chunk is converted to a 384-dimensional vector embedding using `all-MiniLM-L6-v2`. |
| **Input** | Text chunk content. |
| **Output** | Float32 embedding vector stored in the vector index and referenced in the database. |
| **Rules** | Embedding is generated via a Python worker subprocess. Batch size of 32 chunks for efficiency. |

### FR-ING-05 — Progress Feedback
| Field | Detail |
|---|---|
| **Description** | A progress bar reflects ingestion stage and % completion. |
| **Input** | Internal pipeline events (pages extracted, chunks created, embeddings generated). |
| **Output** | Real-time progress in the UI: `Extracting text → Chunking → Generating embeddings → Complete`. |

---

## 2 Document Selection & Library Module

### FR-LIB-01 — Document Selector
| Field | Detail |
|---|---|
| **Description** | The main screen displays a "Select a Document" dropdown or panel listing all ingested PDFs. |
| **Output** | Selecting a document makes it the active target for all searches. The PDF viewer loads the selected document. |
| **Rules** | Only fully ingested documents appear in the selector. Documents mid-ingestion show a spinner. |

### FR-LIB-02 — List Documents
| Field | Detail |
|---|---|
| **Description** | Display all uploaded PDFs with metadata. |
| **Metadata shown** | Title (filename), page count, file size, upload date, ingestion status. |

### FR-LIB-03 — Delete Document
| Field | Detail |
|---|---|
| **Description** | User can remove a document. Deletes PDF, text chunks, embeddings, and highlights. |
| **Rules** | Confirmation dialog required before deletion. |

---

## 3 Semantic Search Module

### FR-SEA-01 — Accept Query
| Field | Detail |
|---|---|
| **Description** | A persistent prompt box accepts natural-language questions. |
| **Input** | User-typed query string (minimum 3 characters). |
| **Output** | Query is sent to the search pipeline for the currently selected document. |
| **Rules** | If no document is selected, show a friendly message: "Please select a document first." Auto-trim whitespace. |

### FR-SEA-02 — Vector Similarity Search
| Field | Detail |
|---|---|
| **Description** | The query is embedded and compared against stored chunk embeddings using cosine similarity. |
| **Input** | Query embedding vector + document ID. |
| **Output** | Top-K (default K=10) ranked results by cosine similarity. |
| **Rules** | Results with similarity < 0.30 are excluded. |

### FR-SEA-03 — Display Results
| Field | Detail |
|---|---|
| **Description** | Results shown in a scrollable panel alongside the PDF viewer. |
| **Per result** | Page number, full scrollable text snippet bounded only by max-height, relevance score badge. |

---

## 4 Navigation & Highlighting Module

### FR-NAV-01 — Click-to-Navigate
| Field | Detail |
|---|---|
| **Description** | Each search result is a clickable link. Clicking it navigates the PDF.js viewer to the source page and scrolls to the passage. |
| **Input** | Click event with `page_number` and `search_text`. |
| **Output** | PDF viewer displays the correct page. The passage is scrolled into view. |

### FR-NAV-02 — Auto-Highlight Passage
| Field | Detail |
|---|---|
| **Description** | Upon navigation, the matching text is highlighted in the PDF.js text layer. |
| **Default color** | Yellow (`#FFE066`). |
| **Rules** | Highlight is an overlay on the PDF.js text layer; the original PDF is never modified. |

### FR-NAV-03 — Multi-Match Highlighting
| Field | Detail |
|---|---|
| **Description** | When a query returns multiple matching locations, ALL matched passages are highlighted simultaneously. |
| **Navigation** | A toolbar shows "Match X of N" with ◀ Previous / ▶ Next buttons. |
| **Rules** | Clicking ▶ jumps the viewer to the next highlighted match. Wraps around from last to first. |

### FR-NAV-04 — Custom Highlight Color
| Field | Detail |
|---|---|
| **Description** | A color picker in the toolbar lets the user change highlight color. |
| **Input** | Color value (hex via native color picker or preset swatches). |
| **Output** | All active highlights update to the chosen color. Future highlights default to this color. |
| **Presets** | Yellow (#FFE066), Green (#A8E6CF), Blue (#87CEEB), Pink (#FFB7B2), Orange (#FFDAC1). |

### FR-NAV-05 — Persistent Highlights
| Field | Detail |
|---|---|
| **Description** | User-applied highlights are saved and restored when the document is reopened. |
| **Storage** | SQLite records keyed by `document_id + page_number + text_content + color`. |

### FR-NAV-06 — Interactive Text Selection Highlighting
| Field | Detail |
|---|---|
| **Description** | Users can highlight freeform text simply by dragging their mouse cursor over sentences on the PDF. |
| **Input** | JS native DOM text selection (`mouseup` event). |
| **Output** | Sends the highlighted text to the backend to be saved as an independent highlight, rendered visually in Light Blue. |

### FR-NAV-07 — "My Highlights" Dashboard Tab
| Field | Detail |
|---|---|
| **Description** | A Tabbed interface in the sidebar to switch between "Search" and "My Highlights". |
| **Content** | Lists all custom highlights saved via mouse drag, displaying the page number, the highlighted content, and an option to delete. Clicking the card jumps the PDF to that page. |

---

## 5 UI / UX Requirements

### FR-UI-01 — Responsive Layout
- **Desktop (≥ 1024px):** Side-by-side layout — Tabbed sidebar for search/highlights (left, ~35%), PDF viewer (right, ~65%).
- **Mobile (< 1024px):** Stacked layout — search bar and results on top, PDF viewer below. Collapsible search panel.

### FR-UI-02 — Cozy Visual Design
- Warm color palette (soft yellows, creams, warm grays).
- Rounded corners on all panels and buttons (border-radius ≥ 8px).
- Soft shadows and gentle transitions.
- Clean sans-serif typography (e.g., "Nunito" or "Inter" from Google Fonts).
- The app should feel like a **comfortable reading companion**, not a technical tool.

### FR-UI-03 — Layman-Friendly Controls
- All buttons have clear text labels (no icon-only buttons).
- Tooltips on hover for all interactive elements.
- No jargon anywhere in the UI (e.g., "Search your document" not "Execute semantic query").

### FR-UI-04 — QG Desktop Launcher
- A `qg.bat` (Windows) / `qg.sh` (macOS/Linux) launcher script that starts the backend and opens the browser.
- A QG logo icon for the desktop shortcut.

### FR-UI-05 — Keyboard Shortcuts (Desktop)
| Shortcut | Action |
|---|---|
| `Ctrl+K` / `Cmd+K` | Focus the search prompt box |
| `Enter` | Submit the search query |
| `Ctrl+→` / `Cmd+→` | Jump to next highlighted match |
| `Ctrl+←` / `Cmd+←` | Jump to previous highlighted match |
| `Esc` | Clear search results |

---

## 6 PDF Storage Location

> [!IMPORTANT]
> **Where PDFs are stored:** All user-selected PDFs are copied into the application's managed directory at:
>
> ```
> Quick_Guide/data/pdfs/
> ```
>
> The user does NOT need to manually place files here. They simply click "Select a Document", pick any PDF from their file system, and the app automatically copies it to this managed location for parsing and indexing. Original files on the user's system are never modified or moved.
