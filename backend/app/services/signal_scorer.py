"""Signal Scoring Engine — Layer 8 of VIL.

Purpose:
Weighted scoring system combining all engine outputs.

Weights (Standard Profile):
- Regime Alignment: 25%
- Structural Bias: 25%
- Breakout/Gates: 15%
- Volatility State: 15%
- Liquidity Conf: 10%
- Event Risk: 10%

Output:
- Final Score (0-100)
- Component Breakdown
"""

from app.services.regime_gates import GateResult
from app.services.regime_classifier import Regime

# ── Adaptive Weight Mappings (Layer 6) ───────────────────────────────────────

REGIME_WEIGHT_MAP = {
    Regime.TRENDING_BULLISH: {
        "regime": 0.35, "structure": 0.35, "confluence": 0.15, "volatility": 0.05, "liquidity": 0.05, "event": 0.05
    },
    Regime.TRENDING_BEARISH: {
        "regime": 0.35, "structure": 0.35, "confluence": 0.15, "volatility": 0.05, "liquidity": 0.05, "event": 0.05
    },
    Regime.RANGING_NARROW: {
        "regime": 0.15, "structure": 0.15, "confluence": 0.10, "volatility": 0.25, "liquidity": 0.25, "event": 0.10
    },
    Regime.RANGING_WIDE: {
        "regime": 0.20, "structure": 0.20, "confluence": 0.10, "volatility": 0.20, "liquidity": 0.20, "event": 0.10
    },
    Regime.HIGH_VOLATILITY: {
        "regime": 0.10, "structure": 0.10, "confluence": 0.05, "volatility": 0.30, "liquidity": 0.20, "event": 0.25
    },
    Regime.VOLATILITY_EXPANSION: {
        "regime": 0.15, "structure": 0.25, "confluence": 0.20, "volatility": 0.25, "liquidity": 0.10, "event": 0.05
    },
    Regime.UNSTABLE: {
        "regime": 0.10, "structure": 0.10, "confluence": 0.10, "volatility": 0.20, "liquidity": 0.20, "event": 0.30
    }
}

DEFAULT_WEIGHTS = {
    "regime": 0.25, "structure": 0.25, "confluence": 0.15, "volatility": 0.15, "liquidity": 0.10, "event": 0.10
}


def score_signal(
    regime_type: Regime,
    regime_confidence: float,
    structure_score: float,
    confluence_score: float, # MTF Alignment
    volatility_score: float, # Volatility Percentile derived
    liquidity_score: float,  # Liquidity/Sweep status
    event_risk_score: float, # Inverse risk (100 = safe)
    asset_profile_weights: dict | None = None,
) -> dict:
    """
    VIL 2.0 Adaptive Scoring Engine.
    Weights are dynamically selected based on the detected market regime.
    """
    # Select weights based on regime
    weights = REGIME_WEIGHT_MAP.get(regime_type, DEFAULT_WEIGHTS).copy()
    
    # Adjust weights based on Asset Profile overrides if present
    if asset_profile_weights:
        if asset_profile_weights.get("trend_weight", 1.0) > 1.2:
            weights["structure"] *= 1.2
            weights["regime"] *= 1.1
    
    # Normalize weights
    total_w = sum(weights.values())
    for k in weights:
        weights[k] /= total_w

    # ── Component Scores Calculation ─────────────────────────────────────────
    
    # 1. Regime Intelligence
    s_regime = regime_confidence
    
    # 2. Structural Confidence
    s_structure = structure_score
    
    # 3. MTF Confluence
    s_conf = confluence_score
    
    # 4. Volatility State
    s_vol = volatility_score
    
    # 5. Liquidity Context
    s_liq = liquidity_score
    
    # 6. Event Safety
    s_event = event_risk_score

    # ── Final Calculation ────────────────────────────────────────────────────
    
    final_score = (
        s_regime * weights["regime"] +
        s_structure * weights["structure"] +
        s_conf * weights["confluence"] +
        s_vol * weights["volatility"] +
        s_liq * weights["liquidity"] +
        s_event * weights["event"]
    )
    
    # Confidence Score is the final score but can be penalized by stability
    
    return {
        "final_score": round(final_score, 1),
        "components": {
            "regime": round(s_regime, 1),
            "structure": round(s_structure, 1),
            "confluence": round(s_conf, 1),
            "volatility": round(s_vol, 1),
            "liquidity": round(s_liq, 1),
            "event": round(s_event, 1),
        },
        "weights_used": {k: round(v, 2) for k, v in weights.items()}
    }
