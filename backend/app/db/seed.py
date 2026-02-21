"""Database seeder — populates tables with realistic sample data."""

import asyncio
import random
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session, init_db
from app.db.models import (
    AIReport,
    Asset,
    AssetType,
    MarketData,
    MarketRegime,
    Signal,
    SignalDirection,
    Timeframe,
    Trade,
    TradeStatus,
    User,
    UserRole,
)
from app.api.auth import _hash_password


ASSETS = [
    # ── Forex Majors (Tier 1) ────────────────────────────────────────────
    ("EUR_USD", AssetType.FOREX, "EUR", "USD", "Euro / US Dollar"),
    ("GBP_USD", AssetType.FOREX, "GBP", "USD", "British Pound / US Dollar"),
    ("USD_JPY", AssetType.FOREX, "USD", "JPY", "US Dollar / Japanese Yen"),
    ("AUD_USD", AssetType.FOREX, "AUD", "USD", "Australian Dollar / US Dollar"),
    ("USD_CHF", AssetType.FOREX, "USD", "CHF", "US Dollar / Swiss Franc"),
    ("USD_CAD", AssetType.FOREX, "USD", "CAD", "US Dollar / Canadian Dollar"),
    ("NZD_USD", AssetType.FOREX, "NZD", "USD", "New Zealand Dollar / US Dollar"),

    # ── Forex Minors / Crosses (Tier 2) ──────────────────────────────────
    ("EUR_GBP", AssetType.FOREX, "EUR", "GBP", "Euro / British Pound"),
    ("EUR_JPY", AssetType.FOREX, "EUR", "JPY", "Euro / Japanese Yen"),
    ("GBP_JPY", AssetType.FOREX, "GBP", "JPY", "British Pound / Japanese Yen"),
    ("AUD_JPY", AssetType.FOREX, "AUD", "JPY", "Australian Dollar / Japanese Yen"),
    ("GBP_AUD", AssetType.FOREX, "GBP", "AUD", "British Pound / Australian Dollar"),
    ("EUR_AUD", AssetType.FOREX, "EUR", "AUD", "Euro / Australian Dollar"),
    ("CHF_JPY", AssetType.FOREX, "CHF", "JPY", "Swiss Franc / Japanese Yen"),
    ("EUR_CAD", AssetType.FOREX, "EUR", "CAD", "Euro / Canadian Dollar"),
    ("GBP_CAD", AssetType.FOREX, "GBP", "CAD", "British Pound / Canadian Dollar"),
    ("AUD_NZD", AssetType.FOREX, "AUD", "NZD", "Australian Dollar / New Zealand Dollar"),
    ("NZD_JPY", AssetType.FOREX, "NZD", "JPY", "New Zealand Dollar / Japanese Yen"),
    ("GBP_NZD", AssetType.FOREX, "GBP", "NZD", "British Pound / New Zealand Dollar"),
    ("EUR_NZD", AssetType.FOREX, "EUR", "NZD", "Euro / New Zealand Dollar"),
    ("CAD_JPY", AssetType.FOREX, "CAD", "JPY", "Canadian Dollar / Japanese Yen"),
    ("AUD_CAD", AssetType.FOREX, "AUD", "CAD", "Australian Dollar / Canadian Dollar"),
    ("GBP_CHF", AssetType.FOREX, "GBP", "CHF", "British Pound / Swiss Franc"),
    ("EUR_CHF", AssetType.FOREX, "EUR", "CHF", "Euro / Swiss Franc"),

    # ── Forex Exotics (Tier 3) ───────────────────────────────────────────
    ("USD_ZAR", AssetType.FOREX, "USD", "ZAR", "US Dollar / South African Rand"),
    ("USD_TRY", AssetType.FOREX, "USD", "TRY", "US Dollar / Turkish Lira"),
    ("USD_MXN", AssetType.FOREX, "USD", "MXN", "US Dollar / Mexican Peso"),
    ("EUR_TRY", AssetType.FOREX, "EUR", "TRY", "Euro / Turkish Lira"),
    ("USD_SGD", AssetType.FOREX, "USD", "SGD", "US Dollar / Singapore Dollar"),
    ("USD_HKD", AssetType.FOREX, "USD", "HKD", "US Dollar / Hong Kong Dollar"),

    # ── Global Indices ───────────────────────────────────────────────────
    ("SPX500_USD", AssetType.INDEX, "SPX500", "USD", "S&P 500 Index"),
    ("NAS100_USD", AssetType.INDEX, "NAS100", "USD", "NASDAQ 100 Index"),
    ("US30_USD",   AssetType.INDEX, "US30",   "USD", "Dow Jones Industrial Average"),
    ("DE30_EUR",   AssetType.INDEX, "DE30",   "EUR", "DAX 40 Index"),
    ("UK100_GBP",  AssetType.INDEX, "UK100",  "GBP", "FTSE 100 Index"),
    ("JP225_USD",  AssetType.INDEX, "JP225",  "USD", "Nikkei 225 Index"),
    ("AU200_AUD",  AssetType.INDEX, "AU200",  "AUD", "ASX 200 Index"),
    ("HK33_HKD",   AssetType.INDEX, "HK33",   "HKD", "Hang Seng 33 Index"),
    ("EU50_EUR",   AssetType.INDEX, "EU50",   "EUR", "Euro Stoxx 50 Index"),

    # ── Commodities — Energy ─────────────────────────────────────────────
    ("BCO_USD",    AssetType.COMMODITY, "BCO",    "USD", "Brent Crude Oil"),
    ("WTICO_USD",  AssetType.COMMODITY, "WTICO",  "USD", "WTI Crude Oil"),
    ("NATGAS_USD", AssetType.COMMODITY, "NATGAS", "USD", "Natural Gas"),

    # ── Commodities — Agricultural ───────────────────────────────────────
    ("WHEAT_USD",  AssetType.COMMODITY, "WHEAT",  "USD", "Wheat"),
    ("CORN_USD",   AssetType.COMMODITY, "CORN",   "USD", "Corn"),
    ("SUGAR_USD",  AssetType.COMMODITY, "SUGAR",  "USD", "Sugar"),
    ("SOYBN_USD",  AssetType.COMMODITY, "SOYBN",  "USD", "Soybeans"),

    # ── Precious Metals ──────────────────────────────────────────────────
    ("XAU_USD", AssetType.METAL, "XAU", "USD", "Gold / US Dollar"),
    ("XAG_USD", AssetType.METAL, "XAG", "USD", "Silver / US Dollar"),
    ("XPT_USD", AssetType.METAL, "XPT", "USD", "Platinum / US Dollar"),
    ("XPD_USD", AssetType.METAL, "XPD", "USD", "Palladium / US Dollar"),

    # ── Crypto CFDs ──────────────────────────────────────────────────────
    ("BTC_USD", AssetType.CRYPTO, "BTC", "USD", "Bitcoin / US Dollar"),
    ("ETH_USD", AssetType.CRYPTO, "ETH", "USD", "Ethereum / US Dollar"),
    ("LTC_USD", AssetType.CRYPTO, "LTC", "USD", "Litecoin / US Dollar"),
    ("BCH_USD", AssetType.CRYPTO, "BCH", "USD", "Bitcoin Cash / US Dollar"),
]

