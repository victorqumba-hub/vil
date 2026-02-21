import asyncio
import httpx
from datetime import datetime
import sys
import os

# Add the project root to sys.path so we can import app modules
sys.path.append(os.getcwd())

from app.db.database import async_session
from app.db.models import Signal, Asset, LifecycleStatus

BASE_URL = "http://localhost:8000/api"

async def verify():
    print("--- Institutional Sidebar Backend Verification ---")
    
    # 1. Login to get token
    async with httpx.AsyncClient() as client:
        print("Logging in...")
        try:
            resp = await client.post(f"{BASE_URL}/login", json={"email": "demo@vil.io", "password": "DemoTrader@2026"})
            if resp.status_code != 200:
                print(f"Login failed: {resp.text}")
                return
            token = resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
        except Exception as e:
            print(f"Connection failed: {e}")
            return

        # 2. Trigger Pipeline Run
        print("Triggering pipeline run...")
        try:
            resp = await client.post(f"{BASE_URL}/pipeline/run", headers=headers, json={}, timeout=60.0)
            if resp.status_code != 200:
                print(f"Pipeline run failed: {resp.text}")
                return
            
            signals_data = resp.json().get("signals", [])
            print(f"Generated {len(signals_data)} signals.")
        except Exception as e:
            print(f"Pipeline trigger error: {e}")
            return

    # 3. Verify DB Records
    async with async_session() as db:
        print("Checking database for enriched signals...")
        from sqlalchemy import select
        query = select(Signal).order_by(Signal.timestamp.desc()).limit(10)
        result = await db.execute(query)
        signals = result.scalars().all()

        if not signals:
            print("No signals found in DB.")
            return

        for s in signals:
            print(f"\nSignal ID: {s.id}")
            print(f"  Score: {s.score} (Delta: {s.score_delta})")
            print(f"  Classification: {s.classification}")
            print(f"  Status: {s.status}")
            print(f"  Composition: R:{s.regime_score}, S:{s.structure_score}, V:{s.volatility_score}, L:{s.liquidity_score}")
            
            # Basic validation
            if s.regime_score is None:
                print("  ❌ MISSING: Regime Score")
            if s.classification is None:
                print("  ❌ MISSING: Classification")
            
        # 4. Simulate Lifecycle Transition
        print("\nSimulating lifecycle transition...")
        test_sig = signals[0]
        test_sig.status = LifecycleStatus.ACTIVE
        await db.commit()
        print(f"Set signal {test_sig.id} to ACTIVE.")

        # Trigger lifecycle update (manually call manager)
        from app.services.lifecycle import lifecycle_manager
        updates = await lifecycle_manager.update_lifecycles(db)
        print(f"Lifecycle updates triggered: {len(updates)}")
        for u in updates:
            print(f"  Update: {u['symbol']} {u['old_status']} -> {u['new_status']}")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify())
