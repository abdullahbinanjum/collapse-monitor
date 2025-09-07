# email_report.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_daily_email(report_data):
    """
    Sends the daily report via email.
    """
    # Email configuration
    sender_email = os.getenv("EMAIL_SENDER")
    receiver_email = os.getenv("EMAIL_RECEIVER")
    password = os.getenv("EMAIL_APP_PASSWORD")

    if not all([sender_email, receiver_email, password]):
        print("Error: Email credentials not found in .env file.")
        return

    # Create the email content
    subject = "Collapse Monitor Daily Report"
    
    # Format the email body
    body = f"""
    Daily Stability Report
    ----------------------
    
    Stability Risk Score: {report_data.get('risk_score', 'N/A')}
    
    Narrative Summary:
    {report_data.get('narrative_summary', 'N/A')}
    
    Top Drivers:
    {report_data.get('top_drivers', ['N/A'])}
    
    Report Generated At: {report_data.get('timestamp', 'N/A')}
    """

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    
    message.attach(MIMEText(body, "plain"))

    # Connect to the email server and send the email
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("Daily report email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        server.quit()