from fastapi import APIRouter, Depends, HTTPException
from app.services.broker_service import broker
from app.api.auth import get_current_user
from typing import List, Dict

router = APIRouter(prefix="/api/broker", tags=["Broker"])

@router.get("/account")
async def get_broker_account(current_user=Depends(get_current_user)):
    """Get live OANDA account metrics."""
    result = await broker.get_account_details()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.get("/trades")
async def get_broker_trades(current_user=Depends(get_current_user)):
    """Get live and recently closed trades from OANDA."""
    open_trades = await broker.get_open_trades()
    closed_trades = await broker.get_transaction_history(limit=20)
    
    return {
        "open": open_trades,
        "history": closed_trades
    }

@router.get("/stats")
async def get_broker_stats(current_user=Depends(get_current_user)):
    """Calculate performance stats based on broker history."""
    history = await broker.get_transaction_history(limit=100)
    
    if not history:
        return {
            "win_rate": 0,
            "avg_pnl": 0,
            "total_realized": 0,
            "trade_count": 0
        }
    
    wins = [t for t in history if t["realized_pnl"] > 0]
    total_pnl = sum(t["realized_pnl"] for t in history)
    
    return {
        "win_rate": round(len(wins) / len(history) * 100, 1),
        "avg_pnl": round(total_pnl / len(history), 2),
        "total_realized": round(total_pnl, 2),
        "trade_count": len(history)
    }
