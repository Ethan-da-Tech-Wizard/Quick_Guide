# ==============================================================================
# Program: pdf_parser.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: PDF document parsing and layout extraction service for QuickGuide.
#          Uses PyMuPDF (fitz) to extract text per page, count total document
#          pages, and search for occurrences of text queries on specific pages
#          returning normalized coordinate bounding boxes for frontend rendering.
# ==============================================================================

# PyMuPDF is imported under its legacy module name `fitz`.
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
    # Accept str or Path so callers (database rows vs. uploads) need not convert.
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Pages without any extractable text (scans/images) are skipped rather than returned
    # as empty strings; page numbers stay tied to the real position, so gaps are possible.
    pages = []
    # Step 1: Open document with PyMuPDF
    # The document is always closed (finally) to release the file handle, even on errors.
    doc = fitz.open(str(pdf_path))
    try:
        # Step 2: Iterate over pages and extract plain text
        for i, page in enumerate(doc):
            # "text" mode returns plain reading-order text without layout information.
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
    # Used for validation at upload time; raises if the file is not a readable PDF.
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
    # A fresh handle per call is simple and stateless; PyMuPDF opens quickly.
    doc = fitz.open(str(pdf_path))
    try:
        # 1-indexed in the API, 0-indexed in PyMuPDF; out-of-range pages return no rectangles.
        # Step 1: Validate page index bounds
        if page_number < 1 or page_number > len(doc):
            return []

        page = doc[page_number - 1]
        
        # Query handling: a chunk of text from a search result may wrap across lines, which
        # search_for cannot match as one phrase. So the query is split into words and each
        # word is searched separately. Words of 1-2 characters are dropped as noise; if that
        # leaves nothing, the whole query is searched as-is.
        # Step 2: Split query into tokens to handle cross-line word wrapping
        words = [w for w in query.replace('\n', ' ').split() if len(w) > 2]
        if not words:
            words = [query]
            
        # Every occurrence of every word is highlighted, so common words can produce many
        # boxes; this is a deliberate approximation rather than exact phrase matching.
        # Step 3: Find bounding rectangles for each word match
        rects = []
        for word in words:
            word_rects = page.search_for(word)
            rects.extend(word_rects)
            
        # Page size in PDF points; dividing by it gives resolution-independent coordinates
        # that the frontend multiplies by 100 to place CSS percentage-based overlays.
        page_rect = page.rect

        # Output keys x0/y0/x1/y1 are the corners (origin top-left, y grows downward) and
        # width/height are convenience values, all as fractions of the page.
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
