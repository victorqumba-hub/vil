import asyncio
import json
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.db.database import async_session
from app.db.models import Signal, Asset, MLSignalDataset, LifecycleStatus, MarketRegime, SignalDirection, SignalClassification
from app.services.ml_client import ml_client

async def test_ml_augmentation_direct():
    print("--- VIL ML Direct Augmentation Test ---")
    
    async with async_session() as session:
        # 1. Ensure we have an asset
        res = await session.execute(select(Asset).limit(1))
        asset = res.scalar_one_or_none()
        if not asset:
            print("No assets found in DB. Please run seed script.")
            return

        print(f"Using Asset: {asset.symbol}")

        # 2. Mock s_data (from orchestrator)
        s_data = {
            "symbol": asset.symbol,
            "direction": "BUY",
            "entry_price": 1.1000,
            "stop_loss": 1.0950,
            "take_profit": 1.1100,
            "score": 85.0,
            "score_delta": 0.0,
            "classification": "FULL_SIGNAL",
            "regime": "TRENDING",
            "scoring": {
                "components": {
                    "regime": 20.0,
                    "structure": 25.0,
                    "volatility": 15.0,
                    "liquidity": 15.0,
                    "event": 10.0
                }
            },
            "risk_reward": 2.0,
            "position_size": 0.01,
            "ttl_hours": 4,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # 3. Build Feature Vector (Simulated)
        ml_features = {
            "symbol": s_data["symbol"],
            "regime": s_data["regime"],
            "direction": s_data["direction"],
            "score": s_data["score"],
            "structure_score": s_data["scoring"]["components"]["structure"],
            "volatility_score": s_data["scoring"]["components"]["volatility"],
            "liquidity_score": s_data["scoring"]["components"]["liquidity"],
            "event_score": s_data["scoring"]["components"]["event"],
            "adx": 30.0,
            "rsi": 65.0,
            "atr_percentile": 0.8,
            "relative_volume": 1.5,
            "session_rank": 1,
            "hour_of_day": datetime.now(timezone.utc).hour,
            "day_of_week": datetime.now(timezone.utc).weekday()
        }

        # 4. Call ML Inference
        print("Calling ML Service...")
        ml_result = await ml_client.get_success_probability(ml_features)
        
        if ml_result:
            print(f"ML Result: {ml_result}")
            
            # 5. Create Signal in DB with ML data
            new_signal = Signal(
                asset_id=asset.id,
                direction=SignalDirection.BUY,
                entry_price=s_data["entry_price"],
                stop_loss=s_data["stop_loss"],
                take_profit=s_data["take_profit"],
                score=s_data["score"],
                regime=MarketRegime.TRENDING,
                status=LifecycleStatus.PENDING,
                # ML Augmentation
                ml_probability=ml_result["successProbability"],
                ml_confidence=ml_result["confidenceScore"],
                model_version=ml_result["modelVersion"],
                timestamp=datetime.utcnow()
            )
            session.add(new_signal)
            await session.flush()
            
            # 6. Store in Dataset Builder
            session.add(MLSignalDataset(
                signal_id=new_signal.id,
                features_json=json.dumps(ml_features),
                is_training_sample=0
            ))
            
            await session.commit()
            print(f"SUCCESS: Signal {new_signal.id} created with ML augmentation and dataset snapshot.")
        else:
            print("FAILURE: ML Service returned None. Check ml_service logs.")

if __name__ == "__main__":
    asyncio.run(test_ml_augmentation_direct())
