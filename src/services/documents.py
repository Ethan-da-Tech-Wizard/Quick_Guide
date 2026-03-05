"""
QuickGuide (QG) — Document Service
Document lifecycle: upload, ingest, list, delete.
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime

from database import get_connection
from config import PDF_DIR, MAX_FILE_SIZE_MB, MAX_PAGES
from services import pdf_parser, chunker, embedder
from services.vector_store import get_store, delete_store

logger = logging.getLogger(__name__)

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
    # Validate file size
    size_mb = len(file_content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large: {size_mb:.1f} MB (max {MAX_FILE_SIZE_MB} MB)")

    # Save PDF to data/pdfs/
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(filename)
    pdf_path = PDF_DIR / safe_name

    # Handle duplicate filenames
    counter = 1
    while pdf_path.exists():
        stem = Path(safe_name).stem
        suffix = Path(safe_name).suffix
        pdf_path = PDF_DIR / f"{stem}_{counter}{suffix}"
        counter += 1

    with open(pdf_path, "wb") as f:
        f.write(file_content)

    # Get page count
    try:
        page_count = pdf_parser.get_page_count(pdf_path)
    except Exception as e:
        pdf_path.unlink(missing_ok=True)
        raise ValueError(f"Could not read PDF: {e}")

    if page_count > MAX_PAGES:
        pdf_path.unlink(missing_ok=True)
        raise ValueError(f"PDF has {page_count} pages (max {MAX_PAGES})")

    # Create database record
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO documents (filename, file_path, page_count, file_size_bytes, status)
           VALUES (?, ?, ?, ?, ?)""",
        (filename, str(pdf_path), page_count, len(file_content), "ingesting")
    )
    doc_id = cursor.lastrowid
    conn.commit()

    _set_progress(doc_id, "ingesting", "extracting", 0.0, "Extracting text from PDF...")

    try:
        # Step 1: Extract text
        pages = pdf_parser.extract_text(pdf_path)
        _set_progress(doc_id, "ingesting", "chunking", 0.25, f"Extracted text from {len(pages)} pages. Chunking...")

        # Step 2: Chunk text
        all_chunks = []
        for page_num, text in pages:
            page_chunks = chunker.chunk_text(page_num, text)
            all_chunks.extend(page_chunks)

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

        # Step 3: Generate embeddings
        if all_chunks:
            texts = [c["text_content"] for c in all_chunks]
            vectors = embedder.embed_texts(texts)

            _set_progress(doc_id, "ingesting", "indexing", 0.80, "Storing embeddings in vector index...")

            # Step 4: Add to vector store
            store = get_store(doc_id)
            store.add(chunk_ids, vectors)

        # Mark complete
        conn.execute("UPDATE documents SET status = 'ready' WHERE id = ?", (doc_id,))
        conn.commit()
        _set_progress(doc_id, "ready", "complete", 1.0, f"Ready! {len(all_chunks)} chunks indexed from {len(pages)} pages.")

    except Exception as e:
        logger.error(f"Ingestion failed for doc {doc_id}: {e}")
        conn.execute("UPDATE documents SET status = 'error' WHERE id = ?", (doc_id,))
        conn.commit()
        _set_progress(doc_id, "error", "failed", 0.0, f"Ingestion failed: {str(e)}")
        raise

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

    # Get file path before deleting
    row = conn.execute("SELECT file_path FROM documents WHERE id = ?", (document_id,)).fetchone()
    if not row:
        return False

    # Delete PDF file
    pdf_path = Path(row["file_path"])
    if pdf_path.exists():
        pdf_path.unlink()

    # Delete vector store
    delete_store(document_id)

    # Delete database records (cascading will handle chunks and highlights)
    conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    conn.commit()

    # Clean up progress
    _progress.pop(document_id, None)

    return True


def _safe_filename(filename: str) -> str:
    """Sanitize a filename."""
    # Keep only safe characters
    safe = "".join(c for c in filename if c.isalnum() or c in "._- ")
    if not safe.lower().endswith(".pdf"):
        safe += ".pdf"
    return safe
