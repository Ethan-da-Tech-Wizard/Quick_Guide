# Program: Quick_Guide - config.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Holds every shared setting (folders, server host/port, embedding model, chunk sizes, search and upload limits) and creates the data folders.
"""
QuickGuide (QG) — Application Configuration
"""

# ── Imports ──────────────────────────────────────
import os                 # os gives us access to environment variables
from pathlib import Path  # Path makes working with folder/file paths easy

# ── Folder locations ─────────────────────────────
# Base directory is the project root (one level up from src/)
# __file__ is this file; resolve() makes the path absolute; parent.parent climbs two levels.
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directories (the "/" operator joins path pieces together)
DATA_DIR = BASE_DIR / "data"            # top-level folder for everything the app stores
PDF_DIR = DATA_DIR / "pdfs"             # uploaded PDF files live here
VECTOR_DIR = DATA_DIR / "vectors"       # saved search indexes (one per document)
MODEL_DIR = DATA_DIR / "models"         # downloaded embedding model files are cached here
DB_PATH = DATA_DIR / "qg.db"            # the SQLite database file

# Ensure data directories exist
# parents=True builds missing parent folders; exist_ok=True means "no error if it already exists".
for d in [DATA_DIR, PDF_DIR, VECTOR_DIR, MODEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Server settings ──────────────────────────────
# os.getenv reads an environment variable, falling back to the default if it is not set.
HOST = os.getenv("QG_HOST", "127.0.0.1")
PORT = int(os.getenv("QG_PORT", "8080"))  # environment values are text, so int() converts to a number

# ── Embedding model ──────────────────────────────
# Embedding model (turns text into lists of numbers so meaning can be compared)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # how many numbers each embedding vector has

# ── Chunking settings ────────────────────────────
# Chunking settings
CHUNK_SIZE = 512      # tokens
CHUNK_OVERLAP = 50    # tokens

# ── Search settings ──────────────────────────────
# Search settings
TOP_K = 10             # default number of results to return
MIN_SIMILARITY = 0.30  # results scoring below this are thrown away

# ── Upload limits ────────────────────────────────
# Upload limits
MAX_FILE_SIZE_MB = 200  # biggest PDF we accept, in megabytes
MAX_PAGES = 2000        # most pages a PDF may have
