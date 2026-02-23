"""Pydantic schemas for market data."""

from datetime import datetime
from pydantic import BaseModel


class MarketDataResponse(BaseModel):
    id: str
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None
    atr: float | None
    adx: float | None
    rsi: float | None
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }


class OHLCVRequest(BaseModel):
    symbol: str
    timeframe: str = "H1"
    limit: int = 100
