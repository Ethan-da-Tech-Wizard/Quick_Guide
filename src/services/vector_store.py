# ==============================================================================
# Program: vector_store.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Vector store service for QuickGuide. Manages per-document vector
#          indices using FAISS (IndexFlatIP) with automatic L2 normalization for
#          cosine similarity, alongside an in-memory NumPy fallback mode.
#          Persists indices and ID mapping dictionaries to disk.
# ==============================================================================

import logging
import json
import numpy as np
from pathlib import Path
from config import VECTOR_DIR, EMBEDDING_DIM

logger = logging.getLogger(__name__)

# FAISS is optional. If it cannot be imported, a pure-NumPy brute-force search is used
# instead (same results, slower on big documents).
# Attempt to load native FAISS library with fallback to pure NumPy
try:
    import faiss
    HAS_FAISS = True
    logger.info("FAISS available — using optimized vector search.")
except ImportError:
    HAS_FAISS = False
    logger.warning("FAISS not available — using numpy cosine similarity fallback.")

# One VectorStore per document. On disk (under data/vectors): doc_<id>.faiss (the index),
# doc_<id>.map (JSON list mapping index position -> chunk id) and, in fallback mode,
# doc_<id>.npy (raw vectors).
class VectorStore:
    """
    Manages vector index persistence and nearest-neighbor search for a single document.
    """
    def __init__(self, document_id: int):
        self.document_id = document_id
        self.index_path = VECTOR_DIR / f"doc_{document_id}.faiss"
        self.map_path = VECTOR_DIR / f"doc_{document_id}.map"
        # The FAISS row number is only a position; chunk_ids[position] gives the SQLite chunk id.
        self.chunk_ids: list[int] = []
        self.index = None
        self._vectors: np.ndarray | None = None  # Storage for NumPy fallback mode

        # Restore any previously saved state immediately on construction.
        self._load()

    def _load(self):
        """Loads index files and chunk ID mappings from disk if present."""
        # Step 1: Load chunk ID mapping list
        if self.map_path.exists():
            # The JSON map must be read in both modes, so it is loaded first.
            with open(self.map_path, "r") as f:
                self.chunk_ids = json.load(f)

        # Step 2: Load FAISS index or NumPy vector array
        if HAS_FAISS and self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        # Note: a store created in FAISS mode will not read .npy files and vice versa, so
        # switching environments between runs strands the old index files.
        elif not HAS_FAISS:
            npy_path = VECTOR_DIR / f"doc_{self.document_id}.npy"
            if npy_path.exists():
                self._vectors = np.load(str(npy_path))

    def add(self, chunk_ids: list[int], vectors: np.ndarray):
        """
        Adds vectors and corresponding chunk IDs to the index.

        Args:
            chunk_ids (list[int]): Database primary keys for the chunks.
            vectors (np.ndarray): Dense embedding matrix.
        """
        # Single vectors are promoted to a 1xN matrix.
        # Step 1: Ensure 2D matrix shape
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        # Step 2: Ingest into FAISS or accumulate in NumPy array
        if HAS_FAISS:
            # IndexFlatIP is an exact (brute-force) inner-product index with no training step.
            if self.index is None:
                self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
            # Mathematical Equivalence: Cosine Similarity via L2-Normalized Inner Product
        # Cosine similarity is defined as (A · B) / (||A|| * ||B||).
        # By pre-normalizing all vectors to unit L2 length (||V||_2 = 1.0), the denominator becomes 1.0.
        # Consequently, FAISS IndexFlatIP (Inner Product) computes exact cosine similarity via fast BLAS matrix multiply.
        faiss.normalize_L2(vectors)
            self.index.add(vectors)
        # Fallback path: normalize rows manually (zero vectors are left unscaled by dividing
        # by 1) and append to the in-memory matrix.
        else:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1
            vectors = vectors / norms
            if self._vectors is None:
                self._vectors = vectors
            else:
                self._vectors = np.vstack([self._vectors, vectors])

        # Persist after every add so the index survives a restart.
        # Step 3: Record IDs and persist to disk
        self.chunk_ids.extend(chunk_ids)
        self._save()

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> list[tuple[int, float]]:
        """
        Executes k-nearest-neighbors search.

        Args:
            query_vector (np.ndarray): Single embedded query vector.
            top_k (int): Number of top results to retrieve.

        Returns:
            list[tuple[int, float]]: List of (chunk_id, score) tuples in descending score order.
        """
        if not self.chunk_ids:
            return []

        # astype(float32) with reshape(1, -1) produces the 2-D float32 batch FAISS expects.
        query_vector = query_vector.reshape(1, -1).astype(np.float32)

        # Step 1: Execute search using FAISS if available
        if HAS_FAISS and self.index is not None:
            faiss.normalize_L2(query_vector)
            # k cannot exceed the number of stored vectors.
            k = min(top_k, len(self.chunk_ids))
            scores, indices = self.index.search(query_vector, k)
            results = []
            # FAISS pads missing results with index -1, hence the bounds check.
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.chunk_ids):
                    results.append((self.chunk_ids[idx], float(score)))
            return results
        # Step 2: Fallback to NumPy matrix multiplication
        elif self._vectors is not None:
            # Fallback: dot product of unit vectors = cosine similarity; argsort ascending then
            # reversed gives best-first order.
            norm = np.linalg.norm(query_vector)
            if norm > 0:
                query_vector = query_vector / norm
            scores = self._vectors @ query_vector.T
            scores = scores.flatten()
            k = min(top_k, len(scores))
            top_indices = np.argsort(scores)[::-1][:k]
            return [(self.chunk_ids[i], float(scores[i])) for i in top_indices]
        else:
            return []

    def _save(self):
        """Serializes current index and mapping metadata to disk."""
        # The map is always written; the vectors go to FAISS or .npy depending on the mode.
        VECTOR_DIR.mkdir(parents=True, exist_ok=True)

        with open(self.map_path, "w") as f:
            json.dump(self.chunk_ids, f)

        if HAS_FAISS and self.index is not None:
            faiss.write_index(self.index, str(self.index_path))
        elif self._vectors is not None:
            npy_path = VECTOR_DIR / f"doc_{self.document_id}.npy"
            np.save(str(npy_path), self._vectors)

    def delete(self):
        """Removes all on-disk index artifacts associated with this document."""
        # Remove every artifact that could exist, regardless of which mode produced it.
        for path in [self.index_path, self.map_path,
                     VECTOR_DIR / f"doc_{self.document_id}.npy"]:
            if path.exists():
                path.unlink()

# ── Module-Level Store Cache ──────────────────────────────────────────────────

# Process-wide cache of open stores, keyed by document id.
_stores: dict[int, VectorStore] = {}

def get_store(document_id: int) -> VectorStore:
    """Retrieve or cache VectorStore instance for a given document."""
    if document_id not in _stores:
        _stores[document_id] = VectorStore(document_id)
    return _stores[document_id]

def delete_store(document_id: int):
    """Evict and delete vector index files for a given document."""
    # Evicting from the cache first ensures no stale in-memory index remains. If the store
    # was never loaded, a temporary instance is created just to locate and delete the files.
    store = _stores.pop(document_id, None)
    if store:
        store.delete()
    else:
        VectorStore(document_id).delete()
