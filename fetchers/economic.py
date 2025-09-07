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