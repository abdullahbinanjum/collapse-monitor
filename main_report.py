# main_report.py
import asyncio
import json
from data_fetcher import fetch_all_sources
from ai_analysis import generate_report_with_ai

CONFIG_FILE = "data_sources.json"

async def main():
    # Step 1: Fetch all live data
    all_data = fetch_all_sources(CONFIG_FILE)

    # Optional: Save raw fetch for audit/debug
    with open("exports/latest_raw_data.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    # Step 2: Aggregate data for AI analysis
    # Flatten or structure as needed by ai_analysis
    structured_data = {}
    for source in all_data:
        structured_data[source["source"]] = source["data"]

    # Step 3: Generate report with AI (includes fallback)
    report = await generate_report_with_ai(structured_data)

    # Step 4: Save report for audit
    with open("exports/latest_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("✅ Daily Collapse Monitor report generated and emailed (if configured).")
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
