import asyncio
import sys
import os
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Add current dir to path
sys.path.append(os.getcwd())
from app.config import settings
from app.db.models import Signal, Asset, LifecycleStatus

async def test():
    print(f"Testing DB connection to: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Test 1: Simple SELECT 1
            res = await session.execute(text("SELECT 1"))
            print(f"Test 1 (SELECT 1) result: {res.scalar()}")
            
            # Test 2: Select from assets
            res = await session.execute(select(Asset.id).limit(1))
            val = res.scalar()
            print(f"Test 2 (Select Asset) result: {val}")
            
            # Test 3: The problematic query
            target_symbols = ["EUR_USD", "GBP_USD", "USD_JPY"]
            subq = (
                select(Signal.id)
                .join(Asset)
                .where(Asset.symbol.in_(target_symbols))
                .where(Signal.status == LifecycleStatus.PENDING)
            )
            print("Executing problematic query...")
            res = await session.execute(subq)
            ids = [r[0] for r in res.all()]
            print(f"Test 3 (Problematic Query) result: {ids}")
            
        except Exception as e:
            print(f"Error during test: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await session.close()
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test())
