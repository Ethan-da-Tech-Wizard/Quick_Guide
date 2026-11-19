# ==============================================================================
# Program: chunker.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Text chunking service for QuickGuide. Breaks full-page extracted text
#          into sliding-window token segments with configurable token overlap.
#          Tracks character offset boundaries (start_char, end_char) and 1-indexed
#          page numbers for accurate UI citation and navigation.
# ==============================================================================

# Only typing helpers and the two tuning constants are needed; CHUNK_SIZE and
# CHUNK_OVERLAP are measured in words (see config.py).
from typing import List, Dict
from config import CHUNK_SIZE, CHUNK_OVERLAP

# Public entry point, called once per page by the ingestion pipeline. Chunks never span
# multiple pages, so every chunk maps to exactly one page for citation in the UI.
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
    # Pages that are blank or only whitespace (e.g. scanned images with no text layer)
    # yield no chunks and therefore nothing to embed.
    # Step 1: Return empty list if input text is empty or whitespace
    if not text or not text.strip():
        return []

    # Splitting on whitespace discards the original spacing. chunk text is therefore
    # rejoined with single spaces, which is why start_char/end_char are computed separately
    # against the original string rather than from the joined text.
    # Step 2: Split text into whitespace-delimited words
    words = text.split()
    if not words:
        return []

    # chunk_index restarts at 0 for every page; start is the index of the first word
    # in the current window.
    chunks = []
    chunk_index = 0
    start = 0

    # Window loop: each pass emits words[start:end]. The final window may be shorter than
    # CHUNK_SIZE.
    # Step 3: Iterate through words using sliding window with overlap
    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))
        chunk_words = words[start:end]
        # Note: this local name shadows the enclosing function's name, which is harmless
        # because the function is not called recursively.
        chunk_text = " ".join(chunk_words)

        # Step 4: Calculate precise character offsets within original text
        # Character offsets let callers map a chunk back to its location in the page text.
        start_char = _find_word_offset(text, words, start)
        # end_char points just past the last word of the chunk.
        end_char = _find_word_offset(text, words, end - 1) + len(words[end - 1]) if end > 0 else len(text)

        chunks.append({
            "page_number": page_number,
            "chunk_index": chunk_index,
            "text_content": chunk_text,
            "start_char": start_char,
            "end_char": end_char,
        })

        chunk_index += 1

        # Advance by CHUNK_SIZE - CHUNK_OVERLAP so consecutive windows share CHUNK_OVERLAP words.
        # Step 5: Advance start pointer forward by (chunk_size - overlap)
        step = CHUNK_SIZE - CHUNK_OVERLAP
        # Defensive guard: if configuration made the overlap >= window size the step would be
        # zero or negative and the loop would never advance, so force progress of 1 word.
        if step <= 0:
            step = 1
        start += step

        # Stop once the window reached the last word; otherwise the overlap would produce a
        # trailing chunk that is a pure duplicate of the previous tail.
        # Step 6: Break loop if remaining words have been fully encompassed
        if end >= len(words):
            break

    return chunks

# Helper: locate the character index where word number `word_index` starts. It replays
# the whitespace split by searching for each preceding word in order, so repeated words
# are matched at the right occurrence. Cost grows with word_index (linear scan per call).
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
    # Word 0 is reported at offset 0, even if the text begins with whitespace.
    if word_index <= 0:
        return 0

    # Walk forward past every earlier word, keeping `offset` just after the last one found.
    offset = 0
    for i in range(min(word_index, len(words))):
        # find() with a start offset guarantees we move left to right through the text.
        pos = text.find(words[i], offset)
        # If a word is somehow not found, keep the old offset instead of failing.
        if pos >= 0:
            offset = pos + len(words[i])

    # Now search for the target word itself, starting after the previous word.
    # Locate start index of target word
    if word_index < len(words):
        pos = text.find(words[word_index], offset)
        return pos if pos >= 0 else offset

    return offset
