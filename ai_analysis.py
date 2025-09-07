# ai_analysis.py
import os
import re
import json
import datetime
import smtplib
import traceback
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import google.generativeai as genai
from dotenv import load_dotenv
import asyncio
import logging

# Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ai_analysis")

load_dotenv()  # load .env at import

# Configure Gemini/generative model
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

try:
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
except Exception:
    model = None
    logger.warning("Could not initialize generative model at import time. Calls will fallback.")

# -------------------------
# Helpers
# -------------------------
def calculate_risk_score(data: dict) -> int:
    score = 50
    fm = data.get("financial_markets") or {}
    if fm.get("nasdaq_volatility") == "high":
        score += 20
    if "+" in str(fm.get("sp500_change", "")):
        score -= 5

    nde = data.get("natural_disaster_events")
    if nde:
        try:
            count = len(nde) if hasattr(nde, "__len__") else int(nde)
        except Exception:
            count = 0
        if count > 5:
            score += 15

    sm = data.get("social_media_posts")
    if sm and len(sm) > 50:
        score += 10

    ns = data.get("news_sentiment") or {}
    sentiment = ns.get("overall_sentiment")
    if sentiment == "negative":
        score += 10
    elif sentiment == "positive":
        score -= 5

    return max(0, min(100, score))

def _extract_json_by_matching_braces(text: str) -> str:
    if not text:
        return "{}"
    start = text.find("{")
    if start == -1:
        return "{}"
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    m = re.search(r"\{.*\}", text, re.DOTALL)
    return m.group(0) if m else "{}"

def save_debug_output(name: str, text: str):
    try:
        os.makedirs("exports", exist_ok=True)
        with open(os.path.join("exports", name), "w", encoding="utf-8") as f:
            f.write(text or "")
        logger.info(f"Saved debug output to exports/{name}")
    except Exception:
        logger.exception("Failed to save debug output")

def deterministic_top_drivers(data: dict) -> list:
    drivers = []
    fm = data.get("financial_markets") or {}
    ns = data.get("news_sentiment") or {}
    sm = data.get("social_media_posts") or []
    nde = data.get("natural_disaster_events") or []

    if fm.get("nasdaq_volatility") == "high":
        drivers.append(f"High market volatility (nasdaq_volatility: {fm.get('nasdaq_volatility')})")
    if ns.get("overall_sentiment") == "negative":
        drivers.append("Negative news sentiment (economic / supply-chain concerns)")
    if sm:
        drivers.append(f"High social media activity ({len(sm)} posts mentioning collapse/risks)")
    if nde:
        drivers.append(f"Natural disaster events reported ({len(nde) if hasattr(nde,'__len__') else nde})")

    while len(drivers) < 5:
        drivers.append("Other systemic indicators (see raw data for details)")

    return drivers[:5]

def deterministic_narrative(risk_score: int, data: dict) -> str:
    drivers = deterministic_top_drivers(data)
    return (
        f"Automated fallback report: computed Stability Risk Score is {risk_score}. "
        f"Top drivers (heuristic): {drivers[0]}; {drivers[1]}; {drivers[2]}. "
        "This message was generated programmatically because the AI generation failed or returned malformed output."
    )

