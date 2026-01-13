import time
import random
import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- CONFIGURATION & SELECTORS ---
# User: Update these selectors based on the actual WaterlooWorks DOM structure.
LOGIN_URL = "https://waterlooworks.uwaterloo.ca/waterloo.htm"
# Example placeholder selectors - REPLACE THESE with actual Inspect Element values
JOB_SEARCH_NAV_LINK = "text='Job Search' or text='Hire Waterloo Co-op'" # Adjust based on dashboard text
JOB_MINE_BUTTON = "text='Hire Waterloo Co-op'" # Usually you click into a specific module
SEARCH_RESULTS_TABLE_ROWS = "table.searchResults tr" # Simplified guess
JOB_LINK_SELECTOR = "a.job-title-link"  # Selector to click into a job from the list
HIRING_HISTORY_TAB = "text='Hiring History'" # Tab text
CHART_CANVAS_SELECTOR = "canvas" # or "img.chart" - selector for the specific chart element

# Output directory for screenshots
SCREENSHOT_DIR = "chart_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def analyze_chart(image_path):
    """
    Placeholder function to mimic Vision API analysis.
    Returns: dict with percentages for 'First' and 'Second' work terms.
    """
    print(f"    [Vision] Analyzing {image_path}...")
    # Simulation: Randomly generate percentages to test the logic
    # In production, this would call an API like OpenAI GPT-4o or Google Cloud Vision
    first_term = random.uniform(0, 40)
    second_term = random.uniform(0, 30)
    return {
        "First": first_term,
        "Second": second_term,
        "Total_Junior": first_term + second_term
    }

def random_sleep(min_seconds=1.5, max_seconds=4.0):
    """Sleep for a random amount of time to mimic human behavior."""
    time.sleep(random.uniform(min_seconds, max_seconds))

