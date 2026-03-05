"""
QuickGuide — Text Chunker Tests
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.chunker import chunk_text


def test_chunk_text_basic():
    """Test basic text chunking produces results."""
    text = " ".join(f"word{i}" for i in range(100))
    chunks = chunk_text(1, text)
    assert len(chunks) > 0
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["chunk_index"] == 0
    assert len(chunks[0]["text_content"]) > 0


def test_chunk_text_empty():
    """Test empty text produces no chunks."""
    assert chunk_text(1, "") == []
    assert chunk_text(1, "   ") == []


def test_chunk_text_short():
    """Test short text produces one chunk."""
    text = "This is a short text."
    chunks = chunk_text(1, text)
    assert len(chunks) == 1
    assert chunks[0]["text_content"] == text


def test_chunk_text_overlap():
    """Test that chunks have overlap."""
    # Create text with exactly 600 words to ensure we get multiple chunks
    text = " ".join(f"word{i}" for i in range(600))
    chunks = chunk_text(1, text)
    assert len(chunks) >= 2

    # Check that chunks share some content (overlap)
    first_words = set(chunks[0]["text_content"].split())
    second_words = set(chunks[1]["text_content"].split())
    overlap = first_words & second_words
    assert len(overlap) > 0, "Chunks should have overlapping words"


def test_chunk_text_preserves_page_number():
    """Test that page number is preserved in all chunks."""
    text = " ".join(f"word{i}" for i in range(600))
    chunks = chunk_text(5, text)
    for chunk in chunks:
        assert chunk["page_number"] == 5


def test_chunk_text_sequential_index():
    """Test that chunk indices are sequential."""
    text = " ".join(f"word{i}" for i in range(600))
    chunks = chunk_text(1, text)
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == i
