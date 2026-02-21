from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import json
from uuid import UUID
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import async_session
from app.forensics import ForensicEngine

app = FastAPI(title="VIL ML Intelligence Service", version="2.0.0")

# ── Schemas ──────────────────────────────────────────────────────────────────

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

class OutcomeLog(BaseModel):
    signalId: UUID
    outcome: str
    rMultiple: float

# ── DB Access Helper ─────────────────────────────────────────────────────────

async def get_db():
    async with async_session() as session:
        yield session

# ── Model Registry / Manager ────────────────────────────────────────────────

import joblib
import os
import pandas as pd

class ModelManager:
    """Institutional model loader with regime-specific routing."""
    
    def __init__(self):
        self.model_dir = os.path.join(os.path.dirname(__file__), "models")
        self.models = {}
        self.load_models()
        
    def load_models(self):
        """Pre-loads all available regime models into memory."""
        try:
            available_files = os.listdir(self.model_dir)
            for f in available_files:
                if f.endswith(".joblib"):
                    regime = f.split("_")[1].upper()
                    self.models[regime] = joblib.load(os.path.join(self.model_dir, f))
                    print(f"[ModelManager] Loaded {regime} model: {f}")
        except Exception as e:
            print(f"[ModelManager] Error loading models: {e}")

    def predict(self, features: FeatureSchema) -> Dict[str, Any]:
        regime = features.regime.upper()
        
        # Determine which model to use
        model_key = "GLOBAL"
        if "TRENDING" in regime: model_key = "TRENDING"
        elif "RANGING" in regime: model_key = "RANGING"
        
        model = self.models.get(model_key) or self.models.get("GLOBAL")
        
        if model:
            try:
                # Prepare features for XGBoost (matching train.py preprocessing)
                feat_dict = features.dict()
                # Create a single-row DataFrame
                input_df = pd.DataFrame([feat_dict])
                
                # Drop non-feature columns
                drop_cols = ['symbol', 'regime', 'direction']
                X = input_df.drop(columns=[c for c in drop_cols if c in input_df.columns])
                
                # Predict probability of class 1 (SUCCESS)
                prob = float(model.predict_proba(X)[0][1])
                version = f"XGB-{model_key}-v1.0"
                
                return {
                    "prob": round(prob, 4),
                    "confidence": 0.90 if prob > 0.7 or prob < 0.3 else 0.75,
                    "version": version
                }
            except Exception as e:
                print(f"[ModelManager] Inference error: {e}. Falling back to heuristics.")

        # Fallback Heuristics (Original Phase 2 Logic)
        prob_multiplier = 1.05 if "TRENDING" in regime else (0.95 if "RANGING" in regime else 1.0)
        success_prob = min(0.98, (features.score / 100.0) * prob_multiplier)
        
        return {
            "prob": round(success_prob, 4),
            "confidence": 0.88 if "TRENDING" in regime else 0.75,
            "version": "Heuristic-Fallback-v1.0"
        }

model_manager = ModelManager()

# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "healthy", "regime_models": ["TRENDING", "RANGING", "VOLATILITY"]}

@app.post("/predict/success", response_model=PredictionResponse)
async def predict_success(features: FeatureSchema):
    start_time = time.time()
    
    result = model_manager.predict(features)
    
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

