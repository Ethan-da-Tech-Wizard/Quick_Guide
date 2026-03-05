"""
QuickGuide (QG) — PDF Parser Service
Extracts text from PDF files using PyMuPDF (fitz).
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple


def extract_text(pdf_path: str | Path) -> List[Tuple[int, str]]:
    """
    Extract text from every page of a PDF.

    Returns:
        List of (page_number, text) tuples. Page numbers are 1-indexed.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages = []
    doc = fitz.open(str(pdf_path))
    try:
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if text and text.strip():
                pages.append((i + 1, text))
    finally:
        doc.close()

    return pages


def get_page_count(pdf_path: str | Path) -> int:
    """Get the total number of pages in a PDF."""
    doc = fitz.open(str(pdf_path))
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
        if page_number < 1 or page_number > len(doc):
            return []

        page = doc[page_number - 1]
        rects = page.search_for(query)
        page_rect = page.rect

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
