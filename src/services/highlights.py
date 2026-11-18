# Program: Quick_Guide - highlights.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Provides add, list, get, recolor and delete functions that store the user's text highlights in the SQLite highlights table.
"""
QuickGuide (QG) — Highlight Service
CRUD operations for persistent highlights.
"""

from database import get_connection  # gives us this thread's database connection


def add_highlight(document_id: int, page_number: int, text_content: str, color: str = "#FFE066") -> dict:
    """Add a highlight annotation."""
    conn = get_connection()
    # The ? marks are placeholders; passing values separately keeps the SQL safe from injection
    cursor = conn.execute(
        """INSERT INTO highlights (document_id, page_number, text_content, color)
           VALUES (?, ?, ?, ?)""",
        (document_id, page_number, text_content, color)
    )
    conn.commit()  # save the new row
    # lastrowid is the id SQLite gave the new row; read it back to return it
    return get_highlight(cursor.lastrowid)


def get_highlights(document_id: int, page_number: int | None = None) -> list[dict]:
    """Get highlights for a document, optionally filtered by page."""
    conn = get_connection()
    if page_number is not None:
        # A page was given: only that page's highlights, in creation order
        rows = conn.execute(
            "SELECT * FROM highlights WHERE document_id = ? AND page_number = ? ORDER BY id",
            (document_id, page_number)
        ).fetchall()
    else:
        # No page given: every highlight in the document, sorted by page then creation order
        rows = conn.execute(
            "SELECT * FROM highlights WHERE document_id = ? ORDER BY page_number, id",
            (document_id,)
        ).fetchall()
    # Turn each database row into a plain dictionary
    return [dict(r) for r in rows]


def get_highlight(highlight_id: int) -> dict | None:
    """Get a single highlight."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM highlights WHERE id = ?", (highlight_id,)).fetchone()
    # fetchone() gives None when nothing matched, so return None in that case
    return dict(row) if row else None


def update_highlight(highlight_id: int, color: str) -> dict | None:
    """Update highlight color."""
    conn = get_connection()
    conn.execute("UPDATE highlights SET color = ? WHERE id = ?", (color, highlight_id))
    conn.commit()
    # Return the updated row (None if the id did not exist)
    return get_highlight(highlight_id)


def delete_highlight(highlight_id: int) -> bool:
    """Delete a highlight."""
    conn = get_connection()
    cursor = conn.execute("DELETE FROM highlights WHERE id = ?", (highlight_id,))
    conn.commit()
    # rowcount is how many rows were deleted; more than 0 means it existed
    return cursor.rowcount > 0
