"""Pydantic schemas for signals."""

from datetime import datetime
from pydantic import BaseModel


class SignalResponse(BaseModel):
    id: str
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    score: float
    score_delta: float | None = None
    regime: str | None
    status: str
    classification: str | None = None
    risk_reward: float | None
    position_size: float | None
    notes: str | None
    asset_class: str | None = None
    tier: int | None = None
    
    # ML Feedback
    ml_probability: float | None = None
    ml_confidence: float | None = None
    model_version: str | None = None
    
    timestamp: datetime

    class Config:
        from_attributes = True


class SignalFilterRequest(BaseModel):
    symbol: str | None = None
    direction: str | None = None
    regime: str | None = None
    min_score: float | None = None
    limit: int = 50
    offset: int = 0
