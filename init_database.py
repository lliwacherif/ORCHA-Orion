"""
Standalone database initialization script.
Run this from the project root: python init_database.py
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.db.models import Base
from app.config import settings

async def create_database():
    """Create the orcha_db database if it doesn't exist."""
    # Connect to default 'postgres' database to create orcha_db
    default_db_url = settings.DATABASE_URL.replace('/orcha_db', '/postgres')
    engine = create_async_engine(default_db_url, isolation_level="AUTOCOMMIT")
    
    async with engine.connect() as conn:
        # Check if database exists
        result = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname='orcha_db'")
        )
        exists = result.scalar()
        
        if not exists:
            await conn.execute(text("CREATE DATABASE orcha_db"))
            print("✅ Database 'orcha_db' created successfully!")
        else:
            print("ℹ️  Database 'orcha_db' already exists")
    
    await engine.dispose()

async def create_tables():
    """Create all tables defined in models."""
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables created successfully!")
        print("   - users")
        print("   - token_usage")
    
    await engine.dispose()

async def init_db():
    """Initialize database: create database and tables."""
    print("🔧 Initializing database...")
    print(f"📍 Database URL: {settings.DATABASE_URL}")
    print()
    
    try:
        await create_database()
        await create_tables()
        print()
        print("✅ Database initialization complete!")
        print()
        print("You can now start the server:")
        print("  uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Make sure PostgreSQL is running")
        print("  2. Check username/password in app/config.py")
        print("  3. Verify postgres user password is '1234'")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(init_db())






