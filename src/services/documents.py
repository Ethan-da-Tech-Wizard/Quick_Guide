# Program: Quick_Guide - documents.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Manages a document's life cycle: saves an uploaded PDF, runs extract/chunk/embed/index ingestion with progress tracking, and lists, fetches or deletes documents.
"""
QuickGuide (QG) — Document Service
Document lifecycle: upload, ingest, list, delete.
"""

# ── Imports ──────────────────────────────────────
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime

# Our own modules: database access, settings, and the processing steps
from database import get_connection
from config import PDF_DIR, MAX_FILE_SIZE_MB, MAX_PAGES
from services import pdf_parser, chunker, embedder
from services.vector_store import get_store, delete_store

# Logger for reporting ingestion errors
logger = logging.getLogger(__name__)

# Remember: this dictionary is lost when the server restarts and is keyed by document id
# In-memory progress tracker
_progress: dict[int, dict] = {}


def get_progress(document_id: int) -> dict:
    """Get ingestion progress for a document."""
    return _progress.get(document_id, {
        "document_id": document_id,
        "status": "unknown",
        "stage": "",
        "progress": 0.0,
        "message": "No ingestion in progress",
    })


def _set_progress(doc_id: int, status: str, stage: str, progress: float, message: str):
    """Record the current ingestion stage and progress for a document."""
    _progress[doc_id] = {
        "document_id": doc_id,
        "status": status,
        "stage": stage,
        "progress": progress,
        "message": message,
    }


def upload_and_ingest(filename: str, file_content: bytes) -> dict:
    """
    Upload a PDF and run the full ingestion pipeline.

    Args:
        filename: Original filename
        file_content: Raw file bytes

    Returns:
        Document record dict
    """
    # Convert bytes to megabytes (1024 * 1024 bytes per MB)
    # Validate file size
    size_mb = len(file_content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large: {size_mb:.1f} MB (max {MAX_FILE_SIZE_MB} MB)")

    # Build the destination path from a cleaned-up filename
    # Save PDF to data/pdfs/
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(filename)
    pdf_path = PDF_DIR / safe_name

    # If the name is taken, add _1, _2 ... until we find a free one
    # Handle duplicate filenames
    counter = 1
    while pdf_path.exists():
        stem = Path(safe_name).stem
        suffix = Path(safe_name).suffix
        pdf_path = PDF_DIR / f"{stem}_{counter}{suffix}"
        counter += 1

    # Write the uploaded bytes to disk in binary mode
    with open(pdf_path, "wb") as f:
        f.write(file_content)

    # Opening the file also proves it really is a readable PDF; if not, delete it again
    # Get page count
    try:
        page_count = pdf_parser.get_page_count(pdf_path)
    except Exception as e:
        pdf_path.unlink(missing_ok=True)
        raise ValueError(f"Could not read PDF: {e}")

    # Enforce the page limit
    if page_count > MAX_PAGES:
        pdf_path.unlink(missing_ok=True)
        raise ValueError(f"PDF has {page_count} pages (max {MAX_PAGES})")

    # Insert a row for the document with status "ingesting"
    # Create database record
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO documents (filename, file_path, page_count, file_size_bytes, status)
           VALUES (?, ?, ?, ?, ?)""",
        (filename, str(pdf_path), page_count, len(file_content), "ingesting")
    )
    doc_id = cursor.lastrowid
    conn.commit()

    # Tell the progress tracker we are starting
    _set_progress(doc_id, "ingesting", "extracting", 0.0, "Extracting text from PDF...")

    try:
        # The pipeline: extract text -> chunk -> save chunks -> embed -> index. Any failure marks the document as an error.
        # Step 1: Extract text
        pages = pdf_parser.extract_text(pdf_path)
        _set_progress(doc_id, "ingesting", "chunking", 0.25, f"Extracted text from {len(pages)} pages. Chunking...")

        # Go page by page and split each page's text into chunks
        # Step 2: Chunk text
        all_chunks = []
        for page_num, text in pages:
            page_chunks = chunker.chunk_text(page_num, text)
            all_chunks.extend(page_chunks)

        # Save each chunk to the database and remember its new id (the vector index maps back to these ids)
        # Store chunks in database
        chunk_ids = []
        for c in all_chunks:
            cursor = conn.execute(
                """INSERT INTO text_chunks (document_id, page_number, chunk_index, text_content, start_char, end_char)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (doc_id, c["page_number"], c["chunk_index"], c["text_content"], c["start_char"], c["end_char"])
            )
            chunk_ids.append(cursor.lastrowid)
        conn.commit()

        _set_progress(doc_id, "ingesting", "embedding", 0.50, f"Created {len(all_chunks)} chunks. Generating embeddings...")

        # Embeddings are the numbers that represent each chunk's meaning
        # Step 3: Generate embeddings
        if all_chunks:
            texts = [c["text_content"] for c in all_chunks]
            vectors = embedder.embed_texts(texts)

            _set_progress(doc_id, "ingesting", "indexing", 0.80, "Storing embeddings in vector index...")

            # Step 4: Add to vector store
            store = get_store(doc_id)
            store.add(chunk_ids, vectors)

        # Flip the document's status so searching is allowed
        # Mark complete
        conn.execute("UPDATE documents SET status = 'ready' WHERE id = ?", (doc_id,))
        conn.commit()
        _set_progress(doc_id, "ready", "complete", 1.0, f"Ready! {len(all_chunks)} chunks indexed from {len(pages)} pages.")

    # Something failed: log it, mark the document as error, tell the progress tracker, then re-raise so the caller sees it
    except Exception as e:
        logger.error(f"Ingestion failed for doc {doc_id}: {e}")
        conn.execute("UPDATE documents SET status = 'error' WHERE id = ?", (doc_id,))
        conn.commit()
        _set_progress(doc_id, "error", "failed", 0.0, f"Ingestion failed: {str(e)}")
        raise

    # Return the finished document record
    return get_document(doc_id)


