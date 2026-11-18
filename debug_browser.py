# Program: Quick_Guide - debug_browser.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Debug helper that opens the running app in a headless Chromium browser, selects the first document, and prints any browser console messages or page errors.
"""Debug script: drive the QuickGuide page with Playwright and print browser errors."""

# Playwright lets Python control a real browser
from playwright.sync_api import sync_playwright

def run():
    """Open the app, pick a document in the dropdown, and report console output."""
    # The "with" block starts Playwright and shuts it down cleanly afterwards
    with sync_playwright() as p:
        # Launch Chromium with no visible window (headless)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Listen for console events
        # Print anything the page writes to its console, and any uncaught JavaScript error
        page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"Browser PageError: {exc}"))
        
        print("Navigating to http://127.0.0.1:8080...")
        # The app must already be running on this address
        page.goto("http://127.0.0.1:8080")
        
        # Wait a bit
        # (milliseconds) give the page time to load its document list
        page.wait_for_timeout(2000)
        
        # Click the dropdown
        print("Selecting document...")
        # index=1 is the first real document (index 0 is the placeholder)
        page.select_option("#doc-select", index=1)
        
        # Wait for rendering attempt
        page.wait_for_timeout(3000)
        
        browser.close()

# Run only when started directly
if __name__ == "__main__":
    run()
