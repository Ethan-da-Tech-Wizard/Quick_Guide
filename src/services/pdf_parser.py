# Program: Quick_Guide - pdf_parser.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Uses PyMuPDF to extract page text from a PDF, count its pages, and find the on-page rectangles of searched words for highlighting.
"""
QuickGuide (QG) — PDF Parser Service
Extracts text from PDF files using PyMuPDF (fitz).
"""

# ── Imports ──────────────────────────────────────
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple


def extract_text(pdf_path: str | Path) -> List[Tuple[int, str]]:
    """
    Extract text from every page of a PDF.

    Returns:
        List of (page_number, text) tuples. Page numbers are 1-indexed.
    """
    # Accept either a string or Path and make it a Path
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Will hold (page number, text) pairs
    pages = []
    # Open the PDF; the try/finally below guarantees it is closed
    doc = fitz.open(str(pdf_path))
    try:
        # enumerate gives each page's 0-based position i
        for i, page in enumerate(doc):
            # Plain text of the page
            text = page.get_text("text")
            # Skip pages with no text (for example, scanned images)
            if text and text.strip():
                pages.append((i + 1, text))
    # Always close the file, even if an error happened
    finally:
        doc.close()

    return pages


def get_page_count(pdf_path: str | Path) -> int:
    """Get the total number of pages in a PDF."""
    doc = fitz.open(str(pdf_path))
    # len(doc) is the number of pages
    count = len(doc)
    doc.close()
    return count


def search_text_on_page(pdf_path: str | Path, page_number: int, query: str) -> list:
    """
    Search for text on a specific page and return bounding-box rectangles.
    Used for precise highlighting in the frontend.

    Args:
        pdf_path: Path to the PDF file
        page_number: 1-indexed page number
        query: Text to search for

    Returns:
        List of dict with x0, y0, x1, y1, width, height coordinates
    """
    doc = fitz.open(str(pdf_path))
    try:
        # Out-of-range page: nothing to find
        if page_number < 1 or page_number > len(doc):
            return []

        # Pages are 0-based inside the library, so subtract 1
        page = doc[page_number - 1]
        
        # Search for each word individually if the query is long, to avoid exact string match failures over line breaks
        words = [w for w in query.replace('\n', ' ').split() if len(w) > 2]
        if not words:
            words = [query]
            
        # Collect the rectangles of every match
        rects = []
        for word in words:
            word_rects = page.search_for(word)
            rects.extend(word_rects)
            
        # Page size, used to turn coordinates into 0-to-1 fractions
        page_rect = page.rect

        # Convert each rectangle to fractions so it works at any zoom level
        results = []
        for rect in rects:
            results.append({
                "x0": rect.x0 / page_rect.width,
                "y0": rect.y0 / page_rect.height,
                "x1": rect.x1 / page_rect.width,
                "y1": rect.y1 / page_rect.height,
                "width": (rect.x1 - rect.x0) / page_rect.width,
                "height": (rect.y1 - rect.y0) / page_rect.height,
            })
        return results
    finally:
        doc.close()
