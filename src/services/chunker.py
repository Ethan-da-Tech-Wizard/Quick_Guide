# ==============================================================================
# Program: chunker.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Text chunking service for QuickGuide. Breaks full-page extracted text
#          into sliding-window token segments with configurable token overlap.
#          Tracks character offset boundaries (start_char, end_char) and 1-indexed
#          page numbers for accurate UI citation and navigation.
# ==============================================================================

from typing import List, Dict
from config import CHUNK_SIZE, CHUNK_OVERLAP

def chunk_text(page_number: int, text: str) -> List[Dict]:
    """
    Splits page text into overlapping token-windowed chunks.

    Args:
        page_number (int): 1-indexed page number of the source text.
        text (str): Full text extracted from the page.

    Returns:
        List[Dict]: List of chunk dictionaries containing page_number,
                    chunk_index, text_content, start_char, and end_char.
    """
    # Step 1: Return empty list if input text is empty or whitespace
    if not text or not text.strip():
        return []

    # Step 2: Split text into whitespace-delimited words
    words = text.split()
    if not words:
        return []

    chunks = []
    chunk_index = 0
    start = 0

    # Step 3: Iterate through words using sliding window with overlap
    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)

        # Step 4: Calculate precise character offsets within original text
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

        # Step 5: Advance start pointer forward by (chunk_size - overlap)
        step = CHUNK_SIZE - CHUNK_OVERLAP
        if step <= 0:
            step = 1
        start += step

        # Step 6: Break loop if remaining words have been fully encompassed
        if end >= len(words):
            break

    return chunks

def _find_word_offset(text: str, words: list, word_index: int) -> int:
    """
    Finds the exact character offset of the nth word in the raw source text.

    Args:
        text (str): Source text string.
        words (list): List of split words.
        word_index (int): Index of target word.

    Returns:
        int: Character offset in string.
    """
    if word_index <= 0:
        return 0

    offset = 0
    for i in range(min(word_index, len(words))):
        pos = text.find(words[i], offset)
        if pos >= 0:
            offset = pos + len(words[i])

    # Locate start index of target word
    if word_index < len(words):
        pos = text.find(words[word_index], offset)
        return pos if pos >= 0 else offset

    return offset
