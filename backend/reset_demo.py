import asyncio
from sqlalchemy import text
from app.db.database import async_session
from app.api.auth import _hash_password

async def reset_demo_user():
    async with async_session() as db:
        password_hash = _hash_password("DemoTrader@2026")
        await db.execute(text("""
            UPDATE users 
            SET password_hash = :hash, is_verified = True, is_active = True 
            WHERE email = 'demo@vil.io'
        """), {"hash": password_hash})
        await db.commit()
        print("Demo user reset successfully.")

if __name__ == "__main__":
    asyncio.run(reset_demo_user())
