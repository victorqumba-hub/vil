"""Non-essential endpoints: news, calendar, quotes, tools."""

from datetime import datetime, timedelta
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["extras"])


# ── Forex Economic Calendar (Mock) ──────────────────────────────────────────

@router.get("/calendar")
async def economic_calendar():
    """Return mock economic calendar events."""
    now = datetime.utcnow()
    return [
        {
            "time": (now + timedelta(hours=i * 3)).isoformat(),
            "currency": c,
            "event": e,
            "impact": imp,
            "forecast": f,
            "previous": p,
        }
        for i, (c, e, imp, f, p) in enumerate([
            ("USD", "Non-Farm Payrolls", "high", "185K", "175K"),
            ("EUR", "ECB Interest Rate Decision", "high", "4.50%", "4.50%"),
            ("GBP", "CPI y/y", "high", "4.1%", "4.0%"),
            ("JPY", "BOJ Policy Rate", "high", "-0.10%", "-0.10%"),
            ("USD", "FOMC Meeting Minutes", "medium", "", ""),
            ("AUD", "Employment Change", "medium", "25.0K", "14.6K"),
            ("CAD", "GDP m/m", "medium", "0.2%", "0.1%"),
            ("CHF", "SNB Policy Rate", "high", "1.75%", "1.75%"),
        ])
    ]


# ── News Feed (Mock) ────────────────────────────────────────────────────────

@router.get("/news")
async def market_news():
    """Return mock financial news headlines."""
    return [
        {
            "title": "Fed Signals Patience on Rate Cuts as Inflation Stalls",
            "source": "Reuters",
            "category": "central_banks",
            "timestamp": datetime.utcnow().isoformat(),
            "url": "#",
        },
        {
            "title": "EUR/USD Breaks Above 1.0900 on Dovish ECB Outlook",
            "source": "FXStreet",
            "category": "forex",
            "timestamp": datetime.utcnow().isoformat(),
            "url": "#",
        },
        {
            "title": "Gold Pushes to New Highs Amid Geopolitical Tensions",
            "source": "Bloomberg",
            "category": "commodities",
            "timestamp": datetime.utcnow().isoformat(),
            "url": "#",
        },
        {
            "title": "Bitcoin Holds $95K as ETF Inflows Surge",
            "source": "CoinDesk",
            "category": "crypto",
            "timestamp": datetime.utcnow().isoformat(),
            "url": "#",
        },
        {
            "title": "GBP/JPY Volatility Spike After BOJ Commentary",
            "source": "DailyFX",
            "category": "forex",
            "timestamp": datetime.utcnow().isoformat(),
            "url": "#",
        },
    ]


# ── Quotes (Mock) ───────────────────────────────────────────────────────────

@router.get("/quotes")
async def live_quotes():
    """Return mock multi-asset quotes."""
    return [
        {"symbol": "EUR/USD", "bid": 1.0876, "ask": 1.0878, "change": 0.12, "type": "forex"},
        {"symbol": "GBP/USD", "bid": 1.2652, "ask": 1.2655, "change": -0.08, "type": "forex"},
        {"symbol": "USD/JPY", "bid": 150.42, "ask": 150.45, "change": 0.25, "type": "forex"},
        {"symbol": "AUD/USD", "bid": 0.6543, "ask": 0.6546, "change": -0.15, "type": "forex"},
        {"symbol": "XAU/USD", "bid": 2045.50, "ask": 2046.20, "change": 0.65, "type": "commodity"},
        {"symbol": "BTC/USD", "bid": 95420.0, "ask": 95480.0, "change": 1.23, "type": "crypto"},
        {"symbol": "ETH/USD", "bid": 3245.0, "ask": 3248.0, "change": 0.87, "type": "crypto"},
        {"symbol": "US500", "bid": 5025.5, "ask": 5026.0, "change": 0.35, "type": "index"},
    ]


# ── Tools ────────────────────────────────────────────────────────────────────

@router.get("/tools/market-hours")
async def market_hours():
    """Return forex market hours status."""
    now = datetime.utcnow()
    hour = now.hour
    return {
        "utc_now": now.isoformat(),
        "sessions": {
            "sydney": {"open": hour >= 21 or hour < 6, "hours": "21:00 - 06:00 UTC"},
            "tokyo": {"open": 0 <= hour < 9, "hours": "00:00 - 09:00 UTC"},
            "london": {"open": 7 <= hour < 16, "hours": "07:00 - 16:00 UTC"},
            "new_york": {"open": 12 <= hour < 21, "hours": "12:00 - 21:00 UTC"},
        },
    }


@router.get("/tools/converter")
async def currency_converter(
    from_currency: str = "EUR",
    to_currency: str = "USD",
    amount: float = 1.0,
):
    """Simple mock currency converter."""
    mock_rates = {
        "EUR/USD": 1.0877, "GBP/USD": 1.2653, "USD/JPY": 150.43,
        "AUD/USD": 0.6544, "USD/CHF": 0.8765, "USD/CAD": 1.3542,
    }
    pair = f"{from_currency.upper()}/{to_currency.upper()}"
    reverse = f"{to_currency.upper()}/{from_currency.upper()}"

    if pair in mock_rates:
        rate = mock_rates[pair]
    elif reverse in mock_rates:
        rate = 1 / mock_rates[reverse]
    else:
        rate = 1.0

    return {
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "amount": amount,
        "rate": round(rate, 5),
        "result": round(amount * rate, 4),
    }
