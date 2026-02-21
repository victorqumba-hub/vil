"""Regime Performance Attribution API — Score Audit Intelligence.

Provides structured winners vs losers analysis with regime transition
attribution, stability scoring, and AI forensic explanation.
"""

import json
from datetime import datetime
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import (
    Signal, Asset, SignalFeatureSnapshot, MLSignalDataset,
    LifecycleStatus, MarketRegime,
)
from app.services.asset_manager import AssetManager

router = APIRouter(prefix="/api/signals", tags=["regime-attribution"])

# Terminal statuses that indicate a completed signal
COMPLETED_STATUSES = [
    LifecycleStatus.SUCCESS,
    LifecycleStatus.FAILED,
    LifecycleStatus.EXPIRED,
    LifecycleStatus.EXPIRED_REGIME_SHIFT,
    LifecycleStatus.EXPIRED_SCORE_DECAY,
    LifecycleStatus.ARCHIVED,
]


def _regime_value(r) -> str:
    """Extract string value from regime enum or string."""
    if r is None:
        return "UNKNOWN"
    return r.value if hasattr(r, "value") else str(r)


def _safe_float(v, default=0.0) -> float:
    """Safely convert to float."""
    try:
        return float(v) if v is not None else default
    except (ValueError, TypeError):
        return default


def _compute_stability_index(signals_data: list[dict]) -> float:
    """Average regime stability across signals."""
    stabilities = [s.get("regime_stability", 50.0) for s in signals_data]
    return round(sum(stabilities) / len(stabilities), 2) if stabilities else 0.0


def _detect_regime_flip(entry_regime: str, exit_regime: str) -> bool:
    """Detect if regime changed between entry and exit."""
    if entry_regime == "UNKNOWN" or exit_regime == "UNKNOWN":
        return False
    return entry_regime != exit_regime


def _compute_regime_change_impact(winners: list, losers: list) -> float:
    """Regime Change Impact Index = flip rate difference between losers and winners."""
    w_flips = sum(1 for w in winners if w.get("regime_flip")) / max(len(winners), 1)
    l_flips = sum(1 for l in losers if l.get("regime_flip")) / max(len(losers), 1)
    return round((l_flips - w_flips) * 100, 1)


def _build_comparison_matrix(winners: list, losers: list) -> list[dict]:
    """Build a structured comparison matrix for winners vs losers."""
    def _avg(items, key):
        vals = [_safe_float(i.get(key)) for i in items if i.get(key) is not None]
        return round(sum(vals) / len(vals), 3) if vals else 0.0

    metrics = [
        ("Regime Stability", "regime_stability"),
        ("Structural Strength", "structure_score"),
        ("ATR Percentile", "volatility_percentile"),
        ("Spread Percentile", "spread_percentile"),
        ("ML Confidence", "ml_confidence"),
        ("Deterministic Score", "score"),
        ("R-Multiple", "r_multiple"),
        ("Time in Trade (min)", "time_in_trade_min"),
        ("Volatility Score", "volatility_score"),
        ("Event Proximity", "event_proximity"),
    ]

    matrix = []
    for label, key in metrics:
        w_avg = _avg(winners, key)
        l_avg = _avg(losers, key)
        delta = round(w_avg - l_avg, 3)
        # Significance: delta > 10% of winner avg
        sig = abs(delta) > (abs(w_avg) * 0.1) if w_avg != 0 else abs(delta) > 0.05
        matrix.append({
            "metric": label,
            "winners_avg": w_avg,
            "losers_avg": l_avg,
            "delta": delta,
            "significant": sig,
        })
    return matrix


