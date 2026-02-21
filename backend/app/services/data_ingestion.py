"""Data Ingestion Layer — Fetches and normalizes market data from providers.

Current implementation uses mock/random data. Real integrations (OANDA, Binance,
etc.) can be swapped in by implementing the abstract methods.
"""

import random
import httpx
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

from app.config import settings


class DataProvider(ABC):
    """Base class for market data providers."""

    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> list[dict]:
        ...

    @abstractmethod
    async def fetch_tick(self, symbol: str) -> dict:
        ...


class MockDataProvider(DataProvider):
    """Generates realistic random OHLCV data for development."""

    BASE_PRICES = {
        # Forex Majors
        "EUR_USD": 1.0877, "GBP_USD": 1.2653, "USD_JPY": 150.43,
        "AUD_USD": 0.6544, "USD_CHF": 0.8765, "USD_CAD": 1.3542,
        "NZD_USD": 0.6120,
        # Forex Minors
        "EUR_GBP": 0.8590, "EUR_JPY": 163.50, "GBP_JPY": 190.20,
        "AUD_JPY": 98.40, "GBP_AUD": 1.9330, "EUR_AUD": 1.6620,
        "CHF_JPY": 171.60, "EUR_CAD": 1.4720, "GBP_CAD": 1.7130,
        "AUD_NZD": 1.0690, "NZD_JPY": 92.10, "GBP_NZD": 2.0680,
        "EUR_NZD": 1.7780, "CAD_JPY": 111.00, "AUD_CAD": 0.8830,
        "GBP_CHF": 1.1130, "EUR_CHF": 0.9530,
        # Forex Exotics
        "USD_ZAR": 18.65, "USD_TRY": 30.85, "USD_MXN": 17.12,
        "EUR_TRY": 33.55, "USD_SGD": 1.3420, "USD_HKD": 7.8150,
        # Indices
        "SPX500_USD": 5025.5, "NAS100_USD": 17650.0, "US30_USD": 38450.0,
        "DE30_EUR": 17200.0, "UK100_GBP": 7650.0, "JP225_USD": 38750.0,
        "AU200_AUD": 7680.0, "HK33_HKD": 16450.0, "EU50_EUR": 4750.0,
        # Commodities
        "BCO_USD": 82.50, "WTICO_USD": 78.30, "NATGAS_USD": 2.45,
        "WHEAT_USD": 5.85, "CORN_USD": 4.52, "SUGAR_USD": 0.2150,
        "SOYBN_USD": 12.35,
        # Metals
        "XAU_USD": 2045.5, "XAG_USD": 23.15, "XPT_USD": 920.0, "XPD_USD": 980.0,
        # Crypto
        "BTC_USD": 95420.0, "ETH_USD": 3245.0, "LTC_USD": 72.50, "BCH_USD": 245.0,
    }

    TIMEFRAME_SECONDS = {
        "M1": 60, "M5": 300, "M15": 900, "M30": 1800,
        "H1": 3600, "H4": 14400, "D1": 86400, "W1": 604800,
    }

    async def fetch_ohlcv(self, symbol: str, timeframe: str = "H1", limit: int = 200) -> list[dict]:
        base = self.BASE_PRICES.get(symbol, 1.0)
        interval = self.TIMEFRAME_SECONDS.get(timeframe, 3600)
        now = datetime.utcnow()
        candles = []
        price = base

        for i in range(limit):
            ts = now - timedelta(seconds=interval * (limit - i))
            volatility = base * 0.002  # 0.2% per candle
            o = price
            move = random.gauss(0, volatility)
            c = o + move
            h = max(o, c) + abs(random.gauss(0, volatility * 0.5))
            l = min(o, c) - abs(random.gauss(0, volatility * 0.5))
            vol = random.uniform(500, 5000)
            price = c

            candles.append({
                "timestamp": ts,
                "open": round(o, 5),
                "high": round(h, 5),
                "low": round(l, 5),
                "close": round(c, 5),
                "volume": round(vol, 0),
            })

        return candles

    async def fetch_tick(self, symbol: str) -> dict:
        base = self.BASE_PRICES.get(symbol, 1.0)
        spread = base * 0.0002  # 2 pip spread approximation
        bid = base + random.gauss(0, base * 0.0005)
        return {
            "symbol": symbol,
            "bid": round(bid, 5),
            "ask": round(bid + spread, 5),
            "timestamp": datetime.utcnow(),
        }


