#!/usr/bin/env python3
"""
Database Migration: Add user_memories table

This migration adds the user_memories table for storing AI-extracted
user information and preferences.

Usage:
    python migrate_add_user_memory.py

Requirements:
    - PostgreSQL database running
    - Database credentials in .env file
"""

import asyncio
import sys
from sqlalchemy import text
from app.db.database import engine, AsyncSessionLocal
from app.config import settings


MIGRATION_SQLS = [
    # Create table
    """
    CREATE TABLE IF NOT EXISTS user_memories (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL UNIQUE,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_user_memory_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,
    # Create index
    "CREATE INDEX IF NOT EXISTS idx_user_memories_user_id ON user_memories(user_id)",
    # Add table comment
    "COMMENT ON TABLE user_memories IS 'Stores AI-extracted user memories and preferences for personalized conversations'",
    # Add column comment
    "COMMENT ON COLUMN user_memories.content IS 'AI-generated summary of user preferences, details, and important information'"
]

ROLLBACK_SQL = "DROP TABLE IF EXISTS user_memories CASCADE"


async def run_migration():
    """Execute the migration."""
    print("Starting User Memory migration...")
    print(f"Database: {settings.DATABASE_URL}")
    print()
    
    try:
        async with engine.begin() as conn:
            print("Executing migration SQL statements...")
            for i, sql in enumerate(MIGRATION_SQLS, 1):
                print(f"  [{i}/{len(MIGRATION_SQLS)}] Executing...")
                await conn.execute(text(sql))
            
            print()
            print("SUCCESS: Migration completed successfully!")
            print()
            print("Created:")
            print("   - user_memories table")
            print("   - idx_user_memories_user_id index")
            print("   - Foreign key constraint to users table")
            print("   - Table and column comments")
            print()
            
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def rollback_migration():
    """Rollback the migration."""
    print("Rolling back User Memory migration...")
    print(f"Database: {settings.DATABASE_URL}")
    print()
    
    try:
        async with engine.begin() as conn:
            print("Executing rollback SQL...")
            await conn.execute(text(ROLLBACK_SQL))
            print("SUCCESS: Rollback completed successfully!")
            print()
            
    except Exception as e:
        print(f"ERROR: Rollback failed: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def verify_migration():
    """Verify the migration was successful."""
    print("Verifying migration...")
    
    try:
        async with engine.begin() as conn:
            # Check if table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_memories'
                );
            """))
            exists = result.scalar()
            
            if exists:
                # Count records
                result = await conn.execute(text("SELECT COUNT(*) FROM user_memories"))
                count = result.scalar()
                
                print(f"SUCCESS: Table 'user_memories' exists")
                print(f"Current memory count: {count}")
                
                # Check indexes
                result = await conn.execute(text("""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename = 'user_memories'
                """))
                indexes = [row[0] for row in result.fetchall()]
                print(f"Indexes: {', '.join(indexes)}")
                
            else:
                print("ERROR: Table 'user_memories' does not exist!")
                sys.exit(1)
                
    except Exception as e:
        print(f"ERROR: Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def main():
    """Main migration script."""
    print("=" * 70)
    print("USER MEMORY TABLE MIGRATION")
    print("=" * 70)
    print()
    
    # Check for rollback flag
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        await rollback_migration()
    else:
        await run_migration()
        await verify_migration()
    
    print()
    print("=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)
    print()
    print("Next Steps:")
    print("   1. Test memory saving: POST /api/v1/memory")
    print("   2. Test memory retrieval: GET /api/v1/memory/{user_id}")
    print("   3. Verify memory is used in chat: Check logs for 'Loaded user memory'")
    print()
    print("   To rollback: python migrate_add_user_memory.py --rollback")
    print()


if __name__ == "__main__":
    asyncio.run(main())


