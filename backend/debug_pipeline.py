import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to sys.path so we can import app modules
sys.path.append(os.getcwd())

from app.config import settings
from app.services.data_ingestion import (
    get_data_provider,
    compute_atr,
    compute_adx,
    compute_rsi,
)
from app.services.preselection import rank_pairs
from app.services.regime_gates import run_all_gates
from app.services.regime_classifier import classify_regime
from app.services.signal_scorer import score_signal
from app.services.risk_engine import calculate_position

ALL_SYMBOLS = [
    "EUR_USD", "GBP_USD", "USD_JPY"
]

BASE_CURRENCIES = {
    "EUR_USD": "EUR", "GBP_USD": "GBP", "USD_JPY": "USD"
}

QUOTE_CURRENCIES = {
    "EUR_USD": "USD", "GBP_USD": "USD", "USD_JPY": "JPY"
}

async def debug_pipeline():
    print(f"[{datetime.now()}] Starting DEBUG Pipeline...")
    
    provider_name = "oanda" if settings.OANDA_API_KEY else "mock"
    print(f"Provider: {provider_name}")
    provider = get_data_provider(provider_name)

    # 1. Pre-selection
    print("\n--- Step 1: Pre-selection ---")
    ranked = await rank_pairs(
        ALL_SYMBOLS,
        base_currencies=BASE_CURRENCIES,
        quote_currencies=QUOTE_CURRENCIES,
        timeframe="H1",
        candle_limit=50,
    )
    print(f"Ranked {len(ranked)} pairs.")
    for r in ranked:
        print(f"  {r['symbol']}: Score={r['score']} (Vol={r['volatility']}, Trend={r['trend']}, Mom={r['momentum']})")

    candidates = ranked[:3]
    print(f"\nProcessing top {len(candidates)} candidates...")

    for candidate in candidates:
        symbol = candidate["symbol"]
        print(f"\n=== Processing {symbol} ===")
        
        try:
            # 2. Fetch Candles
            candles = await provider.fetch_ohlcv(symbol, "H1", 100)
            print(f"Fetched {len(candles)} candles.")
            if len(candles) < 50:
                print("  SKIP: Insufficient candles.")
                continue

            # 3. Indicators
            atr_vals = compute_atr(candles)
            adx_vals = compute_adx(candles)
            rsi_vals = compute_rsi(candles)
            
            latest = candles[-1]
            price = latest["close"]
            atr = atr_vals[-1]
            adx = adx_vals[-1]
            rsi = rsi_vals[-1]
            
            print(f"  Price: {price}")
            print(f"  ATR: {atr:.5f} ({(atr/price)*100:.3f}%)")
            print(f"  ADX: {adx:.2f}")
            print(f"  RSI: {rsi:.2f}")

            # 4. Gates
            closes = [c["close"] for c in candles]
            highs = [c["high"] for c in candles]
            lows = [c["low"] for c in candles]

            passed, gate_results = run_all_gates(
                price=price,
                atr=atr,
                adx=adx,
                rsi=rsi,
                highs=highs,
                lows=lows,
                closes=closes,
                atr_history=atr_vals[-30:],
            )
            
            print("  --- Gate Results ---")
            for g in gate_results:
                status = "PASS" if g.passed else "FAIL"
                print(f"    {g.name}: {status} (Conf: {g.confidence}) - {g.reason}")

            if not passed:
                print("  SKIP: Gates failed.")
                continue

            # 5. Regime
            regime_result = classify_regime(
                adx=adx,
                atr=atr,
                price=price,
                atr_history=atr_vals[-30:],
            )
            print(f"  Regime: {regime_result['regime'].value} (Conf: {regime_result['confidence']})")

            # 6. Risk Engine
            direction = candidate.get("direction_bias", "NEUTRAL")
            if direction == "NEUTRAL":
                direction = "BUY" if rsi < 50 else "SELL"
            
            swing_high = max(highs[-20:])
            swing_low = min(lows[-20:])
            
            position = calculate_position(
                direction=direction,
                entry=price,
                atr=atr,
                regime=regime_result["regime"].value,
                symbol=symbol,
                account_balance=10000.0,
                risk_pct=1.0,
                swing_high=swing_high,
                swing_low=swing_low,
            )
            print(f"  Position: {direction} Size={position.position_size} SL={position.stop_loss} TP={position.take_profit}")

            # 7. Scoring
            scores = score_signal(
                gate_results=gate_results,
                preselection_score=candidate["score"],
                regime=regime_result["regime"].value,
                regime_confidence=regime_result["confidence"],
                rsi=rsi,
                adx=adx,
                risk_reward=position.risk_reward,
            )
            final_score = scores["final_score"]
            print(f"  Final Score: {final_score}")

            if final_score < 40.0:
                print("  SKIP: Score too low.")
            else:
                print("  SUCCESS: Signal generated.")

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_pipeline())
