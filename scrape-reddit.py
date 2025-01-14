import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List
from httpx import AsyncClient

client = AsyncClient(
    base_url="https://www.reddit.com",
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
)

def extract_related_subreddits(description: str) -> List[str]:
    """Extract related subreddits from description"""
    import re
    return list(set(re.findall(r"/r/\w+", description)))

async def get_subreddit_info(subreddit: str) -> Dict:
    """Get subreddit information using Reddit's JSON API"""
    response = await client.get(f"/r/{subreddit}/about.json")
    
    if response.status_code == 200:
        data = response.json()["data"]
        related_subs = extract_related_subreddits(data["description"])
        
        return {
            "id": data["display_name"],
            "title": data["title"],
            "description": data["public_description"],
            "members": data["subscribers"],
            "created_utc": data["created_utc"],
            "nsfw": data["over18"],
            "url": data["url"],
            "related_subreddits": related_subs
        }
    return {}

def save_to_json(data: Dict, output_dir: str = "output") -> str:
    """Save data to JSON file with unique numbering"""
    Path(output_dir).mkdir(exist_ok=True)
    
    # Find next available number
    existing_files = list(Path(output_dir).glob(f"{data['id']}_*.json"))
    next_num = len(existing_files) + 1
    filename = f"{data['id']}_{next_num:04d}.json"
    
    filepath = Path(output_dir) / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    
    return str(filepath)

def display_subreddit_info(info: Dict):
    """Display subreddit information in a readable format"""
    print("\n" + "="*50)
    print(f"Subreddit: r/{info['id']}")
    print(f"Title: {info['title']}")
    print(f"Description: {info['description']}")
    print(f"Members: {info['members']:,}")
    print(f"Created: {info['created_utc']}")
    print(f"NSFW: {'Yes' if info['nsfw'] else 'No'}")
    print(f"URL: {info['url']}")
    print("\nRelated Subreddits:")
    for sub in info['related_subreddits']:
        print(f" - {sub}")
    print("="*50 + "\n")

async def main():
    subreddit = input("Enter subreddit name to scrape (without r/): ").strip()
    result = await get_subreddit_info(subreddit)
    
    if result:
        display_subreddit_info(result)
        saved_path = save_to_json(result)
        print(f"Data saved to: {saved_path}")
    else:
        print(f"Failed to fetch data for r/{subreddit}")

if __name__ == "__main__":
    asyncio.run(main())