# Base prices for seed market data generation
BASE_PRICES = {
    "EUR_USD": 1.0877, "GBP_USD": 1.2653, "USD_JPY": 150.43,
    "AUD_USD": 0.6544, "USD_CHF": 0.8765, "USD_CAD": 1.3542,
    "NZD_USD": 0.6120, "EUR_GBP": 0.8590, "EUR_JPY": 163.50,
    "GBP_JPY": 190.20, "AUD_JPY": 98.40, "GBP_AUD": 1.9330,
    "EUR_AUD": 1.6620, "CHF_JPY": 171.60, "EUR_CAD": 1.4720,
    "GBP_CAD": 1.7130, "AUD_NZD": 1.0690, "NZD_JPY": 92.10,
    "GBP_NZD": 2.0680, "EUR_NZD": 1.7780, "CAD_JPY": 111.00,
    "AUD_CAD": 0.8830, "GBP_CHF": 1.1130, "EUR_CHF": 0.9530,
    "USD_ZAR": 18.65, "USD_TRY": 30.85, "USD_MXN": 17.12,
    "EUR_TRY": 33.55, "USD_SGD": 1.3420, "USD_HKD": 7.8150,
    "SPX500_USD": 5025.5, "NAS100_USD": 17650.0, "US30_USD": 38450.0,
    "DE30_EUR": 17200.0, "UK100_GBP": 7650.0, "JP225_USD": 38750.0,
    "AU200_AUD": 7680.0, "HK33_HKD": 16450.0, "EU50_EUR": 4750.0,
    "BCO_USD": 82.50, "WTICO_USD": 78.30, "NATGAS_USD": 2.45,
    "WHEAT_USD": 5.85, "CORN_USD": 4.52, "SUGAR_USD": 0.2150,
    "SOYBN_USD": 12.35,
    "XAU_USD": 2045.5, "XAG_USD": 23.15, "XPT_USD": 920.0, "XPD_USD": 980.0,
    "BTC_USD": 95420.0, "ETH_USD": 3245.0, "LTC_USD": 72.50, "BCH_USD": 245.0,
}


