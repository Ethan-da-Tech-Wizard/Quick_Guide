# Program: Quick_Guide - embedder.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Loads the sentence-transformers model once and turns lists of texts or a single query into normalized float32 embedding vectors.
"""
QuickGuide (QG) — Embedding Service
Generates vector embeddings using sentence-transformers.
"""

import logging
from sentence_transformers import SentenceTransformer  # library that turns text into number vectors
from config import EMBEDDING_MODEL, MODEL_DIR          # model name and where to cache its files
import numpy as np                                     # numpy holds the vectors as arrays

logger = logging.getLogger(__name__)

# Cache for the model. Loading is slow, so we load it only once and reuse it.
_model = None


def get_model() -> SentenceTransformer:
    """Load and cache the embedding model."""
    global _model  # we assign to the module-level variable, so declare it global
    if _model is None:
        # First call only: load the model (downloads it if not already cached)
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}...")
        _model = SentenceTransformer(
            EMBEDDING_MODEL,
            cache_folder=str(MODEL_DIR)
        )
        logger.info("Embedding model loaded successfully.")
    return _model


def embed_texts(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed
        batch_size: Batch size for encoding

    Returns:
        numpy array of shape (len(texts), EMBEDDING_DIM)
    """
    model = get_model()
    # encode() converts every text into a vector. normalize_embeddings makes each
    # vector length 1, so comparing two vectors is a simple dot product.
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    # float32 uses half the memory of float64 and is what the vector index expects
    return np.array(embeddings, dtype=np.float32)


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string."""
    model = get_model()
    # Wrap the query in a list because encode() works on lists of texts
    embedding = model.encode(
        [query],
        normalize_embeddings=True,
    )
    # [0] picks the one vector out of the 1-row result
    return np.array(embedding, dtype=np.float32)[0]
