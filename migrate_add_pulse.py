#!/usr/bin/env python3
"""
Database migration script to add the Pulse table.
Run this to update your database schema with the new Pulse feature.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings
from app.db.models import Base, Pulse
from app.db.database import engine

async def migrate_database():
    """Create the Pulse table in the database."""
    print("🔄 Starting database migration for Pulse feature...")
    
    try:
        # Create the Pulse table
        async with engine.begin() as conn:
            # Create only the Pulse table (not all tables)
            await conn.run_sync(Pulse.__table__.create, checkfirst=True)
        
        print("✅ Pulse table created successfully!")
        print("\n📋 Migration complete!")
        print("\nYou can now:")
        print("  - Use GET /api/v1/pulse/{user_id} to get user's pulse")
        print("  - Use POST /api/v1/pulse/{user_id}/regenerate to regenerate pulse")
        print("  - Pulses will auto-generate every 24 hours")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(migrate_database())
