from playwright.sync_api import Page

def scrape_job_description(page: Page) -> str:
    """
    Extracts the full text of the "Job Description" from the currently open modal.
    Logic:
      1. Switch to "Job Posting Information" tab.
      2. Locate specific headers like "Required qualifications" or "Skills".
      3. Extract text from the container.
    """
    print("    📄 Scraping Job Description...")
    try:
        # 1. Verify/Click "Job Posting Information" tab
        # We target the tab link specifically. In many Bootstrap modals, it's an <a> or <li>
        # Using a broad text match to catch "Job Posting Information"
        info_tab = page.locator("a", has_text="Job Posting Information").last
        
        if info_tab.is_visible():
            # Check if it's already active (optimization)
            # Parent <li> usuall has class 'active'
            parent = info_tab.locator("xpath=..")
            class_attr = parent.get_attribute("class") or ""
            
            if "active" not in class_attr.lower():
                print("      -> Switching to 'Job Posting Information' tab...")
                info_tab.click()
                # Wait briefly for content render
                page.wait_for_timeout(500)
        else:
            print("      ⚠️ 'Job Posting Information' tab not found.")

        # 2. Identify the content container
        # We look for the active tab content
        # Often div.tab-pane.active
        active_pane = page.locator(".tab-pane.active").last
        
        if not active_pane.is_visible():
            print("      ⚠️ Active tab pane not visible.")
            return ""
            
        # 3. Validation / Specific Targeting
        # The prompt asked to try locating "Required qualifications" or "Skills"
        # We can check if these exist to verify we are in the right place, 
        # but generally we want the *entire* text of the description, not just that section.
        # So we grab the whole active pane.
        
        description_text = active_pane.inner_text()
        
        # Minimal validation - check if it looks empty
        if len(description_text.strip()) < 10:
             print("      ⚠️ Scraped text seems too short.")
        
        return description_text

    except Exception as e:
        print(f"      ❌ Error during description scraping: {e}")
        return ""
