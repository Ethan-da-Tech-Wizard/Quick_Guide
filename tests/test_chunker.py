# ==============================================================================
# Program: test_chunker.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Unit tests for QuickGuide text chunker service. Verifies token windowing,
#          empty text handling, single-chunk short strings, token overlap correctness,
#          preservation of page numbers, and sequential indexing.
# ==============================================================================

# sys/os are used only to extend the import path below.
import sys
import os

# The app uses flat imports (`from config import ...`), so src/ must be on sys.path
# for `services.chunker` to import. This must run before the import that follows.
# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Importing the module also imports config.py, which creates the data/ directories as
# a side effect; the chunker itself needs no model, database or network.
from services.chunker import chunk_text

# Pytest collects any function named test_*; the tests below are plain assertions.
def test_chunk_text_basic():
    """Test basic text chunking produces valid non-empty results."""
    # 100 words is far below CHUNK_SIZE (512), so the text fits in one window.
    text = " ".join(f"word{i}" for i in range(100))
    chunks = chunk_text(1, text)
    # Checks the contract of the returned dicts (page number and index of the first chunk).
    assert len(chunks) > 0
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["chunk_index"] == 0
    assert len(chunks[0]["text_content"]) > 0

# Both empty and whitespace-only input must return [] (chunker's early-exit branch).
def test_chunk_text_empty():
    """Test empty text produces no chunks."""
    assert chunk_text(1, "") == []
    assert chunk_text(1, "   ") == []

def test_chunk_text_short():
    """Test short text within token window produces exactly one chunk."""
    # Text shorter than one window produces a single chunk with the original words intact.
    text = "This is a short text."
    chunks = chunk_text(1, text)
    assert len(chunks) == 1
    assert chunks[0]["text_content"] == text

def test_chunk_text_overlap():
    """Test that consecutive chunks share overlapping words."""
    # Create text with 600 words to ensure multiple chunk boundaries
    # 600 words > CHUNK_SIZE (512), so a second window is required; with a 50-word overlap
    # the second chunk begins at word 462.
    text = " ".join(f"word{i}" for i in range(600))
    chunks = chunk_text(1, text)
    assert len(chunks) >= 2

    # Compare as word sets; the shared words are exactly the overlap region.
    # Check that chunks share some content (overlap)
    first_words = set(chunks[0]["text_content"].split())
    second_words = set(chunks[1]["text_content"].split())
    overlap = first_words & second_words
    assert len(overlap) > 0, "Chunks should have overlapping words"

def test_chunk_text_preserves_page_number():
    """Test that page number is preserved in all generated chunks."""
    # Uses page 5 (not the default 1) to prove the argument is propagated, not hard-coded.
    text = " ".join(f"word{i}" for i in range(600))
    chunks = chunk_text(5, text)
    for chunk in chunks:
        assert chunk["page_number"] == 5

def test_chunk_text_sequential_index():
    """Test that chunk indices are strictly sequential."""
    # Indexes must be 0,1,2,... in order, which the loop below verifies position by position.
    text = " ".join(f"word{i}" for i in range(600))
    chunks = chunk_text(1, text)
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == i
