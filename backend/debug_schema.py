import asyncio
from sqlalchemy import text
from app.db.database import async_session

async def debug_schema():
    async with async_session() as db:
        print("Checking users tables in different schemas...")
        res = await db.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name = 'users'"))
        for row in res.fetchall():
            print(f"Table: {row}")
            
        print("\nChecking role column in different schemas...")
        res = await db.execute(text("SELECT column_name, table_schema FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'role'"))
        for row in res.fetchall():
            print(f"Column: {row}")
            
        print("\nChecking all columns for users table in public schema...")
        res = await db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'users'"))
        cols = [row[0] for row in res.fetchall()]
        print(f"Columns in public.users: {cols}")

if __name__ == "__main__":
    asyncio.run(debug_schema())