def list_documents() -> list[dict]:
    """List all uploaded documents."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, filename, page_count, file_size_bytes, upload_date, status FROM documents ORDER BY upload_date DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_document(document_id: int) -> dict | None:
    """Get a single document by ID."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, filename, page_count, file_size_bytes, upload_date, status FROM documents WHERE id = ?",
        (document_id,)
    ).fetchone()
    return dict(row) if row else None


def get_pdf_path(document_id: int) -> Path | None:
    """Get the file path for a document's PDF."""
    conn = get_connection()
    row = conn.execute("SELECT file_path FROM documents WHERE id = ?", (document_id,)).fetchone()
    if row:
        path = Path(row["file_path"])
        if path.exists():
            return path
    return None


def delete_document(document_id: int) -> bool:
    """Delete a document and all associated data."""
    conn = get_connection()

    # Look up where the PDF is stored
    # Get file path before deleting
    row = conn.execute("SELECT file_path FROM documents WHERE id = ?", (document_id,)).fetchone()
    if not row:
        return False

    # Remove the PDF from disk if it is still there
    # Delete PDF file
    pdf_path = Path(row["file_path"])
    if pdf_path.exists():
        pdf_path.unlink()

    # Remove the saved search index files
    # Delete vector store
    delete_store(document_id)

    # Remove the database row
    # Delete database records (cascading will handle chunks and highlights)
    conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    conn.commit()

    # Forget any saved progress (None as default avoids an error if absent)
    # Clean up progress
    _progress.pop(document_id, None)

    return True


def _safe_filename(filename: str) -> str:
    """Sanitize a filename."""
    # Remove path separators and odd symbols so a filename cannot escape the folder
    # Keep only safe characters
    safe = "".join(c for c in filename if c.isalnum() or c in "._- ")
    if not safe.lower().endswith(".pdf"):
        safe += ".pdf"
    return safe
