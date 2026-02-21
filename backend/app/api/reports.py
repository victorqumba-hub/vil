"""AI report API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import AIReport, Signal, SignalForensicAnalysis, SignalIntelligenceReport
from app.api.auth import get_current_user, User

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/ai")
async def list_reports(
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AIReport)
        .options(selectinload(AIReport.signal).selectinload(Signal.asset))
        .order_by(desc(AIReport.timestamp))
        .limit(limit)
    )
    reports = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "signal_id": str(r.signal_id),
            "symbol": r.signal.asset.symbol if r.signal and r.signal.asset else "?",
            "summary": r.summary,
            "rationale": r.rationale,
            "risk_assessment": r.risk_assessment,
            "timestamp": r.timestamp.isoformat(),
        }
        for r in reports
    ]


@router.post("/generate")
async def generate_report(
    signal_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    # Stub — real Mistral integration in Phase 3
    return {
        "status": "mock",
        "signal_id": signal_id,
        "summary": "AI report generation is pending Mistral API key configuration.",
        "rationale": "This is a placeholder report.",
    }


@router.get("/forensics/analysis/{signal_id}")
async def get_signal_forensic_analysis(
    signal_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Retrieve deep forensic analysis for a specific signal."""
    result = await db.execute(
        select(SignalForensicAnalysis)
        .where(SignalForensicAnalysis.signal_id == signal_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        return {"status": "pending", "message": "Forensic analysis not yet available for this signal."}
    
    return analysis


@router.get("/forensics/intelligence")
async def list_intelligence_reports(
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Retrieve a list of batch intelligence reports."""
    result = await db.execute(
        select(SignalIntelligenceReport)
        .order_by(desc(SignalIntelligenceReport.created_at))
        .limit(limit)
    )
    reports = result.scalars().all()
    return reports
