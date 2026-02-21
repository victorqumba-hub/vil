"""Asset Manager — Defines asset profiles, class parameters, and the full symbol registry."""

from enum import Enum
from pydantic import BaseModel
from typing import Dict, List, Optional


class AssetClass(Enum):
    FOREX = "forex"
    INDEX = "index"
    COMMODITY = "commodity"
    METAL = "metal"
    CRYPTO = "crypto"


class AssetProfile(BaseModel):
    asset_class: AssetClass
    tier: int = 1  # 1: Major, 2: Minor/Cross, 3: Exotic
    volatility_multiplier: float = 1.0
    atr_period: int = 14
    regime_sensitivity: float = 1.0
    breakout_weight: float = 1.0
    mean_reversion_weight: float = 1.0
    trend_weight: float = 1.0
    event_weight: float = 1.0
    news_impact_weight: float = 1.0
    spread_filter: float = 0.0005  # Standard FX spread filter
    risk_reduction_coeff: float = 1.0


# ── Parameter Maps for Asset Classes ─────────────────────────────────────────

CLASS_PROFILES = {
    AssetClass.FOREX: AssetProfile(
        asset_class=AssetClass.FOREX,
        trend_weight=1.0,
        breakout_weight=1.0,
        mean_reversion_weight=1.0,
        event_weight=1.2,
        news_impact_weight=1.2,
    ),
    AssetClass.INDEX: AssetProfile(
        asset_class=AssetClass.INDEX,
        volatility_multiplier=1.2,
        trend_weight=1.5,
        breakout_weight=1.5,
        mean_reversion_weight=0.5,
        event_weight=1.5,
        news_impact_weight=1.8,  # FOMC, CPI, NFP, ECB very impactful
        spread_filter=0.001,
    ),
    AssetClass.COMMODITY: AssetProfile(
        asset_class=AssetClass.COMMODITY,
        regime_sensitivity=1.2,
        trend_weight=1.5,
        breakout_weight=1.5,
        mean_reversion_weight=0.5,
        event_weight=1.0,
        news_impact_weight=1.0,
        spread_filter=0.002,
    ),
    AssetClass.METAL: AssetProfile(
        asset_class=AssetClass.METAL,
        trend_weight=1.2,
        breakout_weight=1.0,
        mean_reversion_weight=1.0,
        event_weight=1.2,
        news_impact_weight=1.2,  # Dollar correlation, macro bias
        spread_filter=0.001,
    ),
    AssetClass.CRYPTO: AssetProfile(
        asset_class=AssetClass.CRYPTO,
        volatility_multiplier=2.5,
        atr_period=20,
        regime_sensitivity=1.5,
        trend_weight=2.0,
        breakout_weight=2.0,
        mean_reversion_weight=0.2,
        event_weight=0.5,
        news_impact_weight=0.5,
        spread_filter=0.005,
        risk_reduction_coeff=0.5,
    ),
}

# ── Exotic Forex Overrides ───────────────────────────────────────────────────

EXOTIC_FOREX_PROFILE = AssetProfile(
    asset_class=AssetClass.FOREX,
    tier=3,
    volatility_multiplier=1.3,
    spread_filter=0.003,
    risk_reduction_coeff=0.7,
    trend_weight=1.0,
    breakout_weight=1.0,
    mean_reversion_weight=0.8,
    event_weight=1.0,
    news_impact_weight=1.0,
)


# ── Full Symbol Registry ────────────────────────────────────────────────────

