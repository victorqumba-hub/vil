import asyncio
from sqlalchemy import text
from app.db.database import async_session

async def check_demo_user():
    async with async_session() as db:
        res = await db.execute(text("SELECT email, role, account_type, is_active, is_verified FROM users WHERE email = 'demo@vil.io'"))
        row = res.fetchone()
        if row:
            print(f"Demo User Found: {row}")
        else:
            print("Demo User NOT Found")

if __name__ == "__main__":
    asyncio.run(check_demo_user())
