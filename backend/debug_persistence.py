import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy import select, desc
from app.db.database import async_session
from app.db.models import Signal, Asset, LifecycleStatus

async def debug_persistence():
    print("--- VIL GLOBAL PERSISTENCE AUDIT ---")
    async with async_session() as session:
        # 1. Total Count
        res = await session.execute(select(Signal))
        total = len(res.scalars().all())
        print(f"Total signals in DB: {total}")

        # 2. Recent Signals (Last 1 Hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        query = select(Signal).where(Signal.timestamp >= one_hour_ago).order_by(desc(Signal.timestamp))
        res = await session.execute(query)
        recent = res.scalars().all()
        print(f"Recent signals (last 1h): {len(recent)}")

        for s in recent:
            print(f" - ID: {str(s.id)[:8]}... | Status: {s.status} | Score: {s.score} | Created: {s.timestamp}")

        # 3. Simulate /api/signals/live Logic
        print("\nSimulating /api/signals/live query...")
        live_query = (
            select(Signal)
            .where(Signal.status.in_([LifecycleStatus.PENDING, LifecycleStatus.ACTIVE, LifecycleStatus.QUEUED]))
        )
        res = await session.execute(live_query)
        live_sigs = res.scalars().all()
        print(f"Signals that would show up in /live: {len(live_sigs)}")
        for s in live_sigs:
             print(f" - ID: {str(s.id)[:8]}... | Status: {s.status}")

        # 4. Check for dropped/expired signals that should have been live
        dropped_query = (
            select(Signal)
            .where(Signal.status.in_([LifecycleStatus.DROPPED, LifecycleStatus.EXPIRED]))
            .where(Signal.timestamp >= one_hour_ago)
        )
        res = await session.execute(dropped_query)
        dropped = res.scalars().all()
        print(f"\nDropped/Expired in last hour: {len(dropped)}")
        for s in dropped:
            print(f" - ID: {str(s.id)[:8]}... | Status: {s.status} | Notes: {s.notes}")

if __name__ == "__main__":
    asyncio.run(debug_persistence())
