# streamlit_app.py
import streamlit as st
import requests
import json
import os
import datetime
import pandas as pd
from dotenv import load_dotenv

# Import the database function
from db_config import get_historical_reports

# Load environment variables
load_dotenv()

# Backend URL
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Collapse Monitor System",
    page_icon="🤖",
    layout="wide",
)

st.title("Collapse Monitor Dashboard")

# --- UI for Daily Report ---
st.header("Daily Risk Report")
st.write("This report provides an automated daily analysis of instability signals.")

# Email input field
email = st.text_input("Enter your email to receive the daily report:")

report = None  # Will store the latest report to display

if st.button("Generate and Email Report"):
    if not email:
        st.error("Please enter a valid email address.")
    else:
        with st.spinner("Generating and sending daily report..."):
            try:
                # Call the backend with email override
                response = requests.get(f"{BACKEND_URL}/daily-report", params={"recipient_email": email})
                response.raise_for_status()
                report = response.json()
                st.success(f"Report has been generated and sent to {email}!")
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to generate report: {e}")

# If no new report was generated, fetch the latest from backend for display
if report is None:
    try:
        response = requests.get(f"{BACKEND_URL}/daily-report")
        response.raise_for_status()
        report = response.json()
    except requests.exceptions.RequestException as e:
        st.warning(f"Could not fetch latest report: {e}")
        report = None

# Display the report if available
if report:
    risk_score = report.get("risk_score", 0)
    st.markdown(
        f"### Stability Risk Score: "
        f"**<span style='color: {'red' if risk_score > 70 else 'orange' if risk_score > 50 else 'green'};'>{risk_score}</span>**",
        unsafe_allow_html=True,
    )
    st.write(f"**Message:** {report.get('message', 'N/A')}")
    st.markdown("---")

    st.subheader("Narrative Summary")
    st.info(report.get("narrative_summary", "No summary available."))

    st.subheader("Top Drivers")
    top_drivers = report.get("top_drivers", [])
    if top_drivers:
        for idx, driver in enumerate(top_drivers, 1):
            st.write(f"{idx}. {driver}")
    else:
        st.write("Top drivers could not be retrieved from the AI analysis.")

# --- UI for Historical Data ---
st.header("Historical Data")
selected_date = st.date_input("Select a date to view a past report:", datetime.date.today())

st.subheader("Risk Score Trend Over Time")
historical_data = get_historical_reports()
if historical_data:
    df = pd.DataFrame(historical_data, columns=["Date", "Risk Score"])
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date")
    st.line_chart(df)
else:
    st.caption("This chart will dynamically update with historical data once connected to a database.")

# --- Project Overview ---
st.sidebar.title("Project Overview")
st.sidebar.markdown("""
    The Collapse Monitor System tracks early warning signals of potential economic, political, social, or environmental instability.
""")
st.sidebar.markdown("---")
st.sidebar.subheader("Project Details")
st.sidebar.markdown("""
* **Milestone:** Fully automated system collecting, analyzing, and reporting daily instability signals.
""")
