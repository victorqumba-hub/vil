from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.ml.engine import model_manager
from app.ml.forensics import ForensicEngine
import time

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])

class FeatureSchema(BaseModel):
    symbol: str
    regime: str
    direction: str
    score: float
    structure_score: float
    volatility_score: float
    liquidity_score: float
    event_score: float
    adx: float
    rsi: float
    atr_percentile: float
    relative_volume: float
    session_rank: int
    hour_of_day: int
    day_of_week: int

class PredictionResponse(BaseModel):
    successProbability: float
    confidenceScore: float
    modelVersion: str
    regime_model: str
    topFeatureContributors: Dict[str, float]
    latency_ms: float

@router.post("/predict/success", response_model=PredictionResponse)
async def predict_success(features: FeatureSchema):
    start_time = time.time()
    result = model_manager.predict(features.dict())
    latency = (time.time() - start_time) * 1000
    
    return {
        "successProbability": result["prob"],
        "confidenceScore": result["confidence"],
        "modelVersion": result["version"],
        "regime_model": features.regime,
        "topFeatureContributors": {
            "score": 0.40,
            "adx": 0.20 if "TRENDING" in features.regime else 0.05,
            "rsi": 0.25 if "RANGING" in features.regime else 0.10
        },
        "latency_ms": round(latency, 2)
    }

@router.post("/forensics/analyze/{signal_id}")
async def analyze_signal(signal_id: UUID, db: AsyncSession = Depends(get_db)):
    """Analyze a specific terminal signal."""
    engine = ForensicEngine(db)
    analysis = await engine.analyze_signal(str(signal_id))
    if not analysis:
        raise HTTPException(status_code=404, detail="Signal or features not found")
    return analysis

@router.post("/forensics/report")
async def generate_forensic_report(db: AsyncSession = Depends(get_db)):
    """Generate a batch intelligence report."""
    engine = ForensicEngine(db)
    report = await engine.generate_batch_report()
    if not report:
        raise HTTPException(status_code=400, detail="Insufficient signals for batch analysis (min 50)")
    return report
