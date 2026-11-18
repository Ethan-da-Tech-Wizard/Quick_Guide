# ==============================================================================
# Program: database.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Database access layer for QuickGuide. Manages thread-local SQLite
#          connections with Write-Ahead Logging (WAL) enabled, runs schema
#          initialization scripts, and enforces relational integrity for
#          documents, text chunks, and highlight annotations.
# ==============================================================================

import sqlite3
import threading
from pathlib import Path
from config import DB_PATH

# Thread-local storage to ensure thread safety across FastAPI async worker threads
_local = threading.local()

def get_connection() -> sqlite3.Connection:
    """
    Retrieve or establish a thread-local SQLite connection with WAL mode enabled.
    
    Returns:
        sqlite3.Connection: Active database connection.
    """
    # Step 1: Check if an active connection already exists on the current thread
    if not hasattr(_local, "conn") or _local.conn is None:
        # Step 2: Open SQLite connection without cross-thread check limitations
        _local.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        # Step 3: Enable dictionary-like column access via sqlite3.Row
        _local.conn.row_factory = sqlite3.Row
        # Step 4: Configure high-concurrency WAL mode and foreign key cascades
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn

def init_db():
    """
    Initializes database schema, creating tables and performance indexes
    if they do not already exist.
    """
    conn = get_connection()
    # Step 1: Execute idempotent DDL statements
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
    # Step 2: Commit schema changes
    conn.commit()
