
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.database import engine

async def fix_enums():
    # Commands to rename enum values from UPPERCASE (old) to lowercase (new Portuguese)
    cmds = [
        "ALTER TYPE nonschooldayreason RENAME VALUE 'SATURDAY' TO 'sabado'",
        "ALTER TYPE nonschooldayreason RENAME VALUE 'SUNDAY' TO 'domingo'",
        "ALTER TYPE nonschooldayreason RENAME VALUE 'HOLIDAY' TO 'feriado'",
        "ALTER TYPE nonschooldayreason RENAME VALUE 'EVENT' TO 'evento'",
        "ALTER TYPE nonschooldayreason RENAME VALUE 'OTHER' TO 'outro'"
        # 'recesso' (lowercase) was presumably added correctly in migration 002
    ]
    
    # We use a connection per command because ALTER TYPE cannot run inside a transaction block 
    # in some contexts, or we want to isolate failures.
    # However, engine.begin() starts a transaction. 
    # ALTER TYPE RENAME VALUE is generally transactional.
    
    print("Starting Enum migration...")
    
    async with engine.connect() as conn:
        for cmd in cmds:
            try:
                print(f"Executing: {cmd}")
                # We need to commit each change if we want isolation, but let's try auto-commit behavior or simple execution
                await conn.execute(text(cmd))
                await conn.commit()
                print("Success.")
            except Exception as e:
                # Expect errors if values are already renamed or don't exist
                print(f"Error (safe to ignore if already migrated): {e}")
                await conn.rollback()

if __name__ == "__main__":
    asyncio.run(fix_enums())
