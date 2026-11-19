# ==============================================================================
# Program: debug_browser.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Headless browser automation test script utilizing Playwright.
#          Navigates to the local QuickGuide web UI, monitors console logs and
#          page errors, selects documents from the selector dropdown, and
#          validates client-side PDF rendering behavior.
# ==============================================================================

# Playwright is a developer-only dependency used for manual browser debugging; it is
# not needed to run the app or the unit tests. It must be installed separately along
# with a Chromium build (`playwright install chromium`).
from playwright.sync_api import sync_playwright

# Prerequisite: the QuickGuide server is already running on 127.0.0.1:8080 and at least
# one document has been uploaded (the script selects the first real option, index 1).
def run():
    """
    Spawns headless Chromium, attaches telemetry event listeners, and drives
    the QuickGuide web application interface.
    """
    # Step 1: Initialize Playwright context and launch browser in headless mode
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # headless=True: no visible window; swap to False when you want to watch the session.
        page = browser.new_page()
        
        # Step 2: Attach log forwarders for browser console outputs and uncaught page exceptions
        page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
        # Forwarding console and uncaught-error output is the main point of this script, since
        # PDF.js failures otherwise only appear in the browser developer tools.
        page.on("pageerror", lambda exc: print(f"Browser PageError: {exc}"))
        
        # Step 3: Navigate to local QuickGuide server endpoint
        print("Navigating to http://127.0.0.1:8080...")
        # The port is hard-coded to the default (config.PORT); change it if QG_PORT is set.
        page.goto("http://127.0.0.1:8080")
        
        # Step 4: Allow initial page assets and PDF.js to load
        # Fixed sleeps are crude but adequate for a debug aid; a robust test would wait on a
        # selector instead.
        page.wait_for_timeout(2000)
        
        # Step 5: Programmatically select document from dropdown menu
        print("Selecting document...")
        # index=0 is the "Select a document" placeholder option, so index=1 is the first
        # uploaded document. Selecting it fires the app's change handler and loads the PDF.
        page.select_option("#doc-select", index=1)
        
        # Step 6: Wait for canvas and text layer rendering cycle
        # Selecting a document triggers PDF.js rendering; the wait lets canvases and the text
        # layer finish so any errors are printed before the browser closes.
        page.wait_for_timeout(3000)
        
        # Step 7: Teardown browser instance
        browser.close()

if __name__ == "__main__":
    # Run directly with `python debug_browser.py`; run() is not called on import.
    run()
