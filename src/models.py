# ==============================================================================
# Program: models.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Data transfer objects (DTOs) and Pydantic validation schemas for
#          QuickGuide API requests and responses. Models search parameters,
#          document metadata, chunk search hits, highlight annotations, and
#          real-time ingestion progress state.
# ==============================================================================

# Pydantic models. FastAPI uses them to parse and validate JSON bodies and to
# build the OpenAPI schema; a validation failure becomes an automatic HTTP 422.
from pydantic import BaseModel, Field
from typing import Optional

# ── API Request Models ────────────────────────────────────────────────────────

# Request body for POST /api/search.
class SearchRequest(BaseModel):
    """Payload specification for executing semantic searches over a document."""
    # Which document's vector index to query.
    document_id: int
    # min_length=3 mirrors the check in the frontend (performSearch) so tiny queries, which
    # embed poorly, are rejected on both sides.
    query: str = Field(..., min_length=3, description="Search question or keyword phrase")
    # Capped at 50 to bound the work done per request; the default of 10 matches config.TOP_K.
    top_k: int = Field(default=10, ge=1, le=50, description="Maximum number of search results to return")

# Request body for POST /api/highlights.
class HighlightCreate(BaseModel):
    """Payload specification for creating a persistent user highlight."""
    document_id: int
    # 1-indexed page number, matching the numbering used by chunks and PDF.js.
    page_number: int
    # The exact text the user selected in the viewer; it is later re-searched on the page
    # to recover bounding boxes, so it is stored verbatim.
    text_content: str
    # Default yellow matches the frontend's default highlight colour.
    color: str = Field(default="#FFE066", description="Hex color code for annotation")

# Request body for PUT /api/highlights/{id}.
class HighlightUpdate(BaseModel):
    """Payload specification for updating an existing highlight's color."""
    color: str

# ── API Response Models ───────────────────────────────────────────────────────

# Response model: mirrors the columns returned by documents.get_document().
class DocumentResponse(BaseModel):
    """Schema representing an uploaded document and its processing status."""
    id: int
    filename: str
    page_count: int
    file_size_bytes: int
    # SQLite datetime('now') string, UTC, formatted "YYYY-MM-DD HH:MM:SS".
    upload_date: str
    # One of: pending, ingesting, ready, error (see documents.upload_and_ingest).
    status: str

# Response model for one search hit. Defined for documentation/typing; the search
# endpoint currently returns plain dicts with these same keys.
class SearchResult(BaseModel):
    """Schema representing an individual semantic match hit."""
    chunk_id: int
    page_number: int
    text_content: str
    # Cosine similarity in [-1, 1] (rounded to 4 places); hits below MIN_SIMILARITY are dropped.
    score: float
    # First ~200 characters of text_content, with an ellipsis if truncated.
    snippet: str

class HighlightResponse(BaseModel):
    """Schema representing a stored highlight annotation."""
    id: int
    document_id: int
    page_number: int
    text_content: str
    color: str
    created_at: str

# Shape of the dict produced by documents.get_progress()/_set_progress().
class IngestionProgress(BaseModel):
    """Schema representing active document ingestion stage and percentage."""
    document_id: int
    status: str
    # Pipeline stage name: extracting, chunking, embedding, indexing, complete or failed.
    stage: str
    progress: float  # Value between 0.0 and 1.0
    message: str
