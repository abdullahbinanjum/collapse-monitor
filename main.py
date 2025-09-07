from fastapi import FastAPI, Query, Response, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import io, csv, json
import logging

from data_sources import fetch_all_data, reddit
from ai_analysis import generate_report_with_ai
from db_config import get_latest_report, get_db_connection  # psycopg v3 helpers

# ----- Logging -----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CollapseMonitor")

app = FastAPI()

# ----- CORS (allow the Streamlit dashboard) -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://collapse-monitor-dashboard.onrender.com",  # your Streamlit service URL
        "http://localhost:8501",                            # local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Models -----
class DailyReport(BaseModel):
    risk_score: int
    top_drivers: list[str]
    narrative_summary: str
    timestamp: str

# ----- Lifecycle -----
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Collapse Monitor System starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down Collapse Monitor System...")
    try:
        await reddit.close()
        logger.info("✅ Reddit client session closed.")
    except Exception as e:
        logger.warning(f"⚠️ Error closing Reddit client: {e}")

# ----- Health -----
@app.get("/")
async def root():
    return {"message": "Collapse Monitor System is running."}

@app.head("/")
async def root_head():
    return Response(status_code=200)

@app.get("/healthz")
async def healthz():
    return {"ok": True}

# ----- Write/Generate endpoint (kept as-is) -----
@app.get("/daily-report", response_model=DailyReport)
async def get_daily_report(
    recipient_email: Optional[str] = Query(
        None,
        alias="recipient_email",
        description="Override recipient email for the report"
    )
):
    """
    Generates the daily collapse risk report:
      1) fetch data
      2) analyze with AI
      3) (optionally) email
      4) return report JSON (and store in DB via your ai_analysis/db layer)
    """
    raw_data = await fetch_all_data()

    final_recipient = recipient_email or "default from .env"
    logger.info(f"Recipient override: {recipient_email}, using: {final_recipient}")

    report_data = await generate_report_with_ai(
        raw_data,
        recipient_override=recipient_email
    )
    return report_data

# ----- Read endpoints used by Streamlit -----
def _row_to_report(row: dict) -> dict:
    """
    Map a daily_reports DB row (dict) to API response.
    daily_reports schema: id, report_date, score, drivers_json, narrative, created_at
    """
    if not row:
        return None
    return {
        "date": row.get("report_date"),
        "risk_score": row.get("score"),
        "top_drivers": row.get("drivers_json"),
        "narrative_summary": row.get("narrative"),
        "created_at": row.get("created_at"),
        "message": "OK",
    }

@app.get("/v1/report/latest")
def get_report_latest():
    row = get_latest_report()
    if not row:
        raise HTTPException(status_code=404, detail="No report found")
    return _row_to_report(row)

@app.get("/v1/report/{date}")
def get_report_by_date(date: str):
    """
    Fetch report for a specific date (YYYY-MM-DD).
    """
    try:
        dt = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM-DD")

    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM daily_reports WHERE report_date = %s LIMIT 1",
            (dt,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No report on that date")
        return _row_to_report(row)

@app.get("/v1/report/latest.csv")
def get_report_latest_csv():
    row = get_latest_report()
    if not row:
        raise HTTPException(status_code=404, detail="No report found")

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["report_date", "score", "drivers_json", "narrative", "created_at"])
    writer.writerow([
        row.get("report_date"),
        row.get("score"),
        json.dumps(row.get("drivers_json")),
        row.get("narrative"),
        row.get("created_at"),
    ])
    return PlainTextResponse(content=buf.getvalue(), media_type="text/csv")
