import time
import random
import os
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- CONFIGURATION & IMPORTS ---
try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False
    print("⚠️ WARNING: PaddleOCR/PaddlePaddle not found.")
    print("   Please run: pip install paddlepaddle paddleocr")

# URL
LOGIN_URL = "https://waterlooworks.uwaterloo.ca/waterloo.htm"

# Selectors
JOB_LINK_SELECTOR = "tr a.overflow--ellipsis"
MODAL_SELECTOR = "div[role='dialog']"
# Loose matching strategy for tabs
WORK_TERM_RATINGS_TEXT = "Work Term Ratings" 
CHART_HEADER_TEXT = "Hires by Student Work Term Number"

# Close buttons (Robust list)
CLOSE_BUTTON_SELECTOR = "button[aria-label='Close'], .icon-cross, button:has-text('Close'), button:has-text('Cancel')"

# File to save results
RESULTS_FILE = "friendly_jobs.txt"
SCREENSHOT_DIR = "chart_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def initialize_ocr():
    """Initialize PaddleOCR if available."""
    if not PADDLE_AVAILABLE:
        return None
    print("🧠 Initializing PaddleOCR (this may take a moment)...")
    # Updated: use_textline_orientation instead of use_angle_cls, removed show_log
    return PaddleOCR(lang='en', use_textline_orientation=True)

def analyze_with_ocr(image_path, ocr_engine):
    """
    Analyzes the image using PaddleOCR to find 'First' and 'Second' term percentages.
    """
    if not ocr_engine:
        print("    ⚠️ OCR Engine not available. Returning 0.")
        return 0
    
    print(f"    🔍 Running OCR on {image_path}...")
    try:
        # PaddleOCR returns a list of result blocks
        # Changed: Removed cls arg entirely as it causes issues in this version
        result = ocr_engine.ocr(image_path)
    except Exception as e:
        print(f"    🔥 OCR Failed: {e}")
        return 0
    
    found_first = 0.0
    found_second = 0.0

    if not result or not result[0]:
        print("    ⚠️ No text detected in image.")
        return 0

    # Extract all text lines plain and simple
    lines = [line[1][0] for line in result[0]]
    print(f"    📝 Detected lines: {lines}")

    for i, text in enumerate(lines):
        text_lower = text.lower()
        
        # Keywords
        is_first = "first" in text_lower or "1st" in text_lower
        is_second = "second" in text_lower or "2nd" in text_lower
        
        if not (is_first or is_second):
            continue

        # Strategy 1: Look for number in the SAME line
        nums = re.findall(r"(\d+(?:\.\d+)?)", text)
        val = 0.0
        
        if nums:
            val = float(nums[-1])
        else:
            # Strategy 2: Look at the NEXT line (handling split labels like ["First:", "10%"])
            if i + 1 < len(lines):
                next_text = lines[i+1]
                next_nums = re.findall(r"(\d+(?:\.\d+)?)", next_text)
                if next_nums:
                    # Valid if it has a % or is a reasonable number
                    val = float(next_nums[0])

        if is_first:
            found_first = max(found_first, val)
            print(f"      => Parsed First: {val}%")
        elif is_second:
            found_second = max(found_second, val)
            print(f"      => Parsed Second: {val}%")

    total = found_first + found_second
    print(f"      > Total Junior Score: {total}%")
    return total

def random_sleep(min_seconds=1.0, max_seconds=2.5):
    """Sleep for a random amount of time to mimic human behavior."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def run_junior_hunter():
    print("🤖 The WaterlooWorks Junior Hunter is initializing (OCR Edition)...")
    
    # Setup OCR
    ocr_engine = initialize_ocr()

    # Clear previous results
    with open(RESULTS_FILE, "a") as f:
        f.write(f"\n--- Run Started: {time.ctime()} ---\n")

    with sync_playwright() as p:
        # Launch browser with slow_mo
        browser = p.chromium.launch(headless=False, slow_mo=50)
        
        context = browser.new_context(
            viewport={'width': 1600, 'height': 900},
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
            
            # Limit for testing
            limit = min(5, total_jobs)
            print(f"bot: Processing first {limit} jobs...")

            for i in range(limit):
                print(f"\n--- Processing Job {i+1} of {limit} ---")
                
                try:
                    # RE-QUERY to avoid StaleElementReferenceError
                    # We query the Nth element again fresh from the DOM
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

                        # Tab Switching: Loose match for "Work Term Ratings"
                        # get_by_text(..., exact=False) is robust for case sensitivity
                        ratings_tab = modal.get_by_text(WORK_TERM_RATINGS_TEXT, exact=False)
                        
                        # Wait for tab to be interactable
                        ratings_tab.wait_for(state="visible", timeout=3000)
                        ratings_tab.click()
                        random_sleep(0.8, 1.5)

                        # Chart Finding
                        # Find header text
                        header = modal.get_by_text(CHART_HEADER_TEXT, exact=False)
                        header.wait_for(state="visible", timeout=5000)
                        header.scroll_into_view_if_needed()
                        
                        # Wait for animation
                        time.sleep(1.0) 

                        # Screenshot of the Chart Element ONLY
                        try:
                            # Try to find the specific chart image/canvas inside the modal to avoid noise
                            # Typically the chart is in a container or is an svg/canvas
                            # We will try to find the container below the header
                            # Fallback to modal screenshot if element not found, but modal screenshot includes text we don't want
                            
                            # Heuristic: Locate the chart by searching for the container
                            # We avoid generic 'svg' to prevent capturing icons (like close buttons)
                            chart_locator = modal.locator(".highcharts-container, .chart-container, div[id*='chart'], canvas, img[src*='chart']").first
                            
                            if chart_locator.is_visible():
                                screenshot_path = os.path.join(SCREENSHOT_DIR, f"job_{i}.png")
                                chart_locator.screenshot(path=screenshot_path)
                            else:
                                # Fallback: screenshot the whole modal
                                screenshot_path = os.path.join(SCREENSHOT_DIR, f"job_{i}.png")
                                modal.screenshot(path=screenshot_path)
                        except:
                            screenshot_path = os.path.join(SCREENSHOT_DIR, f"job_{i}.png")
                            modal.screenshot(path=screenshot_path)
                        
                        # Local OCR Analysis
                        score = analyze_with_ocr(screenshot_path, ocr_engine)
                        
                        # Filter & Save
                        if score > 10:
                            print("    ✅ JUNIOR FRIENDLY! Saving...")
                            with open(RESULTS_FILE, "a") as f:
                                f.write(f"{job_title} | Score: {score}%\n")
                        else:
                            print(f"    ❌ Score too low ({score}%)")

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
                        # Try to find close button inside the modal/page
                        # Using .last to ensure we target the topmost dialog if multiple exist
                        close_btn = page.locator(CLOSE_BUTTON_SELECTOR).last
                        
                        if close_btn.is_visible():
                            close_btn.click()
                        else:
                            print("    ⚠️ Close button missing, using Escape.")
                            page.keyboard.press("Escape")
                        
                        # IMPORTANT: Wait for modal to hide before continuing!
                        # This prevents clicking the next link while the modal is still fading out
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
        
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    run_junior_hunter()