SYMBOL_REGISTRY: Dict[str, AssetClass] = {
    # ── Forex Majors (Tier 1) ────────────────────────────────────────────
    "EUR_USD": AssetClass.FOREX,
    "GBP_USD": AssetClass.FOREX,
    "USD_JPY": AssetClass.FOREX,
    "USD_CHF": AssetClass.FOREX,
    "AUD_USD": AssetClass.FOREX,
    "USD_CAD": AssetClass.FOREX,
    "NZD_USD": AssetClass.FOREX,

    # ── Forex Minors / Crosses (Tier 2) ──────────────────────────────────
    "EUR_GBP": AssetClass.FOREX,
    "EUR_JPY": AssetClass.FOREX,
    "GBP_JPY": AssetClass.FOREX,
    "AUD_JPY": AssetClass.FOREX,
    "GBP_AUD": AssetClass.FOREX,
    "EUR_AUD": AssetClass.FOREX,
    "CHF_JPY": AssetClass.FOREX,
    "EUR_CAD": AssetClass.FOREX,
    "GBP_CAD": AssetClass.FOREX,
    "AUD_NZD": AssetClass.FOREX,
    "NZD_JPY": AssetClass.FOREX,
    "GBP_NZD": AssetClass.FOREX,
    "EUR_NZD": AssetClass.FOREX,
    "CAD_JPY": AssetClass.FOREX,
    "AUD_CAD": AssetClass.FOREX,
    "GBP_CHF": AssetClass.FOREX,
    "EUR_CHF": AssetClass.FOREX,

    # ── Forex Exotics (Tier 3) ───────────────────────────────────────────
    "USD_ZAR": AssetClass.FOREX,
    "USD_TRY": AssetClass.FOREX,
    "USD_MXN": AssetClass.FOREX,
    "EUR_TRY": AssetClass.FOREX,
    "USD_SGD": AssetClass.FOREX,
    "USD_HKD": AssetClass.FOREX,

    # ── Global Indices ───────────────────────────────────────────────────
    "SPX500_USD": AssetClass.INDEX,   # S&P 500
    "NAS100_USD": AssetClass.INDEX,   # NASDAQ 100
    "US30_USD":   AssetClass.INDEX,   # Dow Jones
    "DE30_EUR":   AssetClass.INDEX,   # DAX 40
    "UK100_GBP":  AssetClass.INDEX,   # FTSE 100
    "JP225_USD":  AssetClass.INDEX,   # Nikkei 225
    "AU200_AUD":  AssetClass.INDEX,   # ASX 200
    "HK33_HKD":  AssetClass.INDEX,   # Hang Seng 33
    "EU50_EUR":   AssetClass.INDEX,   # Euro Stoxx 50

    # ── Commodities — Energy ─────────────────────────────────────────────
    "BCO_USD":    AssetClass.COMMODITY,  # Brent Crude
    "WTICO_USD":  AssetClass.COMMODITY,  # WTI Crude
    "NATGAS_USD": AssetClass.COMMODITY,  # Natural Gas

    # ── Commodities — Agricultural ───────────────────────────────────────
    "WHEAT_USD":  AssetClass.COMMODITY,
    "CORN_USD":   AssetClass.COMMODITY,
    "SUGAR_USD":  AssetClass.COMMODITY,
    "SOYBN_USD":  AssetClass.COMMODITY,

    # ── Precious Metals ──────────────────────────────────────────────────
    "XAU_USD": AssetClass.METAL,   # Gold
    "XAG_USD": AssetClass.METAL,   # Silver
    "XPT_USD": AssetClass.METAL,   # Platinum
    "XPD_USD": AssetClass.METAL,   # Palladium

    # ── Crypto CFDs ──────────────────────────────────────────────────────
    "BTC_USD": AssetClass.CRYPTO,
    "ETH_USD": AssetClass.CRYPTO,
    "LTC_USD": AssetClass.CRYPTO,
    "BCH_USD": AssetClass.CRYPTO,
}


# ── Tier Classification ──────────────────────────────────────────────────────

TIER_1_SYMBOLS = {
    # Forex Majors
    "EUR_USD", "GBP_USD", "USD_JPY", "USD_CHF", "AUD_USD", "USD_CAD", "NZD_USD",
    # Flagship others
    "XAU_USD", "SPX500_USD", "NAS100_USD", "WTICO_USD", "BTC_USD",
}

TIER_3_SYMBOLS = {
    # Forex Exotics
    "USD_ZAR", "USD_TRY", "USD_MXN", "EUR_TRY", "USD_SGD", "USD_HKD",
}

