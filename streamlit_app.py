# streamlit_app.py
import os
import datetime
import json
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# DB helpers (for the trend chart)
from db_config import get_historical_reports

load_dotenv()

# --- Config ---
API_BASE = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="Collapse Monitor System", page_icon="🤖", layout="wide")
st.title("Collapse Monitor Dashboard")

# ------------ Helpers ------------
def api_get(path: str, params: dict | None = None, timeout: int = 60):
    url = f"{API_BASE}{path}"
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    # handle JSON or text
    try:
        return r.json()
    except Exception:
        return r.text

def fetch_latest_report():
    # read-only endpoint for display
    return api_get("/v1/report/latest", timeout=30)

def trigger_daily_report(recipient_email: str | None = None):
    # run a fresh daily cycle (fetch, analyze, email, store)
    params = {"recipient_email": recipient_email} if recipient_email else None
    return api_get("/daily-report", params=params, timeout=120)

# ------------ Daily Report UI ------------
st.header("Daily Risk Report")
st.write("This report provides an automated daily analysis of instability signals.")

email = st.text_input("Enter your email to receive the daily report:")

report = None

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Generate and Email Report"):
        if not email:
            st.error("Please enter a valid email address.")
        else:
            with st.spinner("Generating and emailing your daily report..."):
                try:
                    report = trigger_daily_report(email)
                    st.success(f"Report has been generated and sent to {email}!")
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to generate report: {e}")

with col2:
    if st.button("Refresh Latest Report"):
        with st.spinner("Fetching latest report..."):
            try:
                report = fetch_latest_report()
            except requests.exceptions.RequestException as e:
                st.warning(f"Could not fetch latest report: {e}")
                report = None

# On first load (no button pressed), try to show the latest report
if report is None:
    try:
        report = fetch_latest_report()
    except requests.exceptions.RequestException as e:
        st.warning(f"Could not fetch latest report: {e}")
        report = None

# ------------ Display Latest Report ------------
if report:
    risk_score = int(report.get("risk_score", 0))
    color = "red" if risk_score > 70 else ("orange" if risk_score > 50 else "green")
    st.markdown(
        f"### Stability Risk Score: **<span style='color:{color};'>{risk_score}</span>**",
        unsafe_allow_html=True,
    )
    if "message" in report:
        st.write(f"**Message:** {report.get('message')}")
    st.markdown("---")

    st.subheader("Narrative Summary")
    st.info(report.get("narrative_summary", "No summary available."))

    st.subheader("Top Drivers")
    top_drivers = report.get("top_drivers", [])
    if isinstance(top_drivers, list) and top_drivers:
        for i, d in enumerate(top_drivers, 1):
            st.write(f"{i}. {d}")
    else:
        st.write("Top drivers not available.")

# ------------ Historical Data ------------
st.header("Historical Data")
selected_date = st.date_input("Select a date to view a past report:", datetime.date.today())

st.subheader("Risk Score Trend Over Time")
historical_data = get_historical_reports()
if historical_data:
    df = pd.DataFrame(historical_data, columns=["Date", "Risk Score"])
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()
    st.line_chart(df)
else:
    st.caption("This chart will update once historical data is present in the database.")

# ------------ Sidebar ------------
st.sidebar.title("Project Overview")
st.sidebar.markdown("""
The Collapse Monitor System tracks early warning signals of potential economic, political, social, or environmental instability.
""")
st.sidebar.markdown("---")
st.sidebar.subheader("Project Details")
st.sidebar.markdown("""
* **Milestone:** Fully automated system collecting, analyzing, and reporting daily instability signals.
""")
