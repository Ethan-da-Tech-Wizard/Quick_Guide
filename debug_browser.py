from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Listen for console events
        page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"Browser PageError: {exc}"))
        
        print("Navigating to http://127.0.0.1:8080...")
        page.goto("http://127.0.0.1:8080")
        
        # Wait a bit
        page.wait_for_timeout(2000)
        
        # Click the dropdown
        print("Selecting document...")
        page.select_option("#doc-select", index=1)
        
        # Wait for rendering attempt
        page.wait_for_timeout(3000)
        
        browser.close()

if __name__ == "__main__":
    run()
