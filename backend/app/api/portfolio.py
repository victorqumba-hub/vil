"""Portfolio API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import Trade, Signal, User
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("/summary")
async def portfolio_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Trade)
        .options(selectinload(Trade.signal).selectinload(Signal.asset))
        .where(Trade.user_id == user.id)
    )
    trades = result.scalars().all()

    total_pnl = sum(t.pnl or 0.0 for t in trades)
    winning = [t for t in trades if (t.pnl or 0) > 0]
    losing = [t for t in trades if (t.pnl or 0) < 0]
    open_trades = [t for t in trades if t.status.value == "OPEN"]

    return {
        "total_trades": len(trades),
        "open_trades": len(open_trades),
        "total_pnl": round(total_pnl, 2),
        "win_rate": round(len(winning) / max(len(trades), 1) * 100, 1),
        "wins": len(winning),
        "losses": len(losing),
        "avg_win": round(sum(t.pnl for t in winning) / max(len(winning), 1), 2),
        "avg_loss": round(sum(t.pnl for t in losing) / max(len(losing), 1), 2),
    }


@router.get("/trades")
async def list_trades(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Trade)
        .options(selectinload(Trade.signal).selectinload(Signal.asset))
        .where(Trade.user_id == user.id)
        .order_by(Trade.executed_at.desc())
        .limit(100)
    )
    trades = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "symbol": t.signal.asset.symbol if t.signal and t.signal.asset else "?",
            "direction": t.signal.direction.value if t.signal else "?",
            "status": t.status.value,
            "pnl": t.pnl,
            "lots": t.lots,
            "executed_at": t.executed_at.isoformat(),
            "closed_at": t.closed_at.isoformat() if t.closed_at else None,
        }
        for t in trades
    ]