# -------------------------
# HTML Email Helper
# -------------------------
def create_html_email_content(report: dict) -> MIMEText:
    risk_score = report.get("risk_score", 0)
    narrative = report.get("narrative_summary", "No summary available.")
    top_drivers = report.get("top_drivers", [])

    score_color = "red" if risk_score > 70 else "orange" if risk_score > 50 else "green"

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height:1.5; color:#333;">
        <h2 style="color:#2E86C1;">🌍 Collapse Monitor — Daily Risk Report</h2>
        <p><strong>Stability Risk Score:</strong> 
           <span style="color:{score_color}; font-size:18px;">{risk_score}</span>
        </p>
        <h3>Narrative Summary:</h3>
        <p>{narrative}</p>
        <h3>Top Drivers:</h3>
        <ul>
    """
    for driver in top_drivers:
        html_content += f"<li>{driver}</li>\n"

    html_content += """
        </ul>
        <hr>
        <p style="font-size:12px; color:#666;">
            This report is automatically generated by the Collapse Monitor System.
        </p>
    </body>
    </html>
    """
    return MIMEText(html_content, "html")

def send_report_via_email(report: dict, recipient_override: Optional[str] = None) -> Optional[str]:
    load_dotenv(override=True)
    sender = os.getenv("EMAIL_SENDER_ADDRESS")
    password = os.getenv("EMAIL_APP_PASSWORD")
    recipient = recipient_override.strip() if recipient_override else os.getenv("EMAIL_RECIPIENT_ADDRESS")

    if not sender or not password or not recipient:
        logger.error("Email credentials or recipient not found in .env file.")
        return None

    logger.info(f"Sending report email to: {recipient}")

    try:
        subject = f"[Collapse Monitor] Daily Stability Risk Report - {report.get('timestamp','unknown')[:10]}"
        html_body = create_html_email_content(report)

        msg = MIMEMultipart("alternative")
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(html_body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, [recipient], msg.as_string())

        logger.info(f"✅ Report emailed successfully to {recipient}.")
        return recipient
    except Exception:
        logger.exception("Failed to send email")
        return None

# -------------------------
# Main: generate_report_with_ai
# -------------------------
async def generate_report_with_ai(data: dict, recipient_override: Optional[str] = None) -> dict:
    timestamp = datetime.datetime.now().isoformat()
    risk_score = calculate_risk_score(data)

    data_string = json.dumps(data, ensure_ascii=False)
    prompt = (
        "You are an AI assistant specialized in analyzing global instability signals.\n"
        "Analyze the following raw data and produce JSON ONLY, with keys: risk_score (int), "
        "top_drivers (array of strings), narrative_summary (string).\n\n"
        f"Raw Data:\n{data_string}\n\n"
        "Instructions:\n1) Provide the final risk_score (0-100).\n"
        "2) Write a concise narrative (2-4 sentences) referencing specific data points.\n"
        "3) Provide exactly 5 top_drivers ordered by impact. Output JSON only."
    )

    ai_error = None
    raw_ai_output = None
    report_data = None
    max_attempts = 2

    for attempt in range(1, max_attempts + 1):
        if model is None:
            ai_error = "Generative model not initialized"
            logger.warning(ai_error)
            break
        try:
            logger.info(f"Calling generative model (attempt {attempt}/{max_attempts})...")
            response = await model.generate_content_async(prompt)
            raw_ai_output = getattr(response, "text", None) or getattr(response, "output_text", None) or str(response)
            save_debug_output("latest_ai_output.txt", raw_ai_output)
            json_part = _extract_json_by_matching_braces(raw_ai_output)
            try:
                parsed = json.loads(json_part)
                if not isinstance(parsed, dict) or "risk_score" not in parsed:
                    raise ValueError("Parsed JSON missing required fields")
                report_data = parsed
                logger.info("AI output parsed successfully.")
                break
            except Exception as parse_exc:
                ai_error = f"JSON parse error: {parse_exc}"
                logger.warning(ai_error)
                save_debug_output("latest_ai_parse_error.txt", f"{ai_error}\n\nRaw output:\n{raw_ai_output}")
                if attempt < max_attempts:
                    await asyncio.sleep(1 * attempt)
                    continue
                else:
                    break
        except Exception as exc:
            ai_error = f"Model call failed: {exc}"
            logger.warning(ai_error)
            save_debug_output("latest_ai_exception.txt", f"{ai_error}\n\n{traceback.format_exc()}")
            if attempt < max_attempts:
                await asyncio.sleep(1 * attempt)
                continue
            else:
                break

    if report_data:
        risk = int(report_data.get("risk_score", risk_score))
        top = report_data.get("top_drivers") or []
        narrative = str(report_data.get("narrative_summary", "")).strip()
        final = {
            "risk_score": risk,
            "top_drivers": top[:5] if isinstance(top, list) else deterministic_top_drivers(data),
            "narrative_summary": narrative or deterministic_narrative(risk, data),
            "timestamp": timestamp,
            "ai_error": ai_error,
        }
        final["sent_to"] = send_report_via_email(final, recipient_override)
        try:
            os.makedirs("exports", exist_ok=True)
            with open(os.path.join("exports", "latest_report.json"), "w", encoding="utf-8") as f:
                json.dump(final, f, ensure_ascii=False, indent=2)
        except Exception:
            logger.exception("Failed to write latest_report.json")
        return final

    # Fallback
    fallback_report = {
        "risk_score": int(risk_score),
        "top_drivers": deterministic_top_drivers(data),
        "narrative_summary": deterministic_narrative(risk_score, data),
        "timestamp": timestamp,
        "ai_error": ai_error or "AI generation failed",
    }
    fallback_report["sent_to"] = send_report_via_email(fallback_report, recipient_override)
    try:
        os.makedirs("exports", exist_ok=True)
        with open(os.path.join("exports", "latest_report_fallback.json"), "w", encoding="utf-8") as f:
            json.dump(fallback_report, f, ensure_ascii=False, indent=2)
    except Exception:
        logger.exception("Failed to write latest_report_fallback.json")

    return fallback_report