class OANDAProvider(DataProvider):
    """OANDA V20 REST API integration."""

    def __init__(self):
        if not settings.OANDA_API_KEY:
            raise ValueError("OANDA_API_KEY is not set. Cannot initialize OANDAProvider.")
        if not settings.OANDA_ACCOUNT_ID:
            raise ValueError("OANDA_ACCOUNT_ID is not set. Cannot initialize OANDAProvider.")

        self.api_key = settings.OANDA_API_KEY
        self.account_id = settings.OANDA_ACCOUNT_ID
        self.env = settings.OANDA_ENV
        self.base_url = (
            "https://api-fxtrade.oanda.com/v3"
            if self.env == "live"
            else "https://api-fxpractice.oanda.com/v3"
        )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Returns a persistent AsyncClient instance."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    def _map_symbol(self, symbol: str) -> str:
        """Symbols are already in OANDA-native underscore format."""
        return symbol

    def _map_timeframe(self, timeframe: str) -> str:
        mapping = {"D1": "D", "W1": "W"}
        return mapping.get(timeframe, timeframe)

    async def fetch_ohlcv(self, symbol: str, timeframe: str = "H1", limit: int = 200) -> list[dict]:
        if not self.api_key:
            return await MockDataProvider().fetch_ohlcv(symbol, timeframe, limit)

        instrument = self._map_symbol(symbol)
        granularity = self._map_timeframe(timeframe)
        url = f"{self.base_url}/accounts/{self.account_id}/instruments/{instrument}/candles"
        params = {"granularity": granularity, "count": limit}

        print(f"[OANDA] Fetching {limit} candles for {symbol} ({granularity})...")
        try:
            client = await self._get_client()
            resp = await client.get(url, headers=self.headers, params=params)
            if resp.status_code != 200:
                # Limit error text to avoid log flooding with HTML pages
                err_msg = (resp.text[:200] + "...") if len(resp.text) > 200 else resp.text
                print(f"[OANDA] API Error {resp.status_code} for {symbol}: {err_msg}")
                return await MockDataProvider().fetch_ohlcv(symbol, timeframe, limit)

            data = resp.json()
            candles = []
            for c in data.get("candles", []):
                if not c.get("complete"):
                    continue
                mid = c.get("mid", {})
                candles.append({
                    "timestamp": datetime.fromisoformat(c["time"].replace("Z", "+00:00")),
                    "open": float(mid.get("o", 0)),
                    "high": float(mid.get("h", 0)),
                    "low": float(mid.get("l", 0)),
                    "close": float(mid.get("c", 0)),
                    "volume": float(c.get("volume", 0)),
                })
            return candles
        except Exception as e:
            print(f"[OANDA] Unexpected Error for {symbol}: {type(e).__name__} - {str(e)}. Falling back to mock data.")
            return await MockDataProvider().fetch_ohlcv(symbol, timeframe, limit)

    async def fetch_tick(self, symbol: str) -> dict:
        if not self.api_key:
            return await MockDataProvider().fetch_tick(symbol)

        instrument = self._map_symbol(symbol)
        url = f"{self.base_url}/accounts/{self.account_id}/pricing"
        params = {"instruments": instrument}

        try:
            client = await self._get_client()
            resp = await client.get(url, headers=self.headers, params=params)
            if resp.status_code != 200:
                print(f"[OANDA] Error fetching tick for {symbol}: {resp.text}")
                return await MockDataProvider().fetch_tick(symbol)

            data = resp.json()
            prices = data.get("prices", [])
            if not prices:
                return await MockDataProvider().fetch_tick(symbol)

            price = prices[0]
            # OANDA prices have multiple bids/asks; we'll take top one
            bid = float(price["bids"][0]["price"]) if price["bids"] else 0.0
            ask = float(price["asks"][0]["price"]) if price["asks"] else 0.0

            return {
                "symbol": symbol,
                "bid": bid,
                "ask": ask,
                "timestamp": datetime.fromisoformat(price["time"].replace("Z", "+00:00")),
            }
        except Exception as e:
            print(f"[OANDA] Error fetching tick for {symbol}: {e}. Falling back to mock.")
            return await MockDataProvider().fetch_tick(symbol)


