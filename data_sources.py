# data_sources.py
import os
import asyncpraw
import asyncio
import aiohttp
from datetime import datetime, timedelta
from dotenv import load_dotenv
from db_config import save_raw_data

load_dotenv()

# Initialize Reddit client (async)
reddit = asyncpraw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT", "CollapseRiskAnalysis/1.0"),
)


# ---------- Generic safe fetcher ----------
async def safe_get_json(url: str, params: dict = None) -> dict:
    """
    Helper: safely fetch JSON from a URL with aiohttp.
    Always returns a dict (never None).
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, ssl=False, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f"⚠️ Error {resp.status} fetching {url}")
                    return {}
    except Exception as e:
        print(f"⚠️ Exception fetching {url}: {e}")
        return {}


# ---------- Individual data sources ----------
async def get_social_data():
    """Fetch hot posts from r/collapse subreddit."""
    posts_data = []
    try:
        subreddit = await reddit.subreddit("collapse")
        async for submission in subreddit.hot(limit=50):
            posts_data.append({
                "title": submission.title,
                "score": submission.score,
                "num_comments": submission.num_comments,
            })
        # Save without await (sync call)
        save_raw_data("reddit", {"posts": posts_data})
        return {"social_media_posts": posts_data}
    except Exception as e:
        print(f"⚠️ Error fetching social data: {e}")
        return {"social_media_posts": []}


async def get_environmental_data():
    """Fetch natural disaster events from NASA EONET API."""
    NASA_API_KEY = os.getenv("NASA_API_KEY")
    start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

    url = "https://eonet.gsfc.nasa.gov/api/v2.1/events"
    params = {"api_key": NASA_API_KEY, "status": "open", "source": "usgs", "start": start_date}

    try:
        events = await safe_get_json(url, params)
        count = len(events.get("events", []))
        save_raw_data("nasa_eonet", {"events": count})
        return {"natural_disaster_events": count}
    except Exception as e:
        print(f"⚠️ Error fetching NASA data: {e}")
        return {"natural_disaster_events": 0}


async def get_economic_data():
    """Fetch economic overview data from Alpha Vantage API."""
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    url = "https://www.alphavantage.co/query"
    params = {"function": "OVERVIEW", "symbol": "IBM", "apikey": ALPHA_VANTAGE_API_KEY}

    try:
        data = await safe_get_json(url, params)
        save_raw_data("economic", data)
        return {"economic_data": data}
    except Exception as e:
        print(f"⚠️ Error fetching economic data: {e}")
        return {"economic_data": {}}


async def get_financial_markets():
    """Fetch or simulate major financial market data."""
    try:
        data = {"sp500_change": "+1.2%", "nasdaq_volatility": "high"}
        save_raw_data("financial_markets", data)
        return {"financial_markets": data}
    except Exception as e:
        print(f"⚠️ Error fetching financial markets: {e}")
        return {"financial_markets": {}}


async def get_news_sentiment():
    """Fetch or simulate aggregated news sentiment."""
    try:
        data = {"overall_sentiment": "negative", "keywords": ["supply chain", "recession"]}
        save_raw_data("news_sentiment", data)
        return {"news_sentiment": data}
    except Exception as e:
        print(f"⚠️ Error fetching news sentiment: {e}")
        return {"news_sentiment": {}}


# ---------- Master fetch orchestrator ----------
DATA_SOURCES = {
    "economic": get_economic_data,
    "social": get_social_data,
    "environmental": get_environmental_data,
    "financial_markets": get_financial_markets,
    "news_sentiment": get_news_sentiment,
}


async def fetch_all_data():
    """
    Asynchronously fetch data from all defined sources.
    Always returns a dict with keys for each source.
    """
    tasks = {name: func() for name, func in DATA_SOURCES.items()}
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    combined_data = {"timestamp": datetime.utcnow().isoformat()}

    for i, (name, _) in enumerate(tasks.items()):
        result = results[i]
        if isinstance(result, Exception):
            print(f"⚠️ Error in task {name}: {result}")
            combined_data[name] = {}
        else:
            combined_data.update(result)

    return combined_data
