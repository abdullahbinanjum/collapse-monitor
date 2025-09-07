from fastapi import FastAPI, Query
from typing import Optional
from pydantic import BaseModel
from data_sources import fetch_all_data, reddit
from ai_analysis import generate_report_with_ai
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CollapseMonitor")

app = FastAPI()


class DailyReport(BaseModel):
    risk_score: int
    top_drivers: list[str]
    narrative_summary: str
    timestamp: str


@app.on_event("startup")
async def startup_event():
    """Triggered when the FastAPI app starts."""
    logger.info("🚀 Collapse Monitor System starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Triggered when the FastAPI app shuts down."""
    logger.info("🛑 Shutting down Collapse Monitor System...")
    # Properly close the Reddit client session
    try:
        await reddit.close()
        logger.info("✅ Reddit client session closed.")
    except Exception as e:
        logger.warning(f"⚠️ Error closing Reddit client: {e}")


@app.get("/")
async def root():
    return {"message": "Collapse Monitor System is running."}


@app.get("/daily-report", response_model=DailyReport)
async def get_daily_report(
    recipient_email: Optional[str] = Query(
        None,
        alias="recipient_email",
        description="Override recipient email for the report"
    )
):
    """
    Endpoint to generate the daily collapse risk report.
    - Fetches raw data from all configured sources
    - Analyzes data using AI
    - Sends the report via email (user-provided or .env fallback)
    - Returns the report as JSON
    """
    # 1. Fetch raw data from all sources
    raw_data = await fetch_all_data()

    # Log recipient override
    final_recipient = recipient_email or "default from .env"
    logger.info(f"Recipient override: {recipient_email}, using: {final_recipient}")

    # 2. Analyze data and generate report
    report_data = await generate_report_with_ai(
        raw_data,
        recipient_override=recipient_email
    )

    return report_data
