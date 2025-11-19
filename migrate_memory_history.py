"""
Migration script to update user_memories table for history support.

Changes:
1. Remove unique constraint on user_id
2. Add new columns: title, conversation_id, source, tags, is_active
3. Preserve existing data

Run this script: python migrate_memory_history.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import settings

async def migrate():
    """Migrate user_memories table to support history."""
    print("[MIGRATION] Starting user_memories migration for history support...")
    print(f"[INFO] Database URL: {settings.DATABASE_URL}")
    print()
    
    engine = create_async_engine(settings.DATABASE_URL)
    
    try:
        async with engine.begin() as conn:
            # Check if table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user_memories'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("[INFO] user_memories table doesn't exist yet - will be created fresh")
                print("[SUCCESS] No migration needed - table will be created with new schema")
                return
            
            print("[INFO] user_memories table exists - checking schema...")
            
            # Check if new columns already exist
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'user_memories' 
                AND column_name IN ('title', 'conversation_id', 'source', 'tags', 'is_active')
            """))
            existing_new_columns = {row[0] for row in result.fetchall()}
            
            if len(existing_new_columns) == 5:
                print("[INFO] Migration already applied - all new columns exist")
                print("[SUCCESS] No migration needed")
                return
            
            print(f"[INFO] Found {len(existing_new_columns)} new columns already exist")
            print("[INFO] Starting migration...")
            
            # Step 1: Drop unique constraint on user_id if it exists
            print("[1/6] Dropping unique constraint on user_id...")
            await conn.execute(text("""
                DO $$ 
                BEGIN
                    ALTER TABLE user_memories DROP CONSTRAINT IF EXISTS user_memories_user_id_key;
                EXCEPTION
                    WHEN undefined_object THEN
                        RAISE NOTICE 'Constraint does not exist, skipping';
                END $$;
            """))
            print("  [OK] Unique constraint removed")
            
            # Step 2: Add new columns if they don't exist
            print("[2/6] Adding new columns...")
            
            if 'title' not in existing_new_columns:
                await conn.execute(text("""
                    ALTER TABLE user_memories 
                    ADD COLUMN IF NOT EXISTS title VARCHAR(200)
                """))
                print("  [OK] Added 'title' column")
            
            if 'conversation_id' not in existing_new_columns:
                await conn.execute(text("""
                    ALTER TABLE user_memories 
                    ADD COLUMN IF NOT EXISTS conversation_id INTEGER REFERENCES conversations(id)
                """))
                print("  [OK] Added 'conversation_id' column")
            
            if 'source' not in existing_new_columns:
                await conn.execute(text("""
                    ALTER TABLE user_memories 
                    ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual' NOT NULL
                """))
                print("  [OK] Added 'source' column")
            
            if 'tags' not in existing_new_columns:
                await conn.execute(text("""
                    ALTER TABLE user_memories 
                    ADD COLUMN IF NOT EXISTS tags JSONB
                """))
                print("  [OK] Added 'tags' column")
            
            if 'is_active' not in existing_new_columns:
                await conn.execute(text("""
                    ALTER TABLE user_memories 
                    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL
                """))
                print("  [OK] Added 'is_active' column")
            
            # Step 3: Update existing records to have default values
            print("[3/6] Updating existing records with defaults...")
            await conn.execute(text("""
                UPDATE user_memories 
                SET source = 'legacy' 
                WHERE source IS NULL OR source = 'manual'
            """))
            await conn.execute(text("""
                UPDATE user_memories 
                SET is_active = TRUE 
                WHERE is_active IS NULL
            """))
            print("  [OK] Updated existing records")
            
            # Step 4: Create index on user_id for better query performance
            print("[4/6] Creating indexes...")
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_memories_user_id 
                ON user_memories(user_id)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_memories_created_at 
                ON user_memories(created_at DESC)
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_memories_is_active 
                ON user_memories(is_active)
            """))
            print("  [OK] Indexes created")
            
            # Step 5: Verify migration
            print("[5/6] Verifying migration...")
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'user_memories'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            print("  [OK] Current schema:")
            for col in columns:
                print(f"    - {col[0]}: {col[1]} (nullable: {col[2]})")
            
            # Step 6: Count existing memories
            print("[6/6] Counting existing memories...")
            result = await conn.execute(text("SELECT COUNT(*) FROM user_memories"))
            count = result.scalar()
            print(f"  [OK] Found {count} existing memory/memories")
            
        print()
        print("[SUCCESS] Migration completed successfully!")
        print()
        print("Next steps:")
        print("1. Restart your ORCHA server")
        print("2. Test the new memory endpoints")
        print("3. Existing memories have been preserved with source='legacy'")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())

