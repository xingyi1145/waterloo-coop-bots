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

def scrape_job_description(modal: Locator) -> str:
    """
    Extracts the full text of the "Job Description" from the currently open modal.
    Logic:
      1. Switch to "Job Posting Information" tab inside the modal.
      2. Locate active tab pane.
      3. Fallback to full modal text if specific containers aren't found.
    """
    print("    📄 Scraping Job Description...")
    try:
        # 1. Verify/Click "Job Posting Information" tab
        # Use get_by_text for robustness (it might be a span, div, or a tag)
        info_tab = modal.locator(".nav-tabs").get_by_text("Job Posting Information", exact=False).first
        
        if info_tab.count() > 0 and info_tab.is_visible():
            # Check if it's likely active (checking parent or self for 'active')
            # This is heuristic; if checking fails, we just click.
            try:
                # Often the <li> is active, info_tab is the <a> or text inside
                parent_li = info_tab.locator("xpath=./ancestor::li").first
                class_attr = parent_li.get_attribute("class") or ""
                if "active" not in class_attr.lower():
                    print("      -> Switching to 'Job Posting Information' tab...")
                    info_tab.click()
                    pass
            except:
                # If structure is weird, just click the text
                info_tab.click()
        else:
            # It's possible we are already there or the tab UI is different. 
            # We don't abort, we just try to find content.
            pass

        # 2. Identify the content container
        # Try finding the tab-content container directly, often it wraps the panes
        # If we can't find a specific ".active" pane, we grab the whole tab-content
        content_locators = [
            ".tab-pane.active",          # Standard Bootstrap
            ".tab-content .active",      # Variation
            ".tab-content",              # Fallback to all tab content
            "div[id*='postingDiv']"      # Orbis specific often
        ]

        active_pane = None
        for sel in content_locators:
            loc = modal.locator(sel).first
            if loc.count() > 0 and loc.is_visible():
                active_pane = loc
                break
        
        if active_pane:
            text = active_pane.inner_text()
            # If text is very short, it might be the wrong container.
            if len(text) > 50:
                return text
        
        # 3. Fallback: If we verified duration exists, the text IS there.
        # It might not be in .tab-pane.active. 
        # We'll just grab the Main Content of the modal.
        print("      ⚠️ Standard tab structure not detected. Scraped full modal text (safe fallback).")
        full_text = modal.inner_text()
        
        return full_text

    except Exception as e:
        print(f"      ❌ Error during description scraping: {e}")
        # Last resort fallback
        try:
             return modal.inner_text()
        except:
             return ""
