import time
import random
import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- CONFIGURATION & SELECTORS ---
LOGIN_URL = "https://waterlooworks.uwaterloo.ca/waterloo.htm"

# Selectors
JOB_LINK_SELECTOR = "tr a.overflow--ellipsis"
MODAL_SELECTOR = "div[role='dialog']"
WORK_TERM_RATINGS_TAB = "text='Work Term Ratings'"
CHART_HEADER_TEXT = "text='Hires by Student Work Term Number'"

# Try multiple common close button patterns for WaterlooWorks/Orbis
CLOSE_BUTTON_SELECTOR = "button[aria-label='Close'], .icon-cross, button:has-text('Close'), button:has-text('Cancel')"

# File to save results
RESULTS_FILE = "friendly_jobs.txt"
SCREENSHOT_DIR = "chart_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def mock_ai_analyze(image_path):
    """
    Mock AI function. Returns a random percentage (0-50) representing
    historical junior hiring rate.
    """
    # Simulate processing time
    time.sleep(0.5)
    result = random.randint(0, 50)
    return result

def random_sleep(min_seconds=1.0, max_seconds=2.5):
    """Sleep for a random amount of time to mimic human behavior."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def run_junior_hunter():
    print("🤖 The WaterlooWorks Junior Hunter is initializing (Pop-Up Poker Mode)...")
    
    # Initialize/Clear results file
    with open(RESULTS_FILE, "w") as f:
        f.write("--- Junior Friendly Jobs ---\n")

    with sync_playwright() as p:
        # Launch browser with slow_mo
        browser = p.chromium.launch(headless=False, slow_mo=100)
        
        context = browser.new_context(
            viewport={'width': 1600, 'height': 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        page = context.new_page()

        # 1. Launch & Login Hand-off
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
            total_jobs_found = page.locator(JOB_LINK_SELECTOR).count()
            print(f"bot: Found {total_jobs_found} total jobs on page.")
            
            # Limit to first 5 for testing per requirements
            limit = min(5, total_jobs_found)
            print(f"bot: processing first {limit} jobs...")

            for i in range(limit):
                print(f"\n--- Processing Job {i+1} of {limit} ---")
                
                try:
                    # Re-acquire locators inside loop for safety
                    current_link = page.locator(JOB_LINK_SELECTOR).nth(i)
                    
                    # Log Job Title
                    try:
                        job_title = current_link.inner_text().strip()
                    except:
                        job_title = f"Job #{i+1}"
                    
                    print(f"    ➡️  Clicking: {job_title}")
                    
                    # CLICK to open Modal
                    current_link.click()
                    
                    # Wait for Modal
                    try:
                        page.wait_for_selector(MODAL_SELECTOR, state="visible", timeout=5000)
                        print("    📂 Modal opened.")
                    except PlaywrightTimeoutError:
                        print("    ⚠️ Modal did not appear. Skipping...")
                        continue

                    # Inside Modal: Navigate to Ratings
                    # Scope locators to the modal if possible, or page is fine if modal covers it
                    # Using modal_element.locator(...) is safer
                    modal = page.locator(MODAL_SELECTOR).last # Use last in case of nested dialogs
                    
                    ratings_tab = modal.locator(WORK_TERM_RATINGS_TAB)
                    
                    if ratings_tab.is_visible():
                        ratings_tab.click()
                        random_sleep(1, 1.5)
                        
                        # Find Chart
                        header = modal.locator(CHART_HEADER_TEXT)
                        
                        try:
                            header.wait_for(state="visible", timeout=5000)
                            header.scroll_into_view_if_needed()
                            random_sleep(0.5, 1) # Wait for animation
                            
                            # Screenshot
                            screenshot_path = os.path.join(SCREENSHOT_DIR, f"temp_job_{i}.png")
                            # We allow screenshotting the whole page as modals can be tricky to screenshot individually
                            page.screenshot(path=screenshot_path)
                            
                            # Mock Analysis
                            score = mock_ai_analyze(screenshot_path)
                            print(f"    📊 Analysis Score: {score}%")
                            
                            # Filter
                            if score > 10:
                                print(f"    ✅ JUNIOR FRIENDLY! Saving to {RESULTS_FILE}")
                                with open(RESULTS_FILE, "a") as f:
                                    f.write(f"{job_title} | Score: {score}%\n")
                            else:
                                print(f"    ❌ Not friendly (Score: {score}%)")
                                
                        except PlaywrightTimeoutError:
                            print("    ⚠️ Chart header not found in modal.")
                    else:
                        print("    ⚠️ 'Work Term Ratings' tab not found in modal.")

                except Exception as e:
                    print(f"    🔥 Error on Job {i+1}: {e}")
                
                finally:
                    # CRITICAL: Close Modal
                    print("    ✖️  Closing modal...")
                    
                    try:
                        # Try finding the close button
                        close_btn = page.locator(CLOSE_BUTTON_SELECTOR).last 
                        # Use .last because sometimes there are hidden ones
                        
                        if close_btn.is_visible():
                            close_btn.click()
                        else:
                            # Fallback: ESC key
                            print("    ⚠️ Close button not found, pressing ESC.")
                            page.keyboard.press("Escape")
                        
                        # Wait for modal to disappear
                        page.locator(MODAL_SELECTOR).wait_for(state="hidden", timeout=5000)
                        
                    except Exception as close_error:
                        print(f"    🔥 Failed to close modal cleanly: {close_error}")
                        # Last ditch effort to ensure we can proceed
                        page.keyboard.press("Escape")
                        random_sleep(1, 2)
                    
                    # Specific pause between jobs
                    random_sleep(1.0, 2.0)

        except Exception as main_e:
            print(f"\n🔥 Fatal Error: {main_e}")

        print("\n" + "="*60)
        print("🎉 Batch complete.")
        print(f"Check {RESULTS_FILE} for results.")
        print("="*60)
        
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    run_junior_hunter()
