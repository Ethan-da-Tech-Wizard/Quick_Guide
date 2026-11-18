# Program: Quick_Guide - models.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Defines the Pydantic classes that describe the shape of API requests and responses (search, highlights, documents, ingestion progress).
"""
QuickGuide (QG) — Pydantic Models
Request/response DTOs and API models.
"""

# BaseModel validates incoming data; Field adds extra rules (minimum length, ranges, defaults)
from pydantic import BaseModel, Field
from typing import Optional


# ── API Request Models ───────────────────────────

class SearchRequest(BaseModel):
    """Data the browser sends when searching one document."""
    document_id: int                              # which document to search
    query: str = Field(..., min_length=3)         # required text, at least 3 characters
    top_k: int = Field(default=10, ge=1, le=50)   # how many results; must be 1 to 50


class HighlightCreate(BaseModel):
    """Data the browser sends to create a new highlight."""
    document_id: int       # document the highlight belongs to
    page_number: int       # page the highlighted text is on
    text_content: str      # the highlighted text itself
    color: str = Field(default="#FFE066")  # highlight color, default is yellow


class HighlightUpdate(BaseModel):
    """Data the browser sends to change a highlight's color."""
    color: str


# ── API Response Models ──────────────────────────

class DocumentResponse(BaseModel):
    """Information about one uploaded document sent back to the browser."""
    id: int
    filename: str
    page_count: int
    file_size_bytes: int
    upload_date: str
    status: str


class SearchResult(BaseModel):
    """One search hit: which chunk matched, where, and how well."""
    chunk_id: int
    page_number: int
    text_content: str
    score: float      # similarity score
    snippet: str      # short preview of the text


class HighlightResponse(BaseModel):
    """One saved highlight sent back to the browser."""
    id: int
    document_id: int
    page_number: int
    text_content: str
    color: str
    created_at: str


class IngestionProgress(BaseModel):
    """Progress report while a PDF is being processed after upload."""
    document_id: int
    status: str
    stage: str
    progress: float  # 0.0 to 1.0
    message: str
