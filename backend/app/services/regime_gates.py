"""Regime Gate Layers — Six-layer gate system that filters market conditions.

Each gate produces a pass/fail + confidence score. All six must pass for a
signal to proceed through the pipeline.

Gates:
  1. Volatility Gate   — ATR-based, rejects too-quiet or too-wild conditions
  2. Trend Gate        — ADX + MA alignment, confirms directional market
  3. Structural Gate   — Support/resistance + price structure
  4. Breakout Gate     — Range expansion detection
  5. Event Gate        — Economic calendar awareness
  6. Composite Gate    — Weighted aggregate of all gates
"""

from dataclasses import dataclass


@dataclass
class GateResult:
    name: str
    passed: bool
    confidence: float  # 0-100
    reason: str


# ── Gate 1: Volatility ───────────────────────────────────────────────────────

def volatility_gate(
    atr: float, 
    price: float, 
    atr_history: list[float] | None = None,
    volatility_multiplier: float = 1.0,
    spread_filter: float = 0.0005
) -> GateResult:
    """
    Pass if ATR is in a tradeable range (not too quiet, not too wild).
    Uses ATR as % of price and compares to historical ATR percentile.
    """
    atr_pct = (atr / price) * 100 if price else 0

    # Base thresholds
    MIN_VOL = 0.02
    # Dynamic MAX_VOL based on asset class volatility multiplier
    # e.g. Forex: 1.5%, Crypto (multi=2.5): 3.75%
    MAX_VOL = 1.5 * volatility_multiplier

    # Reject if near-zero volatility
    if atr_pct < MIN_VOL:
        return GateResult("Volatility", False, 10.0, "ATR too low — dead market")

    # Reject extreme volatility (news-driven chaos)
    if atr_pct > MAX_VOL:
        return GateResult("Volatility", False, 15.0, f"ATR {atr_pct:.2f}% > {MAX_VOL:.2f}% — uncontrolled volatility")

    # Check ATR expansion if history available
    if atr_history and len(atr_history) >= 20:
        avg_atr = sum(atr_history[-20:]) / 20
        ratio = atr / avg_atr if avg_atr else 1

        # Allow more room for expansion in Indices/Crypto
        MAX_EXPANSION = 3.0 * volatility_multiplier
        if ratio > MAX_EXPANSION:
            return GateResult("Volatility", False, 20.0, f"ATR spiking ({ratio:.1f}x) — possible event danger")
        if ratio < 0.2: # Relaxed from 0.3
            return GateResult("Volatility", False, 15.0, "ATR compressed — no opportunity")

        confidence = min(95, 40 + ratio * 20)
    else:
        # Standard range check
        confidence = 60.0 if (MIN_VOL * 2) < atr_pct < (MAX_VOL * 0.6) else 40.0

    return GateResult("Volatility", True, round(confidence, 1), f"ATR {atr_pct:.3f}% — within range")


# ── Gate 2: Trend ─────────────────────────────────────────────────────────────

def trend_gate(adx: float, rsi: float, closes: list[float] | None = None) -> GateResult:
    """
    Pass if ADX indicates a trending market (>20) and MA alignment confirms.
    """
    if adx < 15:
        return GateResult("Trend", False, 15.0, f"ADX {adx:.1f} — no trend present")

    # Weak trend zone
    if adx < 20:
        return GateResult("Trend", False, 30.0, f"ADX {adx:.1f} — trend forming but too weak")

    # Check MA alignment if closes provided
    ma_aligned = True
    if closes and len(closes) >= 50:
        ma20 = sum(closes[-20:]) / 20
        ma50 = sum(closes[-50:]) / 50
        # Bullish: MA20 > MA50, Bearish: MA20 < MA50
        ma_aligned = abs(ma20 - ma50) / ma50 > 0.001  # At least 0.1% separation

    confidence = min(95, adx * 1.8)  # Scale ADX to confidence
    if not ma_aligned:
        confidence *= 0.7  # Reduce if MAs are tangled

    return GateResult("Trend", True, round(confidence, 1), f"ADX {adx:.1f} — trending confirmed")


# ── Gate 3: Structural ────────────────────────────────────────────────────────

def structural_gate(
    price: float,
    highs: list[float],
    lows: list[float],
    lookback: int = 20,
) -> GateResult:
    """
    Pass if price has clear support/resistance structure.
    Detects swing highs/lows to confirm structural context.
    """
    if len(highs) < lookback or len(lows) < lookback:
        return GateResult("Structural", True, 40.0, "Insufficient data — assuming OK")

    recent_highs = highs[-lookback:]
    recent_lows = lows[-lookback:]

    swing_high = max(recent_highs)
    swing_low = min(recent_lows)
    rng = swing_high - swing_low

    if rng == 0:
        return GateResult("Structural", False, 10.0, "No price range — flat market")

    # Price position within range (0=bottom, 1=top)
    position = (price - swing_low) / rng

    # Near extremes = better structural clarity
    if position < 0.15 or position > 0.85:
        confidence = 85.0
        reason = f"Near swing {'high' if position > 0.5 else 'low'} — clear structure"
    elif position < 0.3 or position > 0.7:
        confidence = 65.0
        reason = "Approaching key level"
    else:
        confidence = 45.0
        reason = "Mid-range — less structural clarity"

    return GateResult("Structural", True, round(confidence, 1), reason)


