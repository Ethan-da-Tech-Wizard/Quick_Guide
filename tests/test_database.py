# Program: Quick_Guide - test_database.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Pytest tests that build scratch SQLite databases to check the schema creates its tables and that deleting a document cascades to its chunks and highlights.
"""
QuickGuide — Database Tests
"""

# Imports: sys/os for paths, sqlite3 for the database, tempfile for throwaway files
import sys
import os
import sqlite3
import tempfile

# (the line below lets the tests import code from the src folder)
# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_database_schema():
    """Test that database schema creates all required tables."""
    # Create a temp database
    # Make a temporary file to act as a scratch database; delete=False so SQLite can reuse it
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        # Open the scratch database and build a copy of the app's tables
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

        # (check below) ask SQLite which tables it now has
        # Verify tables exist
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "documents" in tables
        assert "text_chunks" in tables
        assert "highlights" in tables

        # (check below) a row can be written and read back
        # Verify we can insert and query
        conn.execute(
            "INSERT INTO documents (filename, file_path, status) VALUES (?, ?, ?)",
            ("test.pdf", "/tmp/test.pdf", "ready")
        )
        conn.commit()

        # row[1] is the second column, filename
        row = conn.execute("SELECT * FROM documents WHERE filename = ?", ("test.pdf",)).fetchone()
        assert row is not None
        assert row[1] == "test.pdf"

        conn.close()
    # Always delete the temporary database file, even if an assert failed
    finally:
        os.unlink(db_path)


def test_cascade_delete():
    """Test that deleting a document cascades to chunks and highlights."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        # Second test: a fresh scratch database
        conn = sqlite3.connect(db_path)
        # Foreign keys must be switched on for cascade deletes to work
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

        # (below) one document with one chunk and one highlight attached
        # Insert document and related data
        conn.execute("INSERT INTO documents (id, filename, file_path) VALUES (1, 'test.pdf', '/tmp/test.pdf')")
        conn.execute("INSERT INTO text_chunks (document_id, text_content) VALUES (1, 'Hello world')")
        conn.execute("INSERT INTO highlights (document_id, text_content) VALUES (1, 'Hello')")
        conn.commit()

        # Verify data exists
        assert conn.execute("SELECT COUNT(*) FROM text_chunks").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM highlights").fetchone()[0] == 1

        # (below) deleting the parent row should remove the children automatically
        # Delete document
        conn.execute("DELETE FROM documents WHERE id = 1")
        conn.commit()

        # Verify cascaded delete
        assert conn.execute("SELECT COUNT(*) FROM text_chunks").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM highlights").fetchone()[0] == 0

        conn.close()
    finally:
        os.unlink(db_path)
