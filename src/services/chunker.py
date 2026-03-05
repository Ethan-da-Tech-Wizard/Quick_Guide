"""
QuickGuide (QG) — Text Chunker Service
Splits extracted text into overlapping token-windowed chunks.
"""

from typing import List, Dict
from config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(page_number: int, text: str) -> List[Dict]:
    """
    Split page text into overlapping chunks.

    Args:
        page_number: 1-indexed page number
        text: Full text of the page

    Returns:
        List of chunk dicts with page_number, chunk_index, text_content,
        start_char, end_char
    """
    if not text or not text.strip():
        return []

    words = text.split()
    if not words:
        return []

    chunks = []
    chunk_index = 0
    start = 0

    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)

        # Calculate character offsets in original text
        start_char = _find_word_offset(text, words, start)
        end_char = _find_word_offset(text, words, end - 1) + len(words[end - 1]) if end > 0 else len(text)

        chunks.append({
            "page_number": page_number,
            "chunk_index": chunk_index,
            "text_content": chunk_text,
            "start_char": start_char,
            "end_char": end_char,
        })

        chunk_index += 1

        # Move forward by (chunk_size - overlap)
        step = CHUNK_SIZE - CHUNK_OVERLAP
        if step <= 0:
            step = 1
        start += step

        # Stop if we've already covered everything
        if end >= len(words):
            break

    return chunks


def _find_word_offset(text: str, words: list, word_index: int) -> int:
    """Find the character offset of the nth word in the original text."""
    if word_index <= 0:
        return 0

    offset = 0
    for i in range(min(word_index, len(words))):
        pos = text.find(words[i], offset)
        if pos >= 0:
            offset = pos + len(words[i])

    # Find the start of the target word
    if word_index < len(words):
        pos = text.find(words[word_index], offset)
        return pos if pos >= 0 else offset

    return offset
