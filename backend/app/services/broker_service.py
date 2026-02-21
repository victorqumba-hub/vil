"""OANDA Broker Service — Executes trades on OANDA.

Provides an interface for order placement, management, and account status using OANDA v20 API.
"""

import httpx
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

@dataclass
class OrderResult:
    order_id: str
    symbol: str
    direction: str
    entry: float
    stop_loss: float
    take_profit: float
    units: int
    status: str
    executed_at: str
    message: str

class OandaBroker:
    """OANDA API Integration."""

    def __init__(self):
        self.api_key = settings.OANDA_API_KEY
        self.account_id = settings.OANDA_ACCOUNT_ID
        self.env = settings.OANDA_ENV
        
        if self.env == "live":
            self.base_url = "https://api-fxtrade.oanda.com/v3"
        else:
            self.base_url = "https://api-fxpractice.oanda.com/v3"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, headers=self.headers, json=data, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"OANDA API Error: {e.response.status_code} - {e.response.text}")
                return {"error": e.response.text, "status_code": e.response.status_code}
            except Exception as e:
                logger.error(f"OANDA Request Exception: {e}")
                return {"error": str(e)}

    async def place_order(
        self,
        symbol: str,
        direction: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        units: int,
    ) -> OrderResult:
        """
        Place a Market Order on OANDA.
        OANDA units: Positive for Long, Negative for Short.
        """
        # Format symbol for OANDA (e.g., EUR_USD)
        oanda_symbol = symbol.replace("/", "_")
        
        # Determine units direction
        oanda_units = str(units) if direction == "BUY" else str(-units)

        order_payload = {
            "order": {
                "units": oanda_units,
                "instrument": oanda_symbol,
                "timeInForce": "FOK",
                "type": "MARKET",
                "positionFill": "DEFAULT",
                "stopLossOnFill": {"price": f"{stop_loss:.5f}"},
                "takeProfitOnFill": {"price": f"{take_profit:.5f}"},
            }
        }

        endpoint = f"/accounts/{self.account_id}/orders"
        result = await self._request("POST", endpoint, order_payload)

        if "error" in result:
            return OrderResult(
                order_id="",
                symbol=symbol,
                direction=direction,
                entry=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                units=units,
                status="FAILED",
                executed_at=datetime.utcnow().isoformat(),
                message=f"FAILED: {result.get('error')}",
            )

        # Handle successful transaction
        # OANDA returns a 'orderFillTransaction' if it fills immediately
        fill = result.get("orderFillTransaction", {})
        order_id = fill.get("id", "UNKNOWN")
        price = float(fill.get("price", entry))

        return OrderResult(
            order_id=order_id,
            symbol=symbol,
            direction=direction,
            entry=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            units=units,
            status="EXECUTED",
            executed_at=datetime.utcnow().isoformat(),
            message=f"OANDA order placed: {direction} {units} units {symbol} @ {price}",
        )

    async def get_balance(self) -> dict:
        """Get account summary metrics."""
        endpoint = f"/accounts/{self.account_id}/summary"
        result = await self._request("GET", endpoint)
        
        if "error" in result:
            return {"balance": 0.0, "error": result["error"]}
        
        account = result.get("account", {})
        return {
            "balance": float(account.get("balance", 0.0)),
            "equity": float(account.get("NAV", 0.0)),
            "unrealized_pnl": float(account.get("unrealizedPL", 0.0)),
            "margin_used": float(account.get("marginUsed", 0.0)),
            "margin_available": float(account.get("marginAvailable", 0.0)),
            "margin_level": float(account.get("marginCallPercent", 0.0)) * 100, # Approximation or use another field
            "open_trade_count": account.get("openTradeCount", 0),
        }

    async def get_account_details(self) -> dict:
        """Alias for get_balance with full detail mapping."""
        return await self.get_balance()

    async def get_open_trades(self) -> list:
        """Get list of currently open trades with floating PnL."""
        endpoint = f"/accounts/{self.account_id}/openTrades"
        result = await self._request("GET", endpoint)
        trades = result.get("trades", [])
        
        # Map OANDA fields to VIL format
        formatted_trades = []
        for t in trades:
            formatted_trades.append({
                "broker_order_id": str(t["id"]),
                "symbol": t["instrument"].replace("_", "/"),
                "units": int(t["currentUnits"]),
                "direction": "BUY" if int(t["currentUnits"]) > 0 else "SELL",
                "entry_price": float(t["price"]),
                "current_price": None, # Will be filled if pricing requested
                "stop_loss": float(t.get("stopLossOrder", {}).get("price", 0)),
                "take_profit": float(t.get("takeProfitOrder", {}).get("price", 0)),
                "unrealized_pnl": float(t["unrealizedPL"]),
                "margin_used": float(t.get("marginUsed", 0)),
                "open_time": t["openTime"],
                "status": "OPEN"
            })
        return formatted_trades

    async def get_transaction_history(self, limit: int = 50) -> list:
        """Get recent transaction history to find closed trades."""
        # OANDA transactions are a stream. We'll poll the recent ones.
        # This is a bit simplified; real system might use transaction ID range.
        endpoint = f"/accounts/{self.account_id}/transactions/sinceid?id=1" # Placeholder logic
        # For simplicity, we'll use a different endpoint or filter trades
        # Most practical for a dashboard is probably 'trades' with state=CLOSED
        endpoint = f"/accounts/{self.account_id}/trades?state=CLOSED&count={limit}"
        result = await self._request("GET", endpoint)
        trades = result.get("trades", [])
        
        formatted_history = []
        for t in trades:
            formatted_history.append({
                "broker_order_id": str(t["id"]),
                "symbol": t["instrument"].replace("_", "/"),
                "units": int(t["initialUnits"]),
                "direction": "BUY" if int(t["initialUnits"]) > 0 else "SELL",
                "entry_price": float(t["price"]),
                "exit_price": float(t.get("averageClosePrice", 0)),
                "realized_pnl": float(t.get("realizedPL", 0)),
                "open_time": t["openTime"],
                "close_time": t.get("closeTime"),
                "status": "CLOSED"
            })
        return formatted_history

    async def get_positions(self) -> list:
        endpoint = f"/accounts/{self.account_id}/positions"
        result = await self._request("GET", endpoint)
        return result.get("positions", [])

# Singleton
broker = OandaBroker()
