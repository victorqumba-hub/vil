"""Market Regime Classifier — Classifies current market condition.

Regimes:
  TRENDING       — ADX > 25, clear directional bias
  RANGING        — ADX < 20, price oscillates between S/R
  HIGH_VOLATILITY — ATR spiking above normal, wide candles
  LOW_ACTIVITY   — ATR compressed, narrow candles, low volume
"""

from enum import Enum


class Regime(str, Enum):
    TRENDING_BULLISH = "TRENDING_BULLISH"
    TRENDING_BEARISH = "TRENDING_BEARISH"
    RANGING_NARROW = "RANGING_NARROW"
    RANGING_WIDE = "RANGING_WIDE"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    VOLATILITY_EXPANSION = "VOLATILITY_EXPANSION"
    VOLATILITY_CONTRACTION = "VOLATILITY_CONTRACTION"
    EVENT_RISK = "EVENT_RISK"
    UNSTABLE = "UNSTABLE"


def _calculate_slope(data: list[float], period: int = 10) -> float:
    """Calculates the slope of the data using linear regression."""
    if len(data) < period:
        return 0.0
    
    y = data[-period:]
    x = list(range(period))
    n = period
    
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xx = sum(xi*xi for xi in x)
    sum_xy = sum(xi*yi for xi, yi in zip(x, y))
    
    denom = (n * sum_xx - sum_x**2)
    if denom == 0:
        return 0.0
        
    slope = (n * sum_xy - sum_x * sum_y) / denom
    # Normalize by average price to get % change
    avg_y = sum(y) / n
    return (slope / avg_y) * 100 if avg_y > 0 else 0.0


def _calculate_regime_stability(adx: float, vol_perc: float, slope: float) -> float:
    """Calculates how stable the current environment is (0-100)."""
    # Stability = High ADX + Low/Normal Volatility Percentile + Consistent Slope
    adx_factor = min(1.0, adx / 50.0)
    vol_factor = 1.0 - (abs(vol_perc - 40) / 100.0) # Normal is 40-50
    slope_factor = 1.0 - min(1.0, abs(slope) / 0.5) if abs(slope) > 0.01 else 0.5
    
    stability = (adx_factor * 0.4 + vol_factor * 0.4 + slope_factor * 0.2) * 100
    return round(max(0, min(100, stability)), 1)


def classify_regime(
    closes: list[float],
    adx: float,
    atr: float,
    atr_history: list[float] | None = None,
    vol_percentile: float = 50.0,
    rel_volume: float = 1.0,
    minutes_to_event: int | None = None,
    sensitivity: float = 1.0,
) -> dict:
    """
    VIL 2.0 Multi-Dimensional Regime Engine.
    
    Regime determined by:
    - Trend slope strength
    - ADX / directional strength
    - Volatility expansion vs contraction (ATR Z-Score/Percentile)
    - Market session & relative volume
    """
    price = closes[-1] if closes else 0
    atr_pct = (atr / price * 100) if price else 0
    slope = _calculate_slope(closes, period=20)
    
    # ── 0. EVENT_RISK: High impact event imminent ────────────────────────
    if minutes_to_event is not None and minutes_to_event < 30:
         return {
            "regime": Regime.EVENT_RISK,
            "confidence": 100.0,
            "stability": 0.0,
            "characteristics": {"description": "High impact event imminent"},
        }

    # ── 1. HIGH_VOLATILITY: Extreme expansion ─────────────────────────────
    if vol_percentile > 90 or atr_pct > (1.5 / sensitivity):
        return {
            "regime": Regime.HIGH_VOLATILITY,
            "confidence": round(vol_percentile, 1),
            "stability": 20.0,
            "characteristics": {
                "description": "Extreme volatility — liquidity vacuum likely",
                "slope": round(slope, 4)
            },
        }

    # ── 2. TRENDING ───────────────────────────────────────────────────────
    if adx > 25:
        regime = Regime.TRENDING_BULLISH if slope > 0.005 else Regime.TRENDING_BEARISH
        if abs(slope) < 0.005: 
            # ADX is strong but slope is flat? Could be a rounding/choppy trend
            regime = Regime.UNSTABLE
            
        confidence = min(95, adx * 1.5 + (vol_percentile / 5))
        stability = _calculate_regime_stability(adx, vol_percentile, slope)
        
        return {
            "regime": regime,
            "confidence": round(confidence, 1),
            "stability": stability,
            "characteristics": {
                "slope": round(slope, 4),
                "adx": round(adx, 1),
                "description": f"Strong directional flow ({'Bullish' if slope > 0 else 'Bearish'})"
            },
        }

    # ── 3. VOLATILITY EXPANSION (Pre-Breakout) ────────────────────────────
    if rel_volume > 1.8 and vol_percentile > 60:
        return {
            "regime": Regime.VOLATILITY_EXPANSION,
            "confidence": 75.0,
            "stability": 40.0,
            "characteristics": {"description": "Volume surging — breakout imminent"},
        }

    # ── 4. RANGING ────────────────────────────────────────────────────────
    is_narrow = vol_percentile < 30
    confidence = min(90, 40 + (30 - adx) * 2)
    return {
        "regime": Regime.RANGING_NARROW if is_narrow else Regime.RANGING_WIDE,
        "confidence": round(confidence, 1),
        "stability": 80.0 if is_narrow else 50.0,
        "characteristics": {
            "description": "Mean-reversion environment",
            "vol_perc": round(vol_percentile, 1)
        },
    }
