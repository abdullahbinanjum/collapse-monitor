# generate_report_with_ai.py
import os
import json
import datetime
import asyncio
import logging
from typing import Optional
from data_fetcher import fetch_all_sources
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# -------------------------
# Logging
# -------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ai_analysis")

# -------------------------
# Configure Gemini/Generative Model
# -------------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

generation_config = {
    "temperature": 0.5,
    "max_output_tokens": 1000,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

try:
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
except Exception:
    model = None
    logger.warning("Could not initialize AI model; will use fallback.")

# -------------------------
# Deterministic Fallback
# -------------------------
def deterministic_top_drivers(data: list) -> list:
    drivers = []
    for d in data:
        if d["data_type"] == "news" and len(d["data"]) > 0:
            drivers.append(f"High news activity ({len(d['data'])} articles)")
        if d["data_type"] == "social" and len(d["data"]) > 0:
            drivers.append(f"High social media mentions ({len(d['data'])} posts)")
        if d["data_type"] == "environment" and len(d["data"]) > 0:
            drivers.append(f"Environmental events detected ({len(d['data'])})")
    while len(drivers) < 5:
        drivers.append("Other systemic indicators (see raw data)")
    return drivers[:5]

def deterministic_narrative(score: int, data: list) -> str:
    drivers = deterministic_top_drivers(data)
    return f"Automated fallback report: computed Stability Risk Score is {score}. Top drivers: {drivers[0]}; {drivers[1]}; {drivers[2]}. Fallback narrative generated because AI output failed or was invalid."

# -------------------------
# Email
# -------------------------
def send_report_via_email(report: dict, recipient_override: Optional[str] = None) -> Optional[str]:
    sender = os.getenv("EMAIL_SENDER_ADDRESS")
    password = os.getenv("EMAIL_APP_PASSWORD")
    recipient = recipient_override.strip() if recipient_override else os.getenv("EMAIL_RECIPIENT_ADDRESS")
    if not sender or not password or not recipient:
        logger.error("Email credentials or recipient missing.")
        return None

    try:
        subject = f"[Collapse Monitor] Daily Stability Risk Report - {report['timestamp'][:10]}"
        body = (
            f"Stability Risk Score: {report['risk_score']}\n\n"
            f"Narrative Summary:\n{report['narrative_summary']}\n\n"
            "Top Drivers:\n- " + "\n- ".join(report["top_drivers"])
        )

        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, [recipient], msg.as_string())
        logger.info(f"Report emailed to {recipient}")
        return recipient
    except Exception:
        logger.exception("Failed to send email")
        return None

# -------------------------
# Main Report Generation
# -------------------------
async def generate_report(recipient_override: Optional[str] = None) -> dict:
    timestamp = datetime.datetime.utcnow().isoformat()
    all_data = fetch_all_sources()

    # Compute a simple fallback risk score (average heuristic)
    risk_score = 50
    for d in all_data:
        if d["data_type"] == "news" and len(d["data"]) > 20:
            risk_score += 10
        if d["data_type"] == "social" and len(d["data"]) > 50:
            risk_score += 10
        if d["data_type"] == "environment" and len(d["data"]) > 0:
            risk_score += 10
    risk_score = min(100, risk_score)

    # Build AI prompt
    data_string = json.dumps(all_data, ensure_ascii=False)
    prompt = f"""
You are an AI analyst specialized in global instability signals.
Analyze the following raw data for today.
Output JSON ONLY with keys:
  1) risk_score (int, 0-100)
  2) top_drivers (array of 5 strings)
  3) narrative_summary (string, <=250 words)

Raw Data:
{data_string}

Instructions:
- Use specific mentions: e.g., Nasdaq volatility, tweet counts, environmental events.
- Make narrative concise and insightful.
- Highlight the 5 most impactful drivers in order.
- Output valid JSON only.
"""

    ai_error = None
    report_data = None

    if model:
        try:
            response = await model.generate_content_async(prompt)
            raw_output = getattr(response, "text", None) or str(response)
            # extract JSON part
            start = raw_output.find("{")
            end = raw_output.rfind("}") + 1
            json_part = raw_output[start:end] if start != -1 and end != -1 else "{}"
            report_data = json.loads(json_part)
        except Exception as e:
            ai_error = f"AI generation failed: {e}"
            logger.warning(ai_error)

    # Fallback if AI fails
    if not report_data or not isinstance(report_data, dict):
        report_data = {
            "risk_score": risk_score,
            "top_drivers": deterministic_top_drivers(all_data),
            "narrative_summary": deterministic_narrative(risk_score, all_data),
        }

    final_report = {
        "risk_score": report_data.get("risk_score", risk_score),
        "top_drivers": report_data.get("top_drivers")[:5],
        "narrative_summary": report_data.get("narrative_summary"),
        "timestamp": timestamp,
        "ai_error": ai_error,
    }

    sent_to = send_report_via_email(final_report, recipient_override)
    final_report["sent_to"] = sent_to

    # Save report locally
    os.makedirs("exports", exist_ok=True)
    with open(os.path.join("exports", "latest_report.json"), "w", encoding="utf-8") as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)

    return final_report

# -------------------------
# Run as script
# -------------------------
if __name__ == "__main__":
    import asyncio
    report = asyncio.run(generate_report())
    print(json.dumps(report, indent=2, ensure_ascii=False))
