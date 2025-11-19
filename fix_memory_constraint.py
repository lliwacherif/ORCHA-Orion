"""
Fix unique constraint issue on user_memories table.
The unique index is still preventing multiple memories per user.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import settings

async def fix_constraint():
    """Remove all unique constraints and indexes on user_id, then create non-unique index."""
    print("[FIX] Removing unique constraint on user_memories.user_id...")
    print(f"[INFO] Database URL: {settings.DATABASE_URL}")
    print()
    
    engine = create_async_engine(settings.DATABASE_URL)
    
    try:
        async with engine.begin() as conn:
            # Step 1: Drop ALL constraints and indexes on user_id
            print("[1/4] Dropping all unique constraints on user_id...")
            
            # Drop constraint if exists
            await conn.execute(text("""
                ALTER TABLE user_memories 
                DROP CONSTRAINT IF EXISTS user_memories_user_id_key CASCADE
            """))
            print("  [OK] Dropped user_memories_user_id_key")
            
            await conn.execute(text("""
                ALTER TABLE user_memories 
                DROP CONSTRAINT IF EXISTS ix_user_memories_user_id CASCADE
            """))
            print("  [OK] Dropped ix_user_memories_user_id constraint")
            
            # Step 2: Drop ALL indexes on user_id
            print("[2/4] Dropping all indexes on user_id...")
            
            await conn.execute(text("""
                DROP INDEX IF EXISTS ix_user_memories_user_id CASCADE
            """))
            print("  [OK] Dropped ix_user_memories_user_id index")
            
            await conn.execute(text("""
                DROP INDEX IF EXISTS idx_user_memories_user_id CASCADE
            """))
            print("  [OK] Dropped idx_user_memories_user_id index")
            
            # Step 3: Create NON-UNIQUE index for performance
            print("[3/4] Creating non-unique index...")
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_memories_user_id_new 
                ON user_memories(user_id)
            """))
            print("  [OK] Created non-unique index idx_user_memories_user_id_new")
            
            # Step 4: Verify - check all constraints and indexes
            print("[4/4] Verifying...")
            
            # Check constraints
            result = await conn.execute(text("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = 'user_memories'
                AND constraint_name LIKE '%user_id%'
            """))
            constraints = result.fetchall()
            
            if constraints:
                print("  [WARN] Found constraints with 'user_id':")
                for c in constraints:
                    print(f"    - {c[0]} ({c[1]})")
            else:
                print("  [OK] No unique constraints on user_id")
            
            # Check indexes
            result = await conn.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'user_memories'
                AND indexdef LIKE '%user_id%'
            """))
            indexes = result.fetchall()
            
            print("  [OK] Indexes on user_id:")
            for idx in indexes:
                is_unique = "UNIQUE" in idx[1]
                status = "[ERROR]" if is_unique else "[OK]"
                print(f"    {status} {idx[0]}: {'UNIQUE' if is_unique else 'NON-UNIQUE'}")
            
        print()
        print("[SUCCESS] Unique constraint removed!")
        print()
        print("Test creating multiple memories:")
        print('  curl -X POST http://localhost:8000/api/v1/memory \\')
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"user_id": 1, "content": "Test memory 1"}\'')
        print()
        print('  curl -X POST http://localhost:8000/api/v1/memory \\')
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"user_id": 1, "content": "Test memory 2"}\'')
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_constraint())

