# ==============================================================================
# Program: main.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Main FastAPI application server for QuickGuide.
#          Coordinates RESTful API endpoints for PDF document uploading,
#          status tracking, deletion, vector-powered semantic search, precise
#          bounding-box text location queries, highlight CRUD, and serves
#          static web assets for the browser interface.
# ==============================================================================

# Standard-library imports. os and sys are imported but not referenced in this module;
# webbrowser is used only by the CLI entry point at the bottom.
import os
import sys
import logging
import webbrowser
from pathlib import Path
from contextlib import asynccontextmanager

# Third-party web stack: uvicorn is the ASGI server, FastAPI provides routing and
# request validation, and the response classes below serve the SPA and the raw PDF.
import uvicorn
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

# Local modules. These are imported flat (not as a package) because the app is run
# from inside src/ (see qg.sh: `cd src && python main.py`), so src/ is on sys.path.
from database import init_db
from models import SearchRequest, HighlightCreate, HighlightUpdate
from config import HOST, PORT
from services import documents as doc_service
from services import search as search_service
from services import highlights as highlight_service
from services import pdf_parser

# ── Logging Configuration ─────────────────────────────────────────────────────

# Configure root logging once, at import time, so every module-level
# `logging.getLogger(__name__)` in the services inherits the same handler and format.
# The format is: time, padded level name, logger name, message.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
# Named application logger used by the route handlers in this file.
logger = logging.getLogger("quickguide")

# ── Application Lifespan ──────────────────────────────────────────────────────

# asynccontextmanager turns this generator into the lifespan hook FastAPI expects:
# code before `yield` runs at startup, code after it runs at shutdown.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to handle application startup and teardown tasks.
    Initializes database schema prior to receiving client requests.
    """
    # init_db() is idempotent (CREATE TABLE IF NOT EXISTS), so it is safe on every start.
    # Step 1: Run database migrations / table creation
    init_db()
    logger.info("Database initialized.")
    yield
    # Nothing to release here: SQLite connections are thread-local and the FAISS stores
    # are flushed to disk on every add(), so no explicit shutdown work is needed.
    # Step 2: Perform any required teardown on server shutdown

# The FastAPI application object. `lifespan` wires in the startup hook above.
# uvicorn is pointed at this object via the import string "main:app" below.
app = FastAPI(
    title="QuickGuide",
    version="1.0.0",
    description="Local PDF search and navigation tool",
    lifespan=lifespan,
)

# ── Static File Assets ────────────────────────────────────────────────────────

# Absolute path to the bundled frontend (HTML/JS/CSS), resolved relative to this file
# so the server works regardless of the current working directory.
STATIC_DIR = Path(__file__).parent / "static"
# Expose the frontend assets under /static; index.html references /static/js/app.js
# and /static/css/app.css. Mounted before the API routes; API paths all start with /api.
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ── Frontend Route ────────────────────────────────────────────────────────────

# Root route: return the single-page app shell. response_class=HTMLResponse is mainly
# so the OpenAPI docs describe the response as HTML.
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serves the primary single-page application HTML document."""
    index_path = STATIC_DIR / "index.html"
    return FileResponse(str(index_path), media_type="text/html")

# ── Document Lifecycle API Endpoints ──────────────────────────────────────────

