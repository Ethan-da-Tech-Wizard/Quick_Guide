# ==============================================================================
# Program: generate_test_pdf.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Generates a synthetic test PDF document using PyMuPDF (fitz).
#          Inserts sample technical specification text regarding compaction
#          thickness rules to facilitate end-to-end integration testing and
#          verification of semantic vector search queries.
# ==============================================================================

# fitz is PyMuPDF, the same library the app uses for text extraction. `os` is unused.
import fitz
import os

# Runs at import time (there is no main guard): executing this file writes test_doc.pdf
# into the current working directory, overwriting any existing file of that name.
# Step 1: Create a new in-memory PDF document
doc = fitz.open()

# A new page defaults to A4 size (595 x 842 points).
# Step 2: Allocate a new blank page
page = doc.new_page()

# insert_text takes the baseline origin in points from the top-left corner. The wording
# of these sentences matches the example search hint in the UI, so searching for
# "compaction thickness" should return page 1 of this file.
# Lines are 20 points apart, which leaves room for 12 pt text without overlap.
# Step 3: Insert sample test sentences at specified (x, y) coordinates
page.insert_text((50, 50), "This is a QuickGuide test document.", fontsize=12)
page.insert_text((50, 70), "To verify it works, we will query for compaction thickness rules.", fontsize=12)
page.insert_text((50, 90), "The compaction thickness rule states that layers must not exceed 6 inches.", fontsize=12)

# Step 4: Serialize and save the PDF file to disk
doc.save("test_doc.pdf")
doc.close()

print("Test PDF created successfully.")
