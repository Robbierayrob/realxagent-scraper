import json
import logging
import os
import random
import time
from pathlib import Path
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

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

def save_subreddits(subreddits: list, output_dir: str = "subreddits"):
    """Save subreddits to JSON file with sequential numbering"""
    next_num = get_next_file_number(output_dir)
    filename = f"subreddits_{next_num:04d}.json"
    filepath = Path(output_dir) / filename
    
    with open(filepath, "w") as f:
        json.dump(subreddits, f, indent=2)
    
    return str(filepath)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

async def scrape_leaderboard_page(page_num: int) -> list:
    """Scrape a single leaderboard page for subreddit names using Playwright"""
    url = f"https://www.reddit.com/best/communities/{page_num}/"
    
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
            # Add random delay to mimic human behavior
            await page.wait_for_timeout(random.randint(1000, 3000))
            
            # Navigate to page
            await page.goto(url, wait_until="networkidle")
            
            # Wait for community list to load
            await page.wait_for_selector('div[data-community-id]', timeout=10000)
            
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            
            # Find all community divs
            subreddit_divs = soup.find_all("div", {"data-community-id": True})
            
            subreddits = []
            for div in subreddit_divs:
                subreddit_name = div.get("data-prefixed-name", "")
                if subreddit_name:
                    subreddits.append(subreddit_name)
                    logging.info(f"Found subreddit: {subreddit_name}")
            
            return subreddits
            
        except Exception as e:
            logging.error(f"Error scraping page {page_num}: {str(e)}")
            return []
        finally:
            await browser.close()

async def scrape_all_leaderboards():
    """Scrape the first leaderboard page"""
    logging.info("Starting scraping of first leaderboard page")
    
    try:
        subreddits = await scrape_leaderboard_page(1)
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        return
    
    # Remove duplicates while preserving order
    unique_subreddits = list(dict.fromkeys(subreddits))
    
    # Save the results
    saved_path = save_subreddits(unique_subreddits)
    logging.info(f"\nFound {len(unique_subreddits)} unique subreddits")
    logging.info(f"Saved to: {saved_path}")

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(scrape_all_leaderboards())
    except Exception as e:
        logging.error(f"Error during scraping: {str(e)}")
