# ==============================================================================
# Program: highlights.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Highlight annotation management service for QuickGuide.
#          Executes persistent CRUD operations for user-selected text highlights,
#          including database insertion, retrieval by document/page, color
#          customization updates, and record deletions.
# ==============================================================================

# Thin data-access layer: every function opens (or reuses) the thread-local SQLite
# connection and works with plain dicts, so callers never see sqlite3.Row objects.
from database import get_connection

def add_highlight(document_id: int, page_number: int, text_content: str, color: str = "#FFE066") -> dict:
    """
    Inserts a new highlight record into the relational database.

    Args:
        document_id (int): Target document identifier.
        page_number (int): 1-indexed page containing highlighted selection.
        text_content (str): Selected text string.
        color (str): Hex color code for visual annotation.

    Returns:
        dict: Persisted highlight record dictionary.
    """
    # Parameterized query (?) protects against SQL injection from user-selected text.
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO highlights (document_id, page_number, text_content, color)
           VALUES (?, ?, ?, ?)""",
        (document_id, page_number, text_content, color)
    )
    # Commit before reading back; the row is then re-fetched so created_at (set by the
    # database default) is included in the returned record.
    conn.commit()
    return get_highlight(cursor.lastrowid)

def get_highlights(document_id: int, page_number: int | None = None) -> list[dict]:
    """
    Retrieves stored highlights for a document, optionally scoped to a single page.

    Args:
        document_id (int): Target document identifier.
        page_number (int, optional): Specific page filter.

    Returns:
        list[dict]: List of highlight records.
    """
    conn = get_connection()
    # Two query shapes: a single page ordered by insertion, or the whole document ordered
    # by page then insertion, which is the natural reading order for the sidebar list.
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
    """
    Retrieves a single highlight record by its primary key.

    Args:
        highlight_id (int): Unique identifier of the highlight.

    Returns:
        dict | None: Highlight record dictionary or None if not found.
    """
    conn = get_connection()
    row = conn.execute("SELECT * FROM highlights WHERE id = ?", (highlight_id,)).fetchone()
    return dict(row) if row else None

def update_highlight(highlight_id: int, color: str) -> dict | None:
    """
    Modifies the annotation color for an existing highlight.

    Args:
        highlight_id (int): Unique identifier of the highlight.
        color (str): New hex color string.

    Returns:
        dict | None: Updated highlight record dictionary or None if not found.
    """
    # UPDATE on a nonexistent id affects zero rows and is not an error; the following
    # get_highlight returns None in that case, which the API turns into a 404.
    conn = get_connection()
    conn.execute("UPDATE highlights SET color = ? WHERE id = ?", (color, highlight_id))
    conn.commit()
    return get_highlight(highlight_id)

def delete_highlight(highlight_id: int) -> bool:
    """
    Deletes a highlight annotation from the database.

    Args:
        highlight_id (int): Unique identifier of the highlight.

    Returns:
        bool: True if a row was deleted, False otherwise.
    """
    conn = get_connection()
    # rowcount reports how many rows the DELETE removed (0 means unknown id).
    cursor = conn.execute("DELETE FROM highlights WHERE id = ?", (highlight_id,))
    conn.commit()
    return cursor.rowcount > 0
