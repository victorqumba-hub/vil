import asyncio
import json
from app.services.broker_service import broker

async def get_details():
    trades = await broker.get_open_trades()
    print(json.dumps(trades, indent=2))

if __name__ == "__main__":
    asyncio.run(get_details())
