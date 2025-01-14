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

def get_next_output_filename(output_dir: str = "subreddits") -> Path:
    """Generate a unique output filename with timestamp and sequence number"""
    Path(output_dir).mkdir(exist_ok=True)
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Find the next available sequence number
    existing_files = list(Path(output_dir).glob(f"subreddits_{timestamp}_*.json"))
    next_num = len(existing_files) + 1
    
    # Format the filename
    filename = f"subreddits_{timestamp}_{next_num:06d}.json"
    return Path(output_dir) / filename

def append_to_file(filepath: Path, new_subreddits: list):
    """Append new subreddits to the file while maintaining uniqueness"""
    try:
        # Read existing data
        with open(filepath, "r") as f:
            existing_data = json.load(f)
        
        # Create a set of existing subreddit IDs for quick lookup
        existing_ids = {sub['id'] for sub in existing_data}
        
        # Add only new subreddits that aren't already in the file
        for sub in new_subreddits:
            if sub['id'] not in existing_ids:
                existing_data.append(sub)
                existing_ids.add(sub['id'])
        
        # Write back to file
        with open(filepath, "w") as f:
            json.dump(existing_data, f, indent=2)
            
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
            
            # Find all community divs and extract data in one pass
            subreddit_divs = soup.find_all("div", {"data-community-id": True})
            
            subreddits = []
            total_items = len(subreddit_divs)
            
            # Initialize progress bar
            with tqdm(total=total_items, desc=f"Page {page_num}/{total_pages}", unit="sub") as pbar:
                for div in subreddit_divs:
                    try:
                        # Extract all data attributes at once
                        data_attrs = div.attrs
                        
                        # Extract nested elements
                        rank_element = div.find("h6", class_="flex flex-col")
                        url_element = div.find("a", class_="text-current")
                        icon_element = div.find("faceplate-img")
                        
                        subreddit_data = {
                            "id": data_attrs.get("data-community-id", ""),
                            "name": data_attrs.get("data-prefixed-name", ""),
                            "active_users": int(data_attrs.get("data-active-count", 0)),
                            "icon_url": data_attrs.get("data-icon-url", ""),
                            "description": data_attrs.get("data-public-description-text", ""),
                            "subscribers": int(data_attrs.get("data-subscribers-count", 0)),
                            "metadata": {
                                "rank": rank_element.text.strip() if rank_element else "N/A",
                                "url": url_element["href"] if url_element else "N/A",
                                "icon": icon_element["src"] if icon_element else "N/A",
                                "scraped_at": datetime.now().isoformat()
                            }
                        }
                        
                        if subreddit_data["name"]:
                            subreddits.append(subreddit_data)
                            # Real-time terminal logging
                            print(f"\r\033[KFound: {subreddit_data['name']} ({subreddit_data['subscribers']} subs)", end="", flush=True)
                            pbar.update(1)
                    except Exception as e:
                        logging.error(f"Error parsing subreddit div: {str(e)}")
                        continue
                    
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

def show_menu() -> int:
    """Display interactive menu and return user's choice"""
    print("\nReddit Community Scraper")
    print("=" * 25)
    print("1. Scrape first 50 pages")
    print("2. Scrape first 250 pages")
    print("3. Scrape first 1000 pages")
    print("4. Exit")
    
    while True:
        try:
            choice = int(input("\nEnter your choice (1-4): "))
            if 1 <= choice <= 4:
                return choice
            print("Please enter a number between 1 and 4")
        except ValueError:
            print("Please enter a valid number")

async def scrape_all_leaderboards(total_pages: int):
    """Scrape leaderboard pages with incremental file updates"""
    logging.info(f"Starting scraping of first {total_pages} leaderboard pages")
    
    # Create new output file with timestamp and sequence number
    output_file = get_next_output_filename()
    # Initialize with empty list
    with open(output_file, "w") as f:
        json.dump([], f)
    
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
    
    # Map menu choices to page counts
    PAGE_OPTIONS = {
        1: 50,
        2: 250,
        3: 1000
    }
    
    while True:
        choice = show_menu()
        
        if choice == 4:
            print("\nGoodbye!")
            break
            
        total_pages = PAGE_OPTIONS[choice]
        print(f"\nStarting scrape of {total_pages} pages...")
        
        try:
            asyncio.run(scrape_all_leaderboards(total_pages))
        except Exception as e:
            logging.error(f"Error during scraping: {str(e)}")
        
        # Ask if user wants to continue
        cont = input("\nWould you like to scrape more? (y/n): ").lower()
        if cont != 'y':
            print("\nGoodbye!")
            break
