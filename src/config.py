# ==============================================================================
# Program: config.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Configuration module for QuickGuide application.
#          Defines project directory paths, data storage locations, server host/port
#          settings, embedding model parameters, chunking windows, and file upload
#          safety constraints.
# ==============================================================================

import os
from pathlib import Path

# Step 1: Resolve project root directory (one level above src/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Step 2: Establish paths for persistent storage and data artifacts
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
VECTOR_DIR = DATA_DIR / "vectors"
MODEL_DIR = DATA_DIR / "models"
DB_PATH = DATA_DIR / "qg.db"

# Step 3: Ensure all necessary data storage directories exist
for d in [DATA_DIR, PDF_DIR, VECTOR_DIR, MODEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Step 4: Network server binding parameters
HOST = os.getenv("QG_HOST", "127.0.0.1")
PORT = int(os.getenv("QG_PORT", "8080"))

# Step 5: Sentence transformer embedding model configurations
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Step 6: Text chunking sliding-window parameters
CHUNK_SIZE = 512      # Maximum token/word window size
CHUNK_OVERLAP = 50    # Overlap between consecutive chunks

# Step 7: Semantic vector search thresholds
TOP_K = 10
MIN_SIMILARITY = 0.30

# Step 8: Input validation and file upload limits
MAX_FILE_SIZE_MB = 200
MAX_PAGES = 2000
