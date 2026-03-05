"""
QuickGuide (QG) — Embedding Service
Generates vector embeddings using sentence-transformers.
"""

import logging
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL, MODEL_DIR
import numpy as np

logger = logging.getLogger(__name__)

_model = None


def get_model() -> SentenceTransformer:
    """Load and cache the embedding model."""
    global _model
    if _model is None:
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
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return np.array(embeddings, dtype=np.float32)


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string."""
    model = get_model()
    embedding = model.encode(
        [query],
        normalize_embeddings=True,
    )
    return np.array(embedding, dtype=np.float32)[0]
