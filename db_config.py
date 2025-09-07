# db_config.py
import os
import psycopg2
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "collapse_monitor"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password")
    )
    return conn

def setup_database():
    conn = get_db_connection()
    cur = conn.cursor()

    # Create the raw_data table for flexible data storage
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_data (
            id SERIAL PRIMARY KEY,
            source_name TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            payload_json JSONB NOT NULL
        );
    """)

    # Corrected daily_reports table to match requirements
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
    cur.close()
    conn.close()

def save_raw_data(source_name, data):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO raw_data (source_name, timestamp, payload_json) VALUES (%s, %s, %s)",
        (source_name, datetime.utcnow(), json.dumps(data))
    )
    conn.commit()
    cur.close()
    conn.close()

def save_daily_report(report):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO daily_reports (report_date, score, drivers_json, narrative, created_at) VALUES (%s, %s, %s, %s, %s)",
        (datetime.utcnow().date(), report['risk_score'], json.dumps(report['top_drivers']), report['narrative_summary'], datetime.utcnow())
    )
    conn.commit()
    cur.close()
    conn.close()

def get_latest_report():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM daily_reports ORDER BY report_date DESC LIMIT 1")
    report = cur.fetchone()
    cur.close()
    conn.close()
    if report:
        # Convert row to dictionary
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, report))
    return None
    
def get_historical_reports():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT report_date, score FROM daily_reports ORDER BY report_date ASC")
    reports = cur.fetchall()
    cur.close()
    conn.close()
    return reports

if __name__ == "__main__":
    setup_database()
    print("Database tables created successfully!")