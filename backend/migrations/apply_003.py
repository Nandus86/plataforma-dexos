
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.database import engine

async def apply_migration():
    sql_file = os.path.join(os.path.dirname(__file__), '003_add_break_to_class_group.sql')
    print(f"Applying migration from {sql_file}...")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    try:
        statements = sql.split('-- STATEMENT_END')
        
        async with engine.begin() as conn:
            for stmt in statements:
                stmt = stmt.strip()
                if not stmt:
                    continue
                    
                print(f"Executing: {stmt[:50]}...")
                await conn.execute(text(stmt))
                
            print("Migration applied successfully.")
    except Exception as e:
        print(f"Error applying migration: {e}")

if __name__ == "__main__":
    asyncio.run(apply_migration())
