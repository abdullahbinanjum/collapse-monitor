# fetchers/news.py
import aiohttp

async def fetch_news_sentiment():
    try:
        async with aiohttp.ClientSession() as session:
            # Replace with your news API
            async with session.get("https://example.news/api", timeout=25) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json()
                # normalize
                return {
                    "overall_sentiment": "neutral",  # or "positive"/"negative"
                    "sample": data
                }
    except Exception as e:
        print(f"Error fetching news sentiment: {e}")
        return {}

# fetchers/environment.py
import os, aiohttp
NASA_API_KEY = os.getenv("NASA_API_KEY")

async def fetch_environment():
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
            async with session.get(url, timeout=25) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json()
                # normalize
                return {"natural_disaster_events": []}  # fill with your real feed
    except Exception as e:
        print(f"Error fetching NASA data: {e}")
        return {}

# fetchers/social.py
import aiohttp

async def fetch_social():
    try:
        async with aiohttp.ClientSession() as session:
            # your social source
            async with session.get("https://example.social/api", timeout=25) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json()
                posts = data.get("posts", [])
                return {"social_media_posts": posts[:100]}
    except Exception as e:
        print(f"Error fetching social data: {e}")
        return {}

# fetchers/economic.py
import aiohttp

async def fetch_economic():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://example.econ/api", timeout=25) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json()
                return {"economic_data": data}
    except Exception as e:
        print(f"Error fetching economic data: {e}")
        return {}
