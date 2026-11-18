# Program: Quick_Guide - generate_test_pdf.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Creates a small one-page PDF named test_doc.pdf containing a few sentences about compaction thickness, for trying out the search.
"""Create a tiny sample PDF with PyMuPDF for testing QuickGuide."""

import fitz  # PyMuPDF, the PDF library
import os

# Start a new empty PDF and add one blank page
doc = fitz.open()
page = doc.new_page()
# Write three lines of text; (x, y) is the position in points from the top-left
page.insert_text((50, 50), "This is a QuickGuide test document.", fontsize=12)
page.insert_text((50, 70), "To verify it works, we will query for compaction thickness rules.", fontsize=12)
page.insert_text((50, 90), "The compaction thickness rule states that layers must not exceed 6 inches.", fontsize=12)

# Save to the static dir temporarily
# (it actually saves in the current folder)
doc.save("test_doc.pdf")
doc.close()
print("Test PDF created successfully.")
