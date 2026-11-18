# Program: Quick_Guide - vector_store.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Stores and searches each document's embedding vectors, using a FAISS index when available and a numpy cosine-similarity fallback otherwise, saved to disk.
"""
QuickGuide (QG) — Vector Store Service
FAISS index management with numpy fallback.
"""

# ── Imports ──────────────────────────────────────
import logging
import json
import numpy as np
from pathlib import Path
from config import VECTOR_DIR, EMBEDDING_DIM

# Logger for status messages
logger = logging.getLogger(__name__)

# FAISS is a fast similarity-search library; it is optional here
# Try to import FAISS, fall back to numpy cosine similarity
try:
    import faiss
    HAS_FAISS = True
    logger.info("FAISS available — using optimized vector search.")
except ImportError:
    HAS_FAISS = False
    logger.warning("FAISS not available — using numpy cosine similarity fallback.")


class VectorStore:
    """Per-document vector index."""

    # Set up file locations and empty state, then load anything saved earlier
    def __init__(self, document_id: int):
        self.document_id = document_id
        # One FAISS file and one id-map file per document
        self.index_path = VECTOR_DIR / f"doc_{document_id}.faiss"
        self.map_path = VECTOR_DIR / f"doc_{document_id}.map"
        # Position in the index -> database chunk id
        self.chunk_ids: list[int] = []
        # The FAISS index (None until created)
        self.index = None
        self._vectors: np.ndarray | None = None  # For fallback mode

        # Read saved data from disk if there is any
        self._load()

    def _load(self):
        """Load existing index from disk."""
        # Load the list that maps index positions to chunk ids
        if self.map_path.exists():
            with open(self.map_path, "r") as f:
                self.chunk_ids = json.load(f)

        # Load the saved FAISS index
        if HAS_FAISS and self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        # Fallback: load saved numpy vectors instead
        elif not HAS_FAISS:
            npy_path = VECTOR_DIR / f"doc_{self.document_id}.npy"
            if npy_path.exists():
                self._vectors = np.load(str(npy_path))

    def add(self, chunk_ids: list[int], vectors: np.ndarray):
        """Add vectors to the index."""
        # A single vector becomes a 1-row table
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        # FAISS path: IndexFlatIP compares by inner product (equals cosine similarity once normalized)
        if HAS_FAISS:
            if self.index is None:
                self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
            faiss.normalize_L2(vectors)
            self.index.add(vectors)
        else:
            # Numpy fallback: normalize each vector by hand (avoid dividing by zero)
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1
            vectors = vectors / norms
            if self._vectors is None:
                self._vectors = vectors
            else:
                self._vectors = np.vstack([self._vectors, vectors])

        # Remember the chunk ids, then write everything to disk
        self.chunk_ids.extend(chunk_ids)
        self._save()

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> list[tuple[int, float]]:
        """
        Search for nearest neighbors.

        Returns:
            List of (chunk_id, score) tuples, sorted by descending score.
        """
        # Empty index: nothing to find
        if not self.chunk_ids:
            return []

        # Shape the query as one row of float32 numbers
        query_vector = query_vector.reshape(1, -1).astype(np.float32)

        # FAISS search: returns scores and index positions of the closest vectors
        if HAS_FAISS and self.index is not None:
            faiss.normalize_L2(query_vector)
            # Never ask for more results than we have
            k = min(top_k, len(self.chunk_ids))
            scores, indices = self.index.search(query_vector, k)
            results = []
            # Translate index positions back into chunk ids (-1 means no match)
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.chunk_ids):
                    results.append((self.chunk_ids[idx], float(score)))
            return results
        # Numpy fallback: dot product of every stored vector with the query
        elif self._vectors is not None:
            norm = np.linalg.norm(query_vector)
            if norm > 0:
                query_vector = query_vector / norm
            scores = self._vectors @ query_vector.T
            scores = scores.flatten()
            k = min(top_k, len(scores))
            # Sort highest score first and keep the top k
            top_indices = np.argsort(scores)[::-1][:k]
            return [(self.chunk_ids[i], float(scores[i])) for i in top_indices]
        else:
            # Nothing is loaded
            return []

    def _save(self):
        """Persist index to disk."""
        # Make sure the folder exists before writing
        VECTOR_DIR.mkdir(parents=True, exist_ok=True)

        # Save the id map as JSON
        with open(self.map_path, "w") as f:
            json.dump(self.chunk_ids, f)

        # Save the index in whichever format is in use
        if HAS_FAISS and self.index is not None:
            faiss.write_index(self.index, str(self.index_path))
        elif self._vectors is not None:
            npy_path = VECTOR_DIR / f"doc_{self.document_id}.npy"
            np.save(str(npy_path), self._vectors)

    def delete(self):
        """Delete index files from disk."""
        # Remove every file belonging to this document
        for path in [self.index_path, self.map_path,
                     VECTOR_DIR / f"doc_{self.document_id}.npy"]:
            if path.exists():
                path.unlink()


# ── Module-level cache ───────────────────────────

# Dictionary of already-loaded stores, so each is read from disk only once
_stores: dict[int, VectorStore] = {}


def get_store(document_id: int) -> VectorStore:
    """Get or create a VectorStore for a document."""
    # Create the store on first request, reuse it afterwards
    if document_id not in _stores:
        _stores[document_id] = VectorStore(document_id)
    return _stores[document_id]


def delete_store(document_id: int):
    """Delete a document's vector store."""
    # Remove it from the cache (None if it was not cached)
    store = _stores.pop(document_id, None)
    if store:
        store.delete()
    else:
        # Not cached: load it just so its files can be deleted
        VectorStore(document_id).delete()
