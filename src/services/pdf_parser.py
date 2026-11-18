# ==============================================================================
# Program: pdf_parser.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: PDF document parsing and layout extraction service for QuickGuide.
#          Uses PyMuPDF (fitz) to extract text per page, count total document
#          pages, and search for occurrences of text queries on specific pages
#          returning normalized coordinate bounding boxes for frontend rendering.
# ==============================================================================

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple

def extract_text(pdf_path: str | Path) -> List[Tuple[int, str]]:
    """
    Extracts text sequentially from every page of a PDF document.

    Args:
        pdf_path (str | Path): Filesystem path to the PDF file.

    Returns:
        List[Tuple[int, str]]: List of (page_number, text) tuples (1-indexed).
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages = []
    # Step 1: Open document with PyMuPDF
    doc = fitz.open(str(pdf_path))
    try:
        # Step 2: Iterate over pages and extract plain text
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if text and text.strip():
                pages.append((i + 1, text))
    finally:
        # Step 3: Ensure document descriptor is closed
        doc.close()

    return pages

def get_page_count(pdf_path: str | Path) -> int:
    """
    Returns the total number of pages in the target PDF document.

    Args:
        pdf_path (str | Path): Filesystem path to the PDF file.

    Returns:
        int: Total page count.
    """
    doc = fitz.open(str(pdf_path))
    count = len(doc)
    doc.close()
    return count

def search_text_on_page(pdf_path: str | Path, page_number: int, query: str) -> list:
    """
    Searches for word occurrences on a given page and returns normalized
    bounding-box coordinates (0.0 to 1.0) for visual highlight overlays.

    Args:
        pdf_path (str | Path): Path to the PDF file.
        page_number (int): 1-indexed target page number.
        query (str): Text phrase or words to locate.

    Returns:
        list: Dictionaries containing x0, y0, x1, y1, width, and height.
    """
    doc = fitz.open(str(pdf_path))
    try:
        # Step 1: Validate page index bounds
        if page_number < 1 or page_number > len(doc):
            return []

        page = doc[page_number - 1]
        
        # Step 2: Split query into tokens to handle cross-line word wrapping
        words = [w for w in query.replace('\n', ' ').split() if len(w) > 2]
        if not words:
            words = [query]
            
        # Step 3: Find bounding rectangles for each word match
        rects = []
        for word in words:
            word_rects = page.search_for(word)
            rects.extend(word_rects)
            
        page_rect = page.rect

        # Step 4: Normalize pixel dimensions into percentage ratios (0.0 - 1.0)
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
