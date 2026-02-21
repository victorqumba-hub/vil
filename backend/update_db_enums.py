import asyncio
from sqlalchemy import text
from app.db.database import engine

async def update_enums():
    # 1. LifecycleStatus Enums
    lifecycle_enums = [
        'CREATED', 'VALIDATED', 'PENDING', 'QUEUED', 'ACTIVE', 
        'SUCCESS', 'FAILED', 'EXPIRED', 'DROPPED', 'SUPPRESSED',
        'EXPIRED_REGIME_SHIFT', 'EXPIRED_SCORE_DECAY', 'CANCELLED', 'ARCHIVED'
    ]
    
    # 2. MarketRegime Enums
    regime_enums = [
        'TRENDING_BULLISH', 'TRENDING_BEARISH', 'RANGING_WIDE', 'RANGING_NARROW',
        'VOLATILITY_EXPANSION', 'HIGH_VOLATILITY', 'UNSTABLE', 'EVENT_RISK',
        'TRENDING', 'RANGING', 'LOW_ACTIVITY'
    ]

    async def add_values(type_name, values):
        print(f"Checking enum type: {type_name}")
        for val in values:
            async with engine.begin() as conn:
                try:
                    await conn.execute(text(f"ALTER TYPE {type_name} ADD VALUE '{val}'"))
                    print(f"  [+] Added {val} to {type_name}")
                except Exception as e:
                    if "already exists" in str(e):
                        print(f"  [.] {val} already exists in {type_name}, skipping.")
                    else:
                        print(f"  [!] Error adding {val} to {type_name}: {e}")

    await add_values('lifecyclestatus', lifecycle_enums)
    await add_values('marketregime', regime_enums)

if __name__ == "__main__":
    asyncio.run(update_enums())
