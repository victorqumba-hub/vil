import asyncio
import httpx
from sqlalchemy import select
from app.db.database import async_session
from app.db.models import Signal, MLSignalDataset
from app.services.orchestrator import run_pipeline

async def test_integration():
    print("--- VIL ML Phase 1 Integration Test ---")
    
    # 1. Check ML Service Health
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8001/health")
            print(f"ML Service Health: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"ML Service Health Check FAILED: {e}")
        return

    # 2. Trigger Pipeline Trace
    print("\nTriggering pipeline for EUR_USD...")
    try:
        signals = await run_pipeline(symbols=["EUR_USD"])
        print(f"Pipeline finished. Generated {len(signals)} signals.")
        
        if not signals:
            print("No signals generated. Ending test.")
            return

        # 3. Verify Database
        async with async_session() as db:
            # Fetch latest signal
            res = await db.execute(select(Signal).order_by(Signal.timestamp.desc()).limit(1))
            latest_sig = res.scalar_one_or_none()
            
            if latest_sig:
                print(f"\nLatest Signal ID: {latest_sig.id}")
                print(f" - ML Probability: {latest_sig.ml_probability}")
                print(f" - ML Confidence: {latest_sig.ml_confidence}")
                print(f" - Model Version: {latest_sig.model_version}")
                
                # Verify Dataset persistence
                ds_res = await db.execute(select(MLSignalDataset).where(MLSignalDataset.signal_id == latest_sig.id))
                dataset_entry = ds_res.scalar_one_or_none()
                if dataset_entry:
                    print(f"SUCCESS: Feature snapshot stored in MLSignalDataset.")
                    # print(f" - Features: {dataset_entry.features_json[:100]}...")
                else:
                    print(f"FAILURE: No entry found in MLSignalDataset for signal.")
            else:
                print("FAILURE: No signals found in database after run.")
                
    except Exception as e:
        print(f"Integration Test Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_integration())
