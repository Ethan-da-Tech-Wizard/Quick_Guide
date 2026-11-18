# Program: Quick_Guide - database.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Opens a per-thread SQLite connection and creates the documents, text_chunks and highlights tables and their indexes.
"""
QuickGuide (QG) — Database Service
SQLite setup, migrations, and Dapper-style queries.
"""

# ── Imports ──────────────────────────────────────
import sqlite3            # Python's built-in SQLite database library
import threading          # used to keep one connection per thread
from pathlib import Path
from config import DB_PATH  # where the database file lives (defined in config.py)


# Thread-local storage: each thread gets its own private attributes here,
# so threads never share (and corrupt) one connection.
_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """Get a thread-local SQLite connection with WAL mode."""
    # Only open a new connection if this thread does not have one yet.
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        # Row factory lets us read columns by name, e.g. row["filename"]
        _local.conn.row_factory = sqlite3.Row
        # WAL mode lets reads and writes happen at the same time more smoothly
        _local.conn.execute("PRAGMA journal_mode=WAL")
        # SQLite ignores foreign keys unless we turn them on (needed for ON DELETE CASCADE)
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    # executescript runs several SQL statements in a row.
    # "IF NOT EXISTS" makes it safe to run every time the app starts.
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

        CREATE INDEX IF NOT EXISTS idx_chunks_doc
            ON text_chunks(document_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_doc_page
            ON text_chunks(document_id, page_number);

        CREATE TABLE IF NOT EXISTS highlights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            page_number INTEGER NOT NULL,
            text_content TEXT NOT NULL,
            color TEXT NOT NULL DEFAULT '#FFE066',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_highlights_doc
            ON highlights(document_id);
    """)
    # Save (commit) the changes to the database file
    conn.commit()
