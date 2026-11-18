# Program: Quick_Guide - test_chunker.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Pytest tests for chunk_text: basic output, empty input, short text, overlap between chunks, page number preservation and sequential chunk indexes.
"""
QuickGuide — Text Chunker Tests
"""

# Imports: sys and os let us adjust Python's module search path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# The function under test
from services.chunker import chunk_text


def test_chunk_text_basic():
    """Test basic text chunking produces results."""
    # Build 100 distinct fake words: word0 word1 ... word99
    text = " ".join(f"word{i}" for i in range(100))
    # Run the chunker on page 1
    chunks = chunk_text(1, text)
    # We expect at least one chunk, numbered from 0, on page 1, with real text
    assert len(chunks) > 0
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["chunk_index"] == 0
    assert len(chunks[0]["text_content"]) > 0


def test_chunk_text_empty():
    """Test empty text produces no chunks."""
    # Empty and whitespace-only text must give no chunks
    assert chunk_text(1, "") == []
    assert chunk_text(1, "   ") == []


def test_chunk_text_short():
    """Test short text produces one chunk."""
    # Text far below the chunk size should fit in exactly one chunk
    text = "This is a short text."
    chunks = chunk_text(1, text)
    # One chunk, and its text matches the input unchanged
    assert len(chunks) == 1
    assert chunks[0]["text_content"] == text


def test_chunk_text_overlap():
    """Test that chunks have overlap."""
    # Create text with exactly 600 words to ensure we get multiple chunks
    # 600 words is more than one chunk (chunks hold 512)
    text = " ".join(f"word{i}" for i in range(600))
    chunks = chunk_text(1, text)
    assert len(chunks) >= 2

    # Check that chunks share some content (overlap)
    # Compare the word sets of the first two chunks; any shared word proves they overlap
    first_words = set(chunks[0]["text_content"].split())
    second_words = set(chunks[1]["text_content"].split())
    # The & operator gives the words found in both sets
    overlap = first_words & second_words
    assert len(overlap) > 0, "Chunks should have overlapping words"


def test_chunk_text_preserves_page_number():
    """Test that page number is preserved in all chunks."""
    text = " ".join(f"word{i}" for i in range(600))
    # Use page 5 this time
    chunks = chunk_text(5, text)
    # Every chunk must remember page 5
    for chunk in chunks:
        assert chunk["page_number"] == 5


def test_chunk_text_sequential_index():
    """Test that chunk indices are sequential."""
    text = " ".join(f"word{i}" for i in range(600))
    chunks = chunk_text(1, text)
    # Chunk numbers must count 0, 1, 2 ... with no gaps
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == i