# Upload endpoint. Runs the whole ingestion pipeline synchronously inside the request,
# so the response only returns once the document is searchable (or has failed).
@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Handles file upload, validates PDF extension, and delegates to the
    ingestion pipeline (extraction, chunking, embedding, indexing).
    """
    # Reject early on a missing name or a non-.pdf extension. This is only a cheap filename
    # check; the real readability check is done by PyMuPDF in the ingestion service.
    # Step 1: Validate file format
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted.")

    try:
        # Step 2: Read binary contents and trigger ingestion
        content = await file.read()
        doc = doc_service.upload_and_ingest(file.filename, content)
        return doc
    # ValueError is the service layer's signal for a user-correctable problem (too large,
    # unreadable, too many pages), so it maps to 400 rather than 500.
    except ValueError as e:
        raise HTTPException(400, str(e))
    # Anything else is unexpected: log it server-side and surface a 500 to the client.
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")

# List all documents, newest first (ordering is done in SQL by the service).
@app.get("/api/documents")
async def list_documents():
    """Returns a list of all documents stored in the database."""
    return doc_service.list_documents()

# `document_id` is typed int, so FastAPI returns 422 automatically for non-numeric ids.
@app.get("/api/documents/{document_id}")
async def get_document(document_id: int):
    """Retrieves document record metadata by document ID."""
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc

# Polled by clients to show ingestion progress. Progress lives in process memory only
# (see documents._progress), so after a server restart this reports status "unknown".
@app.get("/api/documents/{document_id}/status")
async def get_document_status(document_id: int):
    """Retrieves the current ingestion progress and stage for a document."""
    # Check the DB first so an id that never existed yields 404 rather than an "unknown"
    # progress record.
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    progress = doc_service.get_progress(document_id)
    return progress

# Deletion removes the PDF, vector index files and DB rows; a False return means
# the id did not exist.
@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: int):
    """Purges a document, its PDF file, vectors, and database records."""
    if not doc_service.delete_document(document_id):
        raise HTTPException(404, "Document not found")
    return {"status": "deleted"}

# Serve the stored PDF inline (not as a download) so PDF.js in the browser can fetch it
# by URL. The filename in Content-Disposition is the on-disk (sanitized) name.
@app.get("/api/documents/{document_id}/pdf")
async def serve_pdf(document_id: int):
    """Streams the raw PDF file for rendering in the PDF.js client viewer."""
    pdf_path = doc_service.get_pdf_path(document_id)
    if not pdf_path:
        raise HTTPException(404, "PDF file not found")
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=\"{pdf_path.name}\""}
    )

# ── Semantic Search API Endpoints ─────────────────────────────────────────────

@app.post("/api/search")
async def search(request: SearchRequest):
    """
    Executes semantic query search over chunk vectors for a given document.
    """
    # Only documents whose ingestion finished can be searched; during ingestion the
    # vector index may be missing or incomplete.
    # Step 1: Verify document existence and ready state
    doc = doc_service.get_document(request.document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc["status"] != "ready":
        raise HTTPException(400, "Document is still being processed. Please wait.")

    # top_k is already bounded (1-50) by the SearchRequest model.
    # Step 2: Execute vector embedding search and return scored chunk hits
    results = search_service.semantic_search(
        request.document_id, request.query, request.top_k
    )
    return {"results": results, "total": len(results)}

# ── Text Position Search ──────────────────────────────────────────────────────

# Used by the frontend to draw highlight rectangles. Returns coordinates normalized
# to 0.0-1.0 of the page size, so they stay valid at any zoom level.
@app.get("/api/documents/{document_id}/text-positions")
async def search_text_positions(
    document_id: int,
    # `...` makes the parameter required; ge/min_length add validation (1-indexed page,
    # non-empty query) enforced by FastAPI before the handler runs.
    page: int = Query(..., ge=1),
    q: str = Query(..., min_length=1),
):
    """
    Searches for text on a specific PDF page and returns bounding-box rectangles
    for client-side visual highlighting overlays.
    """
    pdf_path = doc_service.get_pdf_path(document_id)
    if not pdf_path:
        raise HTTPException(404, "PDF file not found")

    rects = pdf_parser.search_text_on_page(pdf_path, page, q)
    return {"rects": rects, "page": page, "query": q}

# ── Highlights API Endpoints ──────────────────────────────────────────────────

# Create a highlight. The document must exist so we return a clean 404 instead of
# tripping the foreign-key constraint on the highlights table.
@app.post("/api/highlights")
async def add_highlight(data: HighlightCreate):
    """Stores a user-created text highlight annotation."""
    doc = doc_service.get_document(data.document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    highlight = highlight_service.add_highlight(
        data.document_id, data.page_number, data.text_content, data.color
    )
    return highlight

@app.get("/api/documents/{document_id}/highlights")
# `page` is optional: omit it to get every highlight for the document, ordered by page.
async def get_highlights(document_id: int, page: int | None = None):
    """Retrieves saved highlights for a document, optionally filtered by page."""
    return highlight_service.get_highlights(document_id, page)

# Only the colour is editable; the highlighted text and page are immutable.
@app.put("/api/highlights/{highlight_id}")
async def update_highlight(highlight_id: int, data: HighlightUpdate):
    """Updates the highlight color of an existing annotation."""
    # update_highlight returns None when the id is unknown (get_highlight finds no row).
    highlight = highlight_service.update_highlight(highlight_id, data.color)
    if not highlight:
        raise HTTPException(404, "Highlight not found")
    return highlight

@app.delete("/api/highlights/{highlight_id}")
async def delete_highlight(highlight_id: int):
    """Removes a saved highlight annotation."""
    if not highlight_service.delete_highlight(highlight_id):
        raise HTTPException(404, "Highlight not found")
    return {"status": "deleted"}

# ── CLI Entry Point ───────────────────────────────────────────────────────────

# Run only when executed as a script (python main.py), not when uvicorn imports `main`
# by string, which prevents the banner/browser from opening twice.
if __name__ == "__main__":
    print()
    print("=" * 50)
    print("  QuickGuide (QG) — PDF Search & Navigation")
    print(f"  http://{HOST}:{PORT}")
    print("=" * 50)
    print()

    # Convenience for the desktop-style workflow: open the UI in the default browser.
    # Automatically launch default browser to local web application
    webbrowser.open(f"http://{HOST}:{PORT}")

    # reload=False because the auto-reloader would re-run this block in a child process
    # and open a second browser tab. The app is passed as an import string, which uvicorn
    # requires for reload/workers and which also works fine without them.
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )
