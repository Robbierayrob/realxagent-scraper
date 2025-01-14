import json
import logging
import os
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from tqdm import tqdm

# Configure logging and user agents
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)

def get_next_file_number(output_dir: str = "subreddits") -> int:
    """Get the next available file number in the output directory"""
    Path(output_dir).mkdir(exist_ok=True)
    existing_files = list(Path(output_dir).glob("subreddits_*.json"))
    return len(existing_files) + 1

def initialize_output_file(output_dir: str = "subreddits") -> Path:
    """Initialize the output file and return its path"""
    Path(output_dir).mkdir(exist_ok=True)
    filepath = Path(output_dir) / "subreddits.json"
    
    # Create empty file if it doesn't exist
    if not filepath.exists():
        with open(filepath, "w") as f:
            json.dump([], f)
    
    return filepath

def append_to_file(filepath: Path, new_subreddits: list):
    """Append new subreddits to the file while maintaining uniqueness"""
    try:
        # Read existing data
        with open(filepath, "r") as f:
            existing_data = json.load(f)
        
        # Combine and deduplicate
        combined = list(dict.fromkeys(existing_data + new_subreddits))
        
        # Write back to file
        with open(filepath, "w") as f:
            json.dump(combined, f, indent=2)
            
    except Exception as e:
        logging.error(f"Error updating file: {str(e)}")
        raise

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

async def scrape_leaderboard_page(page_num: int, total_pages: int = 1) -> list:
    """Scrape a single leaderboard page for subreddit names using Playwright"""
    url = f"https://www.reddit.com/best/communities/{page_num}/"
    start_time = time.time()
    
    async with async_playwright() as p:
        # Launch browser with random user agent
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        # Add realistic browser headers
        await context.set_extra_http_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        })
        
        page = await context.new_page()
        
        try:
            # Add conservative delay to avoid blocks
            await page.wait_for_timeout(random.randint(1500, 3000))
            
            # Show loading indicator while navigating
            print("\nLoading page...", end="", flush=True)
            
            # Navigate to page
            await page.goto(url, wait_until="networkidle")
            print("\rPage loaded successfully", flush=True)
            
            # Show loading indicator while waiting for content
            print("Loading community list...", end="", flush=True)
            
            # Wait for community list to load
            await page.wait_for_selector('div[data-community-id]', timeout=10000)
            print("\rCommunity list loaded successfully", flush=True)
            
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            
            # Find all community divs
            subreddit_divs = soup.find_all("div", {"data-community-id": True})
            
            subreddits = []
            total_items = len(subreddit_divs)
            
            # Initialize progress bar
            with tqdm(total=total_items, desc=f"Page {page_num}/{total_pages}", unit="sub") as pbar:
                for div in subreddit_divs:
                    subreddit_name = div.get("data-prefixed-name", "")
                    if subreddit_name:
                        subreddits.append(subreddit_name)
                        # Real-time terminal logging
                        print(f"\r\033[KFound: {subreddit_name}", end="", flush=True)
                        pbar.update(1)
                    
                    # Calculate ETA
                    elapsed_time = time.time() - start_time
                    items_processed = pbar.n
                    if items_processed > 0:
                        time_per_item = elapsed_time / items_processed
                        remaining_items = total_items - items_processed
                        eta = timedelta(seconds=int(remaining_items * time_per_item))
                        pbar.set_postfix(ETA=str(eta))
            
            return subreddits
            
        except Exception as e:
            logging.error(f"Error scraping page {page_num}: {str(e)}")
            return []
        finally:
            await browser.close()

async def scrape_all_leaderboards():
    """Scrape the first 50 leaderboard pages with incremental file updates"""
    logging.info("Starting scraping of first 50 leaderboard pages")
    total_pages = 50
    
    # Initialize output file
    output_file = initialize_output_file()
    
    try:
        for page_num in range(1, total_pages + 1):
            print(f"\nStarting scrape of page {page_num}...")
            subreddits = await scrape_leaderboard_page(page_num, total_pages)
            
            # Append results to file after each page
            if subreddits:
                append_to_file(output_file, subreddits)
                print(f"\nAdded {len(subreddits)} subreddits from page {page_num}")
            
            # Add more conservative delay between pages
            if page_num < total_pages:
                delay = random.uniform(3.0, 5.0)
                print(f"\nWaiting {delay:.1f} seconds before next page...")
                await asyncio.sleep(delay)
                
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        return
    
    # Final stats
    with open(output_file, "r") as f:
        final_data = json.load(f)
    
    logging.info(f"\nFound {len(final_data)} unique subreddits")
    logging.info(f"Saved to: {output_file}")

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(scrape_all_leaderboards())
    except Exception as e:
        logging.error(f"Error during scraping: {str(e)}")
