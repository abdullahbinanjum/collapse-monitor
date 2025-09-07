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