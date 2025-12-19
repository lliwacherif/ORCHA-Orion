#!/usr/bin/env python3
"""
Run database migrations using the app's database configuration.
Usage: python run_migration.py
"""
import asyncio
from sqlalchemy import text
from app.db.database import engine
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def run_admin_migration():
    """Run the admin table migration."""
    print("🚀 Running Admin Dashboard migration...")
    
    async with engine.begin() as conn:
        # Create admins table
        print("  Creating admins table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create index
        print("  Creating index...")
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username)
        """))
        
        # Check if admin user already exists
        result = await conn.execute(text("SELECT id FROM admins WHERE username = 'admin'"))
        existing = result.fetchone()
        
        if not existing:
            # Insert default admin user (password: admin)
            print("  Inserting default admin user (admin/admin)...")
            hashed_password = pwd_context.hash("admin")
            await conn.execute(
                text("INSERT INTO admins (username, hashed_password, is_active) VALUES (:username, :password, TRUE)"),
                {"username": "admin", "password": hashed_password}
            )
        else:
            print("  Default admin user already exists, skipping...")
        
        # Create or replace the admin_user_stats view
        print("  Creating admin_user_stats view...")
        await conn.execute(text("""
            CREATE OR REPLACE VIEW admin_user_stats AS
            SELECT 
                u.id,
                u.username,
                u.email,
                u.full_name,
                u.job_title,
                u.is_active,
                u.plan_type,
                u.created_at,
                COUNT(DISTINCT c.id) AS conversation_count,
                COUNT(DISTINCT cm.id) AS message_count,
                MAX(cm.created_at) AS last_activity
            FROM users u
            LEFT JOIN conversations c ON c.user_id = u.id AND c.is_active = TRUE
            LEFT JOIN chat_messages cm ON cm.conversation_id = c.id
            GROUP BY u.id, u.username, u.email, u.full_name, u.job_title, u.is_active, u.plan_type, u.created_at
            ORDER BY u.created_at DESC
        """))
        
        # Create trigger function for updated_at
        print("  Creating trigger function...")
        await conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_admin_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """))
        
        # Drop existing trigger if exists and create new one
        await conn.execute(text("DROP TRIGGER IF EXISTS trigger_update_admin_updated_at ON admins"))
        await conn.execute(text("""
            CREATE TRIGGER trigger_update_admin_updated_at
                BEFORE UPDATE ON admins
                FOR EACH ROW
                EXECUTE FUNCTION update_admin_updated_at()
        """))
        
    print("✅ Admin Dashboard migration completed successfully!")
    print("\n📝 Default credentials:")
    print("   Username: admin")
    print("   Password: admin")


if __name__ == "__main__":
    asyncio.run(run_admin_migration())