@app.post("/dataset/outcome")
async def log_outcome(log: OutcomeLog, db: AsyncSession = Depends(get_db)):
    """
    Closed-Loop Feedback: Updates the ML dataset with the actual trade outcome.
    """
    try:
        # We need the table name without importing models to avoid circularity/paths
        # Using raw SQL for the outcome update for robustness in the microservice
        from sqlalchemy import text
        
        target_reached = 1 if log.outcome == "SUCCESS" else 0
        stop_hit = 1 if log.outcome == "FAILED" else 0
        
        stmt = text("""
            UPDATE ml_signal_dataset 
            SET target_reached = :tr, 
                stop_hit = :sh, 
                r_multiple = :rm,
                created_at = NOW()
            WHERE signal_id = :sid
        """)
        
        result = await db.execute(stmt, {
            "tr": target_reached,
            "sh": stop_hit,
            "rm": log.rMultiple,
            "sid": log.signalId
        })
        
        await db.commit()
        
        if result.rowcount == 0:
            print(f"[ML Service] WARNING: No dataset entry found for signal {log.signalId}")
            return {"status": "ignored", "message": "Signal ID not found in dataset"}
            
        print(f"[ML Service] Outcome logged for {log.signalId}: {log.outcome}")
        return {"status": "success"}
        
    except Exception as e:
        print(f"[ML Service] Error logging outcome: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ── Forensic Endpoints ───────────────────────────────────────────────────────

@app.post("/forensics/analyze/{signal_id}")
async def analyze_signal(signal_id: UUID, db: AsyncSession = Depends(get_db)):
    """Analyze a specific terminal signal."""
    engine = ForensicEngine(db)
    analysis = await engine.analyze_signal(str(signal_id))
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Signal or features not found")
    
    # Persist the analysis
    from sqlalchemy import text
    stmt = text("""
        INSERT INTO signal_forensic_analysis (
            id, signal_id, quality_score, execution_quality_score, 
            structural_integrity_score, regime_compatibility_score, 
            ml_confidence_deviation, causality_summary, engine_critique, 
            suggested_adjustments, analyzed_at
        ) VALUES (
            uuid_generate_v4(), :sid, :qs, :eqs, :sis, :rcs, :mcd, :cs, :ec, :sa, NOW()
        )
        ON CONFLICT (signal_id) DO UPDATE SET
            quality_score = EXCLUDED.quality_score,
            causality_summary = EXCLUDED.causality_summary,
            engine_critique = EXCLUDED.engine_critique,
            analyzed_at = NOW()
    """)
    
    # Note: uuid_generate_v4() might require extension in PG. 
    # For safety, we can generate it in Python or use gen_random_uuid()
    import uuid
    stmt = text("""
        INSERT INTO signal_forensic_analysis (
            id, signal_id, quality_score, execution_quality_score, 
            structural_integrity_score, regime_compatibility_score, 
            ml_confidence_deviation, causality_summary, engine_critique, 
            suggested_adjustments, analyzed_at
        ) VALUES (
            :id, :sid, :qs, :eqs, :sis, :rcs, :mcd, :cs, :ec, :sa, NOW()
        )
        ON CONFLICT (signal_id) DO UPDATE SET
            quality_score = EXCLUDED.quality_score,
            causality_summary = EXCLUDED.causality_summary,
            engine_critique = EXCLUDED.engine_critique,
            analyzed_at = NOW()
    """)
    
    await db.execute(stmt, {
        "id": uuid.uuid4(),
        "sid": signal_id,
        "qs": analysis["quality_score"],
        "eqs": analysis["execution_quality_score"],
        "sis": analysis["structural_integrity_score"],
        "rcs": analysis["regime_compatibility_score"],
        "mcd": analysis["ml_confidence_deviation"],
        "cs": analysis["causality_summary"],
        "ec": analysis["engine_critique"],
        "sa": analysis["suggested_adjustments"]
    })
    
    await db.commit()
    return analysis

@app.post("/forensics/report")
async def generate_forensic_report(db: AsyncSession = Depends(get_db)):
    """Generate a batch intelligence report."""
    engine = ForensicEngine(db)
    report = await engine.generate_batch_report()
    
    if not report:
        raise HTTPException(status_code=400, detail="Insufficient signals for batch analysis (min 50)")
    
    # Persist the report
    from sqlalchemy import text
    import uuid
    stmt = text("""
        INSERT INTO signal_intelligence_reports (
            id, batch_start_date, batch_end_date, signal_count, 
            executive_summary, expectancy, setup_efficiency_json, 
            regime_performance_json, volatility_sensitivity_json, 
            engine_critique_summary, strategic_recommendations, created_at
        ) VALUES (
            :id, :bsd, :bed, :sc, :es, :exp, :sej, :rpj, :vsj, :ecs, :sr, NOW()
        )
    """)
    
    await db.execute(stmt, {
        "id": uuid.uuid4(),
        "bsd": report["batch_start_date"],
        "bed": report["batch_end_date"],
        "sc": report["signal_count"],
        "es": report["executive_summary"],
        "exp": report["expectancy"],
        "sej": report["setup_efficiency_json"],
        "rpj": report["regime_performance_json"],
        "vsj": report["volatility_sensitivity_json"],
        "ecs": report["engine_critique_summary"],
        "sr": report["strategic_recommendations"]
    })
    
    await db.commit()
    return report

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
