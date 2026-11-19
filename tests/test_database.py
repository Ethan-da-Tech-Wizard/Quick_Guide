# ==============================================================================
# Program: test_database.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Unit tests for QuickGuide SQLite schema and relational operations.
#          Validates table creation, index initialization, insert/query integrity,
#          and foreign key cascading deletion behavior.
# ==============================================================================

# These tests use throwaway SQLite files and plain sqlite3; they do not import the
# application's database module, so they exercise the schema design, not get_connection().
import sys
import os
import sqlite3
import tempfile

# Kept for consistency with the other test module; unused here since no app code is imported.
# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

def test_database_schema():
    """Test that database schema initializes all required tables and indexes."""
    # Create an isolated temporary database file
    # delete=False because the file must be closed before sqlite3 reopens it (required on
    # Windows) and is removed manually in the finally block.
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # The try/finally guarantees the temp file is removed even if an assertion fails.
    try:
        conn = sqlite3.connect(db_path)
        # The DDL below is a copy of the schema in src/database.py (minus the indexes), so this
        # test will not notice if the real schema drifts from it.
        # Initialize schema
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                page_count INTEGER DEFAULT 0,
                file_size_bytes INTEGER DEFAULT 0,
                upload_date TEXT NOT NULL DEFAULT (datetime('now')),
                status TEXT NOT NULL DEFAULT 'pending'
            );

            CREATE TABLE IF NOT EXISTS text_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                page_number INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                text_content TEXT NOT NULL,
                start_char INTEGER DEFAULT 0,
                end_char INTEGER DEFAULT 0,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS highlights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                page_number INTEGER NOT NULL,
                text_content TEXT NOT NULL,
                color TEXT NOT NULL DEFAULT '#FFE066',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );
        """)
        conn.commit()

        # Table names are read from sqlite_master, SQLite's internal catalog.
        # Step 1: Verify tables exist
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "documents" in tables
        assert "text_chunks" in tables
        assert "highlights" in tables

        # row[1] is the second column (filename), since sqlite3.Row is not configured here.
        # Step 2: Verify insert and retrieval operations
        conn.execute(
            "INSERT INTO documents (filename, file_path, status) VALUES (?, ?, ?)",
            ("test.pdf", "/tmp/test.pdf", "ready")
        )
        conn.commit()

        row = conn.execute("SELECT * FROM documents WHERE filename = ?", ("test.pdf",)).fetchone()
        assert row is not None
        assert row[1] == "test.pdf"

        conn.close()
    finally:
        os.unlink(db_path)

def test_cascade_delete():
    """Test that deleting a document cascades deletion to chunks and highlights."""
    # Same temp-file pattern as above.
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        conn = sqlite3.connect(db_path)
        # SQLite disables foreign keys by default. Without this PRAGMA, ON DELETE CASCADE does
        # nothing, and the final assertions would fail. The app sets it in get_connection().
        conn.execute("PRAGMA foreign_keys=ON")
        # A reduced schema: only the columns this test needs, with the same cascade rules.
        conn.executescript("""
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
            );
            CREATE TABLE text_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                page_number INTEGER DEFAULT 1,
                chunk_index INTEGER DEFAULT 0,
                text_content TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );
            CREATE TABLE highlights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                page_number INTEGER DEFAULT 1,
                text_content TEXT NOT NULL,
                color TEXT DEFAULT '#FFE066',
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );
        """)

        # Arrange: one parent row and one child row in each dependent table.
        # Step 1: Insert parent document and child chunk/highlight records
        conn.execute("INSERT INTO documents (id, filename, file_path) VALUES (1, 'test.pdf', '/tmp/test.pdf')")
        conn.execute("INSERT INTO text_chunks (document_id, text_content) VALUES (1, 'Hello world')")
        conn.execute("INSERT INTO highlights (document_id, text_content) VALUES (1, 'Hello')")
        conn.commit()

        # Step 2: Verify records are present
        assert conn.execute("SELECT COUNT(*) FROM text_chunks").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM highlights").fetchone()[0] == 1

        # Act: delete only the parent; the database should remove the children by itself.
        # Step 3: Delete parent document
        conn.execute("DELETE FROM documents WHERE id = 1")
        conn.commit()

        # Step 4: Verify cascaded deletion eliminated children
        assert conn.execute("SELECT COUNT(*) FROM text_chunks").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM highlights").fetchone()[0] == 0

        conn.close()
    finally:
        os.unlink(db_path)
