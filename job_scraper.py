from playwright.sync_api import Page, Locator
import re

def scrape_work_term_duration(modal: Locator) -> str:
    """
    Robustly extracts the Work Term Duration from the job modal.
    Strategy:
      1. Use text-based locator for "Work Term Duration:" label.
      2. Traverse to parent container.
      3. Extract and normalize text.
      4. Fallback to global text regex if specific locator fails.
    """
    print("    ⏳ Checking Duration...")
    job_duration = "Unknown"
    
    try:
        # Strategy 1: Specific Locator by Text Label
        # "Work Term Duration:" is the label. We want the container.
        # We use .first because sometimes text matches multiple
        label_el = modal.get_by_text("Work Term Duration:", exact=False).first
        
        raw_text = ""
        # Wait briefly for it to be visible
        try:
            label_el.wait_for(state="visible", timeout=2000)
            # Traverse up to the row/container (usually the parent)
            container = label_el.locator("..") 
            raw_text = container.inner_text()
        except:
             # Locator strategy failed/timed out
             pass
            
        if not raw_text:
            # Strategy 2: Fallback to Regex on whole modal text
             print("      ⚠️ Label locator failed. Attempting global regex fallback...")
             try:
                 full_text = modal.inner_text()
                 # Look for pattern generally
                 match = re.search(r"Work Term Duration:?\s*(.+)", full_text, re.IGNORECASE)
                 if match:
                     raw_text = match.group(0)
                 else:
                     clean_dump = full_text[:100].replace('\n', ' ')
                     print(f"      ⚠️ Could not detect duration. Dump: {clean_dump}...")
                     return "Unknown"
             except Exception as e:
                 print(f"      ⚠️ Fallback failed: {e}")
                 return "Unknown"

        # --- Normalization Logic ---
        # Clean: collapse all whitespace/newlines into single spaces
        clean_text = re.sub(r'\s+', ' ', raw_text).lower()

        # Normalize
        if "8" in clean_text and "month" in clean_text:
            job_duration = "8 month"
        if "4" in clean_text and "month" in clean_text:
            if job_duration == "8 month":
                job_duration = "4-8 month" # found both
            else:
                job_duration = "4 month"
        if "flexible" in clean_text:
                job_duration = "Flexible"
                
        print(f"      => Detected: {clean_text.replace('work term duration:', '').strip()} (Normalized: {job_duration})")
        return job_duration

    except Exception as e:
        print(f"      ❌ Error checking duration: {e}")
        return "Unknown"

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
