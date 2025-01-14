import json
import os
from pathlib import Path
import httpx
from bs4 import BeautifulSoup

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
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            subreddit_divs = soup.find_all("div", {"data-prefixed-name": True})
            return [div["data-prefixed-name"] for div in subreddit_divs]
        return []

async def scrape_all_leaderboards(max_pages: int = 10):
    """Scrape multiple leaderboard pages"""
    all_subreddits = []
    
    for page_num in range(1, max_pages + 1):
        print(f"Scraping page {page_num}...")
        subreddits = await scrape_leaderboard_page(page_num)
        all_subreddits.extend(subreddits)
    
    # Remove duplicates while preserving order
    unique_subreddits = list(dict.fromkeys(all_subreddits))
    
    # Save the results
    saved_path = save_subreddits(unique_subreddits)
    print(f"\nFound {len(unique_subreddits)} unique subreddits")
    print(f"Saved to: {saved_path}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(scrape_all_leaderboards())
