"""Structural Detection Engine — Identifies institutional market structure.

Detects:
- Swing Highs / Lows (Fractals)
- Break of Structure (BOS)
- Change of Character (CHOCH)
- Order Blocks (OB)
- Fair Value Gaps (FVG)
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class StructuralBias(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass
class StructureResult:
    bias: StructuralBias
    strength: float  # 0-100
    last_bos: Optional[float] = None
    last_choch: Optional[float] = None
    displacement_score: float = 0.0
    liquidity_sweep: bool = False
    details: dict = None


class StructureEngine:
    def __init__(self, fractal_period: int = 5):
        self.fractal_period = fractal_period

    def get_swing_highs(self, highs: List[float]) -> List[dict]:
        """Detects fractal swing highs."""
        swings = []
        for i in range(self.fractal_period, len(highs) - self.fractal_period):
            is_high = True
            for j in range(1, self.fractal_period + 1):
                if highs[i] < highs[i-j] or highs[i] < highs[i+j]:
                    is_high = False
                    break
            if is_high:
                swings.append({"index": i, "price": highs[i]})
        return swings

    def get_swing_lows(self, lows: List[float]) -> List[dict]:
        """Detects fractal swing lows."""
        swings = []
        for i in range(self.fractal_period, len(lows) - self.fractal_period):
            is_low = True
            for j in range(1, self.fractal_period + 1):
                if lows[i] > lows[i-j] or lows[i] > lows[i+j]:
                    is_low = False
                    break
            if is_low:
                swings.append({"index": i, "price": lows[i]})
        return swings

    def detect_fvg(self, candles: List[dict]) -> List[dict]:
        """Detects Fair Value Gaps (FVGs)."""
        fvgs = []
        for i in range(2, len(candles)):
            # Bullish FVG
            if candles[i-2]["high"] < candles[i]["low"]:
                fvgs.append({
                    "type": "BULLISH",
                    "top": candles[i]["low"],
                    "bottom": candles[i-2]["high"],
                    "index": i-1
                })
            # Bearish FVG
            elif candles[i-2]["low"] > candles[i]["high"]:
                fvgs.append({
                    "type": "BEARISH",
                    "top": candles[i-2]["low"],
                    "bottom": candles[i]["high"],
                    "index": i-1
                })
        return fvgs

    def detect_structure(self, candles: List[dict]) -> StructureResult:
        """Main detection logic for VIL 2.0 Structural Detection."""
        if len(candles) < 20:
            return StructureResult(StructuralBias.NEUTRAL, 0.0)

        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        closes = [c["close"] for c in candles]
        
        swing_highs = self.get_swing_highs(highs)
        swing_lows = self.get_swing_lows(lows)
        
        if not swing_highs or not swing_lows:
            return StructureResult(StructuralBias.NEUTRAL, 20.0)

        curr_price = closes[-1]
        last_sh = swing_highs[-1]["price"]
        last_sl = swing_lows[-1]["price"]
        
        # ── 1. Break of Structure (BOS) ──────────────────────────────────
        # Price closes above historical high or below historical low in trend
        bos = None
        choch = None
        bias = StructuralBias.NEUTRAL
        strength = 50.0
        
        # Determine current trend to classify BOS vs CHOCH
        # Simple check: is price making higher highs/lows?
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            prev_sh = swing_highs[-2]["price"]
            prev_sl = swing_lows[-2]["price"]
            
            if curr_price > last_sh:
                if last_sh > prev_sh:
                    bos = last_sh
                    bias = StructuralBias.BULLISH
                else:
                    choch = last_sh
                    bias = StructuralBias.BULLISH
                    strength = 70.0 # CHOCH is stronger reversal
            elif curr_price < last_sl:
                if last_sl < prev_sl:
                    bos = last_sl
                    bias = StructuralBias.BEARISH
                else:
                    choch = last_sl
                    bias = StructuralBias.BEARISH
                    strength = 70.0
        
        # ── 2. Displacement Score ────────────────────────────────────────
        # Large candles (relative to ATR) confirm structural breaks
        recent_candle = candles[-1]
        body_size = abs(recent_candle["close"] - recent_candle["open"])
        # Simple estimate of displacement if body is > 1.5x average body
        avg_body = sum(abs(c["close"] - c["open"]) for c in candles[-10:]) / 10
        disp_score = (body_size / avg_body) * 50 if avg_body > 0 else 0
        
        # ── 3. Liquidity Sweep ───────────────────────────────────────────
        # Wicks poking past swings then reversing
        sweep = False
        if recent_candle["high"] > last_sh and recent_candle["close"] < last_sh:
            sweep = True
        elif recent_candle["low"] < last_sl and recent_candle["close"] > last_sl:
            sweep = True

        # Final score adjustments
        if bos: strength += 10
        if sweep: strength += 20
        if disp_score > 60: strength += 10
        
        return StructureResult(
            bias=bias,
            strength=round(min(100, strength), 1),
            last_bos=bos,
            last_choch=choch,
            displacement_score=round(disp_score, 1),
            liquidity_sweep=sweep,
            details={
                "sh_count": len(swing_highs),
                "sl_count": len(swing_lows),
                "fvg_present": len(self.detect_fvg(candles[-5:])) > 0
            }
        )
