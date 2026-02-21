import asyncio
import json
from app.services.broker_service import broker
from sqlalchemy import select, func
from app.db.database import async_session
from app.db.models import Trade

async def check_account_status():
    print("--- OANDA Account & VIL Trade Status ---")
    
    # 1. Get OANDA Account Summary
    summary = await broker.get_balance()
    if "error" in summary:
        print(f"Error fetching OANDA summary: {summary['error']}")
    else:
        print(f"\nOANDA Account Summary:")
        print(f" - Balance: ${summary['balance']:.2f}")
        print(f" - Equity (NAV): ${summary['equity']:.2f}")
        print(f" - Unrealized PnL: ${summary['unrealized_pnl']:.2f}")
        print(f" - Open Trade Count: {summary['open_trade_count']}")

    # 2. Get Trade History from OANDA
    history = await broker.get_transaction_history(limit=50)
    print(f"\nOANDA Transaction History (Closed Trades):")
    print(f" - Total Closed Trades found: {len(history)}")
    if history:
        total_realized_pnl = sum(t['realized_pnl'] for t in history)
        print(f" - Total Realized PnL (Recent 50): ${total_realized_pnl:.2f}")

    # 3. Check VIL Database Trades
    async with async_session() as session:
        count_res = await session.execute(select(func.count()).select_from(Trade))
        total_vil_trades = count_res.scalar()
        
        open_res = await session.execute(select(func.count()).select_from(Trade).where(Trade.status == "OPEN"))
        open_vil_trades = open_res.scalar()
        
        closed_res = await session.execute(select(func.count()).select_from(Trade).where(Trade.status != "OPEN"))
        closed_vil_trades = closed_res.scalar()

        print(f"\nVIL Database Statistics:")
        print(f" - Total VIL Managed Trades: {total_vil_trades}")
        print(f" - Currently Open in VIL: {open_vil_trades}")
        print(f" - Closed in VIL: {closed_vil_trades}")

if __name__ == "__main__":
    asyncio.run(check_account_status())
