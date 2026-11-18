# Program: Quick_Guide - main.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Creates the FastAPI web app, serves the frontend, and exposes the REST API for uploading PDFs, searching them, viewing text positions and managing highlights.
"""
QuickGuide (QG) — FastAPI Application

Local PDF search and navigation tool.
Run:  python main.py
  or: uvicorn main:app --host 127.0.0.1 --port 8080
"""

# ── Imports ──────────────────────────────────────
# Standard library modules
import os
import sys
import logging
import webbrowser
from pathlib import Path
from contextlib import asynccontextmanager

# Third-party web framework pieces: FastAPI builds the API, uvicorn runs the server
import uvicorn
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

# Our own modules (database setup, request models, settings, and the service layer)
from database import init_db
from models import SearchRequest, HighlightCreate, HighlightUpdate
from config import HOST, PORT
from services import documents as doc_service
from services import search as search_service
from services import highlights as highlight_service
from services import pdf_parser


# ── Logging ──────────────────────────────────────

# Configure how log messages look: time, level, logger name, then the message
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
# Named logger used by this file
logger = logging.getLogger("quickguide")


# ── Lifespan ─────────────────────────────────────

# This decorator lets the function below run code at startup (before yield) and shutdown (after yield)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    # Create the database tables if they are missing
    init_db()
    logger.info("Database initialized.")
    # The app serves requests while paused here
    yield


# Create the web application object; every route below attaches to it
app = FastAPI(
    title="QuickGuide",
    version="1.0.0",
    description="Local PDF search and navigation tool",
    lifespan=lifespan,
)


# ── Static files ─────────────────────────────────

# Folder holding the HTML, CSS and JavaScript the browser loads
STATIC_DIR = Path(__file__).parent / "static"
# Serve everything in that folder under the /static URL
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Frontend ─────────────────────────────────────

# GET / returns the main web page
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main HTML page."""
    # Full path to index.html
    index_path = STATIC_DIR / "index.html"
    return FileResponse(str(index_path), media_type="text/html")


# ── Document API ─────────────────────────────────

# POST upload: receives a PDF, saves it, and builds its search index
@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a PDF document."""
    # Reject anything that is not named like a PDF
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted.")

    try:
        # Read the uploaded bytes (await pauses until the upload is read)
        content = await file.read()
        doc = doc_service.upload_and_ingest(file.filename, content)
        return doc
    # ValueError means a user problem (too big, unreadable): report it as HTTP 400
    except ValueError as e:
        raise HTTPException(400, str(e))
    # Anything else is unexpected: log it and report HTTP 500
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")


# GET list: returns every uploaded document
@app.get("/api/documents")
async def list_documents():
    """List all uploaded documents."""
    return doc_service.list_documents()


# GET one document by its id, or 404 if missing
@app.get("/api/documents/{document_id}")
async def get_document(document_id: int):
    """Get a specific document."""
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


# GET status: lets the browser poll how far ingestion has progressed
@app.get("/api/documents/{document_id}/status")
async def get_document_status(document_id: int):
    """Get the ingestion status of a document."""
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    progress = doc_service.get_progress(document_id)
    return progress


# DELETE document: removes the PDF, its index and its database rows
@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: int):
    """Delete a document and all associated data."""
    if not doc_service.delete_document(document_id):
        raise HTTPException(404, "Document not found")
    return {"status": "deleted"}


# GET pdf: streams the PDF file so the browser viewer can display it
@app.get("/api/documents/{document_id}/pdf")
async def serve_pdf(document_id: int):
    """Serve the PDF file for the viewer."""
    pdf_path = doc_service.get_pdf_path(document_id)
    if not pdf_path:
        raise HTTPException(404, "PDF file not found")
    # Send the PDF; the "inline" header below tells the browser to show it rather than download it
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=\"{pdf_path.name}\""}
    )


# ── Search API ───────────────────────────────────

# POST search: finds the passages that best match a plain-English question
@app.post("/api/search")
async def search(request: SearchRequest):
    """Perform semantic search on a document."""
    doc = doc_service.get_document(request.document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    # Searching only works once the document has finished processing
    if doc["status"] != "ready":
        raise HTTPException(400, "Document is still being processed. Please wait.")

    # Run the semantic search using the document id, the query text and the result count
    results = search_service.semantic_search(
        request.document_id, request.query, request.top_k
    )
    return {"results": results, "total": len(results)}


# ── Text Position Search (for precise highlighting) ──

# GET text-positions: asks the PDF where certain text sits on a page
@app.get("/api/documents/{document_id}/text-positions")
async def search_text_positions(
    document_id: int,
    page: int = Query(..., ge=1),
    q: str = Query(..., min_length=1),
):
    """
    Search for text on a specific page and return bounding-box rectangles.
    Used by the frontend to highlight exact text positions.
    """
    pdf_path = doc_service.get_pdf_path(document_id)
    if not pdf_path:
        raise HTTPException(404, "PDF file not found")

    # Rectangles (as fractions of page size) that the browser draws highlights on
    rects = pdf_parser.search_text_on_page(pdf_path, page, q)
    return {"rects": rects, "page": page, "query": q}


# ── Highlights API ───────────────────────────────

# POST highlight: saves a new highlight for a document
@app.post("/api/highlights")
async def add_highlight(data: HighlightCreate):
    """Add a highlight annotation."""
    doc = doc_service.get_document(data.document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    highlight = highlight_service.add_highlight(
        data.document_id, data.page_number, data.text_content, data.color
    )
    return highlight


# GET highlights: all highlights for a document, optionally for one page
@app.get("/api/documents/{document_id}/highlights")
async def get_highlights(document_id: int, page: int | None = None):
    """Get highlights for a document."""
    return highlight_service.get_highlights(document_id, page)


# PUT highlight: changes a highlight's color
@app.put("/api/highlights/{highlight_id}")
async def update_highlight(highlight_id: int, data: HighlightUpdate):
    """Update highlight color."""
    highlight = highlight_service.update_highlight(highlight_id, data.color)
    if not highlight:
        raise HTTPException(404, "Highlight not found")
    return highlight


# DELETE highlight: removes one highlight
@app.delete("/api/highlights/{highlight_id}")
async def delete_highlight(highlight_id: int):
    """Delete a highlight."""
    if not highlight_service.delete_highlight(highlight_id):
        raise HTTPException(404, "Highlight not found")
    return {"status": "deleted"}


# ── Entry Point ──────────────────────────────────

# This block only runs when the file is started directly (python main.py)
if __name__ == "__main__":
    print()
    print("=" * 50)
    print("  QuickGuide (QG) — PDF Search & Navigation")
    print(f"  http://{HOST}:{PORT}")
    print("=" * 50)
    print()

    # Open browser automatically
    # Open the default web browser on the app's address
    webbrowser.open(f"http://{HOST}:{PORT}")

    # Start the web server; reload=False means it will not restart on file changes
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )
