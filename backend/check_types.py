import asyncio
from sqlalchemy import text
from app.db.database import async_session

async def check_types():
    async with async_session() as db:
        res = await db.execute(text("""
            SELECT t.typname, e.enumlabel 
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid 
            WHERE t.typname IN ('accounttype', 'userrole')
        """))
        for row in res.fetchall():
            print(row)

if __name__ == "__main__":
    asyncio.run(check_types())
