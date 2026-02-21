import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to sys.path so we can import app modules
sys.path.append(os.getcwd())

from dotenv import load_dotenv

# Load environment variables first
load_dotenv(os.path.join(os.path.dirname(__file__), 'app', '.env'))

from app.services.data_ingestion import get_data_provider
from app.services.asset_manager import AssetManager, AssetClass

async def main():
    print("--- Starting Multi-Asset Verification ---")
    
    # diverse set of symbols to test
    test_symbols = [
        "EUR_USD",      # Forex Major
        "GBP_JPY",      # Forex Cross
        "USD_MXN",      # Forex Exotic
        "SPX500_USD",   # Index
        "NAS100_USD",   # Index
        "XAU_USD",      # Metal
        "WTICO_USD",    # Oil
        "BTC_USD",      # Crypto
        "ETH_USD",      # Crypto
    ]

    provider = get_data_provider("oanda")
    print(f"Using Provider: {provider.__class__.__name__}")
    
    results = {}

    for symbol in test_symbols:
        print(f"\nTesting {symbol}...")
        try:
            # 1. Check Asset Profile
            profile = AssetManager.get_profile(symbol)
            print(f"  - Class: {profile.asset_class.value}")
            print(f"  - Tier: {profile.tier}")
            
            # 2. Fetch Candles (Get more for indicators)
            candles = await provider.fetch_ohlcv(symbol, timeframe="H1", limit=100)
            if candles:
                print(f"  - Fetch SUCCESS: Got {len(candles)} candles")
                print(f"  - Latest Close: {candles[-1]['close']}")
                
                # 3. Real Pipeline Processing
                # Instantiate Engines
                from app.services.regime_classifier import classify_regime, Regime
                from app.services.structure_engine import StructureEngine
                from app.services.liquidity_engine import LiquidityEngine
                from app.services.regime_gates import run_all_gates
                from app.services.signal_scorer import score_signal
                from app.services.data_ingestion import compute_atr, compute_adx, compute_rsi

                struct_engine = StructureEngine()
                liq_engine = LiquidityEngine()

                # Indicators
                atr_vals = compute_atr(candles, period=profile.atr_period)
                adx_vals = compute_adx(candles, period=profile.atr_period)
                rsi_vals = compute_rsi(candles, period=profile.atr_period)
                
                latest = candles[-1]
                price = latest["close"]
                atr = atr_vals[-1] * profile.volatility_multiplier
                adx = adx_vals[-1]
                rsi = rsi_vals[-1]
                atr_hist = atr_vals[-30:]

                # Layer 5: Regime
                regime_res = classify_regime(adx, atr, price, atr_hist, sensitivity=profile.regime_sensitivity)
                regime = regime_res["regime"]
                print(f"  - Regime: {regime.value} ({regime_res['confidence']}%)")

                closes = [c["close"] for c in candles]
                highs = [c["high"] for c in candles]
                lows = [c["low"] for c in candles]

                # Layer 6: Structure
                bias = struct_engine.analyze_structure(highs, lows, closes)
                print(f"  - Structure: {bias.direction} ({bias.reason})")

                # Layer 7: Liquidity
                # Mock spread for verification as we don't fetch ticks here usually
                spread = price * 0.0001 
                # Re-find swings for liquidity
                temp_sh = struct_engine._find_swing_highs(highs)
                temp_sl = struct_engine._find_swing_lows(lows)
                sh_prices = [p.price for p in temp_sh]
                sl_prices = [p.price for p in temp_sl]
                
                liq = liq_engine.analyze_liquidity(highs, lows, closes, atr, spread, profile.spread_filter, sh_prices, sl_prices)
                print(f"  - Liquidity: {liq.volatility_state} (Sweep: {liq.sweep_detected})")

                # Gates
                passed, gates = run_all_gates(price, atr, adx, rsi, highs, lows, closes, atr_hist, spread_filter=profile.spread_filter)
                print(f"  - Gates Passed: {passed}")

                # Layer 8: Scoring
                # Alignment
                direction = "BUY" if bias.direction == "BULLISH" else ("SELL" if bias.direction == "BEARISH" else "NEUTRAL")
                regime_align = True # Simplified for test
                
                scores = score_signal(
                    gate_results=gates,
                    regime_confidence=regime_res["confidence"],
                    regime_align=regime_align,
                    structure_confidence=bias.confidence,
                    structure_align=True,
                    volatility_score=100.0 if liq.volatility_state == "EXPANSION" else 50.0,
                    liquidity_score=liq.liquidity_score,
                    event_risk_score=100.0,
                    asset_profile_weights=profile.dict()
                )
                print(f"  - Final Score: {scores['final_score']}")

                results[symbol] = f"SUCCESS (Score: {scores['final_score']})"
            else:
                print("  - Fetch FAILED: No candles returned")
                results[symbol] = "FAILED (No Data)"
                
        except Exception as e:
            print(f"  - ERROR: {e}")
            results[symbol] = f"ERROR: {str(e)}"

    print("\n--- Summary ---")
    for sym, res in results.items():
        print(f"{sym}: {res}")

if __name__ == "__main__":
    asyncio.run(main())
