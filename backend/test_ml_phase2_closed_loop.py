import asyncio
import httpx
import json
from uuid import UUID
from sqlalchemy import select
from app.db.database import async_session
from app.db.models import Signal, Asset, MLSignalDataset, LifecycleStatus, MarketRegime, SignalDirection

async def test_phase2_closed_loop():
    print("--- VIL ML Phase 2 Closed-Loop & Regime Test ---")
    
    # 1. Test Regime-Specific Routing
    print("\n[1] Testing Regime-Specific Routing...")
    regimes_to_test = ["TRENDING", "RANGING", "UNSTABLE"]
    async with httpx.AsyncClient() as client:
        for reg in regimes_to_test:
            features = {
                "symbol": "EUR_USD",
                "regime": reg,
                "direction": "BUY",
                "score": 80.0,
                "structure_score": 20.0,
                "volatility_score": 15.0,
                "liquidity_score": 15.0,
                "event_score": 10.0,
                "adx": 35.0 if reg == "TRENDING" else 15.0,
                "rsi": 65.0,
                "atr_percentile": 0.5,
                "relative_volume": 1.1,
                "session_rank": 1,
                "hour_of_day": 14,
                "day_of_week": 1
            }
            resp = await client.post("http://localhost:8001/predict/success", json=features)
            data = resp.json()
            print(f" - Regime: {reg:10} -> Model: {data['modelVersion']:25} Prob: {data['successProbability']}")

    # 2. Test Outcome Logging (Closed-Loop)
    print("\n[2] Testing Outcome Logging (Closed-Loop)...")
    async with async_session() as session:
        # Get the latest signal that has a dataset entry
        res = await session.execute(
            select(MLSignalDataset).order_by(MLSignalDataset.created_at.desc()).limit(1)
        )
        ds_entry = res.scalar_one_or_none()
        if not ds_entry:
            print("FAILURE: No MLSignalDataset entry found. Run Phase 1 test first.")
            return

        signal_id = ds_entry.signal_id
        print(f"Logging SUCCESS for Signal ID: {signal_id}")
        
        # Call the log_outcome endpoint
        payload = {
            "signalId": str(signal_id),
            "outcome": "SUCCESS",
            "rMultiple": 2.5
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post("http://localhost:8001/dataset/outcome", json=payload)
            print(f"Outcome Log Response: {resp.status_code} - {resp.json()}")

        # 3. Verify in DB (using a fresh session to avoid cache)
        async with async_session() as verify_session:
            res = await verify_session.execute(select(MLSignalDataset).where(MLSignalDataset.signal_id == signal_id))
            updated_ds = res.scalar_one_or_none()
            
            if updated_ds and updated_ds.target_reached == 1 and updated_ds.r_multiple == 2.5:
                print(f"SUCCESS: Database verified. target_reached=1, r_multiple=2.5")
            else:
                print(f"FAILURE: Data not updated. target_reached={updated_ds.target_reached if updated_ds else 'N/A'}")

if __name__ == "__main__":
    asyncio.run(test_phase2_closed_loop())
