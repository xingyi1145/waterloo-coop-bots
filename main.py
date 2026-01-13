import time
import random
import os
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- CONFIGURATION ---
# URL
LOGIN_URL = "https://waterlooworks.uwaterloo.ca/waterloo.htm"

# Selectors
JOB_LINK_SELECTOR = "tr a.overflow--ellipsis"
MODAL_SELECTOR = "div[role='dialog']"
WORK_TERM_RATINGS_TEXT = "Work Term Ratings" 
CHART_HEADER_TEXT = "Hires by Student Work Term Number"

# Close buttons (Robust list)
CLOSE_BUTTON_SELECTOR = "button[aria-label='Close'], .icon-cross, button:has-text('Close'), button:has-text('Cancel')"

# File to save results
RESULTS_FILE = "friendly_jobs.txt"

def random_sleep(min_seconds=1.0, max_seconds=2.5):
    """Sleep for a random amount of time to mimic human behavior."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def parse_modal_text(text):
    """
    Parses the modal text to find 'First' and 'Second' term percentages.
    """
    print("    🔍 Scanning text for junior data...")
    
    # Normalize text
    text = text.replace('\n', ' ')
    
    # Regex patterns (flexible to catch 'First:', 'First Work Term:', etc.)
    # Looking for "First" ... number ... "%"
    # Matches: "First: 10%", "First work term: 10.5%"
    first_pattern = r"(?:First|1st).*?(\d+(?:\.\d+)?)%"
    second_pattern = r"(?:Second|2nd).*?(\d+(?:\.\d+)?)%"
    
    found_first = 0.0
    found_second = 0.0
    
    # Search
    first_match = re.search(first_pattern, text, re.IGNORECASE)
    second_match = re.search(second_pattern, text, re.IGNORECASE)
    
    if first_match:
        found_first = float(first_match.group(1))
        print(f"      => Parsed First: {found_first}%")
    
    if second_match:
        found_second = float(second_match.group(1))
        print(f"      => Parsed Second: {found_second}%")
        
    total = found_first + found_second
    print(f"      > Total Junior Score: {total}%")
    return total

def run_junior_hunter():
    print("🤖 The WaterlooWorks Junior Hunter is initializing (DOM Edition)...")
    
    # Clear previous results
    with open(RESULTS_FILE, "a") as f:
        f.write(f"\n--- Run Started: {time.ctime()} ---\n")

    with sync_playwright() as p:
        # Launch browser with slow_mo
        browser = p.chromium.launch(headless=False, slow_mo=50)
        
        # Standard context is enough for DOM scraping
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()

        # 1. Login Phase
        print(f"🚀 Navigating to {LOGIN_URL}")
        page.goto(LOGIN_URL)
        
        print("\n" + "="*60)
        print("🛑 ACTION REQUIRED: Please log in manually.")
        print("   1. Complete 2FA.")
        print("   2. Navigate to the 'Job Search' results page.")
        input("👉 Press ENTER in this console once you are on the Job Search Results page...")
        print("="*60 + "\n")
        
        print("bot: Taking control...")

        # 2. Main Loop
        try:
            # Wait for table to ensure we are ready
            page.wait_for_selector(JOB_LINK_SELECTOR, timeout=10000)
            
            # Count total jobs
            total_jobs = page.locator(JOB_LINK_SELECTOR).count()
            print(f"bot: Found {total_jobs} total jobs on page.")
            
            # Scan all jobs (loop limit = total_jobs)
            limit = total_jobs
            print(f"bot: Processing all {limit} jobs...")

            for i in range(limit):
                print(f"\n--- Processing Job {i+1} of {limit} ---")
                
                try:
                    # RE-QUERY to avoid StaleElementReferenceError
                    current_link = page.locator(JOB_LINK_SELECTOR).nth(i)
                    
                    try:
                        job_title = current_link.inner_text().strip()
                    except:
                        job_title = f"Job #{i+1}"
                    
                    print(f"    ➡️  Clicking: {job_title}")
                    
                    # Click to open Modal
                    current_link.click()
                    
                    # --- INSIDE MODAL ---
                    try:
                        # Wait specifically for the modal
                        page.wait_for_selector(MODAL_SELECTOR, state="visible", timeout=5000)
                        
                        # Scope to modal for precision
                        modal = page.locator(MODAL_SELECTOR).last
                        print("    📂 Modal opened.")

                        # Tab Switching
                        ratings_tab = modal.get_by_text(WORK_TERM_RATINGS_TEXT, exact=False)
                        ratings_tab.wait_for(state="visible", timeout=3000)
                        ratings_tab.click()
                        random_sleep(0.8, 1.5)

                        # Chart Finding
                        header = modal.get_by_text(CHART_HEADER_TEXT, exact=False)
                        header.wait_for(state="visible", timeout=5000)
                        header.scroll_into_view_if_needed()
                        
                        # Wait for Data in DOM
                        print("    ⏳ Waiting for chart text data...")
                        try:
                            # Wait for "First" or "1st" to confirm data loaded
                            # We use a try/except block to catch timeouts if the data doesn't appear
                            try:
                                modal.wait_for_selector("text=First", timeout=5000)
                            except:
                                # Fallback mostly for cases where "First" might be "1st" or slow
                                time.sleep(1.0)
                            
                            # Grab all text content from the modal
                            full_text = modal.inner_text()
                            
                            # Parse
                            score = parse_modal_text(full_text)
                            
                            # Save
                            if score > 10:
                                print("    ✅ JUNIOR FRIENDLY! Saving...")
                                with open(RESULTS_FILE, "a") as f:
                                    f.write(f"{job_title} | Score: {score}%\n")
                            else:
                                print(f"    ❌ Score too low ({score}%)")

                        except Exception as e:
                            print(f"    ⚠️ Failed to parse chart data: {e}")

                    except PlaywrightTimeoutError as pte:
                        print(f"    ⚠️ Timeout inside modal: {pte}")
                    except Exception as inner_e:
                        print(f"    ⚠️ Error inside modal logic: {inner_e}")

                except Exception as e:
                    print(f"    🔥 Error navigating to job {i+1}: {e}")

                finally:
                    # CLEANUP: Close Modal
                    print("    ✖️  Closing modal...")
                    try:
                        close_btn = page.locator(CLOSE_BUTTON_SELECTOR).last
                        if close_btn.is_visible():
                            close_btn.click()
                        else:
                            print("    ⚠️ Close button missing, using Escape.")
                            page.keyboard.press("Escape")
                        
                        page.locator(MODAL_SELECTOR).wait_for(state="hidden", timeout=5000)
                        
                    except Exception as close_e:
                        print(f"    🔥 Forced escape due to close error: {close_e}")
                        page.keyboard.press("Escape")
                        time.sleep(1)

                    random_sleep(1.0, 2.0)

        except Exception as main_e:
            print(f"\n🔥 Fatal Error: {main_e}")

        print("\n" + "="*60)
        print("🎉 Batch complete.")
        print("="*60)
        
        # Keep browser open until user is ready to close
        input("Press Enter to close the browser...")
        browser.close()

if __name__ == "__main__":
    run_junior_hunter()