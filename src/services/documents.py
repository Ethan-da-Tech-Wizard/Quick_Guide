# ==============================================================================
# Program: documents.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Document lifecycle management service for QuickGuide. Orchestrates
#          the ingestion pipeline: file validation, local disk persistence,
#          text extraction via PyMuPDF, sliding-window chunking, dense vector
#          embedding generation via SentenceTransformers, index persistence
#          via FAISS, and relational metadata updates in SQLite.
# ==============================================================================

# os and datetime are imported but not referenced in this module; shutil likewise.
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime

# database/config give DB access and limits; the sibling services do the heavy lifting
# (PDF parsing, chunking, embedding); get_store/delete_store manage per-document vectors.
from database import get_connection
from config import PDF_DIR, MAX_FILE_SIZE_MB, MAX_PAGES
from services import pdf_parser, chunker, embedder
from services.vector_store import get_store, delete_store

logger = logging.getLogger(__name__)

# Maps document_id -> latest progress dict. This is plain process memory, not durable:
# it is lost on restart and not shared between worker processes (the app runs a single
# process). Individual dict assignments are atomic under the GIL, which is enough here.
# Thread-safe in-memory state tracking for active ingestion jobs
_progress: dict[int, dict] = {}

def get_progress(document_id: int) -> dict:
    """
    Retrieve real-time ingestion progress and status for a document.

    Args:
        document_id (int): Target document identifier.

    Returns:
        dict: Progress payload including status, stage, float progress, and message.
    """
    # Documents with no tracked job (finished before a restart, or never ingested here)
    # fall back to this "unknown" placeholder.
    return _progress.get(document_id, {
        "document_id": document_id,
        "status": "unknown",
        "stage": "",
        "progress": 0.0,
        "message": "No ingestion in progress",
    })

# Replaces the whole record each time, so readers never see a half-updated entry.
def _set_progress(doc_id: int, status: str, stage: str, progress: float, message: str):
    """Internal helper to update the progress tracker dictionary."""
    _progress[doc_id] = {
        "document_id": doc_id,
        "status": status,
        "stage": stage,
        "progress": progress,
        "message": message,
    }