class BinanceProvider(DataProvider):
    """Stub for Binance REST API integration."""

    async def fetch_ohlcv(self, symbol: str, timeframe: str = "H1", limit: int = 200) -> list[dict]:
        raise NotImplementedError("Binance integration not yet configured")

    async def fetch_tick(self, symbol: str) -> dict:
        raise NotImplementedError("Binance integration not yet configured")


# ── Factory (Singleton Pattern) ──────────────────────────────────────────────
_provider_instances: dict[str, DataProvider] = {}

def get_data_provider(provider: str = "oanda") -> DataProvider:
    """Returns a singleton instance of the requested market data provider."""
    global _provider_instances
    
    if provider not in _provider_instances:
        providers = {
            "oanda": OANDAProvider,
            "binance": BinanceProvider,
            "mock": MockDataProvider,
        }
        cls = providers.get(provider, OANDAProvider)
        _provider_instances[provider] = cls()
        
    return _provider_instances[provider]


# ── Indicator Helpers ────────────────────────────────────────────────────────

def compute_atr(candles: list[dict], period: int = 14) -> list[float]:
    """Compute Average True Range from OHLCV candles."""
    atrs = []
    for i, c in enumerate(candles):
        tr = c["high"] - c["low"]
        if i > 0:
            prev_close = candles[i - 1]["close"]
            tr = max(tr, abs(c["high"] - prev_close), abs(c["low"] - prev_close))
        atrs.append(tr)

    # Simple moving average of TR
    result = []
    for i in range(len(atrs)):
        if i < period - 1:
            result.append(sum(atrs[: i + 1]) / (i + 1))
        else:
            result.append(sum(atrs[i - period + 1: i + 1]) / period)
    return result


def compute_adx(candles: list[dict], period: int = 14) -> list[float]:
    """Compute Average Directional Index (simplified)."""
    if len(candles) < period + 1:
        return [25.0] * len(candles)  # Default neutral

    plus_dm = []
    minus_dm = []
    tr_list = []

    for i in range(1, len(candles)):
        high_diff = candles[i]["high"] - candles[i - 1]["high"]
        low_diff = candles[i - 1]["low"] - candles[i]["low"]

        plus_dm.append(max(high_diff, 0) if high_diff > low_diff else 0)
        minus_dm.append(max(low_diff, 0) if low_diff > high_diff else 0)

        tr = max(
            candles[i]["high"] - candles[i]["low"],
            abs(candles[i]["high"] - candles[i - 1]["close"]),
            abs(candles[i]["low"] - candles[i - 1]["close"]),
        )
        tr_list.append(tr)

    # Smoothed averages
    def smooth(data, n):
        result = [sum(data[:n]) / n]
        for val in data[n:]:
            result.append((result[-1] * (n - 1) + val) / n)
        return result

    if len(tr_list) < period:
        return [25.0] * len(candles)

    atr_s = smooth(tr_list, period)
    pdm_s = smooth(plus_dm, period)
    mdm_s = smooth(minus_dm, period)

    dx_list = []
    for a, p, m in zip(atr_s, pdm_s, mdm_s):
        if a == 0:
            dx_list.append(0)
            continue
        pdi = (p / a) * 100
        mdi = (m / a) * 100
        denom = pdi + mdi
        dx_list.append(abs(pdi - mdi) / denom * 100 if denom else 0)

    adx_vals = smooth(dx_list, period) if len(dx_list) >= period else dx_list

    # Pad to match candle count
    result = [25.0] + [round(v, 2) for v in adx_vals]
    while len(result) < len(candles):
        result.insert(0, result[0] if result else 25.0)
    return result[:len(candles)]


