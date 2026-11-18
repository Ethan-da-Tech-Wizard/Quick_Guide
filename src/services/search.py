# ==============================================================================
# Program: search.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Semantic search orchestration service for QuickGuide. Converts
#          natural language user queries into vector embeddings, performs
#          cosine similarity nearest-neighbor lookup in the document's FAISS
#          vector store, filters by minimum threshold, and enriches search hits
#          with chunk text content from SQLite.
# ==============================================================================

import logging
from services import embedder
from services.vector_store import get_store
from database import get_connection
from config import MIN_SIMILARITY

logger = logging.getLogger(__name__)

def semantic_search(document_id: int, query: str, top_k: int = 10) -> list[dict]:
    """
    Executes semantic vector search against indexed document chunks.

    Args:
        document_id (int): Target document identifier.
        query (str): Natural language search query.
        top_k (int): Number of top results to return.

    Returns:
        list[dict]: Scored result dictionaries containing chunk_id, page_number,
                    text_content, score, and snippet preview.
    """
    # Step 1: Compute query embedding vector
    query_vector = embedder.embed_query(query)

    # Step 2: Query FAISS nearest-neighbor index
    store = get_store(document_id)
    raw_results = store.search(query_vector, top_k=top_k)

    if not raw_results:
        return []

    # Step 3: Filter results by minimum cosine similarity threshold
    filtered = [(cid, score) for cid, score in raw_results if score >= MIN_SIMILARITY]

    if not filtered:
        return []

    # Step 4: Batch fetch text chunk records from SQLite
    conn = get_connection()
    chunk_ids = [cid for cid, _ in filtered]
    placeholders = ",".join("?" * len(chunk_ids))

    rows = conn.execute(
        f"SELECT id, page_number, text_content FROM text_chunks WHERE id IN ({placeholders})",
        chunk_ids
    ).fetchall()

    chunk_map = {row["id"]: dict(row) for row in rows}

    # Step 5: Format response payload with formatted snippets and scores
    results = []
    for chunk_id, score in filtered:
        chunk = chunk_map.get(chunk_id)
        if chunk:
            text = chunk["text_content"]
            snippet = text[:200] + "..." if len(text) > 200 else text
            results.append({
                "chunk_id": chunk_id,
                "page_number": chunk["page_number"],
                "text_content": text,
                "score": round(score, 4),
                "snippet": snippet,
            })

    return results
