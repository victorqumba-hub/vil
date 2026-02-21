import asyncio
import logging
from sqlalchemy import text
from app.db.database import async_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate():
    """Add missing execution columns to the signals table."""
    columns_to_add = [
        ("broker_order_id", "VARCHAR(50)"),
        ("execution_price", "DOUBLE PRECISION"),
        ("executed_at", "TIMESTAMP"),
        ("execution_mode", "VARCHAR(20) DEFAULT 'AUTO'"),
        ("execution_source", "VARCHAR(50) DEFAULT 'OANDA_API'")
    ]
    
    async with async_session() as session:
        # Check existing columns first to avoid errors
        result = await session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'signals'
        """))
        existing_columns = {row[0] for row in result.fetchall()}
        
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                logger.info(f"Adding column '{col_name}' to 'signals' table...")
                try:
                    await session.execute(text(f"ALTER TABLE signals ADD COLUMN {col_name} {col_type}"))
                    logger.info(f"Successfully added '{col_name}'.")
                except Exception as e:
                    logger.error(f"Error adding '{col_name}': {e}")
            else:
                logger.info(f"Column '{col_name}' already exists.")
        
        await session.commit()
        logger.info("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
