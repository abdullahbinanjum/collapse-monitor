import os
import json
import asyncpg

DB_HOST=os.getenv("DB_HOST")
DB_NAME=os.getenv("DB_NAME")
DB_USER=os.getenv("DB_USER")
DB_PASSWORD=os.getenv("DB_PASSWORD")
DB_PORT=int(os.getenv("DB_PORT", "5432"))

async def get_pool():
    return await asyncpg.create_pool(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME, min_size=1, max_size=5
    )

async def init_schema():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(open("storage/schema.sql","r",encoding="utf-8").read())
    await pool.close()

async def save_snapshot(source: str, payload: dict):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO raw_snapshots (source, payload) VALUES ($1, $2)",
            source, json.dumps(payload)
        )
    await pool.close()

async def save_report(report: dict):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO daily_reports (risk_score, top_drivers, narrative_summary)
            VALUES ($1, $2, $3)
            """,
            int(report.get("risk_score", 0)),
            json.dumps(report.get("top_drivers", [])),
            report.get("narrative_summary", "")
        )
    await pool.close()
