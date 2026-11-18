# ==============================================================================
# Program: models.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Data transfer objects (DTOs) and Pydantic validation schemas for
#          QuickGuide API requests and responses. Models search parameters,
#          document metadata, chunk search hits, highlight annotations, and
#          real-time ingestion progress state.
# ==============================================================================

from pydantic import BaseModel, Field
from typing import Optional

# ── API Request Models ────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    """Payload specification for executing semantic searches over a document."""
    document_id: int
    query: str = Field(..., min_length=3, description="Search question or keyword phrase")
    top_k: int = Field(default=10, ge=1, le=50, description="Maximum number of search results to return")

class HighlightCreate(BaseModel):
    """Payload specification for creating a persistent user highlight."""
    document_id: int
    page_number: int
    text_content: str
    color: str = Field(default="#FFE066", description="Hex color code for annotation")

class HighlightUpdate(BaseModel):
    """Payload specification for updating an existing highlight's color."""
    color: str

# ── API Response Models ───────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    """Schema representing an uploaded document and its processing status."""
    id: int
    filename: str
    page_count: int
    file_size_bytes: int
    upload_date: str
    status: str

class SearchResult(BaseModel):
    """Schema representing an individual semantic match hit."""
    chunk_id: int
    page_number: int
    text_content: str
    score: float
    snippet: str

class HighlightResponse(BaseModel):
    """Schema representing a stored highlight annotation."""
    id: int
    document_id: int
    page_number: int
    text_content: str
    color: str
    created_at: str

class IngestionProgress(BaseModel):
    """Schema representing active document ingestion stage and percentage."""
    document_id: int
    status: str
    stage: str
    progress: float  # Value between 0.0 and 1.0
    message: str
