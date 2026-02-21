import asyncio
import httpx

async def verify_broker_api():
    base_url = "http://localhost:8001/api" # VIL backend port
    
    # First, we might need to login if authentication is enforced
    # For this test, we'll assume there is a way to bypass or we'll just test the broker service directly
    from app.services.broker_service import broker
    
    print("--- Testing Broker Service Directly ---")
    account = await broker.get_account_details()
    print(f"Account: {account}")
    
    trades = await broker.get_open_trades()
    print(f"Open Trades: {len(trades)}")
    for t in trades:
        print(f"  - {t['symbol']} ID:{t['broker_order_id']} PnL:{t['unrealized_pnl']}")
    
    history = await broker.get_transaction_history(limit=5)
    print(f"History Trades: {len(history)}")
    for t in history:
        print(f"  - {t['symbol']} ID:{t['broker_order_id']} Realized:{t['realized_pnl']}")

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.getcwd())
    asyncio.run(verify_broker_api())
