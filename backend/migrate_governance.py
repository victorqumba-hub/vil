import asyncio
import logging
from sqlalchemy import text
from app.db.database import async_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate():
    """Apply institutional governance schema changes."""
    
    # 1. Columns for signals table
    signal_columns = [
        ("valid_from", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("valid_until", "TIMESTAMP"),
        ("entry_window_until", "TIMESTAMP"),
        ("expiration_reason", "VARCHAR(100)"),
        ("score_at_expiration", "DOUBLE PRECISION"),
        ("regime_at_expiration", "VARCHAR(50)"),
        ("signal_group_id", "UUID"),
        ("signal_version", "INTEGER DEFAULT 1"),
        ("decay_rate", "DOUBLE PRECISION"),
        ("archived_at", "TIMESTAMP")
    ]
    
    async with async_session() as session:
        # Update tables and columns
        logger.info("Starting institutional governance migration...")
        
        # Check existing columns in 'signals'
        res = await session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'signals'
        """))
        existing_signal_columns = {row[0] for row in res.fetchall()}
        
        for col_name, col_type in signal_columns:
            if col_name not in existing_signal_columns:
                logger.info(f"Adding column '{col_name}' to 'signals' table...")
                try:
                    await session.execute(text(f"ALTER TABLE signals ADD COLUMN {col_name} {col_type}"))
                except Exception as e:
                    logger.error(f"Error adding '{col_name}': {e}")
            else:
                logger.info(f"Column '{col_name}' already exists in 'signals'.")

        # Create signal_feature_snapshots table
        logger.info("Creating 'signal_feature_snapshots' table if not exists...")
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS signal_feature_snapshots (
                id UUID PRIMARY KEY,
                signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,
                regime_state VARCHAR(50),
                volatility_percentile DOUBLE PRECISION,
                atr DOUBLE PRECISION,
                session VARCHAR(20),
                liquidity_sweep_flag INTEGER,
                spread_at_creation DOUBLE PRECISION,
                event_proximity_score DOUBLE PRECISION,
                structural_break_type VARCHAR(50),
                correlation_snapshot TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create signal_audit_events table
        logger.info("Creating 'signal_audit_events' table if not exists...")
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS signal_audit_events (
                id UUID PRIMARY KEY,
                signal_id UUID NOT NULL REFERENCES signals(id) ON DELETE CASCADE,
                previous_state VARCHAR(50),
                new_state VARCHAR(50),
                reason VARCHAR(255),
                triggered_by VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Add indexes for performance
        logger.info("Adding indexes for performance...")
        indices = [
            ("idx_signals_valid_until", "signals(valid_until)"),
            ("idx_signals_signal_group_id", "signals(signal_group_id)"),
            ("idx_feature_snapshots_signal_id", "signal_feature_snapshots(signal_id)"),
            ("idx_audit_events_signal_id", "signal_audit_events(signal_id)")
        ]
        
        for idx_name, idx_def in indices:
            try:
                await session.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}"))
            except Exception as e:
                logger.warning(f"Could not create index {idx_name}: {e}")

        await session.commit()
        logger.info("Institutional governance migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
