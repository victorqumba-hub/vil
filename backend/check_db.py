import asyncio
import os
import sys

# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.getcwd())

from app.db.database import async_session
from app.db.models import Signal, SignalFeatureSnapshot, Asset
from sqlalchemy import select

async def check():
    async with async_session() as s:
        # Get the latest signal with asset info
        res = await s.execute(
            select(Signal)
            .join(Asset)
            .order_by(Signal.timestamp.desc())
            .limit(1)
        )
        sig = res.scalar()
        if not sig:
            print("No signals found.")
            return

        print(f"--- Signal Forensic Check ---")
        print(f"Symbol: {sig.asset.symbol}")
        print(f"Score: {sig.score}")
        print(f"Version: {sig.signal_version}")
        print(f"Equity at Entry: {sig.equity_at_entry}")
        print(f"Risk Allocation: {sig.risk_allocation}")
        print(f"Engine Hash: {sig.engine_version_hash}")
        
        # Get the snapshot
        res2 = await s.execute(select(SignalFeatureSnapshot).where(SignalFeatureSnapshot.signal_id == sig.id))
        feat = res2.scalar()
        if feat:
            print(f"\n--- Technical Snapshot ---")
            print(f"EMA Fast: {feat.ema_fast}")
            print(f"EMA Slow: {feat.ema_slow}")
            print(f"VWAP: {feat.vwap}")
            print(f"RSI: {feat.rsi}")
            print(f"Volume Spike: {feat.volume_spike_flag}")
            print(f"Liquidity Status: {feat.liquidity_zone_status}")
        else:
            print("\nNo technical snapshot found for this signal.")

if __name__ == "__main__":
    asyncio.run(check())
