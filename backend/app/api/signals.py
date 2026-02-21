"""Signal API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import Signal, Asset, LifecycleStatus
from app.schemas.signals import SignalResponse
from app.services.asset_manager import AssetManager

router = APIRouter(prefix="/api/signals", tags=["signals"])


def _signal_to_response(s: Signal) -> SignalResponse:
    symbol = s.asset.symbol if s.asset else "UNKNOWN"
    return SignalResponse(
        id=str(s.id),
        symbol=symbol,
        direction=s.direction.value,
        entry_price=s.entry_price,
        stop_loss=s.stop_loss,
        take_profit=s.take_profit,
        score=s.score,
        score_delta=s.score_delta,
        regime=s.regime.value if s.regime else None,
        status=s.status.value if s.status else "PENDING",
        classification=s.classification.value if s.classification else None,
        risk_reward=s.risk_reward,
        position_size=s.position_size,
        notes=s.notes,
        asset_class=AssetManager.get_asset_class(symbol),
        tier=AssetManager.get_profile(symbol).tier,
        ml_probability=s.ml_probability,
        ml_confidence=s.ml_confidence,
        model_version=s.model_version,
        timestamp=s.timestamp,
    )


@router.get("/live", response_model=list[SignalResponse])
async def live_signals(
    limit: int = Query(20, le=100),
    asset_class: str | None = Query(None, description="Filter by asset class"),
    db: AsyncSession = Depends(get_db),
):
    """Fetch signals currently in PENDING, ACTIVE, or QUEUED state."""
    query = (
        select(Signal)
        .options(selectinload(Signal.asset))
        .where(Signal.status.in_([LifecycleStatus.PENDING, LifecycleStatus.ACTIVE, LifecycleStatus.QUEUED]))
        .order_by(desc(Signal.score))
        .limit(limit)
    )
    if asset_class:
        query = query.join(Asset).where(Asset.asset_type == asset_class)
    result = await db.execute(query)
    return [_signal_to_response(s) for s in result.scalars().all()]


@router.get("/history", response_model=list[SignalResponse])
async def historical_signals(
    symbol: str | None = None,
    direction: str | None = None,
    status: str | None = None,
    min_score: float | None = None,
    asset_class: str | None = Query(None, description="Filter by asset class"),
    group_id: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Comprehensive historical query for the Forensic Lab."""
    query = select(Signal).options(selectinload(Signal.asset))

    if symbol:
        query = query.join(Asset).where(Asset.symbol == symbol.upper())
    if asset_class:
        query = query.join(Asset).where(Asset.asset_type == asset_class)
    if direction:
        query = query.where(Signal.direction == direction.upper())
    if status:
        query = query.where(Signal.status == status.upper())
    if min_score is not None:
        query = query.where(Signal.score >= min_score)
    if group_id:
        query = query.where(Signal.signal_group_id == group_id)

    query = query.order_by(desc(Signal.timestamp)).offset(offset).limit(limit)
    result = await db.execute(query)
    return [_signal_to_response(s) for s in result.scalars().all()]


@router.get("/{signal_id}/forensic")
async def get_signal_forensic(
    signal_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full ML feature snapshot and audit lineage for a signal."""
    from app.db.models import SignalFeatureSnapshot, SignalAuditEvent
    
    # 1. Fetch Signal
    sig_res = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = sig_res.scalar_one_or_none()
    if not signal:
        return {"error": "Signal not found"}

    # 2. Fetch Snapshot
    feat_res = await db.execute(select(SignalFeatureSnapshot).where(SignalFeatureSnapshot.signal_id == signal_id))
    features = feat_res.scalars().first()

    # 3. Fetch Audits
    audit_res = await db.execute(select(SignalAuditEvent).where(SignalAuditEvent.signal_id == signal_id).order_by(SignalAuditEvent.timestamp))
    audits = audit_res.scalars().all()

    return {
        "signal": _signal_to_response(signal),
        "features": features,
        "audits": audits
    }
