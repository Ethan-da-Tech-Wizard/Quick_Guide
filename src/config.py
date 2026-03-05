"""
QuickGuide (QG) — Application Configuration
"""

import os
from pathlib import Path

# Base directory is the project root (one level up from src/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
VECTOR_DIR = DATA_DIR / "vectors"
MODEL_DIR = DATA_DIR / "models"
DB_PATH = DATA_DIR / "qg.db"

# Ensure data directories exist
for d in [DATA_DIR, PDF_DIR, VECTOR_DIR, MODEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Server settings
HOST = os.getenv("QG_HOST", "127.0.0.1")
PORT = int(os.getenv("QG_PORT", "8080"))

# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Chunking settings
CHUNK_SIZE = 512      # tokens
CHUNK_OVERLAP = 50    # tokens

# Search settings
TOP_K = 10
MIN_SIMILARITY = 0.30

# Upload limits
MAX_FILE_SIZE_MB = 200
MAX_PAGES = 2000
