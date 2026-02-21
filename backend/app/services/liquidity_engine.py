"""Liquidity & Volatility Engine — Layer 7 of VIL.

Purpose:
Assess volatility state and liquidity conditions.
- Detects Liquidity Sweeps (price taking out swing points but closing back inside).
- Classifies Volatility State (Expansion, Compression, Normal).
- Checks Spread feasibility.

Output:
LiquidityState {
    volatility_state: "EXPANSION" | "COMPRESSION" | "NORMAL"
    sweep_detected: bool
    spread_ok: bool
    liquidity_score: 0-100
}
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class LiquidityState:
    volatility_state: str
    sweep_detected: bool
    sweep_level: Optional[float]
    spread_ok: bool
    liquidity_score: float
    reason: str

class LiquidityEngine:
    def __init__(self, spread_threshold: float = 0.0005):
        self.spread_threshold = spread_threshold

    def analyze_liquidity(
        self,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        atr: float,
        current_spread: float,
        asset_class_spread_filter: float,
        swing_highs: List[float], # Prices of recent swing highs
        swing_lows: List[float]   # Prices of recent swing lows
    ) -> LiquidityState:
        
        # 1. Spread Check
        spread_ok = current_spread <= asset_class_spread_filter
        if not spread_ok:
            return LiquidityState(
                "NORMAL", False, None, False, 0.0, 
                f"Spread {current_spread:.5f} exceeds limit {asset_class_spread_filter}"
            )

        # 2. Volatility State (ATR Expansion/Compression)
        # We need ATR history ideally, but for now we look at candle range vs ATR
        if not highs or not lows:
             return LiquidityState("NORMAL", False, None, True, 50.0, "Insufficient data")

        current_range = highs[-1] - lows[-1]
        
        vol_state = "NORMAL"
        if current_range > (atr * 1.5):
            vol_state = "EXPANSION"
        elif current_range < (atr * 0.5):
            vol_state = "COMPRESSION"

        # 3. Liquidity Sweep Detection (Key "Smart Money" concept)
        # A sweep is: Breaking a Swing High/Low but closing back inside the range.
        
        sweep_detected = False
        sweep_level = None
        sweep_reason = ""
        
        current_close = closes[-1]
        current_high = highs[-1]
        current_low = lows[-1]
        
        # Check High Sweeps (Bearish Sweep)
        # Price went above a swing high, but closed BELOW it
        if swing_highs:
            recent_sh = max(swing_highs[-3:]) if len(swing_highs) >=3 else swing_highs[-1]
            if current_high > recent_sh and current_close < recent_sh:
                sweep_detected = True
                sweep_level = recent_sh
                sweep_reason = f"Swept High {recent_sh:.5f}"

        # Check Low Sweeps (Bullish Sweep)
        # Price went below a swing low, but closed ABOVE it
        if swing_lows and not sweep_detected:
             recent_sl = min(swing_lows[-3:]) if len(swing_lows) >=3 else swing_lows[-1]
             if current_low < recent_sl and current_close > recent_sl:
                 sweep_detected = True
                 sweep_level = recent_sl
                 sweep_reason = f"Swept Low {recent_sl:.5f}"

        # Score
        score = 50.0
        if vol_state == "EXPANSION":
            score += 10
        if sweep_detected:
            score += 20
        if not spread_ok:
            score = 0
            
        return LiquidityState(
            volatility_state=vol_state,
            sweep_detected=sweep_detected,
            sweep_level=sweep_level,
            spread_ok=spread_ok,
            liquidity_score=min(100.0, score),
            reason=sweep_reason or f"Vol: {vol_state}"
        )
