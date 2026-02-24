
import asyncio
import os
import sys

# Add project root to path to allow imports from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.database import engine

async def apply_migration():
    sql_file = os.path.join(os.path.dirname(__file__), '002_add_advanced_period_features.sql')
    print(f"Applying migration from {sql_file}...")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    try:
        # Split statements by custom delimiter
        statements = sql.split('-- STATEMENT_END')
        
        async with engine.begin() as conn:
            for stmt in statements:
                stmt = stmt.strip()
                if not stmt:
                    continue
                    
                print(f"Executing: {stmt[:50]}...")
                # Execute each statement individually
                await conn.execute(text(stmt))
                
            print("Migration applied successfully.")
    except Exception as e:
        print(f"Error applying migration: {e}")

if __name__ == "__main__":
    asyncio.run(apply_migration())
