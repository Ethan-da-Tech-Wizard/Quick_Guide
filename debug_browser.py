# ==============================================================================
# Program: debug_browser.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Headless browser automation test script utilizing Playwright.
#          Navigates to the local QuickGuide web UI, monitors console logs and
#          page errors, selects documents from the selector dropdown, and
#          validates client-side PDF rendering behavior.
# ==============================================================================

from playwright.sync_api import sync_playwright

def run():
    """
    Spawns headless Chromium, attaches telemetry event listeners, and drives
    the QuickGuide web application interface.
    """
    # Step 1: Initialize Playwright context and launch browser in headless mode
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Step 2: Attach log forwarders for browser console outputs and uncaught page exceptions
        page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"Browser PageError: {exc}"))
        
        # Step 3: Navigate to local QuickGuide server endpoint
        print("Navigating to http://127.0.0.1:8080...")
        page.goto("http://127.0.0.1:8080")
        
        # Step 4: Allow initial page assets and PDF.js to load
        page.wait_for_timeout(2000)
        
        # Step 5: Programmatically select document from dropdown menu
        print("Selecting document...")
        page.select_option("#doc-select", index=1)
        
        # Step 6: Wait for canvas and text layer rendering cycle
        page.wait_for_timeout(3000)
        
        # Step 7: Teardown browser instance
        browser.close()

if __name__ == "__main__":
    run()