# ── Gate 4: Breakout ──────────────────────────────────────────────────────────

def breakout_gate(
    close: float,
    highs: list[float],
    lows: list[float],
    atr: float,
    lookback: int = 20,
) -> GateResult:
    """
    Detect range expansion / breakout conditions.
    Uses Bollinger-like range width and price distance from range boundary.
    """
    if len(highs) < lookback:
        return GateResult("Breakout", True, 30.0, "Insufficient data")

    recent_highs = highs[-lookback:]
    recent_lows = lows[-lookback:]
    range_high = max(recent_highs)
    range_low = min(recent_lows)
    range_width = range_high - range_low

    if range_width == 0 or atr == 0:
        return GateResult("Breakout", False, 10.0, "No range to break")

    # Range width relative to ATR (narrow range = potential breakout)
    compression = range_width / atr
    exceeded_high = close > range_high
    exceeded_low = close < range_low

    if exceeded_high or exceeded_low:
        direction = "upside" if exceeded_high else "downside"
        confidence = min(95, 60 + (abs(close - (range_high if exceeded_high else range_low)) / atr) * 20)
        return GateResult("Breakout", True, round(confidence, 1), f"Breakout {direction} confirmed")

    if compression < 3:
        return GateResult("Breakout", True, 70.0, "Tight range — breakout imminent")

    if compression < 6:
        return GateResult("Breakout", True, 50.0, "Moderate range — watching for break")

    return GateResult("Breakout", True, 35.0, "Wide range — breakout not imminent")


# ── Gate 5: Event ─────────────────────────────────────────────────────────────

def event_gate(
    upcoming_high_impact: list[dict] | None = None,
    minutes_to_next: int | None = None,
) -> GateResult:
    """
    Reduce confidence or reject if high-impact events are imminent.
    """
    if not upcoming_high_impact:
        return GateResult("Event", True, 80.0, "No high-impact events scheduled")

    if minutes_to_next is not None:
        if minutes_to_next < 15:
            return GateResult("Event", False, 10.0, "High-impact event < 15 min away — stand aside")
        if minutes_to_next < 60:
            return GateResult("Event", True, 35.0, "High-impact event within 1 hour — caution")
        if minutes_to_next < 180:
            return GateResult("Event", True, 60.0, "Event within 3 hours — monitor")

    return GateResult("Event", True, 75.0, "Events scheduled but not imminent")


# ── Gate 6: Composite ─────────────────────────────────────────────────────────

GATE_WEIGHTS = {
    "Volatility": 0.20,
    "Trend": 0.25,
    "Structural": 0.20,
    "Breakout": 0.15,
    "Event": 0.20,
}


def composite_gate(gates: list[GateResult]) -> GateResult:
    """
    Aggregate all gate results into a composite pass/fail.
    Requires ALL individual gates to pass.
    """
    all_passed = all(g.passed for g in gates)

    weighted_confidence = 0.0
    for g in gates:
        weight = GATE_WEIGHTS.get(g.name, 0.2)
        weighted_confidence += g.confidence * weight

    if not all_passed:
        failed = [g.name for g in gates if not g.passed]
        return GateResult(
            "Composite",
            False,
            round(weighted_confidence * 0.5, 1),
            f"Failed gates: {', '.join(failed)}",
        )

    return GateResult("Composite", True, round(weighted_confidence, 1), "All gates passed")


# ── Pipeline Runner ───────────────────────────────────────────────────────────

def run_all_gates(
    price: float,
    atr: float,
    adx: float,
    rsi: float,
    highs: list[float],
    lows: list[float],
    closes: list[float],
    atr_history: list[float] | None = None,
    upcoming_events: list[dict] | None = None,
    minutes_to_event: int | None = None,
    spread_filter: float = 0.0005,
    volatility_multiplier: float = 1.0,
) -> tuple[bool, list[GateResult]]:
    """
    Run all 6 gate layers and return (passed, gate_results).
    """
    gates = [
        volatility_gate(atr, price, atr_history, volatility_multiplier, spread_filter),
        trend_gate(adx, rsi, closes),
        structural_gate(price, highs, lows),
        breakout_gate(price, highs, lows, atr),
        event_gate(upcoming_events, minutes_to_event),
    ]

    composite = composite_gate(gates)
    gates.append(composite)

    return composite.passed, gates
