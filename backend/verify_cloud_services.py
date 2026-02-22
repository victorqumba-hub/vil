import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import redis.asyncio as redis

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

async def test_cloud_services():
    print(f"--- VERIFYING CLOUD SERVICES ---")
    
    # 1. Test Supabase (PostgreSQL)
    print(f"Testing Supabase Connection...")
    try:
        # Note: asyncpg requires the pooler in transaction mode to have statement_cache_size=0
        engine = create_async_engine(DATABASE_URL, connect_args={"statement_cache_size": 0})
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            result = await session.execute(text("SELECT email FROM users LIMIT 1"))
            user_email = result.scalar()
            print(f"  Supabase Success! Found user: {user_email}")
        await engine.dispose()
    except Exception as e:
        print(f"  Supabase Failure: {e}")

    # 2. Test Upstash (Redis)
    print(f"Testing Upstash Connection...")
    try:
        r = redis.from_url(REDIS_URL)
        await r.set("vil_test_key", "cloud_verified")
        val = await r.get("vil_test_key")
        print(f"  Upstash Success! Value: {val}")
        await r.close()
    except Exception as e:
        print(f"  Upstash Failure: {e}")

    print(f"--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(test_cloud_services())
