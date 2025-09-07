Collapse Monitor System

An AI-powered automation system that tracks global instability signals (finance, news, social, environment) and generates a daily collapse risk report.

The system:

Collects data from multiple live sources (Reddit, NASA, Alpha Vantage, RSS news, etc.).

Stores both raw data and daily summaries in PostgreSQL.

Uses LLM analysis (Gemini) to assign a Stability Risk Score (0–100), highlight the Top 5 Drivers, and write a narrative summary (≤250 words).

Sends the report via email and makes it available through an API + dashboard.

Fully automated with scheduling and containerized deployment.

Features

Daily automation → runs on a fixed schedule with no manual steps.

Multi-source ingestion → finance, sentiment, environment, social media, news.

Database-backed → raw + report tables for history and analytics.

AI analysis → GPT/Gemini model for scoring and narrative generation.

Alerts → optional email alerts if risk exceeds a threshold.

API access → JSON & CSV endpoints for latest and historical reports.

Dashboard → Streamlit app with charts and downloadable exports.

Containerized → Docker + docker-compose setup for easy deploys.

Project Structure
collapse-monitor/
├── ai_analysis.py         # AI report generation + email
├── data_sources.py        # Async data fetchers
├── db_config.py           # PostgreSQL storage helpers
├── main.py                # FastAPI backend
├── streamlit_app.py       # Dashboard
├── prompt.txt             # Editable LLM prompt template
├── requirements.txt       # Python dependencies
├── Dockerfile             # API container
├── docker-compose.yml     # API + DB + Dashboard stack
└── .env.example           # Example environment variables

Getting Started
1. Clone the repo
git clone https://github.com/<your-username>/collapse-monitor.git
cd collapse-monitor

2. Create .env

Copy .env.example → .env and fill in your keys:

DB_HOST=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_PORT=5432
NASA_API_KEY=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=CollapseRiskAnalysis/1.0
ALPHA_VANTAGE_API_KEY=...
GEMINI_API_KEY=...
EMAIL_SENDER_ADDRESS=...
EMAIL_APP_PASSWORD=...
EMAIL_RECIPIENT_ADDRESS=...
ALERT_THRESHOLD=75

3. Install dependencies (local run)
pip install -r requirements.txt

4. Run API
uvicorn main:app --reload


Visit http://localhost:8000
.

/ → health check

/daily-report → fetches data, runs AI, emails + saves report

/v1/report/latest → get last report

/v1/report/{date} → get report for a specific date (YYYY-MM-DD)

/v1/report/latest.csv → download as CSV

5. Run dashboard
streamlit run streamlit_app.py


Open http://localhost:8501
.

Deployment
Docker (recommended)
docker build -t collapse-api .
docker run --env-file .env -p 8000:8000 collapse-api

Docker Compose (API + DB + Dashboard)
docker compose up --build

Render / PaaS

Point to this repo.

Build command: pip install -r requirements.txt

Start command: uvicorn main:app --host 0.0.0.0 --port 8000

Set env vars in the Render dashboard.

Add a Render Cron Job:

curl -fsS "https://<your-service>.onrender.com/daily-report"


scheduled once per day.

Roadmap

 Replace simulated finance & sentiment with real feeds

 Add more environmental/social signals

 Add Slack/Discord alerting

 Add test coverage & CI/CD

License

MIT License — free to use, modify, and distribute.