"""Pipeline API — Exposes the signal generation orchestrator via REST."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.api.auth import get_current_user
from app.services.orchestrator import run_pipeline


router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


from app.ws.websocket import manager as ws_manager

from app.schemas.pipeline import PipelineRunRequest

@router.post("/run")
async def trigger_pipeline(
    request: PipelineRunRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Run the full signal generation pipeline.

    Requires authentication. Returns generated signals sorted by quality score.
    """
    print(f"API: Triggering pipeline with {request}")
    import traceback
    try:
        signals = await run_pipeline(
            symbols=request.symbols,
            timeframe=request.timeframe,
            top_n=request.top_n,
            min_score=request.min_score,
            db=db,
        )
    except Exception as e:
        print(f"API: Pipeline crashed during execution: {e}")
        traceback.print_exc()
        raise e

    print("API: Run pipeline completed. Starting broadcast...")

    try:
        # Broadcast new signals to WebSocket
        if signals:
            for s in signals:
                await ws_manager.broadcast("signals", {
                    "eventType": "SIGNAL_UPDATE",
                    "signalId": str(s.get("id")), # Ensure string
                    "symbol": s.get("symbol"),
                    "assetClass": s.get("asset_class"),
                    "direction": s.get("direction"),
                    "score": s.get("score"),
                    "scoreDelta": s.get("score_delta"),
                    "classification": s.get("classification"),
                    "regime": str(s.get("regime")), # Ensure string
                    "structuralConfidence": s.get("scores", {}).get("structure", 0),
                    "volatilityScore": s.get("scores", {}).get("volatility", 0),
                    "liquidityScore": s.get("scores", {}).get("liquidity", 0),
                    "status": s.get("status"),
                    "timestamp": s.get("timestamp")
                })
        print("API: Broadcast completed.")
    except Exception as e:
         print(f"API: Broadcast crashed: {e}")
         traceback.print_exc()
         # Non-fatal? Maybe we still want to return results

    print("API: Returning results...")
    try:
        return {
            "count": len(signals),
            "timeframe": request.timeframe,
            "signals": signals,
        }
    except Exception as e:
        print(f"API: Return serialization crashed: {e}")
        traceback.print_exc()
        raise e


@router.get("/status")
async def pipeline_status():
    """Returns the current state of the pipeline monitor."""
    from app.services.pipeline_monitor import monitor
    return monitor.get_status()