def _generate_forensic_analysis(
    winners: list, losers: list, matrix: list[dict],
    regime_flip_rate_w: float, regime_flip_rate_l: float,
    total_signals: int, win_rate: float,
) -> dict:
    """Generate structured, quantitative AI forensic analysis."""

    # ── Extract key statistics ──
    def _avg(items, key):
        vals = [_safe_float(i.get(key)) for i in items if i.get(key) is not None]
        return round(sum(vals) / len(vals), 3) if vals else 0.0

    w_stability = _avg(winners, "regime_stability")
    l_stability = _avg(losers, "regime_stability")
    w_structure = _avg(winners, "structure_score")
    l_structure = _avg(losers, "structure_score")
    w_ml = _avg(winners, "ml_confidence")
    l_ml = _avg(losers, "ml_confidence")
    w_spread = _avg(winners, "spread_percentile")
    l_spread = _avg(losers, "spread_percentile")
    w_vol = _avg(winners, "volatility_percentile")
    l_vol = _avg(losers, "volatility_percentile")

    # ── Regime stability impact ──
    low_stability_losers = sum(1 for l in losers if _safe_float(l.get("regime_stability")) < 45)
    low_stability_pct = round(low_stability_losers / max(len(losers), 1) * 100, 0)

    # ── High spread losers ──
    high_spread_losers = sum(1 for l in losers if _safe_float(l.get("spread_percentile")) > 80)
    high_spread_pct = round(high_spread_losers / max(len(losers), 1) * 100, 0)

    # ── Build primary drivers ──
    drivers = []

    if low_stability_pct > 40:
        drivers.append(
            f"{int(low_stability_pct)}% of losing trades occurred during regime instability "
            f"(stability index < 0.45)"
        )

    structure_diff = round(w_structure - l_structure, 1)
    if structure_diff > 5:
        drivers.append(
            f"Winners had {structure_diff:.0f}% higher structural strength score on average"
        )

    if high_spread_pct > 30:
        drivers.append(
            f"{int(high_spread_pct)}% of losers had spread percentile > 80th percentile"
        )

    if w_ml > 0 and l_ml > 0:
        drivers.append(
            f"ML confidence for winners averaged {w_ml:.2f} vs {l_ml:.2f} for losers"
        )

    if regime_flip_rate_l > regime_flip_rate_w * 1.5 and regime_flip_rate_l > 0.1:
        drivers.append(
            f"Regime flip occurred in {regime_flip_rate_l * 100:.0f}% of losing trades "
            f"vs {regime_flip_rate_w * 100:.0f}% of winners"
        )

    if w_stability > l_stability + 10:
        drivers.append(
            f"Average regime stability: winners {w_stability:.1f} vs losers {l_stability:.1f}"
        )

    if not drivers:
        drivers.append("Insufficient divergence detected between winners and losers in current sample")

    # ── Build conclusion ──
    conclusion_factors = []
    if l_stability < 50:
        conclusion_factors.append("Regime instability")
    if abs(w_vol - l_vol) > 10:
        conclusion_factors.append("Volatility compression misalignment")
    if high_spread_pct > 30:
        conclusion_factors.append("Liquidity sweep false breakouts")
    if regime_flip_rate_l > 0.2:
        conclusion_factors.append("Mid-trade regime transitions")
    if w_ml - l_ml > 0.1:
        conclusion_factors.append("ML confidence divergence")

    if not conclusion_factors:
        conclusion_factors.append("Microstructure variance under uniform engine governance")

    conclusion = (
        "Despite identical engine governance, outcome divergence was primarily driven by:\n"
        + "\n".join(f"{i+1}. {f}" for i, f in enumerate(conclusion_factors[:5]))
    )

    # ── Dimensional analysis ──
    dimensions = {
        "regime_stability_impact": {
            "winners_stable": w_stability,
            "losers_stable": l_stability,
            "low_stability_loser_pct": low_stability_pct,
            "verdict": "Losers skewed to unstable regimes" if l_stability < w_stability - 5 else "Regime stability comparable",
        },
        "structural_integrity": {
            "winners_avg": w_structure,
            "losers_avg": l_structure,
            "delta": structure_diff,
        },
        "volatility_conditions": {
            "winners_vol_pct": w_vol,
            "losers_vol_pct": l_vol,
            "aligned": abs(w_vol - l_vol) < 10,
        },
        "ml_confidence": {
            "winners_avg": w_ml,
            "losers_avg": l_ml,
            "confidence_gap": round(w_ml - l_ml, 3),
        },
        "execution_microstructure": {
            "winners_spread_pct": w_spread,
            "losers_spread_pct": l_spread,
            "high_spread_loser_pct": high_spread_pct,
        },
    }

    return {
        "primary_drivers": drivers,
        "conclusion": conclusion,
        "dimensions": dimensions,
    }


