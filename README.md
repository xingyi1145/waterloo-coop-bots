# WaterlooWorks Junior Hunter

**WaterlooWorks Junior Hunter** is an automated bot designed to help University of Waterloo co-op students (specifically 1st and 2nd years) identify "junior-friendly" job postings on WaterlooWorks.

Instead of manually clicking through hundreds of postings to check the "Work Term Ratings" charts, this bot automates the navigation, extracts the hiring history data directly from the DOM, and filters for jobs that have a history of hiring junior students.

## Features

*   **Automated Navigation**: handling job list iteration and modal interactions using [Playwright](https://playwright.dev/).
*   **Smart Filtering**: Scrapes the "Hires by Student Work Term Number" chart.
*   **OCR-Free Extraction**: Uses direct DOM text extraction and Regex for 100% accuracy and speed (no flaky image recognition).
*   **Junior Focused**: Flags jobs where the sum of "First" and "Second" work term hires is greater than 10%.
*   **Result Persistence**: Saves promising leads to `friendly_jobs.txt`.
*   **Manual Login Hand-off**: Pauses to allow you to securely handle 2FA/Duo login manually.

## Prerequisites

*   Python 3.8+
*   A valid WaterlooWorks account.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/waterloo_coop_bot.git
    cd waterloo_coop_bot
    ```

2.  **Set up a virtual environment (optional but recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright browsers:**
    ```bash
    playwright install chromium
    ```

## Usage

1.  **Run the bot:**
    ```bash
    python3 main.py
    ```

2.  **Login Manually:**
    The browser will open and navigate to the WaterlooWorks login page.
    *   Enter your credentials.
    *   Complete the 2FA (Duo) challenge.
    *   Navigate to the **Job Search Results** page (where the table of jobs is listed) and don't forget to selet "My Program".

3.  **Start Automating:**
    Once you are on the search results page, press **ENTER** in the terminal console.

4.  **Watch it go:**
    The bot will iterate through the jobs, open modals, check the stats, and print results to the console.

5.  **Check Results:**
    Promising jobs are saved to `friendly_jobs.txt`.

## How It Works

1.  **Navigation**: The bot uses Playwright to click job links one by one.
2.  **Modal Handling**: It waits for the job detail modal to appear.
3.  **Tab Switching**: It clicks the "Work Term Ratings" tab.
4.  **Data Extraction**: Instead of taking screenshots, the bot grabs the raw text content from the modal. It looks for patterns like:
    *   `First: 10%`
    *   `1st Work Term: 15%`
5.  **Scoring**: It sums the percentages for 1st and 2nd work terms. If the score is > 10%, it's a match!
