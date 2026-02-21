import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import select, update
from app.db.database import async_session
from app.db.models import Signal, Asset, LifecycleStatus, SignalDirection, SignalClassification

async def test_superseding():
    print("--- Testing Signal Superseding ---")
    async with async_session() as db:
        # 1. Ensure EUR_USD asset exists
        res = await db.execute(select(Asset).where(Asset.symbol == "EUR_USD"))
        asset = res.scalar_one_or_none()
        if not asset:
            from app.db.seed import seed_assets
            await seed_assets()
            res = await db.execute(select(Asset).where(Asset.symbol == "EUR_USD"))
            asset = res.scalar_one_or_none()

        # 2. Seed a PENDING signal
        old_signal = Signal(
            asset_id=asset.id,
            direction=SignalDirection.BUY,
            entry_price=1.1000,
            stop_loss=1.0900,
            take_profit=1.1200,
            score=75.0,
            status=LifecycleStatus.PENDING,
            timestamp=datetime.utcnow() - timedelta(hours=2)
        )
        db.add(old_signal)
        await db.commit()
        print(f"Seeded PENDING signal for {asset.symbol}")

        # 3. Simulate Orchestrator Superseding Logic
        target_symbols = ["EUR_USD", "GBP_USD"]
        print(f"Simulating scan for: {target_symbols}")
        
        stmt = (
            update(Signal)
            .where(Signal.status == LifecycleStatus.PENDING)
            .where(Signal.asset_id == Asset.id)
            .where(Asset.symbol.in_(target_symbols))
            .values(
                status=LifecycleStatus.DROPPED,
                notes="Superseded by fresh scan"
            )
        )
        await db.execute(stmt)
        await db.commit()
        print("Superseding logic applied.")

        # 4. Verify result
        await db.refresh(old_signal)
        print(f"Signal Status: {old_signal.status}")
        print(f"Signal Notes: {old_signal.notes}")

        if old_signal.status == LifecycleStatus.DROPPED:
            print(" SUCCESS: Old pending signal was correctly superseded.")
        else:
            print(" FAILURE: Old pending signal was not dropped.")

if __name__ == "__main__":
    asyncio.run(test_superseding())
