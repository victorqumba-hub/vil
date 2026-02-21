import asyncio
from sqlalchemy import text
from app.db.database import engine, Base
from app.db.models import ModelRegistry, MLSignalDataset

async def migrate():
    print("--- Starting ML Phase 1 Migration ---")
    
    async with engine.begin() as conn:
        # 1. Add columns to 'signals' table
        print("Adding ML columns to 'signals' table...")
        cols_to_add = [
            ("ml_probability", "DOUBLE PRECISION"),
            ("ml_confidence", "DOUBLE PRECISION"),
            ("model_version", "VARCHAR(50)")
        ]
        
        for col_name, col_type in cols_to_add:
            try:
                await conn.execute(text(f"ALTER TABLE signals ADD COLUMN {col_name} {col_type};"))
                print(f" - Added {col_name}")
            except Exception as e:
                if "already exists" in str(e):
                    print(f" - {col_name} already exists, skipping.")
                else:
                    print(f" - Error adding {col_name}: {e}")

        # 2. Create new tables
        print("Creating new tables (model_registry, ml_signal_dataset)...")
        await conn.run_sync(Base.metadata.create_all)
        print(" - Tables created (if not existing)")

    print("\nSUCCESS: ML Phase 1 Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
