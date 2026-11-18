# Program: Quick_Guide - chunker.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Splits one page of text into overlapping word-based chunks and records each chunk's character offsets in the original text.
"""
QuickGuide (QG) — Text Chunker Service
Splits extracted text into overlapping token-windowed chunks.
"""

from typing import List, Dict
from config import CHUNK_SIZE, CHUNK_OVERLAP  # chunk length and overlap, measured in words here


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
    # Nothing to do for empty or whitespace-only pages
    if not text or not text.strip():
        return []

    # split() with no argument breaks the text on any whitespace into words
    words = text.split()
    if not words:
        return []

    chunks = []        # the finished chunks will be collected here
    chunk_index = 0    # counts chunks within this page
    start = 0          # index of the first word in the current chunk

    # Keep making chunks until we run out of words
    while start < len(words):
        # The chunk ends CHUNK_SIZE words later, or at the last word, whichever comes first
        end = min(start + CHUNK_SIZE, len(words))
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)  # glue the words back into one string

        # Calculate character offsets in original text
        start_char = _find_word_offset(text, words, start)
        end_char = _find_word_offset(text, words, end - 1) + len(words[end - 1]) if end > 0 else len(text)

        # Save this chunk as a dictionary
        chunks.append({
            "page_number": page_number,
            "chunk_index": chunk_index,
            "text_content": chunk_text,
            "start_char": start_char,
            "end_char": end_char,
        })

        chunk_index += 1

        # Move forward by (chunk_size - overlap)
        # so neighbouring chunks share some words and sentences are not cut off cleanly.
        step = CHUNK_SIZE - CHUNK_OVERLAP
        if step <= 0:
            step = 1  # safety: always move forward at least one word
        start += step

        # Stop if we've already covered everything
        if end >= len(words):
            break

    return chunks


def _find_word_offset(text: str, words: list, word_index: int) -> int:
    """Find the character offset of the nth word in the original text."""
    # The first word always starts at the beginning
    if word_index <= 0:
        return 0

    # Walk past every earlier word, searching forward each time so repeated
    # words are matched in order rather than at their first occurrence.
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
