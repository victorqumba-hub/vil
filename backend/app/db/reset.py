import asyncio
from app.db.database import engine, Base
# Import models to ensure they are registered with Base
from app.db import models

async def reset():
    print("Resetting database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("Dropped all tables.")
        await conn.run_sync(Base.metadata.create_all)
        print("Created all tables.")

if __name__ == "__main__":
    asyncio.run(reset())
