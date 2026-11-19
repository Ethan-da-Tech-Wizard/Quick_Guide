# ==============================================================================
# Program: embedder.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Embedding service for QuickGuide using SentenceTransformers.
#          Loads and caches the all-MiniLM-L6-v2 transformer model, encodes
#          text chunks into normalized 384-dimensional dense vectors, and
#          provides batch encoding as well as single-query inference.
# ==============================================================================

# sentence_transformers pulls in torch, so importing this module is slow; the model
# itself is not loaded until the first call to get_model().
import logging
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL, MODEL_DIR
import numpy as np

logger = logging.getLogger(__name__)

# Cached singleton: loading the transformer takes seconds and hundreds of MB, so it is
# done at most once per process.
# Cached singleton model instance
_model = None

def get_model() -> SentenceTransformer:
    """
    Retrieves or lazily instantiates the SentenceTransformer model.
    Caches model weights within the configured model storage directory.
    
    Returns:
        SentenceTransformer: Active sentence encoder instance.
    """
    # Module-level cache; no lock is used, so two threads racing on the very first call
    # could both load the model (wasteful but not incorrect).
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}...")
        # cache_folder keeps downloaded weights under data/models so they are reused on later
        # runs. The first run needs network access to fetch them; afterwards it works offline.
        _model = SentenceTransformer(
            EMBEDDING_MODEL,
            cache_folder=str(MODEL_DIR)
        )
        logger.info("Embedding model loaded successfully.")
    return _model

def embed_texts(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """
    Generates normalized dense vector embeddings for a list of text strings.

    Args:
        texts (list[str]): Text strings to encode.
        batch_size (int): Mini-batch size for transformer forward pass.

    Returns:
        np.ndarray: Matrix of shape (len(texts), EMBEDDING_DIM) as float32.
    """
    # Called for document chunks. Input order is preserved in the output rows.
    # Step 1: Ensure model is loaded
    model = get_model()

    # normalize_embeddings=True makes every vector unit length, so an inner product between
    # two vectors equals their cosine similarity (relied on by vector_store).
    # Step 2: Encode texts with L2 normalization enabled
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    # float32 is the dtype FAISS requires.
    return np.array(embeddings, dtype=np.float32)

def embed_query(query: str) -> np.ndarray:
    """
    Encodes a single natural language search query into a normalized vector.

    Args:
        query (str): Natural language search query string.

    Returns:
        np.ndarray: Vector of shape (EMBEDDING_DIM,) as float32.
    """
    # Used for search queries. The query is wrapped in a list because encode() works on
    # batches; the [0] below unwraps the single row.
    # Step 1: Ensure model is loaded
    model = get_model()

    # Step 2: Encode single query text
    embedding = model.encode(
        [query],
        normalize_embeddings=True,
    # Same normalization as documents so query/document scores are comparable.
    )
    return np.array(embedding, dtype=np.float32)[0]
