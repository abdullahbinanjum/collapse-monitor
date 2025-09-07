CREATE TABLE IF NOT EXISTS daily_reports (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  risk_score INT NOT NULL,
  top_drivers JSONB NOT NULL,
  narrative_summary TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_snapshots (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  source TEXT NOT NULL,
  payload JSONB NOT NULL
);