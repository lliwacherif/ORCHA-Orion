# app/db/init_db.py
"""
Database initialization script.
Creates the database and all tables.
Run this once to set up your database.
"""
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
        # Drop all tables (uncomment if you want fresh start)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables created successfully!")
    
    await engine.dispose()

async def init_db():
    """Initialize database: create database and tables."""
    print("🔧 Initializing database...")
    await create_database()
    await create_tables()
    print("✅ Database initialization complete!")

if __name__ == "__main__":
    asyncio.run(init_db())















