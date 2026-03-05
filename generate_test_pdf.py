import fitz
import os

doc = fitz.open()
page = doc.new_page()
page.insert_text((50, 50), "This is a QuickGuide test document.", fontsize=12)
page.insert_text((50, 70), "To verify it works, we will query for compaction thickness rules.", fontsize=12)
page.insert_text((50, 90), "The compaction thickness rule states that layers must not exceed 6 inches.", fontsize=12)

# Save to the static dir temporarily
doc.save("C:/Users/eman7/.gemini/antigravity/scratch/Quick_Guide/test_doc.pdf")
doc.close()
print("Test PDF created successfully.")