def _build_signal_entry(
    signal: Signal,
    snapshot: SignalFeatureSnapshot | None,
    ml_data: MLSignalDataset | None,
) -> dict:
    """Build a unified signal data dict for analysis."""
    symbol = signal.asset.symbol if signal.asset else "UNKNOWN"
    entry_regime = _regime_value(signal.regime)
    exit_regime = _regime_value(signal.regime_at_expiration)
    regime_flip = _detect_regime_flip(entry_regime, exit_regime)

    r_multiple = _safe_float(ml_data.r_multiple) if ml_data else 0.0
    is_winner = (ml_data.target_reached == 1) if ml_data and ml_data.target_reached is not None else (
        signal.status == LifecycleStatus.SUCCESS
    )

    # Time in trade
    time_in_trade_min = 0
    if signal.executed_at and signal.valid_until:
        delta = (signal.valid_until - signal.executed_at).total_seconds() / 60
        time_in_trade_min = round(max(0, delta), 1)
    elif signal.timestamp and signal.valid_until:
        delta = (signal.valid_until - signal.timestamp).total_seconds() / 60
        time_in_trade_min = round(max(0, delta), 1)

    # Feature snapshot data
    vol_pct = _safe_float(snapshot.volatility_percentile, 50.0) if snapshot else 50.0
    atr_val = _safe_float(snapshot.atr) if snapshot else 0.0
    spread_val = _safe_float(snapshot.spread_at_creation) if snapshot else 0.0
    event_prox = _safe_float(snapshot.event_proximity_score) if snapshot else 0.0
    liq_sweep = (snapshot.liquidity_sweep_flag == 1) if snapshot and snapshot.liquidity_sweep_flag is not None else False
    struct_break = snapshot.structural_break_type if snapshot else None
    session = snapshot.session if snapshot else None

    # Compute a regime stability proxy from feature data
    # Using volatility percentile and structural data as proxy
    regime_stability = max(0, min(100, 100 - abs(vol_pct - 40) * 1.5))

    return {
        "signal_id": str(signal.id),
        "symbol": symbol,
        "asset_class": AssetManager.get_asset_class(symbol),
        "direction": signal.direction.value if signal.direction else "UNKNOWN",
        "regime_at_entry": entry_regime,
        "regime_at_exit": exit_regime,
        "regime_flip": regime_flip,
        "regime_stability": round(regime_stability, 1),
        "ml_confidence": _safe_float(signal.ml_confidence),
        "score": _safe_float(signal.score),
        "structure_score": _safe_float(signal.structure_score),
        "volatility_score": _safe_float(signal.volatility_score),
        "regime_score": _safe_float(signal.regime_score),
        "liquidity_score": _safe_float(signal.liquidity_score),
        "r_multiple": r_multiple,
        "is_winner": is_winner,
        "time_in_trade_min": time_in_trade_min,
        "volatility_percentile": vol_pct,
        "atr": atr_val,
        "spread_percentile": spread_val,
        "event_proximity": event_prox,
        "liquidity_sweep": liq_sweep,
        "structural_break": struct_break,
        "session": session,
        "failure_category": signal.failure_category,
        "status": signal.status.value if signal.status else "UNKNOWN",
        "timestamp": signal.timestamp.isoformat() if signal.timestamp else None,
    }


