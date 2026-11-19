# ==============================================================================
# Program: config.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Configuration module for QuickGuide application.
#          Defines project directory paths, data storage locations, server host/port
#          settings, embedding model parameters, chunking windows, and file upload
#          safety constraints.
# ==============================================================================

# os is needed for reading environment-variable overrides; Path for portable file paths.
import os
from pathlib import Path

# Step 1: Resolve project root directory (one level above src/)
# BASE_DIR is the repository root, so data lives next to the code regardless of the
# working directory the server is launched from.
BASE_DIR = Path(__file__).resolve().parent.parent

# Step 2: Establish paths for persistent storage and data artifacts
# Everything the app writes lives under data/: uploaded PDFs, one vector index per
# document, the cached transformer model, and the SQLite file.
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
VECTOR_DIR = DATA_DIR / "vectors"
MODEL_DIR = DATA_DIR / "models"
DB_PATH = DATA_DIR / "qg.db"

# Step 3: Ensure all necessary data storage directories exist
# Directories are created at import time (a side effect) so later code can assume they
# exist. exist_ok makes repeated imports harmless.
for d in [DATA_DIR, PDF_DIR, VECTOR_DIR, MODEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Step 4: Network server binding parameters
# Defaults to loopback only, so the server is not reachable from other machines unless
# the user explicitly sets QG_HOST. Both values can be overridden via the environment.
HOST = os.getenv("QG_HOST", "127.0.0.1")
PORT = int(os.getenv("QG_PORT", "8080"))

# Step 5: Sentence transformer embedding model configurations
# all-MiniLM-L6-v2 is a small, CPU-friendly model that outputs 384-dimensional vectors.
# EMBEDDING_DIM must match the model, because the vector index is built with this width.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Step 6: Text chunking sliding-window parameters
# Chunk sizes are counted in whitespace-delimited words (not model tokens), see
# services/chunker.py. A 512-word chunk can exceed the model's own input limit, in which
# case the encoder truncates the tail.
CHUNK_SIZE = 512      # Maximum token/word window size
# Overlap keeps sentences that straddle a chunk boundary findable from both chunks.
CHUNK_OVERLAP = 50    # Overlap between consecutive chunks

# Step 7: Semantic vector search thresholds
# TOP_K is the default result count. MIN_SIMILARITY is the cosine-similarity floor
# (vectors are normalized, so scores lie in [-1, 1]); weaker hits are dropped.
TOP_K = 10
MIN_SIMILARITY = 0.30

# Step 8: Input validation and file upload limits
# Upload guards: size is checked on the raw bytes, page count after opening the PDF.
# Both are enforced in services/documents.py.
MAX_FILE_SIZE_MB = 200
MAX_PAGES = 2000