# Pipeline overview, with the progress fraction reported at each stage:
#   0.00 extracting -> 0.25 chunking -> 0.50 embedding -> 0.80 indexing -> 1.00 ready.
# The document row is created with status 'ingesting' before heavy work starts, so a
# failure can be recorded as status 'error' instead of vanishing.
def upload_and_ingest(filename: str, file_content: bytes) -> dict:
    """
    Upload a PDF and execute end-to-end ingestion pipeline:
    extract -> chunk -> embed -> index.

    Args:
        filename (str): Original uploaded file name.
        file_content (bytes): Raw binary bytes of uploaded PDF.

    Returns:
        dict: Newly created document metadata record.
    """
    # Size is measured on the in-memory bytes before anything touches the disk.
    # Step 1: Validate file size against maximum threshold
    size_mb = len(file_content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large: {size_mb:.1f} MB (max {MAX_FILE_SIZE_MB} MB)")

    # _safe_filename strips path separators and other odd characters, which prevents
    # directory traversal (e.g. "../../x.pdf") through the user-supplied name.
    # Step 2: Ensure destination directory exists and sanitize file path
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(filename)
    pdf_path = PDF_DIR / safe_name

    # Never overwrite an existing upload: append _1, _2, ... until the name is free.
    # There is no lock, so two simultaneous uploads of the same name could still race.
    # Step 3: Handle filename collisions with incremental suffixes
    counter = 1
    while pdf_path.exists():
        stem = Path(safe_name).stem
        suffix = Path(safe_name).suffix
        pdf_path = PDF_DIR / f"{stem}_{counter}{suffix}"
        counter += 1

    with open(pdf_path, "wb") as f:
        f.write(file_content)

    # A parse failure or an over-long PDF is cleaned up from disk right away so rejected
    # uploads do not accumulate in data/pdfs. Both raise ValueError, which main.py maps to 400.
    # Step 4: Validate readability and verify page limits
    try:
        page_count = pdf_parser.get_page_count(pdf_path)
    except Exception as e:
        pdf_path.unlink(missing_ok=True)
        raise ValueError(f"Could not read PDF: {e}")

    if page_count > MAX_PAGES:
        pdf_path.unlink(missing_ok=True)
        raise ValueError(f"PDF has {page_count} pages (max {MAX_PAGES})")

    # The original filename is stored for display, and file_path for the sanitized on-disk
    # copy. Commit immediately so the id is visible to status polling.
    # Step 5: Insert document record into SQLite database with 'ingesting' status
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO documents (filename, file_path, page_count, file_size_bytes, status)
           VALUES (?, ?, ?, ?, ?)""",
        (filename, str(pdf_path), page_count, len(file_content), "ingesting")
    )
    doc_id = cursor.lastrowid
    conn.commit()

    _set_progress(doc_id, "ingesting", "extracting", 0.0, "Extracting text from PDF...")

    # Everything from here on is wrapped so that any failure marks the document 'error'.
    try:
        # extract_text only returns pages that contain text, so len(pages) can be smaller
        # than page_count for PDFs with blank or image-only pages.
        # Step 6: Extract full-page text representations
        pages = pdf_parser.extract_text(pdf_path)
        _set_progress(doc_id, "ingesting", "chunking", 0.25, f"Extracted text from {len(pages)} pages. Chunking...")

        # Step 7: Break pages into overlapping chunks
        all_chunks = []
        for page_num, text in pages:
            page_chunks = chunker.chunk_text(page_num, text)
            all_chunks.extend(page_chunks)

        # Chunk ids must be the SQLite primary keys, because the vector index stores those ids
        # and search results are resolved back to text by id.
        # Step 8: Persist text chunks to relational database
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

        # Embedding every chunk in one batch is the slowest stage (CPU transformer inference);
        # the model is downloaded/loaded lazily on first use by embedder.get_model().
        # Step 9: Generate dense vector embeddings for chunks
        if all_chunks:
            # Order matters: vectors[i] must correspond to chunk_ids[i], which holds because both
            # are built by iterating all_chunks in order.
            texts = [c["text_content"] for c in all_chunks]
            vectors = embedder.embed_texts(texts)

            _set_progress(doc_id, "ingesting", "indexing", 0.80, "Storing embeddings in vector index...")

            # A PDF with no extractable text has no chunks, so no index is created; the document
            # is still marked ready and later searches simply return nothing.
            # Step 10: Store embeddings and chunk IDs in FAISS vector store
            store = get_store(doc_id)
            store.add(chunk_ids, vectors)

        # Step 11: Mark document status as 'ready'
        conn.execute("UPDATE documents SET status = 'ready' WHERE id = ?", (doc_id,))
        conn.commit()
        _set_progress(doc_id, "ready", "complete", 1.0, f"Ready! {len(all_chunks)} chunks indexed from {len(pages)} pages.")

    # On any failure: record the error status, publish it to the progress tracker, then
    # re-raise so the HTTP layer reports it. The PDF and any partial rows are left in place.
    except Exception as e:
        logger.error(f"Ingestion failed for doc {doc_id}: {e}")
        conn.execute("UPDATE documents SET status = 'error' WHERE id = ?", (doc_id,))
        conn.commit()
        _set_progress(doc_id, "error", "failed", 0.0, f"Ingestion failed: {str(e)}")
        raise

    return get_document(doc_id)

# Newest uploads first. upload_date has one-second resolution, so ties are possible.
def list_documents() -> list[dict]:
    """Retrieve metadata records for all uploaded documents."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, filename, page_count, file_size_bytes, upload_date, status FROM documents ORDER BY upload_date DESC"
    ).fetchall()
    return [dict(r) for r in rows]

def get_document(document_id: int) -> dict | None:
    """Retrieve a single document's record by document ID."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, filename, page_count, file_size_bytes, upload_date, status FROM documents WHERE id = ?",
        (document_id,)
    ).fetchone()
    return dict(row) if row else None

def get_pdf_path(document_id: int) -> Path | None:
    """Locate the on-disk file path for an ingested document's PDF."""
    conn = get_connection()
    row = conn.execute("SELECT file_path FROM documents WHERE id = ?", (document_id,)).fetchone()
    if row:
        path = Path(row["file_path"])
        if path.exists():
            return path
    return None

# Cleanup order: read the path while the row still exists, remove files, then the row.
def delete_document(document_id: int) -> bool:
    """
    Deletes a document along with all associated artifacts (disk PDF,
    FAISS index, SQLite chunks, and highlights).
    """
    conn = get_connection()

    # Step 1: Query file path prior to deleting database record
    row = conn.execute("SELECT file_path FROM documents WHERE id = ?", (document_id,)).fetchone()
    if not row:
        return False

    # Step 2: Remove PDF binary from disk
    pdf_path = Path(row["file_path"])
    if pdf_path.exists():
        pdf_path.unlink()

    # The vector index is not in SQLite, so it must be removed explicitly.
    # Step 3: Delete vector index files
    delete_store(document_id)

    # Step 4: Delete database record (foreign key cascades remove chunks and highlights)
    conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    conn.commit()

    # Step 5: Clean in-memory progress tracker
    _progress.pop(document_id, None)

    return True

# Whitelist filter: keep letters, digits and "._- ", drop everything else (including
# / and \). The .pdf suffix is enforced so the stored name is always a PDF name.
# Note isalnum() accepts non-ASCII letters, which are kept.
def _safe_filename(filename: str) -> str:
    """Sanitizes user input to create a safe filesystem filename."""
    safe = "".join(c for c in filename if c.isalnum() or c in "._- ")
    if not safe.lower().endswith(".pdf"):
        safe += ".pdf"
    return safe