@router.get("/regime-attribution")
async def regime_attribution(
    limit: int = Query(50, le=200, description="Number of signals to analyze"),
    asset_class: str | None = Query(None, description="Filter by asset class"),
    regime_type: str | None = Query(None, description="Filter by regime at entry"),
    min_confidence: float | None = Query(None, description="Min ML confidence threshold"),
    regime_flip_only: bool = Query(False, description="Only show regime-flip signals"),
    db: AsyncSession = Depends(get_db),
):
    """Regime-based performance attribution analysis for Score Audit."""

    # ── 1. Query completed signals ──
    query = (
        select(Signal)
        .options(
            selectinload(Signal.asset),
            selectinload(Signal.feature_snapshots),
        )
        .where(Signal.status.in_(COMPLETED_STATUSES))
        .order_by(desc(Signal.timestamp))
        .limit(limit)
    )

    if asset_class:
        query = query.join(Asset).where(Asset.asset_type == asset_class)
    if regime_type:
        try:
            query = query.where(Signal.regime == MarketRegime(regime_type))
        except ValueError:
            pass
    if min_confidence is not None:
        query = query.where(Signal.ml_confidence >= min_confidence)

    result = await db.execute(query)
    signals = result.scalars().unique().all()

    if not signals:
        return {
            "header": {"total_signals": 0, "win_rate": 0, "avg_r_winners": 0, "avg_r_losers": 0, "regime_flip_rate": 0, "stability_index": 0},
            "winners": [],
            "losers": [],
            "comparison_matrix": [],
            "forensic_analysis": {"primary_drivers": ["No completed signals found"], "conclusion": "Insufficient data", "dimensions": {}},
            "regime_breakdown": {},
        }

    # ── 2. Fetch ML dataset records for these signals ──
    signal_ids = [s.id for s in signals]
    ml_query = select(MLSignalDataset).where(MLSignalDataset.signal_id.in_(signal_ids))
    ml_result = await db.execute(ml_query)
    ml_records = {str(m.signal_id): m for m in ml_result.scalars().all()}

    # ── 3. Build signal entries ──
    all_entries = []
    for sig in signals:
        snapshot = sig.feature_snapshots[0] if sig.feature_snapshots else None
        ml_data = ml_records.get(str(sig.id))
        entry = _build_signal_entry(sig, snapshot, ml_data)
        all_entries.append(entry)

    # ── 4. Apply regime-flip filter ──
    if regime_flip_only:
        all_entries = [e for e in all_entries if e["regime_flip"]]

    # ── 5. Split winners / losers ──
    winners = [e for e in all_entries if e["is_winner"]]
    losers = [e for e in all_entries if not e["is_winner"]]

    total = len(all_entries)
    win_rate = round(len(winners) / max(total, 1) * 100, 1)

    avg_r_w = round(sum(_safe_float(w["r_multiple"]) for w in winners) / max(len(winners), 1), 2)
    avg_r_l = round(sum(_safe_float(l["r_multiple"]) for l in losers) / max(len(losers), 1), 2)

    regime_flip_rate_w = sum(1 for w in winners if w["regime_flip"]) / max(len(winners), 1)
    regime_flip_rate_l = sum(1 for l in losers if l["regime_flip"]) / max(len(losers), 1)
    overall_flip_rate = round(
        sum(1 for e in all_entries if e["regime_flip"]) / max(total, 1) * 100, 1
    )

    stability_index = _compute_stability_index(all_entries)

    # ── 6. Regime breakdown ──
    regime_counts = defaultdict(lambda: {"total": 0, "wins": 0})
    for e in all_entries:
        r = e["regime_at_entry"]
        regime_counts[r]["total"] += 1
        if e["is_winner"]:
            regime_counts[r]["wins"] += 1

    regime_breakdown = {
        regime: {
            "total": data["total"],
            "wins": data["wins"],
            "win_rate": round(data["wins"] / max(data["total"], 1) * 100, 1),
        }
        for regime, data in regime_counts.items()
    }

    # ── 7. Build comparison matrix ──
    matrix = _build_comparison_matrix(winners, losers)

    # ── 8. AI forensic analysis ──
    forensic = _generate_forensic_analysis(
        winners, losers, matrix,
        regime_flip_rate_w, regime_flip_rate_l,
        total, win_rate,
    )

    return {
        "header": {
            "total_signals": total,
            "winners_count": len(winners),
            "losers_count": len(losers),
            "win_rate": win_rate,
            "avg_r_winners": avg_r_w,
            "avg_r_losers": avg_r_l,
            "regime_flip_rate": overall_flip_rate,
            "stability_index": stability_index,
        },
        "winners": winners[:25],  # Cap for performance
        "losers": losers[:25],
        "comparison_matrix": matrix,
        "forensic_analysis": forensic,
        "regime_breakdown": regime_breakdown,
    }
