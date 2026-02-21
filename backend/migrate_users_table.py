
import asyncio
from sqlalchemy import text
from app.db.database import async_session

async def migrate():
    print("--- Starting Users Table Migration ---")
    async with async_session() as db:
        try:
            # Define columns to add
            to_add = {
                "full_name": "ALTER TABLE users ADD COLUMN full_name VARCHAR(200)",
                "display_name": "ALTER TABLE users ADD COLUMN display_name VARCHAR(100)",
                "phone": "ALTER TABLE users ADD COLUMN phone VARCHAR(30)",
                "country": "ALTER TABLE users ADD COLUMN country VARCHAR(100)",
                "is_verified": "ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE",
                "is_active": "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE",
                "is_locked": "ALTER TABLE users ADD COLUMN is_locked BOOLEAN DEFAULT FALSE",
                "verification_token": "ALTER TABLE users ADD COLUMN verification_token VARCHAR(255)",
                "terms_accepted_at": "ALTER TABLE users ADD COLUMN terms_accepted_at TIMESTAMP WITHOUT TIME ZONE",
                "account_type": "ALTER TABLE users ADD COLUMN account_type accounttype DEFAULT 'DEMO' NOT NULL",
                "role": "ALTER TABLE users ADD COLUMN role userrole DEFAULT 'USER' NOT NULL",
                "failed_login_attempts": "ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0 NOT NULL",
                "locked_until": "ALTER TABLE users ADD COLUMN locked_until TIMESTAMP WITHOUT TIME ZONE",
                "last_login_at": "ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP WITHOUT TIME ZONE",
                "last_login_ip": "ALTER TABLE users ADD COLUMN last_login_ip VARCHAR(45)"
            }

            # Create Enum Types if they don't exist
            try:
                await db.execute(text("DROP TYPE IF EXISTS accounttype CASCADE"))
                await db.execute(text("CREATE TYPE accounttype AS ENUM ('DEMO', 'LIVE')"))
                await db.commit()
                print("Created type: accounttype")
            except Exception as e:
                await db.rollback()
                print(f"Failed to recreate accounttype: {e}")
            
            try:
                await db.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
                await db.execute(text("CREATE TYPE userrole AS ENUM ('USER', 'ADMIN', 'SUPER_ADMIN')"))
                await db.commit()
                print("Created type: userrole")
            except Exception as e:
                await db.rollback()
                print(f"Failed to recreate userrole: {e}")

            # NOW check existing columns
            result = await db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND table_schema = 'public'"))
            existing_columns = [row[0] for row in result.fetchall()]
            print(f"Existing columns: {existing_columns}")

            for col, sql in to_add.items():
                if col not in existing_columns:
                    print(f"Adding column: {col}")
                    await db.execute(text(sql))
                else:
                    print(f"Column already exists: {col}")

            await db.commit()
            print("--- Migration Completed Successfully ---")
        except Exception as e:
            print(f"Migration failed: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(migrate())
