"""
QuickGuide (QG) — Highlight Service
CRUD operations for persistent highlights.
"""

from database import get_connection


def add_highlight(document_id: int, page_number: int, text_content: str, color: str = "#FFE066") -> dict:
    """Add a highlight annotation."""
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO highlights (document_id, page_number, text_content, color)
           VALUES (?, ?, ?, ?)""",
        (document_id, page_number, text_content, color)
    )
    conn.commit()
    return get_highlight(cursor.lastrowid)


def get_highlights(document_id: int, page_number: int | None = None) -> list[dict]:
    """Get highlights for a document, optionally filtered by page."""
    conn = get_connection()
    if page_number is not None:
        rows = conn.execute(
            "SELECT * FROM highlights WHERE document_id = ? AND page_number = ? ORDER BY id",
            (document_id, page_number)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM highlights WHERE document_id = ? ORDER BY page_number, id",
            (document_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_highlight(highlight_id: int) -> dict | None:
    """Get a single highlight."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM highlights WHERE id = ?", (highlight_id,)).fetchone()
    return dict(row) if row else None


def update_highlight(highlight_id: int, color: str) -> dict | None:
    """Update highlight color."""
    conn = get_connection()
    conn.execute("UPDATE highlights SET color = ? WHERE id = ?", (color, highlight_id))
    conn.commit()
    return get_highlight(highlight_id)


def delete_highlight(highlight_id: int) -> bool:
    """Delete a highlight."""
    conn = get_connection()
    cursor = conn.execute("DELETE FROM highlights WHERE id = ?", (highlight_id,))
    conn.commit()
    return cursor.rowcount > 0
