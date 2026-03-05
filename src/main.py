"""
QuickGuide (QG) — FastAPI Application

Local PDF search and navigation tool.
Run:  python main.py
  or: uvicorn main:app --host 127.0.0.1 --port 8080
"""

import os
import sys
import logging
import webbrowser
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from database import init_db
from models import SearchRequest, HighlightCreate, HighlightUpdate
from config import HOST, PORT
from services import documents as doc_service
from services import search as search_service
from services import highlights as highlight_service
from services import pdf_parser


# ── Logging ──────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("quickguide")


# ── Lifespan ─────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    logger.info("Database initialized.")
    yield


app = FastAPI(
    title="QuickGuide",
    version="1.0.0",
    description="Local PDF search and navigation tool",
    lifespan=lifespan,
)


# ── Static files ─────────────────────────────────

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Frontend ─────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main HTML page."""
    index_path = STATIC_DIR / "index.html"
    return FileResponse(str(index_path), media_type="text/html")


# ── Document API ─────────────────────────────────

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a PDF document."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted.")

    try:
        content = await file.read()
        doc = doc_service.upload_and_ingest(file.filename, content)
        return doc
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")


@app.get("/api/documents")
async def list_documents():
    """List all uploaded documents."""
    return doc_service.list_documents()


@app.get("/api/documents/{document_id}")
async def get_document(document_id: int):
    """Get a specific document."""
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@app.get("/api/documents/{document_id}/status")
async def get_document_status(document_id: int):
    """Get the ingestion status of a document."""
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    progress = doc_service.get_progress(document_id)
    return progress


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: int):
    """Delete a document and all associated data."""
    if not doc_service.delete_document(document_id):
        raise HTTPException(404, "Document not found")
    return {"status": "deleted"}


@app.get("/api/documents/{document_id}/pdf")
async def serve_pdf(document_id: int):
    """Serve the PDF file for the viewer."""
    pdf_path = doc_service.get_pdf_path(document_id)
    if not pdf_path:
        raise HTTPException(404, "PDF file not found")
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=\"{pdf_path.name}\""}
    )


# ── Search API ───────────────────────────────────

@app.post("/api/search")
async def search(request: SearchRequest):
    """Perform semantic search on a document."""
    doc = doc_service.get_document(request.document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc["status"] != "ready":
        raise HTTPException(400, "Document is still being processed. Please wait.")

    results = search_service.semantic_search(
        request.document_id, request.query, request.top_k
    )
    return {"results": results, "total": len(results)}


# ── Text Position Search (for precise highlighting) ──

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

    rects = pdf_parser.search_text_on_page(pdf_path, page, q)
    return {"rects": rects, "page": page, "query": q}


# ── Highlights API ───────────────────────────────

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


@app.get("/api/documents/{document_id}/highlights")
async def get_highlights(document_id: int, page: int | None = None):
    """Get highlights for a document."""
    return highlight_service.get_highlights(document_id, page)


@app.put("/api/highlights/{highlight_id}")
async def update_highlight(highlight_id: int, data: HighlightUpdate):
    """Update highlight color."""
    highlight = highlight_service.update_highlight(highlight_id, data.color)
    if not highlight:
        raise HTTPException(404, "Highlight not found")
    return highlight


@app.delete("/api/highlights/{highlight_id}")
async def delete_highlight(highlight_id: int):
    """Delete a highlight."""
    if not highlight_service.delete_highlight(highlight_id):
        raise HTTPException(404, "Highlight not found")
    return {"status": "deleted"}


# ── Entry Point ──────────────────────────────────

if __name__ == "__main__":
    print()
    print("=" * 50)
    print("  QuickGuide (QG) — PDF Search & Navigation")
    print(f"  http://{HOST}:{PORT}")
    print("=" * 50)
    print()

    # Open browser automatically
    webbrowser.open(f"http://{HOST}:{PORT}")

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )
