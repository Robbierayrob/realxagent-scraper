import json
import logging
import os
from pathlib import Path
import httpx
from bs4 import BeautifulSoup

# Configure logging
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

async def scrape_leaderboard_page(page_num: int) -> list:
    """Scrape a single leaderboard page for subreddit names"""
    url = f"https://www.reddit.com/best/communities/{page_num}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Add more headers to look like a real browser
        headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
        
        # Add cookies to handle reddit's initial redirect
        cookies = {
            "reddit_session": "null",  # Placeholder for session
            "over18": "1"  # Bypass age gate
        }
        
        response = await client.get(url, headers=headers, cookies=cookies)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # Find all community divs with data-community-id
            subreddit_divs = soup.find_all("div", {"data-community-id": True})
            
            subreddits = []
            for div in subreddit_divs:
                # Extract the subreddit name from data-prefixed-name
                subreddit_name = div.get("data-prefixed-name", "")
                if subreddit_name:
                    subreddits.append(subreddit_name)
                    logging.info(f"Found subreddit: {subreddit_name}")
            
            return subreddits
        logging.warning(f"Failed to fetch page {page_num}: HTTP {response.status_code}")
        return []

async def scrape_all_leaderboards():
    """Scrape the first leaderboard page"""
    logging.info("Starting scraping of first leaderboard page")
    
    try:
        subreddits = await scrape_leaderboard_page(1)
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP error occurred: {str(e)}")
        logging.error(f"Response content: {e.response.text}")
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
