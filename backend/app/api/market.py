"""Market data API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import MarketData, Asset
from app.schemas.market import MarketDataResponse

router = APIRouter(prefix="/api/marketdata", tags=["market"])


@router.get("/ohlcv", response_model=list[MarketDataResponse])
async def get_ohlcv(
    symbol: str = Query(...),
    timeframe: str = Query("H1"),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MarketData)
        .options(selectinload(MarketData.asset))
        .join(Asset)
        .where(Asset.symbol == symbol.upper(), MarketData.timeframe == timeframe)
        .order_by(desc(MarketData.timestamp))
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        MarketDataResponse(
            id=str(m.id),
            symbol=m.asset.symbol,
            timeframe=m.timeframe.value,
            open=m.open,
            high=m.high,
            low=m.low,
            close=m.close,
            volume=m.volume,
            atr=m.atr,
            adx=m.adx,
            rsi=m.rsi,
            timestamp=m.timestamp,
        )
        for m in rows
    ]


@router.get("/assets")
async def list_assets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Asset).order_by(Asset.symbol))
    return [
        {
            "id": str(a.id),
            "symbol": a.symbol,
            "asset_type": a.asset_type.value,
            "base_currency": a.base_currency,
            "quote_currency": a.quote_currency,
            "description": a.description,
        }
        for a in result.scalars().all()
    ]
