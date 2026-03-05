"""
QuickGuide (QG) — Pydantic Models
Request/response DTOs and API models.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── API Request Models ───────────────────────────

class SearchRequest(BaseModel):
    document_id: int
    query: str = Field(..., min_length=3)
    top_k: int = Field(default=10, ge=1, le=50)


class HighlightCreate(BaseModel):
    document_id: int
    page_number: int
    text_content: str
    color: str = Field(default="#FFE066")


class HighlightUpdate(BaseModel):
    color: str


# ── API Response Models ──────────────────────────

class DocumentResponse(BaseModel):
    id: int
    filename: str
    page_count: int
    file_size_bytes: int
    upload_date: str
    status: str


class SearchResult(BaseModel):
    chunk_id: int
    page_number: int
    text_content: str
    score: float
    snippet: str


class HighlightResponse(BaseModel):
    id: int
    document_id: int
    page_number: int
    text_content: str
    color: str
    created_at: str


class IngestionProgress(BaseModel):
    document_id: int
    status: str
    stage: str
    progress: float  # 0.0 to 1.0
    message: str
