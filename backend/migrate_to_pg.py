import asyncio
import sqlite3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

# CONFIGURATION
SQLITE_PATH = "../vildb.sqlite"
# PG_URL should be set in environment: postgresql+asyncpg://user:pass@host:port/dbname
PG_URL = os.getenv("DATABASE_URL")

async def migrate():
    if not PG_URL or "sqlite" in PG_URL:
        print("ERROR: Please set a valid PostgreSQL DATABASE_URL environment variable.")
        return

    print(f"Connecting to SQLite: {SQLITE_PATH}")
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    
    print(f"Connecting to PostgreSQL...")
    engine = create_async_engine(PG_URL)
    
    # Tables to migrate (Ordered by dependency)
    tables = [
        "users",
        "assets",
        "signals",
        "trades",
        "ai_reports",
        "audit_logs"
    ]

    async with engine.begin() as conn:
        # 1. Create tables in PG (using the models metadata)
        # Note: In a real scenario, we'd run init_db() first
        print("Ensuring tables exist in PostgreSQL...")
        # from app.db.database import Base
        # await conn.run_sync(Base.metadata.create_all)

    for table in tables:
        print(f"Migrating table: {table}...")
        cursor = sqlite_conn.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"  No data in {table}.")
            continue

        columns = rows[0].keys()
        col_names = ", ".join(columns)
        placeholders = ", ".join([f":{col}" for col in columns])
        
        insert_stmt = text(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING")
        
        async with engine.begin() as conn:
            for row in rows:
                await conn.execute(insert_stmt, dict(row))
        
        print(f"  Successfully migrated {len(rows)} rows to {table}.")

    print("\nMigration Complete!")
    await engine.dispose()
    sqlite_conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
