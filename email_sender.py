# main.py
from fastapi import FastAPI
import asyncio

from fetchers.finance import fetch_financial_markets
from fetchers.news import fetch_news_sentiment
from fetchers.environment import fetch_environment
from fetchers.social import fetch_social
from fetchers.economic import fetch_economic

from ai_analysis import generate_report_with_ai

app = FastAPI()

@app.get("/daily-report")
async def daily_report():
    # Run fetchers concurrently
    finance, news, env, social, econ = await asyncio.gather(
        fetch_financial_markets(),
        fetch_news_sentiment(),
        fetch_environment(),
        fetch_social(),
        fetch_economic(),
        return_exceptions=False
    )

    # Build normalized input for scoring
    raw_data = {
        "financial_markets": finance or {},
        "news_sentiment": news or {},
        "natural_disaster_events": env.get("natural_disaster_events", []) if env else [],
        "social_media_posts": social.get("social_media_posts", []) if social else [],
        "economic_data": econ.get("economic_data", {}) if econ else {},
    }

    report = await generate_report_with_ai(raw_data)
    return report
