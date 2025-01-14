import asyncio
from httpx import AsyncClient
from typing import Dict

client = AsyncClient(
    base_url="https://www.reddit.com",
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
)

async def get_subreddit_info(subreddit: str) -> Dict:
    """Get subreddit information using Reddit's JSON API"""
    # Reddit provides a .json version of any page
    response = await client.get(f"/r/{subreddit}/about.json")
    
    if response.status_code == 200:
        data = response.json()["data"]
        return {
            "id": data["display_name"],
            "description": data["public_description"],
            "members": data["subscribers"],
            "created_utc": data["created_utc"],
            "nsfw": data["over18"],
            "url": data["url"]
        }
    return {}

async def main():
    result = await get_subreddit_info("python")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())