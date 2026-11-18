# Program: Quick_Guide - search.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Runs a semantic search on one document by embedding the query, searching its vector index, filtering weak matches and loading chunk text from SQLite.
"""
QuickGuide (QG) — Search Service
Orchestrates semantic search: embed query → FAISS search → enrich results.
"""

import logging
from services import embedder                    # turns the query into a vector
from services.vector_store import get_store      # finds the saved index for a document
from database import get_connection              # access to the SQLite database
from config import MIN_SIMILARITY                # minimum score a result must reach

logger = logging.getLogger(__name__)


def semantic_search(document_id: int, query: str, top_k: int = 10) -> list[dict]:
    """
    Perform semantic search on a document.

    Args:
        document_id: The document to search
        query: Natural-language query string
        top_k: Number of results to return

    Returns:
        List of result dicts with chunk_id, page_number, text_content, score, snippet
    """
    # 1. Embed the query
    query_vector = embedder.embed_query(query)

    # 2. Search the vector store
    store = get_store(document_id)
    raw_results = store.search(query_vector, top_k=top_k)

    # No matches at all: return an empty list
    if not raw_results:
        return []

    # 3. Filter by minimum similarity
    # Keep only (chunk id, score) pairs whose score is high enough
    filtered = [(cid, score) for cid, score in raw_results if score >= MIN_SIMILARITY]

    if not filtered:
        return []

    # 4. Fetch chunk text from SQLite
    conn = get_connection()
    chunk_ids = [cid for cid, _ in filtered]
    # Build "?,?,?" with one question mark per id for the SQL IN (...) list
    placeholders = ",".join("?" * len(chunk_ids))

    rows = conn.execute(
        f"SELECT id, page_number, text_content FROM text_chunks WHERE id IN ({placeholders})",
        chunk_ids
    ).fetchall()

    # Dictionary so each chunk can be looked up quickly by its id
    chunk_map = {row["id"]: dict(row) for row in rows}

    # 5. Build results
    results = []
    # Loop in score order so the best match stays first
    for chunk_id, score in filtered:
        chunk = chunk_map.get(chunk_id)
        if chunk:  # skip ids that are in the index but missing from the database
            text = chunk["text_content"]
            # Preview: first 200 characters, with "..." if the text was cut
            snippet = text[:200] + "..." if len(text) > 200 else text
            results.append({
                "chunk_id": chunk_id,
                "page_number": chunk["page_number"],
                "text_content": text,
                "score": round(score, 4),  # round to 4 decimals for tidy output
                "snippet": snippet,
            })

    return results
