"""
QuickGuide — Database Tests
"""

import sys
import os
import sqlite3
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_database_schema():
    """Test that database schema creates all required tables."""
    # Create a temp database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        conn = sqlite3.connect(db_path)
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

        # Verify tables exist
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "documents" in tables
        assert "text_chunks" in tables
        assert "highlights" in tables

        # Verify we can insert and query
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
    """Test that deleting a document cascades to chunks and highlights."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys=ON")
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

        # Insert document and related data
        conn.execute("INSERT INTO documents (id, filename, file_path) VALUES (1, 'test.pdf', '/tmp/test.pdf')")
        conn.execute("INSERT INTO text_chunks (document_id, text_content) VALUES (1, 'Hello world')")
        conn.execute("INSERT INTO highlights (document_id, text_content) VALUES (1, 'Hello')")
        conn.commit()

        # Verify data exists
        assert conn.execute("SELECT COUNT(*) FROM text_chunks").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM highlights").fetchone()[0] == 1

        # Delete document
        conn.execute("DELETE FROM documents WHERE id = 1")
        conn.commit()

        # Verify cascaded delete
        assert conn.execute("SELECT COUNT(*) FROM text_chunks").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM highlights").fetchone()[0] == 0

        conn.close()
    finally:
        os.unlink(db_path)