def compute_rsi(candles: list[dict], period: int = 14) -> list[float]:
    """Compute Relative Strength Index."""
    closes = [c["close"] for c in candles]
    if len(closes) < period + 1:
        return [50.0] * len(closes)

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsi_vals = [50.0] * period  # Pad initial values

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi_vals.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_vals.append(round(100 - (100 / (1 + rs)), 2))

    # Pad to match candle count
    rsi_vals.insert(0, rsi_vals[0] if rsi_vals else 50.0)
    while len(rsi_vals) < len(candles):
        rsi_vals.insert(0, 50.0)
    return rsi_vals[:len(candles)]


# ── VIL 2.0 Layer 1 Metrics ──────────────────────────────────────────────────

def compute_volatility_percentile(atr_history: list[float], lookback: int = 100) -> float:
    """Calculates the percentile rank of the current ATR vs historical values (0-100)."""
    if not atr_history:
        return 50.0
    
    current = atr_history[-1]
    window = atr_history[-lookback:] if len(atr_history) > lookback else atr_history
    
    if len(window) < 2:
        return 50.0
        
    count = sum(1 for x in window if x < current)
    return (count / len(window)) * 100


def compute_relative_volume(candles: list[dict], period: int = 20) -> float:
    """Compares current volume to the average volume (1.0 = normal, >2.0 = high)."""
    if len(candles) < period:
        return 1.0
        
    current_vol = candles[-1].get("volume", 0)
    recent_vols = [c.get("volume", 0) for c in candles[-(period+1):-1]]
    avg_vol = sum(recent_vols) / len(recent_vols) if recent_vols else 1.0
    
    return current_vol / avg_vol if avg_vol > 0 else 1.0


def get_session_state(utc_hour: int) -> dict:
    """Returns liquidity session state and classification."""
    state = {
        "session": "ASIAN",
        "liquidity": "LOW",
        "rank": 1
    }
    
    # ── Asian Session (21:00 - 06:00 UTC) ───────────────────
    if 21 <= utc_hour or utc_hour < 6:
        state = {"session": "ASIAN", "liquidity": "LOW", "rank": 1}
        
    # ── London Session (07:00 - 16:00 UTC) ──────────────────
    if 7 <= utc_hour < 16:
        state = {"session": "LONDON", "liquidity": "HIGH", "rank": 3}
        
    # ── New York Session (12:00 - 21:00 UTC) ────────────────
    if 12 <= utc_hour < 21:
        # NY Overlap with London is the highest liquidity
        if 12 <= utc_hour < 16:
            state = {"session": "OVERLAP (LDN/NY)", "liquidity": "MAX", "rank": 4}
        else:
            state = {"session": "NEW_YORK", "liquidity": "MEDIUM", "rank": 2}
            
    return state


def compute_ema(candles: list[dict], period: int = 14) -> list[float]:
    """Compute Exponential Moving Average."""
    closes = [c["close"] for c in candles]
    if len(closes) < period:
        return [closes[-1]] * len(closes) if closes else [0.0] * len(candles)

    ema = [sum(closes[:period]) / period]
    multiplier = 2 / (period + 1)
    
    for i in range(period, len(closes)):
        ema.append((closes[i] - ema[-1]) * multiplier + ema[-1])
        
    # Pad at start
    result = [ema[0]] * (period - 1) + ema
    return [round(v, 5) for v in result]


def compute_vwap(candles: list[dict]) -> list[float]:
    """Compute Volume Weighted Average Price."""
    vwaps = []
    cumulative_pv = 0.0
    cumulative_vol = 0.0
    
    for c in candles:
        tp = (c["high"] + c["low"] + c["close"]) / 3
        vol = c.get("volume", 1.0)
        cumulative_pv += tp * vol
        cumulative_vol += vol
        vwaps.append(cumulative_pv / cumulative_vol if cumulative_vol > 0 else tp)
        
    return [round(v, 5) for v in vwaps]
