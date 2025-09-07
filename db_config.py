# db_config.py
import os
import json
from datetime import datetime

import psycopg  # psycopg v3
from psycopg.rows import dict_row
from psycopg.types.json import Json
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """
    psycopg v3 connection with dict_row so fetchone()/fetchall() return dicts.
    """
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        dbname=os.getenv("DB_NAME", "collapse_monitor"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password"),
        port=int(os.getenv("DB_PORT", "5432")),
        row_factory=dict_row,
    )


def setup_database():
    with get_db_connection() as conn, conn.cursor() as cur:
        # raw_data stores normalized JSON payloads from each source
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw_data (
                id SERIAL PRIMARY KEY,
                source_name TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                payload_json JSONB NOT NULL
            );
        """)

        # daily_reports matches the app’s report schema
        cur.execute("""
            CREATE TABLE IF NOT EXISTS daily_reports (
                id SERIAL PRIMARY KEY,
                report_date DATE NOT NULL,
                score INTEGER NOT NULL,
                drivers_json JSONB NOT NULL,
                narrative TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            );
        """)
        conn.commit()


def save_raw_data(source_name: str, data):
    """
    Save raw source payload; Json(...) ensures correct JSONB handling.
    """
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO raw_data (source_name, timestamp, payload_json)
            VALUES (%s, %s, %s)
            """,
            (source_name, datetime.utcnow(), Json(data)),
        )
        conn.commit()


def save_daily_report(report: dict):
    """
    Persist the daily AI report.
    Expects keys: risk_score (int), top_drivers (list/obj), narrative_summary (str)
    """
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO daily_reports (report_date, score, drivers_json, narrative, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                datetime.utcnow().date(),
                int(report["risk_score"]),
                Json(report["top_drivers"]),
                report["narrative_summary"],
                datetime.utcnow(),
            ),
        )
        conn.commit()


def get_latest_report():
    """
    Returns the most recent report as a dict (thanks to dict_row),
    or None if no rows exist.
    """
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM daily_reports ORDER BY report_date DESC LIMIT 1")
        row = cur.fetchone()  # already a dict
        return row or None


def get_historical_reports():
    """
    Returns (report_date, score) over time.
    If your downstream code expects tuples, use a plain cursor (no dict_row) here.
    """
    with get_db_connection() as conn, conn.cursor(row_factory=None) as cur:
        cur.execute("SELECT report_date, score FROM daily_reports ORDER BY report_date ASC")
        return cur.fetchall()  # list of tuples


if __name__ == "__main__":
    setup_database()
    print("Database tables created successfully!")