# Display-friendly names for the UI
DISPLAY_NAMES = {
    "EUR_USD": "EUR/USD", "GBP_USD": "GBP/USD", "USD_JPY": "USD/JPY",
    "USD_CHF": "USD/CHF", "AUD_USD": "AUD/USD", "USD_CAD": "USD/CAD",
    "NZD_USD": "NZD/USD", "EUR_GBP": "EUR/GBP", "EUR_JPY": "EUR/JPY",
    "GBP_JPY": "GBP/JPY", "AUD_JPY": "AUD/JPY", "GBP_AUD": "GBP/AUD",
    "EUR_AUD": "EUR/AUD", "CHF_JPY": "CHF/JPY", "EUR_CAD": "EUR/CAD",
    "GBP_CAD": "GBP/CAD", "AUD_NZD": "AUD/NZD", "NZD_JPY": "NZD/JPY",
    "GBP_NZD": "GBP/NZD", "EUR_NZD": "EUR/NZD", "CAD_JPY": "CAD/JPY",
    "AUD_CAD": "AUD/CAD", "GBP_CHF": "GBP/CHF", "EUR_CHF": "EUR/CHF",
    "USD_ZAR": "USD/ZAR", "USD_TRY": "USD/TRY", "USD_MXN": "USD/MXN",
    "EUR_TRY": "EUR/TRY", "USD_SGD": "USD/SGD", "USD_HKD": "USD/HKD",
    "SPX500_USD": "SPX500", "NAS100_USD": "NAS100", "US30_USD": "US30",
    "DE30_EUR": "DAX40", "UK100_GBP": "FTSE100", "JP225_USD": "JP225",
    "AU200_AUD": "AUS200", "HK33_HKD": "HK33", "EU50_EUR": "EU50",
    "BCO_USD": "Brent Crude", "WTICO_USD": "WTI Crude",
    "NATGAS_USD": "Natural Gas",
    "WHEAT_USD": "Wheat", "CORN_USD": "Corn",
    "SUGAR_USD": "Sugar", "SOYBN_USD": "Soybeans",
    "XAU_USD": "XAU/USD", "XAG_USD": "XAG/USD",
    "XPT_USD": "XPT/USD", "XPD_USD": "XPD/USD",
    "BTC_USD": "BTC/USD", "ETH_USD": "ETH/USD",
    "LTC_USD": "LTC/USD", "BCH_USD": "BCH/USD",
}


class AssetManager:
    @staticmethod
    def get_profile(symbol: str) -> AssetProfile:
        """Get the full AssetProfile for a given OANDA symbol."""
        asset_class = SYMBOL_REGISTRY.get(symbol, AssetClass.FOREX)

        # Exotic forex pairs get their own adjusted profile
        if symbol in TIER_3_SYMBOLS and asset_class == AssetClass.FOREX:
            return EXOTIC_FOREX_PROFILE.model_copy()

        profile = CLASS_PROFILES.get(asset_class, CLASS_PROFILES[AssetClass.FOREX]).model_copy()

        # Tier assignment
        if symbol in TIER_1_SYMBOLS:
            profile.tier = 1
        elif symbol in TIER_3_SYMBOLS:
            profile.tier = 3
        else:
            profile.tier = 2

        return profile

    @staticmethod
    def get_all_symbols() -> List[str]:
        """Return all registered OANDA symbols."""
        return list(SYMBOL_REGISTRY.keys())

    @staticmethod
    def get_symbols_by_class(asset_class: AssetClass) -> List[str]:
        """Return symbols filtered by asset class."""
        return [sym for sym, cls in SYMBOL_REGISTRY.items() if cls == asset_class]

    @staticmethod
    def get_display_name(symbol: str) -> str:
        """Get a human-friendly display name for a symbol."""
        return DISPLAY_NAMES.get(symbol, symbol.replace("_", "/"))

    @staticmethod
    def get_asset_class(symbol: str) -> str:
        """Get the asset class string for a symbol."""
        return SYMBOL_REGISTRY.get(symbol, AssetClass.FOREX).value
