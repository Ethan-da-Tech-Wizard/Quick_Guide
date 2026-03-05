"""
QuickGuide (QG) — Search Service
Orchestrates semantic search: embed query → FAISS search → enrich results.
"""

import logging
from services import embedder
from services.vector_store import get_store
from database import get_connection
from config import MIN_SIMILARITY

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

    if not raw_results:
        return []

    # 3. Filter by minimum similarity
    filtered = [(cid, score) for cid, score in raw_results if score >= MIN_SIMILARITY]

    if not filtered:
        return []

    # 4. Fetch chunk text from SQLite
    conn = get_connection()
    chunk_ids = [cid for cid, _ in filtered]
    placeholders = ",".join("?" * len(chunk_ids))

    rows = conn.execute(
        f"SELECT id, page_number, text_content FROM text_chunks WHERE id IN ({placeholders})",
        chunk_ids
    ).fetchall()

    chunk_map = {row["id"]: dict(row) for row in rows}

    # 5. Build results
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
