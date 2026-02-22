import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import os
import uuid
from urllib.parse import urlparse, unquote
import time

# CONFIGURATION
SQLITE_PATH = "../vildb.sqlite"
PG_URL = os.getenv("DATABASE_URL", "").replace("+asyncpg", "")

def get_pg_connection(hostname, database, username, password, port):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=hostname,
                database=database,
                user=username,
                password=password,
                port=port,
                sslmode='require',
                connect_timeout=10
            )
            conn.autocommit = True
            return conn
        except Exception as e:
            print(f"  Connection attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise e

def migrate():
    print("--- MIGRATION STARTING (Resilient) ---")
    if not PG_URL or "sqlite" in PG_URL:
        print("ERROR: Please set a valid PostgreSQL DATABASE_URL environment variable.")
        return

    print(f"Connecting to SQLite: {SQLITE_PATH}")
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    
    # Parse URL for explicit parameters
    result = urlparse(PG_URL)
    username = unquote(result.username) if result.username else ""
    password = unquote(result.password) if result.password else ""
    database = result.path[1:]
    hostname = result.hostname
    port = result.port or 5432

    print(f"Connecting to PostgreSQL (Sync) at {hostname}:{port}...")
    try:
        pg_conn = get_pg_connection(hostname, database, username, password, port)
        print("Connected successfully!")
    except Exception as e:
        print(f"PostgreSQL Connection Error: {e}")
        return
    
    # Tables to migrate (Ordered by dependency)
    tables = [
        "users",
        "broker_accounts",
        "refresh_tokens",
        "assets",
        "market_data",
        "signals",
        "signal_feature_snapshots",
        "signal_audit_events",
        "ai_reports",
        "trades",
        "model_registry",
        "ml_signal_dataset",
        "signal_forensic_analysis",
        "signal_intelligence_reports",
        "audit_logs"
    ]

    for table in tables:
        print(f"Migrating table: {table}...")
        try:
            cursor = sqlite_conn.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
        except Exception as e:
            print(f"  Error reading SQLite table {table}: {e}")
            continue
        
        if not rows:
            print(f"  No data in {table}.")
            continue

        columns = rows[0].keys()
        col_list = list(columns)
        col_names = ", ".join([f'"{c}"' for c in col_list])
        placeholders = ", ".join(["%s"] * len(col_list))
        
        insert_stmt = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
        
        # Prepare data for batch insert
        batch_data = []
        for row in rows:
            data = dict(row)
            values = []
            for col in col_list:
                val = data[col]
                
                # Convert 0/1 to True/False ONLY for columns that are BOOLEAN in Postgres
                is_boolean = False
                if table == 'users' and col in ['is_verified', 'is_active', 'is_locked']:
                    is_boolean = True
                elif table == 'refresh_tokens' and col == 'is_revoked':
                    is_boolean = True
                elif table == 'broker_accounts' and col == 'is_active':
                    is_boolean = True
                elif col in ['regime_shift_during_trade', 'volume_spike_flag']:
                    is_boolean = True
                
                if is_boolean and val is not None:
                    val = bool(val)
                
                # Convert hex strings to UUIDs
                if (col == 'id' or col.endswith('_id')) and isinstance(val, str) and len(val) >= 32:
                    try:
                        val = str(uuid.UUID(val))
                    except ValueError:
                        pass
                
                values.append(val)
            batch_data.append(tuple(values))

        # Perform batch insert
        print(f"  Inserting {len(batch_data)} rows in batches...")
        try:
            with pg_conn.cursor() as pg_cur:
                execute_batch(pg_cur, insert_stmt, batch_data, page_size=100)
            print(f"  Successfully migrated {len(batch_data)} rows to {table}.")
        except Exception as e:
            print(f"  Batch Error in {table}: {e}")
            # Reconnect if connection was lost
            if "closed" in str(e).lower() or "terminated" in str(e).lower():
                print("  Connection lost. Attempting to reconnect...")
                try:
                    pg_conn = get_pg_connection(hostname, database, username, password, port)
                except:
                    print("  Failed to reconnect. Skipping remaining tables.")
                    break

    print("\nMigration Complete!")
    pg_conn.close()
    sqlite_conn.close()

if __name__ == "__main__":
    migrate()