def run_junior_hunter():
    print("🤖 The WaterlooWorks Junior Hunter is initializing...")

    with sync_playwright() as p:
        # Launch browser with slow_mo to mimic human speed
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()

        # 1. Launch & Login Hand-off
        print(f"🚀 Navigating to {LOGIN_URL}")
        page.goto(LOGIN_URL)
        
        print("\n" + "="*60)
        print("🛑 ACTION REQUIRED: Please log in repeatedly manually.")
        print("   Complete 2FA (Duo Push) if requested.")
        print("   Navigate SPECIFICALLY to the 'Search Results' page where the list of jobs is visible.")
        input("👉 Press ENTER in this console once you are on the Job Search Results page...")
        print("="*60 + "\n")
        
        print("bot: Taking control...")

        # 2. Iterate through jobs
        # NOTE: In complex lists, it's safer to grab all URLs first if possible, 
        # or handle the "stale element" issue by querying index by index.
        # Here we will try to gather all job links first to avoid stale elements when going back.
        
        print("bot: Scanning for job links...")
        
        # User defined generic logic for finding job links. 
        # Ideally, look for specific table rows or card titles.
        # This is a generic robust locator strategy:
        try:
            # Wait for at least one job link to be visible to ensure page loaded
            # Adjust this selector to match the actual job title links
            # Generic guess: often <a> tags inside a table or list
            # Wait a bit for dynamic content
            page.wait_for_timeout(2000) 
            
            # Using a generic strategy for the user to refine: grab all 'a' tags that look like job titles
            # For now, we assume the user will provide a specific selector. 
            # We'll mock finding elements if the selector isn't real.
            
            # CRITICAL: Since we don't know the real selector, we ask the user to input/check it.
            # providing a generic "get all links" is dangerous.
            
            # Use specific locator (placeholder)
            job_links = page.locator(JOB_LINK_SELECTOR).all()
            
            # If no links found with specific selector, try a fallback for demo purposes
            if not job_links:
                print(f"⚠️  No jobs found with selector '{JOB_LINK_SELECTOR}'.")
                print("    (Please update the JOB_LINK_SELECTOR constant in the script)")
                # For safety, we stop here rather than clicking random things
                # return 
                
                # DEMO OVERRIDE: If this was a real run, we return. 
                # For now, let's pretend we found some for flow demonstration if scraping fails.
                pass 

            print(f"bot: Found {len(job_links)} potential jobs.")
            
            junior_friendly_jobs = []

            # We loop by index to handle re-querying if the DOM refreshes
            count = len(job_links)
            
            # Safety cap for testing
            if count == 0:
                 print("    (No jobs found to iterate. Check your selectors.)")
            
            for i in range(count):
                print(f"\n--- Processing Job {i+1}/{count} ---")
                
                # Re-query elements to avoid StaleElementReference errors (common in React/Angular apps)
                # We need to ensure we are on the results page.
                # Ideally, check for a "Results" element.
                
                current_job_links = page.locator(JOB_LINK_SELECTOR).all()
                if i >= len(current_job_links):
                    print("⚠️  Index out of bounds - list changed?")
                    break
                    
                job_element = current_job_links[i]
                
                # Get text for logging
                try:
                    job_title = job_element.inner_text().strip()
                except:
                    job_title = f"Job #{i+1}"
                
                print(f"bot: Clicking '{job_title}'...")
                
                try:
                    # 3. Inspect Job
                    # Ctrl+Click (new tab) is often safer than navigation for list handling,
                    # but "go back" mimics human behavior better for detection avoidance.
                    job_element.click()
                    
                    # Wait for job details to load
                    page.wait_for_load_state("domcontentloaded")
                    random_sleep(2, 4) # Reading time
                    
                    # 4. Find Hiring History
                    # Using get_by_role or text is robust
                    hiring_tab = page.get_by_text("Hiring History", exact=False)
                    
                    if hiring_tab.count() > 0 and hiring_tab.is_visible():
                        hiring_tab.click()
                        random_sleep(1, 2)
                        
                        # 5. Vision / Screenshot
                        # Locate the chart. 
                        # This might need a frame locator if it's in an iframe.
                        chart = page.locator(CHART_CANVAS_SELECTOR).first
                        
                        if chart.count() > 0:
                            screenshot_path = os.path.join(SCREENSHOT_DIR, f"job_{i}_{int(time.time())}.png")
                            chart.screenshot(path=screenshot_path)
                            print(f"    📸 Chart captured: {screenshot_path}")
                            
                            # 6. Analyze
                            data = analyze_chart(screenshot_path)
                            total_score = data["Total_Junior"]
                            print(f"    📊 Analysis: 1st={data['First']:.1f}%, 2nd={data['Second']:.1f}% (Total: {total_score:.1f}%)")
                            
                            # 7. Filter
                            if total_score > 30.0: # Threshold
                                print("    ✅ JUNIOR FRIENDLY! Adding to list.")
                                junior_friendly_jobs.append({
                                    "title": job_title,
                                    "score": total_score,
                                    "url": page.url
                                })
                            else:
                                print("    ❌ Not junior friendly.")
                        else:
                            print("    ⚠️  Could not find chart element (canvas/img).")
                    else:
                        print("    ⚠️  'Hiring History' tab not found.")

                except Exception as e:
                    print(f"    🔥 Error processing job: {e}")
                
                finally:
                    # 8. Return to list
                    # Go back to search results
                    print("bot: Returning to search results...")
                    page.go_back()
                    page.wait_for_load_state("domcontentloaded")
                    random_sleep(1, 2) # Wait before next action
            
            # Report
            print("\n" + "="*60)
            print("🎉 COMPLETED")
            print(f"Found {len(junior_friendly_jobs)} junior-friendly jobs:")
            for job in junior_friendly_jobs:
                print(f"- {job['title']} (Score: {job['score']:.1f}%)")
            print("="*60)

        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user.")
        except Exception as e:
            print(f"\n🔥 Fatal Error: {e}")

        # Keep browser open briefly to see results if needed
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    run_junior_hunter()