async def seed() -> None:
    await init_db()
    async with async_session() as db:
        # ── Demo user ────────────────────────────────────────────
        # Check if users exist
        stmt = select(User).where(User.email == "demo@vil.io")
        existing_demo = (await db.execute(stmt)).scalar_one_or_none()
        
        if not existing_demo:
            demo = User(
                email="demo@vil.io",
                password_hash=_hash_password("DemoTrader@2026"),
                full_name="Demo Trader",
                display_name="Demo",
                role=UserRole.USER,
                is_verified=True,
                is_active=True,
                terms_accepted_at=datetime.utcnow(),
            )
            db.add(demo)
            
        stmt = select(User).where(User.email == "admin@vil.io")
        existing_admin = (await db.execute(stmt)).scalar_one_or_none()
        
        if not existing_admin:
            admin = User(
                email="admin@vil.io",
                password_hash=_hash_password("AdminVIL@2026!"),
                full_name="VIL Administrator",
                display_name="Admin",
                role=UserRole.ADMIN,
                is_verified=True,
                is_active=True,
                terms_accepted_at=datetime.utcnow(),
            )
            db.add(admin)
            
        await db.flush()

        # ── Assets ───────────────────────────────────────────────
        asset_objs: list[Asset] = []
        for sym, atype, base, quote, desc in ASSETS:
            # Check if asset exists
            stmt = select(Asset).where(Asset.symbol == sym)
            existing_asset = (await db.execute(stmt)).scalar_one_or_none()
            
            if not existing_asset:
                a = Asset(
                    symbol=sym,
                    asset_type=atype,
                    base_currency=base,
                    quote_currency=quote,
                    description=desc,
                )
                asset_objs.append(a)
                db.add(a)
            else:
                asset_objs.append(existing_asset)
                
        await db.flush()

        now = datetime.utcnow()

        # ── Market data (H1 candles, ~200 per asset) ─────────────
        for asset in asset_objs:
            base_price = BASE_PRICES.get(asset.symbol, 1.0)

            price = base_price
            candles = []
            for i in range(200):
                o = price
                h = o * (1 + random.uniform(0, 0.003))
                l = o * (1 - random.uniform(0, 0.003))
                c = random.uniform(l, h)
                price = c
                candles.append(
                    MarketData(
                        asset_id=asset.id,
                        timeframe=Timeframe.H1,
                        open=round(o, 5),
                        high=round(h, 5),
                        low=round(l, 5),
                        close=round(c, 5),
                        volume=round(random.uniform(500, 5000), 0),
                        atr=round(abs(h - l), 5),
                        adx=round(random.uniform(15, 60), 1),
                        rsi=round(random.uniform(25, 75), 1),
                        timestamp=now - timedelta(hours=200 - i),
                    )
                )
            db.add_all(candles)

        await db.flush()

        # ── Signals (generated by OANDA pipeline only) ────────────
        # No mock signals — the OANDA pipeline produces real signals.

        await db.commit()
        print("[OK] Database seeded successfully!")
        print(f"   Users: 2 (demo@vil.io / admin@vil.io)")
        print(f"   Assets: {len(asset_objs)}")
        print(f"   Market data candles: {len(asset_objs) * 200}")


if __name__ == "__main__":
    asyncio.run(seed())
