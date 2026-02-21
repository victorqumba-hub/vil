"""Pre-Selection Module — Ranks forex pairs by opportunity score.

Evaluates each asset using volatility (ATR), trend strength (ADX),
momentum (RSI), and session relevance to produce a ranked watchlist.
"""

from datetime import datetime
from typing import Any
import asyncio
from app.services.data_ingestion import (
    get_data_provider,
    compute_atr,
    compute_adx,
    compute_rsi,
)


# ── Scoring Weights ──────────────────────────────────────────────────────────

WEIGHTS = {
    "volatility": 0.30,   # Sufficient movement for entries
    "trend":      0.30,   # Directional clarity
    "momentum":   0.20,   # RSI extremes = opp. zones
    "session":    0.20,   # Relevance to active session
}

# ── Session currency affinity ────────────────────────────────────────────────

SESSION_CURRENCIES = {
    "sydney":   {"AUD", "NZD", "JPY"},
    "tokyo":    {"JPY", "AUD", "NZD"},
    "london":   {"EUR", "GBP", "CHF"},
    "new_york": {"USD", "CAD"},
}


def _active_sessions(utc_hour: int) -> list[str]:
    sessions = []
    if 21 <= utc_hour or utc_hour < 6:
        sessions.append("sydney")
    if 0 <= utc_hour < 9:
        sessions.append("tokyo")
    if 7 <= utc_hour < 16:
        sessions.append("london")
    if 12 <= utc_hour < 21:
        sessions.append("new_york")
    return sessions


def _session_relevance(base: str, quote: str, utc_hour: int) -> float:
    """0-100 score based on whether the pair's currencies are session-active."""
    active = _active_sessions(utc_hour)
    if not active:
        return 30.0  # Weekend / off-hours baseline

    relevant_currencies = set()
    for s in active:
        relevant_currencies |= SESSION_CURRENCIES.get(s, set())

    matches = 0
    if base in relevant_currencies:
        matches += 1
    if quote in relevant_currencies:
        matches += 1

    return {0: 20.0, 1: 60.0, 2: 100.0}[matches]


def _volatility_score(atr_pct: float) -> float:
    """Score ATR as % of price. Ideal range: 0.1% – 0.5%."""
    if atr_pct < 0.02:
        return 10.0   # Too quiet
    if atr_pct < 0.08:
        return 40.0
    if atr_pct < 0.15:
        return 70.0
    if atr_pct < 0.40:
        return 100.0  # Sweet spot
    if atr_pct < 0.80:
        return 70.0   # Getting risky
    return 40.0        # Extreme volatility


def _trend_score(adx: float) -> float:
    """ADX-based trend strength. >25 = trending, >40 = strong trend."""
    if adx < 15:
        return 15.0
    if adx < 25:
        return 40.0
    if adx < 35:
        return 70.0
    if adx < 50:
        return 95.0
    return 100.0


def _momentum_score(rsi: float) -> float:
    """RSI extremes create opportunities. 30-70 is neutral; outside = opportunity."""
    if rsi < 20 or rsi > 80:
        return 95.0   # Strong reversal zone
    if rsi < 30 or rsi > 70:
        return 75.0   # Approaching extreme
    if rsi < 40 or rsi > 60:
        return 50.0   # Mild bias
    return 25.0        # Neutral → low opportunity


# ── Main Ranking Function ────────────────────────────────────────────────────

async def _rank_single_symbol(
    symbol: str, 
    provider: Any, 
    timeframe: str, 
    candle_limit: int, 
    utc_hour: int,
    semaphore: asyncio.Semaphore
) -> dict | None:
    """Helper for parallel ranking."""
    async with semaphore:
        try:
            candles = await provider.fetch_ohlcv(symbol, timeframe, candle_limit)
            if len(candles) < 20:
                return None

            atr_vals = compute_atr(candles)
            adx_vals = compute_adx(candles)
            rsi_vals = compute_rsi(candles)

            latest_close = candles[-1]["close"]
            latest_atr = atr_vals[-1]
            latest_adx = adx_vals[-1]
            latest_rsi = rsi_vals[-1]

            atr_pct = (latest_atr / latest_close) * 100 if latest_close else 0

            vol_score = _volatility_score(atr_pct)
            trnd_score = _trend_score(latest_adx)
            mom_score = _momentum_score(latest_rsi)

            # Better handling for Indices/Metals/Crypto base/quote
            if "_" in symbol:
                parts = symbol.split("_")
                base = parts[0]
                quote = parts[1]
            else:
                base = symbol[:3]
                quote = "USD"

            # Session relevance overrides for Global Assets
            if any(x in symbol for x in ["SPX", "NAS", "US30", "XAU", "XAG"]):
                # 80 baseline for major session overlap
                sess_score = 80.0 if (12 <= utc_hour < 21 or 7 <= utc_hour < 16) else 40.0
            elif "BTC" in symbol or "ETH" in symbol:
                sess_score = 100.0 # Crypto 24/7
            else:
                sess_score = _session_relevance(base, quote, utc_hour)

            composite = (
                vol_score * WEIGHTS["volatility"]
                + trnd_score * WEIGHTS["trend"]
                + mom_score * WEIGHTS["momentum"]
                + sess_score * WEIGHTS["session"]
            )

            # Direction bias from RSI
            if latest_rsi < 35:
                bias = "BUY"
            elif latest_rsi > 65:
                bias = "SELL"
            else:
                bias = "NEUTRAL"

            return {
                "symbol": symbol,
                "score": round(composite, 1),
                "volatility": round(vol_score, 1),
                "trend": round(trnd_score, 1),
                "momentum": round(mom_score, 1),
                "session": round(sess_score, 1),
                "direction_bias": bias,
                "atr": round(latest_atr, 5),
                "adx": round(latest_adx, 1),
                "rsi": round(latest_rsi, 1),
            }
        except Exception as e:
            print(f"[Pre-Selection] Error ranking {symbol}: {e}")
            return None


async def rank_pairs(
    symbols: list[str],
    base_currencies: dict[str, str] | None = None,
    quote_currencies: dict[str, str] | None = None,
    timeframe: str = "H1",
    candle_limit: int = 100,
    provider_name: str = "oanda"
) -> list[dict]:
    """
    Rank a list of asset symbols by trading opportunity.
    Parallelized for high throughput.
    """
    import asyncio
    from app.services.data_ingestion import get_data_provider
    provider = get_data_provider(provider_name)
    utc_hour = datetime.utcnow().hour
    
    # Process in parallel with a semaphore to avoid overloading the provider/network
    semaphore = asyncio.Semaphore(10)
    tasks = [
        _rank_single_symbol(s, provider, timeframe, candle_limit, utc_hour, semaphore)
        for s in symbols
    ]
    
    raw_results = await asyncio.gather(*tasks)
    results = [r for r in raw_results if r is not None]

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
