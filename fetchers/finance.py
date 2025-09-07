# fetchers/finance.py
import os
import aiohttp

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

async def fetch_financial_markets():
    """
    Return dict like:
    {
      "sp500_change": "+0.4%",
      "nasdaq_volatility": "low"|"medium"|"high"
    }
    """
    try:
        # Example: call any finance API you use; this is a safe template
        async with aiohttp.ClientSession() as session:
            # Replace with your real endpoint(s)
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=SPY&apikey={ALPHA_VANTAGE_API_KEY}"
            async with session.get(url, timeout=25) as resp:
                if resp.status != 200:
                    return {}

                data = await resp.json()
                # Map from vendor fields -> your normalized fields
                # (Use a real calculation here)
                change = data.get("Global Quote", {}).get("10. change percent", "")
                return {
                    "sp500_change": change or "",
                    "nasdaq_volatility": "medium"  # stub: replace with real signal
                }
    except Exception as e:
        print(f"Error fetching financial markets: {e}")
        return {}
