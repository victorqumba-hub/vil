
import asyncio
from sqlalchemy import select
from app.db.database import async_session
from app.db.models import User

async def verify_user():
    email = "demo@vil.io"
    print(f"Checking for user: {email}")
    async with async_session() as session:
        try:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                print(f"User FOUND: {user.email}, ID: {user.id}, Role: {user.role}")
            else:
                print("User NOT FOUND.")
        except Exception as e:
            print(f"Error querying user: {e}")

if __name__ == "__main__":
    asyncio.run(verify_user())
