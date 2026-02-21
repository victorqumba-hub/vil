import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add current dir to path
sys.path.append(os.getcwd())
from app.config import settings

async def migrate():
    print(f"Connecting to: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        print("Adding missing columns to 'signals' table...")
        
        # Columns to add
        alter_statements = [
            "ALTER TABLE signals ADD COLUMN IF NOT EXISTS failure_category VARCHAR(50)",
            "ALTER TABLE signals ADD COLUMN IF NOT EXISTS score_at_expiration FLOAT",
            "ALTER TABLE signals ADD COLUMN IF NOT EXISTS regime_at_expiration VARCHAR(50)", # Simplified as string for migration if enum is tricky
            "ALTER TABLE signals ADD COLUMN IF NOT EXISTS signal_group_id UUID",
            "ALTER TABLE signals ADD COLUMN IF NOT EXISTS signal_version INTEGER DEFAULT 1",
            "ALTER TABLE signals ADD COLUMN IF NOT EXISTS decay_rate FLOAT",
            "ALTER TABLE signals ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP",
        ]
        
        for stmt in alter_statements:
            try:
                await conn.execute(text(stmt))
                print(f"Success: {stmt}")
            except Exception as e:
                print(f"Error executing {stmt}: {e}")
                
    print("Migration complete.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
