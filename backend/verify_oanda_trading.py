import asyncio
import logging
import sys
import os

# Add the current directory to sys.path to allow importing from 'app'
sys.path.append(os.getcwd())

from app.services.broker_service import broker
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_oanda_connection():
    print("--- OANDA Connectivity Test ---")
    print(f"Env: {settings.OANDA_ENV}")
    print(f"Account: {settings.OANDA_ACCOUNT_ID}")
    
    # 1. Check Balance
    balance_info = await broker.get_balance()
    if "error" in balance_info:
        print(f"FAILED to fetch balance: {balance_info['error']}")
        return
    
    print(f"SUCCESS: Balance = {balance_info['balance']}, Equity = {balance_info['equity']}")

    # 2. Place a small test order (1 unit of EUR/USD)
    print("\n--- Placing Test Order (1 unit EUR_USD) ---")
    # Fetch current price first to set reasonable SL/TP
    import httpx
    async with httpx.AsyncClient() as client:
        url = f"{broker.base_url}/accounts/{broker.account_id}/instruments/EUR_USD/candles?count=1&price=M&granularity=S5"
        resp = await client.get(url, headers=broker.headers)
        data = resp.json()
        current_price = float(data['candles'][0]['mid']['c'])
    
    print(f"Current EUR_USD Price: {current_price}")
    
    # Place Long with 50 pip SL/TP
    sl = current_price - 0.0050
    tp = current_price + 0.0050
    
    order_res = await broker.place_order(
        symbol="EUR_USD",
        direction="BUY",
        entry=current_price,
        stop_loss=sl,
        take_profit=tp,
        units=1
    )
    
    print(f"Order Status: {order_res.status}")
    print(f"Message: {order_res.message}")
    
    if order_res.status == "EXECUTED":
        print(f"Order ID: {order_res.order_id}")
        
    # 3. List Positions
    print("\n--- Open Positions ---")
    positions = await broker.get_positions()
    print(f"Found {len(positions)} position entries.")
    for pos in positions:
        print(f"Instrument: {pos.get('instrument')}, Long Units: {pos.get('long', {}).get('units')}, Short Units: {pos.get('short', {}).get('units')}")

if __name__ == "__main__":
    asyncio.run(test_oanda_connection())
